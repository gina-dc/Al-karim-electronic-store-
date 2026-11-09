import csv
from datetime import date
from io import StringIO

from fastapi import APIRouter, Query
from fastapi.responses import Response
from tortoise.transactions import in_transaction

from app.api.v1.business import Auth, Key
from app.models.auth import AuditLog
from app.models.business import Expense, Receipt
from app.schemas.business import ExpenseInput
from app.services.common import (
    digest,
    get_record,
    idempotent,
    record_data,
    require_role,
    valid_date,
)
from app.services.reporting import report_data

router = APIRouter(tags=["Reports"])


@router.get("/reports")
async def reports(session: Auth, start: date | None = None, end: date | None = None):
    require_role(session.user, "owner")
    return await report_data(start, end)


@router.get("/dashboard")
async def dashboard(session: Auth, start: date | None = None, end: date | None = None):
    if session.user.role == "owner":
        return await report_data(start, end)
    return {
        "pending_repairs": await Receipt.filter(
            status="posted", transaction_type="repair", completed_at=None
        ).count(),
        "drafts": await Receipt.filter(status="draft").count(),
    }


@router.post("/expenses", status_code=201)
async def expense_create(payload: ExpenseInput, session: Auth, key: Key):
    require_role(session.user, "owner")
    valid_date(payload.expense_date)
    if payload.receipt_id:
        await get_record(Receipt, payload.receipt_id)
    async with in_transaction():
        existing = await idempotent(Expense, key, payload)
        if existing:
            return record_data(existing)
        expense = await Expense.create(
            **payload.model_dump(),
            recorded_by=session.user,
            idempotency_key=key,
            request_hash=digest(payload),
        )
        await AuditLog.create(
            user=session.user, action="expense.create", details={"id": str(expense.id)}
        )
    return record_data(expense)


def safe_cell(value):
    text = str(value)
    return "'" + text if text.startswith(("=", "+", "-", "@", "\t", "\r")) else text


@router.get("/reports/export.csv")
async def export_csv(
    session: Auth,
    start: date | None = None,
    end: date | None = None,
    kind: str = Query(
        "summary",
        pattern="^(summary|dues|payroll|expenses|inventory|jobs|movements|worker_payments)$",
    ),
):
    require_role(session.user, "owner")
    data = await report_data(start, end)
    rows = (
        [{"metric": key, "value": value} for key, value in data["kpis"].items()]
        if kind == "summary"
        else data[kind]
    )
    output = StringIO()
    if rows:
        columns = list(rows[0])
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(
            {key: safe_cell(value) for key, value in row.items()} for row in rows
        )
    return Response(
        "\ufeff" + output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{kind}-{data["start"]}-{data["end"]}.csv"'
        },
    )


@router.get("/reports/export.pdf")
async def export_pdf(session: Auth, start: date | None = None, end: date | None = None):
    from app.documents.base import Document
    from app.models.business import ShopSettings

    require_role(session.user, "owner")
    data = await report_data(start, end)
    settings, _ = await ShopSettings.get_or_create(id=1)
    doc = Document("کاروباری رپورٹ / Business report", settings)
    doc.line(f"{data['start']} — {data['end']}")
    for key, value in data["kpis"].items():
        doc.line(f"{key.replace('_', ' ').title()}: {value}")
    doc.line("گاہکوں کا بقایا / Customer dues", 14)
    for row in data["dues"]:
        doc.line(f"{row['number']} — {row['customer']} — {row['balance']} PKR", 10)
    doc.line("کاریگروں کا بقایا / Worker payables", 14)
    for row in data["payroll"]:
        doc.line(f"{row['name']} — {row['payable']} PKR", 10)
    return Response(
        doc.finish(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="report-{data["start"]}-{data["end"]}.pdf"'
        },
    )
