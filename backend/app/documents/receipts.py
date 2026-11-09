from app.documents.base import Document
from app.models.business import ShopSettings
from app.services.receipts import receipt_data


async def receipt_pdf(receipt):
    settings, _ = await ShopSettings.get_or_create(id=1)
    data = await receipt_data(receipt)
    doc = Document(
        f"بلٹی نمبر / Receipt: {receipt.number}",
        settings,
        thermal=settings.print_format == "thermal",
    )
    line = doc.line
    line(settings.receipt_header, 10)
    line(f"تاریخ / Date: {receipt.transaction_date}")
    transaction_label = {
        "sale": "فروخت / Sale",
        "purchase": "خریداری / Purchase",
        "repair": "مرمت / Repair",
    }[receipt.transaction_type]
    status_label = {
        "draft": "مسودہ / Draft",
        "posted": "حتمی / Posted",
        "void": "منسوخ / Void",
    }[receipt.status]
    party_label = {
        "sale": "خریدار / Buyer",
        "purchase": "فروخت کنندہ / Seller",
        "repair": "گاہک / Customer",
    }[receipt.transaction_type]
    line(f"قسم: {transaction_label}")
    line(f"حالت: {status_label}")
    customer = data["customer"] or {
        "name": "واک اِن گاہک / Walk-in",
        "phone": "",
        "address": "",
    }
    line(f"{party_label}: {customer['name']}")
    line(f"فون / Phone: {customer['phone']}")
    if customer["address"]:
        line(f"پتہ / Address: {customer['address']}", 10)
    for item in data["items"]:
        line(f"{item['name']} {item['brand']} {item['model']}")
        if item["serial_number"]:
            line(f"سیریل نمبر / Serial: {item['serial_number']}", 10)
        line(
            f"تعداد / Qty: {item['quantity']} × {item['unit_price']} {settings.currency}"
        )
    line(f"کل رقم / Total: {data['total']} {settings.currency}", 14)
    line(f"ادا شدہ / Paid: {data['paid']} {settings.currency}")
    line(f"بقایا / Dues: {data['balance']} {settings.currency}")
    if receipt.transaction_type == "purchase":
        line("خریداری کی ادائیگی / Payment to seller", 10)
    if receipt.work_description:
        line(f"کام کی تفصیل / Work: {receipt.work_description}", 10)
    if receipt.notes:
        line(f"نوٹس / Notes: {receipt.notes}", 10)
    line("مجاز دستخط / Authorized signature: __________________", 10)
    line(settings.receipt_footer, 10)
    return doc.finish()
