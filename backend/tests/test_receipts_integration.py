import asyncio
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.auth import User
from app.models.business import InventoryItem, Payment, Receipt, StockMovement
from app.schemas.business import PaymentInput, ReceiptInput
from app.services.common import today, total
from app.services.receipts import (
    create_receipt,
    post_receipt,
    receipt_data,
    record_payment,
)


@pytest.fixture
async def owner(db):
    return await User.create(
        username="owner",
        display_name="Owner",
        role="owner",
        password_hash="test-only-unused",
    )


def repair():
    return ReceiptInput(
        transaction_type="repair",
        transaction_date=today(),
        items=[{"name": "Motor repair", "quantity": 1, "unit_price": "15000.00"}],
    )


async def test_concurrent_numbers_and_idempotency(owner):
    results = await asyncio.gather(
        *(create_receipt(repair(), uuid4(), owner) for _ in range(8))
    )
    assert len({r["number"] for r in results}) == 8
    key = uuid4()
    repeated = await asyncio.gather(
        *(create_receipt(repair(), key, owner) for _ in range(3))
    )
    assert len({r["id"] for r in repeated}) == 1
    assert await Receipt.all().count() == 9


async def test_partial_payments_and_concurrent_duplicate(owner):
    data = await create_receipt(repair(), uuid4(), owner)
    await post_receipt(data["id"], owner)
    payload = PaymentInput(
        receipt_id=data["id"], amount="5000", payment_date=today(), method="cash"
    )
    key = uuid4()
    await asyncio.gather(*(record_payment(payload, key, owner) for _ in range(3)))
    assert await Payment.all().count() == 1
    assert await total(Payment.all()) == Decimal(5000)
    receipt = await Receipt.get(id=data["id"])
    assert (await receipt_data(receipt))["balance"] == "10000.00"
    await record_payment(
        payload.model_copy(update={"amount": Decimal(10000)}), uuid4(), owner
    )
    result = await receipt_data(receipt)
    assert Decimal(result["balance"]) == 0 and result["payment_status"] == "paid"
    with pytest.raises(HTTPException):
        await record_payment(payload, uuid4(), owner)


async def test_stock_posting_and_rollback(owner):
    item = await InventoryItem.create(
        code="M1",
        name="Motor",
        category="Motor",
        condition="used",
        selling_price="2000",
    )
    purchase = ReceiptInput(
        transaction_type="purchase",
        transaction_date=today(),
        items=[
            {
                "inventory_id": item.id,
                "name": "Motor",
                "quantity": 2,
                "unit_price": "1000",
            }
        ],
    )
    data = await create_receipt(purchase, uuid4(), owner)
    await post_receipt(data["id"], owner)
    sale = purchase.model_copy(update={"transaction_type": "sale"})
    data = await create_receipt(sale, uuid4(), owner)
    await asyncio.gather(*(post_receipt(data["id"], owner) for _ in range(2)))
    await item.refresh_from_db()
    assert item.quantity == 0
    assert await StockMovement.filter(kind="sold").count() == 1
    assert (await Receipt.get(id=data["id"])).status == "posted"
    failed = await create_receipt(sale, uuid4(), owner)
    with pytest.raises(HTTPException):
        await post_receipt(failed["id"], owner)
    assert (await Receipt.get(id=failed["id"])).status == "draft"
    assert await StockMovement.filter(kind="sold").count() == 1
