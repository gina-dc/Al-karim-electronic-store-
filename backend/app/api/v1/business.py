from datetime import UTC, date, datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from tortoise.expressions import F, Q
from tortoise.functions import Coalesce, Sum
from tortoise.transactions import in_transaction

from app.models.auth import AuditLog, Session
from app.models.business import (
    Customer,
    InventoryItem,
    Payment,
    Receipt,
    ReceiptItem,
    StockLot,
    StockMovement,
    WorkerJob,
)
from app.schemas.business import (
    CustomerInput,
    InventoryInput,
    PaymentInput,
    ReasonInput,
    ReceiptInput,
)
from app.security.dependencies import current_session
from app.services.common import get_record, record_data, require_role, total
from app.services.receipts import (
    create_receipt,
    post_receipt,
    receipt_data,
    record_payment,
)

router = APIRouter(tags=["Business operations"])
Auth = Annotated[Session, Depends(current_session)]
Key = Annotated[UUID, Header(alias="Idempotency-Key")]


def permitted_receipt(receipt, user):
    if receipt.transaction_type == "purchase":
        require_role(user, "owner", "manager")


def visible_receipt(data, user):
    if user.role != "owner":
        for item in data["items"]:
            item.pop("cost_total", None)
            item.pop("cost_allocations", None)
    return data


@router.get("/customers")
async def customers(
    session: Auth,
    search: str = Query(default="", max_length=150),
    sort: Literal["name", "-name", "created_at", "-created_at"] = "-created_at",
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    query = Customer.filter(Q(name__icontains=search) | Q(phone__icontains=search))
    return {
        "total": await query.count(),
        "items": [
            record_data(r)
            for r in await query.order_by(sort, "id").offset(offset).limit(limit)
        ],
    }


@router.post("/customers", status_code=201)
async def customer_create(payload: CustomerInput, session: Auth):
    async with in_transaction():
        customer = await Customer.create(**payload.model_dump())
        await AuditLog.create(
            user=session.user,
            action="customer.create",
            details={"id": str(customer.id)},
        )
    return record_data(customer)


@router.patch("/customers/{record_id}")
async def customer_edit(record_id: UUID, payload: CustomerInput, session: Auth):
    async with in_transaction():
        customer = await get_record(Customer, record_id, lock=True)
        customer.update_from_dict(payload.model_dump())
        await customer.save()
        await AuditLog.create(
            user=session.user,
            action="customer.update",
            details={"id": str(customer.id)},
        )
    return record_data(customer)


@router.get("/customers/{record_id}/history")
async def customer_history(record_id: UUID, session: Auth):
    customer = await get_record(Customer, record_id)
    receipts = Receipt.filter(customer=customer)
    if session.user.role == "staff":
        receipts = receipts.exclude(transaction_type="purchase")
    return {
        "customer": record_data(customer),
        "receipts": [
            visible_receipt(await receipt_data(r), session.user)
            for r in await receipts.order_by("-transaction_date").limit(100)
        ],
    }


@router.get("/inventory")
async def inventory_list(
    session: Auth,
    search: str = Query("", max_length=150),
    sort: Literal[
        "code", "-code", "name", "-name", "created_at", "-created_at"
    ] = "-created_at",
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    query = InventoryItem.filter(Q(name__icontains=search) | Q(code__icontains=search))
    return {
        "total": await query.count(),
        "items": [
            record_data(r)
            for r in await query.order_by(sort, "id").offset(offset).limit(limit)
        ],
    }


@router.post("/inventory", status_code=201)
async def inventory_create(payload: InventoryInput, session: Auth):
    require_role(session.user, "owner", "manager")
    async with in_transaction():
        item = await InventoryItem.create(**payload.model_dump())
        await AuditLog.create(
            user=session.user, action="inventory.create", details={"id": str(item.id)}
        )
    return record_data(item)


@router.patch("/inventory/{record_id}")
async def inventory_update(record_id: UUID, payload: InventoryInput, session: Auth):
    require_role(session.user, "owner", "manager")
    async with in_transaction():
        item = await get_record(InventoryItem, record_id, lock=True)
        if payload.serial_number and item.quantity > 1:
            raise HTTPException(409, "Bulk stock cannot become a serialized unit")
        if payload.serial_number != item.serial_number:
            raise HTTPException(
                409, "Serial identity cannot be changed; create a separate item"
            )
        old_condition = item.condition
        old_availability = item.availability
        if payload.availability == "sold" and item.quantity:
            raise HTTPException(409, "Only empty inventory can be marked sold")
        item.update_from_dict(payload.model_dump())
        await item.save()
        if old_availability != item.availability:
            await StockMovement.create(
                inventory=item,
                kind="reserved"
                if item.availability == "reserved"
                else "released"
                if old_availability == "reserved"
                else "availability_changed",
                quantity=0,
                notes=f"{old_availability} -> {item.availability}; stock quantity: {item.quantity}",
                recorded_by=session.user,
            )
        if old_condition != item.condition:
            await StockMovement.create(
                inventory=item,
                kind="repaired"
                if item.condition == "repaired"
                else "condition_changed",
                quantity=0,
                notes=f"{old_condition} -> {item.condition}",
                recorded_by=session.user,
            )
        await AuditLog.create(
            user=session.user, action="inventory.update", details={"id": str(item.id)}
        )
    return record_data(item)


@router.get("/inventory/{record_id}/movements")
async def inventory_movements(record_id: UUID, session: Auth):
    require_role(session.user, "owner", "manager")
    await get_record(InventoryItem, record_id)
    return [
        record_data(r)
        for r in await StockMovement.filter(inventory_id=record_id)
        .order_by("-created_at")
        .limit(200)
    ]


@router.get("/receipts")
async def receipts(
    session: Auth,
    search: str = Query("", max_length=150),
    transaction_type: Literal["sale", "repair", "purchase"] | None = None,
    payment_status: Literal["unpaid", "partial", "paid"] | None = None,
    status: Literal["draft", "posted", "void"] | None = None,
    customer_id: UUID | None = None,
    sort: Literal[
        "number",
        "-number",
        "transaction_date",
        "-transaction_date",
        "total",
        "-total",
        "-created_at",
    ] = "-created_at",
    start: date | None = None,
    end: date | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    query = Receipt.filter(
        Q(number__icontains=search) | Q(customer__name__icontains=search)
    )
    if session.user.role == "staff":
        query = query.exclude(transaction_type="purchase")
    if transaction_type:
        query = query.filter(transaction_type=transaction_type)
    if customer_id:
        query = query.filter(customer_id=customer_id)
    if status:
        query = query.filter(status=status)
    if payment_status:
        query = query.exclude(status="void")
        query = query.annotate(paid_total=Coalesce(Sum("payments__amount"), 0))
        if payment_status == "paid":
            query = query.filter(paid_total=F("total"))
        elif payment_status == "unpaid":
            query = query.filter(paid_total=0, total__gt=0)
        else:
            query = query.filter(paid_total__gt=0, paid_total__lt=F("total"))
    if start:
        query = query.filter(transaction_date__gte=start)
    if end:
        query = query.filter(transaction_date__lte=end)
    return {
        "total": await query.count(),
        "items": [
            visible_receipt(await receipt_data(r), session.user)
            for r in await query.order_by(sort, "id").offset(offset).limit(limit)
        ],
    }


@router.post("/receipts", status_code=201)
async def receipt_create(payload: ReceiptInput, session: Auth, key: Key):
    if payload.transaction_type == "purchase":
        require_role(session.user, "owner", "manager")
    return visible_receipt(
        await create_receipt(payload, key, session.user), session.user
    )


@router.get("/receipts/{record_id}")
async def receipt_get(record_id: UUID, session: Auth):
    receipt = await get_record(Receipt, record_id)
    permitted_receipt(receipt, session.user)
    return visible_receipt(await receipt_data(receipt), session.user)


@router.put("/receipts/{record_id}")
async def receipt_edit(record_id: UUID, payload: ReceiptInput, session: Auth):
    from app.services.common import valid_date

    valid_date(payload.transaction_date, session.user)
    if payload.post or payload.initial_payment:
        raise HTTPException(422, "Edit a draft first, then use the posting endpoint")
    if payload.transaction_type == "purchase":
        require_role(session.user, "owner", "manager")
    async with in_transaction():
        receipt = await get_record(Receipt, record_id, lock=True)
        permitted_receipt(receipt, session.user)
        if receipt.status != "draft":
            raise HTTPException(409, "Only drafts can be edited")
        if payload.customer_id:
            await get_record(Customer, payload.customer_id)
        for item in payload.items:
            if item.inventory_id:
                await get_record(InventoryItem, item.inventory_id)
        receipt.update_from_dict(
            payload.model_dump(
                exclude={"items", "post", "initial_payment", "payment_method"}
            )
        )
        receipt.total = sum(i.unit_price * i.quantity for i in payload.items)
        await receipt.save()
        await ReceiptItem.filter(receipt=receipt).delete()
        for item in payload.items:
            await ReceiptItem.create(receipt=receipt, **item.model_dump())
        await AuditLog.create(
            user=session.user, action="receipt.edit", details={"id": str(receipt.id)}
        )
    return visible_receipt(await receipt_data(receipt), session.user)


@router.post("/receipts/{record_id}/post")
async def receipt_post(record_id: UUID, session: Auth):
    receipt = await get_record(Receipt, record_id)
    permitted_receipt(receipt, session.user)
    return visible_receipt(await post_receipt(record_id, session.user), session.user)


@router.post("/receipts/{record_id}/complete")
async def complete_repair(record_id: UUID, session: Auth):
    async with in_transaction():
        receipt = await get_record(Receipt, record_id, lock=True)
        if receipt.status != "posted" or receipt.transaction_type != "repair":
            raise HTTPException(409, "A posted repair receipt is required")
        if (
            await WorkerJob.filter(receipt_item__receipt=receipt)
            .exclude(status__in=["completed", "cancelled"])
            .exists()
        ):
            raise HTTPException(409, "Finish assigned worker jobs first")
        if not receipt.completed_at:
            receipt.completed_at = datetime.now(UTC)
            await receipt.save()
            await AuditLog.create(
                user=session.user,
                action="repair.complete",
                details={"id": str(receipt.id)},
            )
    return visible_receipt(await receipt_data(receipt), session.user)


@router.post("/receipts/{record_id}/void")
async def receipt_void(record_id: UUID, payload: ReasonInput, session: Auth):
    require_role(session.user, "owner")
    async with in_transaction():
        receipt = await get_record(Receipt, record_id, lock=True)
        if receipt.status == "void":
            return visible_receipt(await receipt_data(receipt), session.user)
        if receipt.status == "posted":
            if await total(Payment.filter(receipt=receipt)):
                raise HTTPException(
                    409,
                    "Reverse erroneous payments before voiding; customer refunds are not supported",
                )
            if (
                await WorkerJob.filter(receipt_item__receipt=receipt)
                .exclude(status="cancelled")
                .exists()
            ):
                raise HTTPException(
                    409, "Receipts with active or earned worker jobs cannot be voided"
                )
            for line in await ReceiptItem.filter(receipt=receipt).order_by(
                "inventory_id", "id"
            ):
                if receipt.transaction_type == "repair":
                    continue
                item = await get_record(InventoryItem, line.inventory_id, lock=True)
                if receipt.transaction_type == "sale":
                    if item.serial_number and item.quantity:
                        raise HTTPException(
                            409,
                            "Serialized stock already exists; correction requires investigation",
                        )
                    if not line.cost_allocations:
                        raise HTTPException(
                            409, "Historical cost allocations are unavailable"
                        )
                    for allocation in line.cost_allocations:
                        lot = await get_record(
                            StockLot, allocation["lot_id"], lock=True
                        )
                        lot.quantity += allocation["quantity"]
                        await lot.save()
                    item.quantity += line.quantity
                    if item.availability == "sold":
                        item.availability = "available"
                    delta, cost = line.quantity, line.cost_total
                else:
                    lot = (
                        await StockLot.filter(receipt_item=line)
                        .select_for_update()
                        .first()
                    )
                    if not lot or lot.quantity != line.quantity:
                        raise HTTPException(
                            409,
                            "Purchased stock has already been used; purchase cannot be voided",
                        )
                    lot.quantity = 0
                    await lot.save()
                    item.quantity -= line.quantity
                    delta, cost = -line.quantity, -line.quantity * line.unit_price
                await item.save()
                await StockMovement.create(
                    inventory=item,
                    receipt_item=line,
                    kind="void_correction",
                    quantity=delta,
                    cost=cost,
                    notes=payload.reason,
                    recorded_by=session.user,
                )
        receipt.status, receipt.void_reason = "void", payload.reason
        await receipt.save()
        await AuditLog.create(
            user=session.user,
            action="receipt.void",
            details={"id": str(receipt.id), "reason": payload.reason},
        )
    return visible_receipt(await receipt_data(receipt), session.user)


@router.get("/payments")
async def payment_list(
    session: Auth,
    receipt_id: UUID | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    query = Payment.all()
    if receipt_id:
        query = query.filter(receipt_id=receipt_id)
    if session.user.role == "staff":
        query = query.exclude(receipt__transaction_type="purchase")
    rows = []
    for payment in (
        await query.select_related("receipt")
        .order_by("-created_at")
        .offset(offset)
        .limit(limit)
    ):
        rows.append(
            {
                **record_data(payment),
                "receipt_number": payment.receipt.number,
                "transaction_type": payment.receipt.transaction_type,
            }
        )
    return {"total": await query.count(), "items": rows}


@router.post("/payments", status_code=201)
async def payment_create(payload: PaymentInput, session: Auth, key: Key):
    receipt = await get_record(Receipt, payload.receipt_id)
    permitted_receipt(receipt, session.user)
    return await record_payment(payload, key, session.user)


@router.get("/receipts/{record_id}/pdf")
async def download_receipt(record_id: UUID, session: Auth):
    from fastapi.responses import Response

    from app.documents.receipts import receipt_pdf

    receipt = await get_record(Receipt, record_id)
    permitted_receipt(receipt, session.user)
    return Response(
        await receipt_pdf(receipt),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="receipt-{receipt.number}.pdf"'
        },
    )


@router.post("/payments/{record_id}/reverse")
async def payment_reverse(record_id: UUID, payload: ReasonInput, session: Auth):
    from uuid import uuid5

    from app.models.business import PaymentReversal
    from app.services.common import digest, today

    require_role(session.user, "owner")
    async with in_transaction():
        initial = await get_record(Payment, record_id)
        await get_record(Receipt, initial.receipt_id, lock=True)
        payment = await get_record(Payment, record_id, lock=True)
        existing = await PaymentReversal.filter(original=payment).first()
        if existing:
            if existing.reason != payload.reason:
                raise HTTPException(409, "Payment is already reversed")
            return record_data(await Payment.get(id=existing.correction_id))
        if payment.amount <= 0:
            raise HTTPException(409, "A reversal cannot itself be reversed")
        correction = await Payment.create(
            receipt_id=payment.receipt_id,
            amount=-payment.amount,
            payment_date=today(),
            method=payment.method,
            reference=payment.reference,
            notes=payload.reason,
            recorded_by=session.user,
            idempotency_key=uuid5(payment.id, "reversal"),
            request_hash=digest(payload),
        )
        await PaymentReversal.create(
            original=payment, correction=correction, reason=payload.reason
        )
        await AuditLog.create(
            user=session.user,
            action="payment.reverse",
            details={"id": str(payment.id), "reason": payload.reason},
        )
    return record_data(correction)


@router.get("/inventory-summary")
async def inventory_summary(session: Auth):
    from collections import defaultdict
    from decimal import Decimal

    conditions = defaultdict(int)
    availability = defaultdict(int)
    estimated = Decimal(0)
    items = await InventoryItem.all()
    for item in items:
        conditions[item.condition] += item.quantity
        availability[item.availability] += item.quantity
        estimated += item.quantity * item.selling_price
    sold = await total(
        ReceiptItem.filter(receipt__status="posted", receipt__transaction_type="sale"),
        "quantity",
    )
    data = {
        "records": len(items),
        "units": sum(i.quantity for i in items),
        "conditions": dict(conditions),
        "availability": dict(availability),
        "sold_units": int(sold),
    }
    if session.user.role == "owner":
        data["acquisition_cost"] = str(
            sum(
                (lot.quantity * lot.unit_cost for lot in await StockLot.all()),
                Decimal(0),
            )
        )
        data["estimated_selling_value"] = str(estimated)
    return data
