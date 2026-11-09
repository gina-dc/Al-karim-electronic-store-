from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.api.v1.business import Auth, Key
from app.models.auth import AuditLog
from app.models.business import (
    Receipt,
    ReceiptItem,
    Worker,
    WorkerEarning,
    WorkerJob,
    WorkerPayment,
)
from app.schemas.business import (
    JobInput,
    JobStatusInput,
    WorkerInput,
    WorkerPaymentInput,
)
from app.services.common import (
    digest,
    get_record,
    idempotent,
    record_data,
    require_role,
    today,
    total,
    valid_date,
)

router = APIRouter(tags=["Workforce"])


@router.get("/workers")
async def workers(
    session: Auth,
    search: str = Query("", max_length=150),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    query = Worker.filter(Q(name__icontains=search) | Q(code__icontains=search))
    return {
        "total": await query.count(),
        "items": [
            record_data(r)
            for r in await query.order_by("name").offset(offset).limit(limit)
        ],
    }


@router.post("/workers", status_code=201)
async def worker_create(payload: WorkerInput, session: Auth):
    require_role(session.user, "owner", "manager")
    valid_date(payload.joining_date)
    async with in_transaction():
        worker = await Worker.create(**payload.model_dump())
        await AuditLog.create(
            user=session.user, action="worker.create", details={"id": str(worker.id)}
        )
    return record_data(worker)


@router.patch("/workers/{record_id}")
async def worker_edit(record_id: UUID, payload: WorkerInput, session: Auth):
    require_role(session.user, "owner", "manager")
    valid_date(payload.joining_date)
    async with in_transaction():
        worker = await get_record(Worker, record_id, lock=True)
        worker.update_from_dict(payload.model_dump())
        await worker.save()
        await AuditLog.create(
            user=session.user, action="worker.update", details={"id": str(worker.id)}
        )
    return record_data(worker)


@router.get("/jobs")
async def jobs(
    session: Auth,
    status: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    query = WorkerJob.all()
    if status:
        query = query.filter(status=status)
    result = []
    for job in (
        await query.select_related("worker", "receipt_item__receipt")
        .order_by("-created_at")
        .offset(offset)
        .limit(limit)
    ):
        row = record_data(job)
        row.update(
            worker_name=job.worker.name,
            receipt_number=job.receipt_item.receipt.number,
            receipt_id=str(job.receipt_item.receipt_id),
            equipment=job.receipt_item.name,
        )
        if session.user.role == "staff":
            row.pop("labor_amount", None)
        result.append(row)
    return {"total": await query.count(), "items": result}


@router.post("/jobs", status_code=201)
async def job_create(payload: JobInput, session: Auth):
    require_role(session.user, "owner", "manager")
    valid_date(payload.assigned_date)
    async with in_transaction():
        line = await get_record(ReceiptItem, payload.receipt_item_id)
        receipt = await get_record(Receipt, line.receipt_id, lock=True)
        worker = await get_record(Worker, payload.worker_id, lock=True)
        if (
            receipt.status != "posted"
            or receipt.transaction_type != "repair"
            or receipt.completed_at
        ):
            raise HTTPException(409, "Assign jobs to an active posted repair receipt")
        if not worker.active:
            raise HTTPException(409, "Worker is inactive")
        if payload.assigned_date < receipt.transaction_date:
            raise HTTPException(422, "Assignment cannot precede the receipt")
        job = await WorkerJob.create(**payload.model_dump())
        await AuditLog.create(
            user=session.user, action="job.assign", details={"id": str(job.id)}
        )
    return record_data(job)


@router.patch("/jobs/{record_id}/status")
async def job_status(record_id: UUID, payload: JobStatusInput, session: Auth):
    require_role(session.user, "owner", "manager")
    async with in_transaction():
        initial = await get_record(WorkerJob, record_id)
        line = await get_record(ReceiptItem, initial.receipt_item_id)
        await get_record(Receipt, line.receipt_id, lock=True)
        await get_record(Worker, initial.worker_id, lock=True)
        job = await get_record(WorkerJob, record_id, lock=True)
        if job.status == payload.status:
            return record_data(job)
        if job.status in {"completed", "cancelled"}:
            raise HTTPException(
                409, "Completed/cancelled jobs are locked to protect earnings"
            )
        job.status = payload.status
        if payload.status == "completed":
            job.completed_at = datetime.now(UTC)
            await WorkerEarning.create(
                job=job,
                worker_id=job.worker_id,
                amount=job.labor_amount,
                earned_date=today(),
            )
        await job.save()
        await AuditLog.create(
            user=session.user,
            action="job.status",
            details={"id": str(job.id), "status": job.status},
        )
    return record_data(job)


@router.get("/workers/{record_id}/statement")
async def worker_statement(
    record_id: UUID, session: Auth, start: date | None = None, end: date | None = None
):
    require_role(session.user, "owner")
    worker = await get_record(Worker, record_id)
    end = end or today()
    start = start or end.replace(day=1)
    if start > end:
        raise HTTPException(422, "Start date must precede end date")
    from app.services.reporting import bounds

    _, _, since, until = bounds(start, end)
    earned = await total(
        WorkerEarning.filter(
            worker=worker, earned_date__gte=start, earned_date__lte=end
        )
    )
    paid = await total(
        WorkerPayment.filter(
            worker=worker, payment_date__gte=start, payment_date__lte=end
        )
    )
    previous = await total(
        WorkerEarning.filter(worker=worker, earned_date__lt=start)
    ) - await total(WorkerPayment.filter(worker=worker, payment_date__lt=start))
    return {
        "worker": record_data(worker),
        "start": start,
        "end": end,
        "earned": str(earned),
        "paid": str(paid),
        "previous_unpaid": str(previous),
        "payable": str(previous + earned - paid),
        "jobs": [
            record_data(r)
            for r in await WorkerJob.filter(
                worker=worker, completed_at__gte=since, completed_at__lt=until
            ).order_by("-created_at")
        ],
        "payments": [
            record_data(r)
            for r in await WorkerPayment.filter(
                worker=worker, payment_date__lte=end
            ).order_by("-payment_date")
        ],
    }


@router.post("/worker-payments", status_code=201)
async def worker_pay(payload: WorkerPaymentInput, session: Auth, key: Key):
    require_role(session.user, "owner")
    valid_date(payload.payment_date)
    async with in_transaction():
        existing = await idempotent(WorkerPayment, key, payload)
        if existing:
            return record_data(existing)
        worker = await get_record(Worker, payload.worker_id, lock=True)
        payable = await total(
            WorkerEarning.filter(worker=worker, earned_date__lte=payload.payment_date)
        ) - await total(
            WorkerPayment.filter(worker=worker, payment_date__lte=payload.payment_date)
        )
        latest = (
            await WorkerPayment.filter(worker=worker).order_by("-payment_date").first()
        )
        if latest and payload.payment_date < latest.payment_date:
            raise HTTPException(
                409, "Worker payments cannot precede an existing payment date"
            )
        overall = await total(WorkerEarning.filter(worker=worker)) - await total(
            WorkerPayment.filter(worker=worker)
        )
        if payload.amount > min(payable, overall):
            raise HTTPException(409, "Payment exceeds eligible unpaid worker earnings")
        payment = await WorkerPayment.create(
            **payload.model_dump(),
            idempotency_key=key,
            request_hash=digest(payload),
            recorded_by=session.user,
        )
        await AuditLog.create(
            user=session.user, action="worker.payment", details={"id": str(payment.id)}
        )
    return record_data(payment)


@router.get("/workers/{record_id}/statement.pdf")
async def statement_pdf(
    record_id: UUID, session: Auth, start: date | None = None, end: date | None = None
):
    from fastapi.responses import Response

    from app.documents.base import Document
    from app.models.business import ShopSettings

    data = await worker_statement(record_id, session, start, end)
    settings, _ = await ShopSettings.get_or_create(id=1)
    doc = Document("کاریگر کا بیان / Worker statement", settings)
    doc.line(data["worker"]["name"], 14)
    doc.line(f"{data['start']} — {data['end']}")
    for key, label in [
        ("earned", "کمائی / Earned"),
        ("previous_unpaid", "پچھلا بقایا / Previous unpaid"),
        ("paid", "ادا شدہ / Paid"),
        ("payable", "واجب الادا / Payable"),
    ]:
        doc.line(f"{label}: {data[key]} PKR")
    for job in data["jobs"]:
        doc.line(
            f"{job['description']} — {job['labor_amount']} PKR — {job['status']}", 10
        )
    for payment in data["payments"]:
        doc.line(f"Payment {payment['payment_date']}: {payment['amount']} PKR", 10)
    return Response(
        doc.finish(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="worker-{record_id}-statement.pdf"'
        },
    )


@router.get("/worker-payments/{record_id}/pdf")
async def worker_payment_pdf(record_id: UUID, session: Auth):
    from fastapi.responses import Response

    from app.documents.base import Document
    from app.models.business import ShopSettings

    require_role(session.user, "owner")
    payment = await get_record(WorkerPayment, record_id)
    worker = await get_record(Worker, payment.worker_id)
    settings, _ = await ShopSettings.get_or_create(id=1)
    doc = Document("کاریگر کی ادائیگی / Worker payment receipt", settings)
    doc.line(f"{worker.code} — {worker.name}", 14)
    doc.line(f"تاریخ / Date: {payment.payment_date}")
    doc.line(f"رقم / Amount: {payment.amount} PKR", 14)
    doc.line(f"طریقہ / Method: {payment.method}")
    doc.line(f"حوالہ / Reference: {payment.reference}")
    doc.line(payment.notes)
    doc.line("وصول کنندہ کے دستخط / Received by: __________________")
    return Response(
        doc.finish(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="worker-payment-{payment.id}.pdf"'
        },
    )
