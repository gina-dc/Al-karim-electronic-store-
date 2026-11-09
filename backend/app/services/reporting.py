from collections import defaultdict
from datetime import datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from fastapi import HTTPException

from app.models.business import (
    Customer,
    Expense,
    InventoryItem,
    Payment,
    Receipt,
    ReceiptItem,
    StockLot,
    StockMovement,
    Worker,
    WorkerEarning,
    WorkerJob,
    WorkerPayment,
)
from app.services.common import record_data, today, total


def bounds(start, end):
    end = end or today()
    start = start or end.replace(day=1)
    if start > end or (end - start).days > 366:
        raise HTTPException(422, "Choose a date range of up to 367 days")
    zone = ZoneInfo("Asia/Karachi")
    return (
        start,
        end,
        datetime.combine(start, time.min, zone),
        datetime.combine(end + timedelta(days=1), time.min, zone),
    )


async def report_data(start=None, end=None):
    from tortoise.transactions import in_transaction

    async with in_transaction() as conn:
        await conn.execute_query(
            "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"
        )
        return await _report_data(start, end)


async def _report_data(start=None, end=None):
    start, end, since, until = bounds(start, end)
    sales = Receipt.filter(
        status="posted",
        transaction_type="sale",
        transaction_date__gte=start,
        transaction_date__lte=end,
    )
    repairs = Receipt.filter(
        status="posted",
        transaction_type="repair",
        completed_at__gte=since,
        completed_at__lt=until,
    )
    sales_revenue, repair_revenue = (
        await total(sales, "total"),
        await total(repairs, "total"),
    )
    stock_cost = await total(
        ReceiptItem.filter(receipt_id__in=await sales.values_list("id", flat=True)),
        "cost_total",
    )
    repair_cost = await total(
        Expense.filter(
            category="repair", expense_date__gte=start, expense_date__lte=end
        )
    )
    operating = await total(
        Expense.filter(
            category="operating", expense_date__gte=start, expense_date__lte=end
        )
    )
    labor = await total(
        WorkerEarning.filter(earned_date__gte=start, earned_date__lte=end)
    )
    incoming = Payment.filter(
        receipt__status="posted",
        receipt__transaction_type__in=["sale", "repair"],
        payment_date__gte=start,
        payment_date__lte=end,
    )
    cash = await total(incoming)
    acquisition = await total(
        Receipt.filter(
            status="posted",
            transaction_type="purchase",
            transaction_date__gte=start,
            transaction_date__lte=end,
        ),
        "total",
    )
    revenue, direct = sales_revenue + repair_revenue, stock_cost + repair_cost + labor
    dues, advances, outstanding = Decimal(0), Decimal(0), []
    for receipt in await Receipt.filter(
        status="posted",
        transaction_type__in=["sale", "repair"],
        transaction_date__lte=end,
    ).select_related("customer"):
        paid = await total(Payment.filter(receipt=receipt, payment_date__lte=end))
        balance = receipt.total - paid
        if balance:
            dues += balance
            outstanding.append(
                {
                    "id": str(receipt.id),
                    "number": receipt.number,
                    "customer": receipt.customer.name
                    if receipt.customer
                    else "Walk-in",
                    "total": str(receipt.total),
                    "paid": str(paid),
                    "balance": str(balance),
                }
            )
        if receipt.transaction_type == "repair" and (
            not receipt.completed_at or receipt.completed_at >= until
        ):
            advances += paid
    earnings_total = await total(WorkerEarning.filter(earned_date__lte=end))
    worker_paid = await total(WorkerPayment.filter(payment_date__lte=end))
    stock_value, estimated_value = Decimal(0), Decimal(0)
    for lot in await StockLot.all():
        stock_value += lot.quantity * lot.unit_cost
    conditions = defaultdict(int)
    for item in await InventoryItem.all():
        conditions[item.condition] += item.quantity
        estimated_value += item.quantity * item.selling_price
    daily = defaultdict(
        lambda: {
            "revenue": Decimal(0),
            "sales": Decimal(0),
            "costs": Decimal(0),
            "expenses": Decimal(0),
        }
    )
    for receipt in await sales:
        daily[receipt.transaction_date.isoformat()]["revenue"] += receipt.total
        daily[receipt.transaction_date.isoformat()]["sales"] += receipt.total
        daily[receipt.transaction_date.isoformat()]["costs"] += await total(
            ReceiptItem.filter(receipt=receipt), "cost_total"
        )
    for receipt in await repairs:
        day = (
            receipt.completed_at.astimezone(ZoneInfo("Asia/Karachi")).date().isoformat()
        )
        daily[day]["revenue"] += receipt.total
    for expense in await Expense.filter(expense_date__gte=start, expense_date__lte=end):
        daily[expense.expense_date.isoformat()]["expenses"] += expense.amount
        daily[expense.expense_date.isoformat()]["costs"] += expense.amount
    for earning in await WorkerEarning.filter(
        earned_date__gte=start, earned_date__lte=end
    ):
        daily[earning.earned_date.isoformat()]["costs"] += earning.amount
    series = []
    monthly = defaultdict(Decimal)
    cursor = start
    while cursor <= end:
        point = daily[cursor.isoformat()]
        series.append(
            {
                "date": cursor.isoformat(),
                **{key: str(value) for key, value in point.items()},
            }
        )
        monthly[cursor.strftime("%Y-%m")] += point["revenue"]
        cursor += timedelta(days=1)
    payroll = []
    for worker in await Worker.all():
        earned = await total(WorkerEarning.filter(worker=worker, earned_date__lte=end))
        paid = await total(WorkerPayment.filter(worker=worker, payment_date__lte=end))
        payroll.append(
            {
                "id": str(worker.id),
                "name": worker.name,
                "earned": str(earned),
                "paid": str(paid),
                "payable": str(earned - paid),
                "completed": await WorkerJob.filter(
                    worker=worker, status="completed"
                ).count(),
                "pending": await WorkerJob.filter(
                    worker=worker, status__in=["assigned", "in_progress"]
                ).count(),
            }
        )
    valuation = []
    for item in await InventoryItem.all().order_by("code"):
        cost = sum(
            (
                lot.quantity * lot.unit_cost
                for lot in await StockLot.filter(inventory=item)
            ),
            Decimal(0),
        )
        valuation.append(
            {
                "code": item.code,
                "name": item.name,
                "condition": item.condition,
                "availability": item.availability,
                "quantity": item.quantity,
                "cost": str(cost),
                "estimated_selling_value": str(item.quantity * item.selling_price),
            }
        )
    movements = []
    for movement in (
        await StockMovement.filter(created_at__gte=since, created_at__lt=until)
        .select_related("inventory", "receipt_item__receipt")
        .order_by("-created_at")
    ):
        movements.append(
            {
                "code": movement.inventory.code,
                "name": movement.inventory.name,
                "kind": movement.kind,
                "quantity": movement.quantity,
                "cost": str(movement.cost),
                "recorded_at": movement.created_at.isoformat(),
                "receipt_number": movement.receipt_item.receipt.number
                if movement.receipt_item
                else "",
                "notes": movement.notes,
            }
        )
    job_rows = []
    for job in (
        await WorkerJob.filter(assigned_date__gte=start, assigned_date__lte=end)
        .select_related("worker", "receipt_item__receipt")
        .order_by("-assigned_date")
    ):
        job_rows.append(
            {
                "receipt_number": job.receipt_item.receipt.number,
                "equipment": job.receipt_item.name,
                "worker": job.worker.name,
                "description": job.description,
                "status": job.status,
                "assigned_date": str(job.assigned_date),
                "labor_amount": str(job.labor_amount),
                "completed_at": job.completed_at.isoformat()
                if job.completed_at
                else "",
            }
        )
    worker_payments = []
    for payment in (
        await WorkerPayment.filter(payment_date__gte=start, payment_date__lte=end)
        .select_related("worker")
        .order_by("-payment_date")
    ):
        worker_payments.append(
            {
                "worker_code": payment.worker.code,
                "worker": payment.worker.name,
                "amount": str(payment.amount),
                "payment_date": str(payment.payment_date),
                "method": payment.method,
                "reference": payment.reference,
                "notes": payment.notes,
            }
        )
    return {
        "inventory": valuation,
        "movements": movements,
        "jobs": job_rows,
        "worker_payments": worker_payments,
        "start": str(start),
        "end": str(end),
        "kpis": {
            "revenue": str(revenue),
            "sales_revenue": str(sales_revenue),
            "repair_revenue": str(repair_revenue),
            "costs": str(direct + operating),
            "gross_profit": str(revenue - direct),
            "net_profit": str(revenue - direct - operating),
            "stock_cost": str(stock_cost),
            "repair_cost": str(repair_cost),
            "labor_cost": str(labor),
            "operating_expenses": str(operating),
            "cash_received": str(cash),
            "advances": str(advances),
            "dues": str(dues),
            "worker_due": str(earnings_total - worker_paid),
            "acquisitions": str(acquisition),
            "inventory_cost": str(stock_value),
            "estimated_inventory_value": str(estimated_value),
            "sales_count": await sales.count(),
            "customers": await Customer.all().count(),
            "inventory_items": await InventoryItem.all().count(),
            "available_stock": int(
                await total(InventoryItem.filter(availability="available"), "quantity")
            ),
            "under_repair": int(
                await total(InventoryItem.filter(condition="under_repair"), "quantity")
            ),
        },
        "daily": series,
        "monthly": [
            {"month": month, "revenue": str(value)}
            for month, value in sorted(monthly.items())
        ],
        "conditions": [
            {"name": name, "quantity": qty} for name, qty in conditions.items()
        ],
        "dues": outstanding,
        "payroll": payroll,
        "expenses": [
            record_data(e)
            for e in await Expense.filter(
                expense_date__gte=start, expense_date__lte=end
            ).order_by("-expense_date")
        ],
        "pending_repairs": [
            record_data(r)
            for r in await Receipt.filter(
                status="posted", transaction_type="repair", completed_at=None
            )
            .order_by("transaction_date")
            .limit(20)
        ],
        "low_stock": [
            record_data(i)
            for i in await InventoryItem.filter(
                quantity__lte=2, availability="available"
            )
            .order_by("quantity")
            .limit(20)
        ],
    }
