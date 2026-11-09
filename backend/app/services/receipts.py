from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid5

from fastapi import HTTPException
from tortoise.transactions import in_transaction

from app.models.auth import AuditLog
from app.models.business import (
    Customer,
    InventoryItem,
    Payment,
    Receipt,
    ReceiptItem,
    ReceiptSequence,
    StockLot,
    StockMovement,
)
from app.schemas.business import PaymentInput
from app.services.common import (
    digest,
    get_record,
    idempotent,
    record_data,
    total,
    valid_date,
)


async def receipt_data(receipt):
    data = record_data(receipt)
    data["items"] = [
        record_data(item)
        for item in await ReceiptItem.filter(receipt=receipt).order_by(
            "created_at", "id"
        )
    ]
    paid = await total(Payment.filter(receipt=receipt))
    due = Decimal(0) if receipt.status == "void" else receipt.total - paid
    data.update(
        paid=str(paid),
        balance=str(due),
        payment_status="paid" if not due else "unpaid" if not paid else "partial",
    )
    data["customer"] = (
        record_data(await Customer.get(id=receipt.customer_id))
        if receipt.customer_id
        else None
    )
    return data


async def create_receipt(payload, key, user):
    valid_date(payload.transaction_date, user)
    async with in_transaction() as conn:
        existing = await idempotent(Receipt, key, payload)
        if existing:
            if existing.created_by_id != user.id:
                raise HTTPException(409, "Idempotency key is already in use")
            return await receipt_data(existing)
        if payload.customer_id:
            await get_record(Customer, payload.customer_id)
        for item in payload.items:
            if item.inventory_id:
                await get_record(InventoryItem, item.inventory_id)
        await conn.execute_query("SELECT pg_advisory_xact_lock(81234002)")
        seq, _ = await ReceiptSequence.get_or_create(
            name="receipt", defaults={"value": 0}
        )
        seq.value += 1
        await seq.save()
        receipt = await Receipt.create(
            number=f"{seq.value:06d}",
            customer_id=payload.customer_id,
            transaction_type=payload.transaction_type,
            transaction_date=payload.transaction_date,
            total=sum((i.unit_price * i.quantity for i in payload.items), Decimal(0)),
            notes=payload.notes,
            work_description=payload.work_description,
            created_by=user,
            idempotency_key=key,
            request_hash=digest(payload),
        )
        for item in payload.items:
            await ReceiptItem.create(receipt=receipt, **item.model_dump())
        await AuditLog.create(
            user=user, action="receipt.create", details={"receipt": str(receipt.id)}
        )
        if payload.post:
            await post_receipt(receipt.id, user)
            if payload.initial_payment:
                await record_payment(
                    PaymentInput(
                        receipt_id=receipt.id,
                        amount=payload.initial_payment,
                        payment_date=payload.transaction_date,
                        method=payload.payment_method,
                    ),
                    uuid5(key, "initial-payment"),
                    user,
                )
            await receipt.refresh_from_db()
        return await receipt_data(receipt)


async def post_receipt(receipt_id, user):
    async with in_transaction():
        receipt = await get_record(Receipt, receipt_id, lock=True)
        if receipt.status == "posted":
            return await receipt_data(receipt)
        if receipt.status != "draft":
            raise HTTPException(409, "Only a draft can be posted")
        items = await ReceiptItem.filter(receipt=receipt).order_by("inventory_id", "id")
        for line in items:
            if receipt.transaction_type == "repair":
                continue
            inventory = await get_record(InventoryItem, line.inventory_id, lock=True)
            if receipt.transaction_type == "sale":
                if (
                    inventory.availability != "available"
                    or inventory.quantity < line.quantity
                ):
                    raise HTTPException(409, "Insufficient available stock")
                left, cost = line.quantity, Decimal(0)
                lots = (
                    await StockLot.filter(
                        inventory=inventory,
                        quantity__gt=0,
                        purchase_date__lte=receipt.transaction_date,
                    )
                    .select_for_update()
                    .order_by("purchase_date", "created_at", "id")
                )
                allocations = []
                for lot in lots:
                    take = min(left, lot.quantity)
                    lot.quantity -= take
                    left -= take
                    cost += take * lot.unit_cost
                    allocations.append({"lot_id": str(lot.id), "quantity": take})
                    await lot.save()
                    if not left:
                        break
                if left:
                    raise HTTPException(409, "Inventory cost ledger does not reconcile")
                inventory.quantity -= line.quantity
                if not inventory.quantity:
                    inventory.availability = "sold"
                line.cost_total = cost
                line.cost_allocations = allocations
                await line.save()
                await StockMovement.create(
                    inventory=inventory,
                    receipt_item=line,
                    kind="sold",
                    quantity=-line.quantity,
                    cost=-cost,
                    recorded_by=user,
                )
            else:
                if inventory.serial_number and (
                    inventory.quantity or line.quantity != 1
                ):
                    raise HTTPException(
                        409, "Serialized equipment must have a single unit"
                    )
                inventory.quantity += line.quantity
                if inventory.availability == "sold":
                    inventory.availability = "available"
                await StockLot.create(
                    inventory=inventory,
                    receipt_item=line,
                    quantity=line.quantity,
                    unit_cost=line.unit_price,
                    purchase_date=receipt.transaction_date,
                )
                await StockMovement.create(
                    inventory=inventory,
                    receipt_item=line,
                    kind="received",
                    quantity=line.quantity,
                    cost=line.quantity * line.unit_price,
                    recorded_by=user,
                )
            await inventory.save()
        receipt.status = "posted"
        receipt.posted_at = datetime.now(UTC)
        await receipt.save()
        await AuditLog.create(
            user=user, action="receipt.post", details={"receipt": str(receipt.id)}
        )
        return await receipt_data(receipt)


async def record_payment(payload, key, user):
    valid_date(payload.payment_date, user)
    async with in_transaction():
        existing = await idempotent(Payment, key, payload)
        if existing:
            if existing.recorded_by_id != user.id:
                raise HTTPException(409, "Idempotency key is already in use")
            return record_data(existing)
        receipt = await get_record(Receipt, payload.receipt_id, lock=True)
        if receipt.status != "posted":
            raise HTTPException(409, "Only posted receipts accept payments")
        if payload.payment_date < receipt.transaction_date:
            raise HTTPException(422, "Payment date cannot precede the receipt")
        if payload.amount > receipt.total - await total(
            Payment.filter(receipt=receipt)
        ):
            raise HTTPException(409, "Payment exceeds remaining balance")
        payment = await Payment.create(
            **payload.model_dump(),
            recorded_by=user,
            idempotency_key=key,
            request_hash=digest(payload),
        )
        await AuditLog.create(
            user=user, action="payment.record", details={"payment": str(payment.id)}
        )
        return record_data(payment)
