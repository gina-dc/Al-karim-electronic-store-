from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.business import InventoryItem, Payment, Receipt, WorkerEarning
from app.schemas.business import ReceiptInput
from app.services.common import today, total
from app.services.receipts import create_receipt
from app.services.reporting import report_data


def repair_payload():
    return ReceiptInput(
        transaction_type="repair",
        transaction_date=today(),
        post=True,
        initial_payment="5000",
        items=[
            {
                "name": "موٹر مرمت / Motor repair / Ahmed ki motor",
                "quantity": 1,
                "unit_price": "15000",
            }
        ],
    )


async def test_atomic_post_and_advance_is_not_revenue(owner):
    result = await create_receipt(repair_payload(), uuid4(), owner)
    assert result["status"] == "posted"
    assert Decimal(result["paid"]) == 5000
    report = await report_data()
    assert Decimal(report["kpis"]["revenue"]) == 0
    assert Decimal(report["kpis"]["cash_received"]) == 5000
    assert Decimal(report["kpis"]["advances"]) == 5000
    item = await InventoryItem.create(
        code="empty",
        name="Empty stock",
        category="Motor",
        condition="used",
        selling_price="10",
    )
    invalid = ReceiptInput(
        transaction_type="sale",
        transaction_date=today(),
        post=True,
        initial_payment="1",
        items=[
            {
                "inventory_id": item.id,
                "name": "Empty stock",
                "quantity": 1,
                "unit_price": "10",
            }
        ],
    )
    with pytest.raises(HTTPException):
        await create_receipt(invalid, uuid4(), owner)
    assert await Receipt.all().count() == 1
    assert await Payment.all().count() == 1


async def test_worker_earnings_partial_payments_and_reports(owner_client):
    client, owner = owner_client
    receipt = await create_receipt(repair_payload(), uuid4(), owner)
    worker = (
        await client.post(
            "/api/v1/workers",
            json={
                "code": "W01",
                "name": "احمد",
                "specialization": "Motor repair",
                "joining_date": str(today()),
            },
        )
    ).json()
    response = await client.post(
        "/api/v1/jobs",
        json={
            "receipt_item_id": receipt["items"][0]["id"],
            "worker_id": worker["id"],
            "description": "Repair winding",
            "assigned_date": str(today()),
            "labor_amount": "1500",
        },
    )
    assert response.status_code == 201, response.text
    job = response.json()
    assert await WorkerEarning.all().count() == 0
    for _ in range(2):
        assert (
            await client.patch(
                f"/api/v1/jobs/{job['id']}/status", json={"status": "completed"}
            )
        ).status_code == 200
    assert await WorkerEarning.all().count() == 1
    assert await total(WorkerEarning.all()) == 1500
    assert (
        await client.post(f"/api/v1/receipts/{receipt['id']}/complete")
    ).status_code == 200
    key = str(uuid4())
    payload = {
        "worker_id": worker["id"],
        "amount": "500",
        "payment_date": str(today()),
        "method": "cash",
    }
    for _ in range(2):
        response = await client.post(
            "/api/v1/worker-payments", json=payload, headers={"Idempotency-Key": key}
        )
        assert response.status_code == 201, response.text
    statement = (await client.get(f"/api/v1/workers/{worker['id']}/statement")).json()
    assert Decimal(statement["payable"]) == 1000
    response = await client.post(
        "/api/v1/worker-payments",
        json={**payload, "amount": "1001"},
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert response.status_code == 409
    report = (await client.get("/api/v1/reports")).json()
    assert Decimal(report["kpis"]["revenue"]) == 15000
    assert Decimal(report["kpis"]["labor_cost"]) == 1500
    assert Decimal(report["kpis"]["gross_profit"]) == 13500
    assert Decimal(report["kpis"]["advances"]) == 0


async def test_purchase_is_inventory_not_revenue(owner):
    item = await InventoryItem.create(
        code="M1",
        name="Motor",
        category="Motor",
        condition="used",
        selling_price="3000",
    )
    purchase = ReceiptInput(
        transaction_type="purchase",
        transaction_date=today(),
        post=True,
        items=[
            {
                "inventory_id": item.id,
                "name": "Motor",
                "quantity": 2,
                "unit_price": "1000",
            }
        ],
    )
    await create_receipt(purchase, uuid4(), owner)
    report = await report_data()
    assert Decimal(report["kpis"]["revenue"]) == 0
    assert Decimal(report["kpis"]["costs"]) == 0
    assert Decimal(report["kpis"]["inventory_cost"]) == 2000
    sale = purchase.model_copy(
        update={
            "transaction_type": "sale",
            "items": [
                purchase.items[0].model_copy(
                    update={"quantity": 1, "unit_price": Decimal(3000)}
                )
            ],
        }
    )
    await create_receipt(sale, uuid4(), owner)
    report = await report_data()
    assert Decimal(report["kpis"]["revenue"]) == 3000
    assert Decimal(report["kpis"]["gross_profit"]) == 2000
    assert Decimal(report["kpis"]["inventory_cost"]) == 1000


async def test_urdu_pdf_contains_embedded_font_and_renders(owner):
    from pathlib import Path

    import pymupdf

    from app.documents.receipts import receipt_pdf
    from app.models.business import Customer, ShopSettings

    await ShopSettings.create(
        id=1,
        name_ur="الکریم الیکٹرک سروس",
        address_ur="اظہر کلینک کے سامنے، ممتاز آباد، ملتان",
        phone="03017458983 / 03346141413",
    )
    customer = await Customer.create(
        name="احمد / Ahmed", phone="03001234567", address="ملتان / Multan"
    )
    payload = repair_payload().model_copy(update={"customer_id": customer.id})
    data = await create_receipt(payload, uuid4(), owner)
    receipt = await Receipt.get(id=data["id"])
    pdf = await receipt_pdf(receipt)
    assert pdf.startswith(b"%PDF")
    document = pymupdf.open(stream=pdf, filetype="pdf")
    assert len(document) == 1
    assert "Electronics Shop" in document[0].get_text()
    assert "Motor repair" in document[0].get_text()
    assert "Ahmed" in document[0].get_text()
    assert "03001234567" in document[0].get_text()
    assert "Multan" in document[0].get_text()
    assert "03017458983" in document[0].get_text()
    assert "03346141413" in document[0].get_text()
    assert any("NotoNaskh" in str(font) for font in document[0].get_fonts())
    pixmap = document[0].get_pixmap()
    output = Path("../.runtime")
    output.mkdir(exist_ok=True)
    (output / "receipt-urdu.pdf").write_bytes(pdf)
    pixmap.save(str(output / "receipt-urdu.png"))
    assert len(pdf) > 10000


async def test_payment_reversal_and_void_preserve_history(owner_client):
    client, owner = owner_client
    receipt = await create_receipt(repair_payload(), uuid4(), owner)
    payment = await Payment.get(receipt_id=receipt["id"])
    response = await client.post(
        f"/api/v1/receipts/{receipt['id']}/void",
        json={"reason": "Incorrect duplicate receipt"},
    )
    assert response.status_code == 409
    for _ in range(2):
        response = await client.post(
            f"/api/v1/payments/{payment.id}/reverse",
            json={"reason": "Incorrect duplicate payment"},
        )
        assert response.status_code == 200, response.text
    assert await Payment.filter(receipt_id=receipt["id"]).count() == 2
    assert await total(Payment.filter(receipt_id=receipt["id"])) == 0
    assert (
        await client.post(
            f"/api/v1/receipts/{receipt['id']}/void",
            json={"reason": "Incorrect duplicate receipt"},
        )
    ).status_code == 200
    assert (await Receipt.get(id=receipt["id"])).status == "void"
    next_receipt = await create_receipt(repair_payload(), uuid4(), owner)
    assert int(next_receipt["number"]) > int(receipt["number"])


async def test_void_restores_original_inventory_lots(owner_client):
    from app.models.business import StockLot, StockMovement

    client, owner = owner_client
    item = await InventoryItem.create(
        code="M1",
        name="Motor",
        category="Motor",
        condition="used",
        selling_price="3000",
    )
    payload = ReceiptInput(
        transaction_type="purchase",
        transaction_date=today(),
        post=True,
        items=[
            {
                "inventory_id": item.id,
                "name": "Motor",
                "quantity": 2,
                "unit_price": "1000",
            }
        ],
    )
    purchase = await create_receipt(payload, uuid4(), owner)
    sale = await create_receipt(
        payload.model_copy(update={"transaction_type": "sale"}), uuid4(), owner
    )
    await item.refresh_from_db()
    assert item.quantity == 0
    response = await client.post(
        f"/api/v1/receipts/{sale['id']}/void",
        json={"reason": "Sale was entered in error"},
    )
    assert response.status_code == 200, response.text
    await item.refresh_from_db()
    assert item.quantity == 2 and item.availability == "available"
    assert await total(StockLot.filter(inventory=item), "quantity") == 2
    assert await StockMovement.filter(kind="void_correction").count() == 1
    assert (
        await client.post(
            f"/api/v1/receipts/{purchase['id']}/void",
            json={"reason": "Purchase entered in error"},
        )
    ).status_code == 200
    await item.refresh_from_db()
    assert item.quantity == 0


async def test_staff_cannot_read_owner_financial_reports(owner_client):
    client, owner = owner_client
    owner.role = "staff"
    await owner.save()
    assert (await client.get("/api/v1/reports")).status_code == 403
    assert (await client.get("/api/v1/reports/export.csv")).status_code == 403
    assert (await client.get("/api/v1/users")).status_code == 403
    assert (
        await client.put("/api/v1/settings", json={"name": "Unauthorized"})
    ).status_code == 403
    assert (await client.get("/api/v1/dashboard")).status_code == 200
    assert "kpis" not in (await client.get("/api/v1/dashboard")).json()


async def test_receipt_filters_and_report_exports(owner_client):
    client, owner = owner_client
    receipt = await create_receipt(repair_payload(), uuid4(), owner)
    response = await client.get("/api/v1/receipts?payment_status=partial&sort=-total")
    assert response.status_code == 200, response.text
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == receipt["id"]
    response = await client.get("/api/v1/receipts?payment_status=paid")
    assert response.status_code == 200, response.text
    assert response.json()["total"] == 0
    for kind in [
        "summary",
        "dues",
        "payroll",
        "expenses",
        "inventory",
        "jobs",
        "movements",
        "worker_payments",
    ]:
        response = await client.get(f"/api/v1/reports/export.csv?kind={kind}")
        assert response.status_code == 200, response.text
        assert "text/csv" in response.headers["content-type"]
    response = await client.get("/api/v1/reports/export.pdf")
    assert response.status_code == 200 and response.content.startswith(b"%PDF")


async def test_inventory_summary_and_last_owner_protection(owner_client):
    client, owner = owner_client
    response = await client.get("/api/v1/inventory-summary")
    assert response.status_code == 200
    assert response.json()["units"] == 0
    assert "acquisition_cost" in response.json()
    response = await client.patch(
        f"/api/v1/users/{owner.id}",
        json={"display_name": "Owner", "role": "staff", "active": True},
    )
    assert response.status_code == 409
    await owner.refresh_from_db()
    assert owner.role == "owner"
    owner.role = "staff"
    await owner.save()
    response = await client.get("/api/v1/inventory-summary")
    assert response.status_code == 200
    assert "acquisition_cost" not in response.json()
