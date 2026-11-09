import type { Field, Resource } from "./types"
const f = (
  key: string,
  ur: string,
  en: string,
  type: Field["type"] = "text",
  required = false
): Field => ({ key, ur, en, type, required })
const condition: Field = {
  key: "condition",
  ur: "حالت",
  en: "Condition",
  type: "select",
  options: [
    { value: "new", ur: "نیا", en: "New" },
    { value: "used", ur: "استعمال شدہ", en: "Used" },
    { value: "damaged", ur: "خراب", en: "Damaged" },
    { value: "under_repair", ur: "زیر مرمت", en: "Under repair" },
    { value: "repaired", ur: "مرمت شدہ", en: "Repaired" },
    { value: "scrap", ur: "کباڑ", en: "Scrap" },
  ],
}
export const resources: Record<string, Resource> = {
  customers: {
    path: "customers",
    ur: "گاہک",
    en: "Customers",
    editable: true,
    fields: [
      f("name", "نام", "Name", "text", true),
      f("phone", "فون", "Phone"),
      f("address", "پتہ", "Address", "textarea"),
      f("notes", "نوٹس", "Notes", "textarea"),
    ],
    columns: ["name", "phone", "address"],
  },
  inventory: {
    path: "inventory",
    ur: "اسٹاک",
    en: "Inventory",
    editable: true,
    ownerOnly: true,
    fields: [
      f("code", "اسٹاک کوڈ", "Inventory code", "text", true),
      f("name", "سامان کا نام", "Equipment name", "text", true),
      f("category", "قسم", "Category", "text", true),
      f("brand", "برانڈ", "Brand"),
      f("model", "ماڈل", "Model"),
      f("serial_number", "سیریل نمبر", "Serial number"),
      condition,
      {
        key: "availability",
        ur: "دستیابی",
        en: "Availability",
        type: "select",
        options: [
          { value: "available", ur: "دستیاب", en: "Available" },
          { value: "reserved", ur: "محفوظ", en: "Reserved" },
          { value: "unavailable", ur: "غیر دستیاب", en: "Unavailable" },
          { value: "sold", ur: "فروخت شدہ", en: "Sold" },
        ],
      },
      f("selling_price", "فروخت کی قیمت", "Selling price", "number", true),
      f(
        "estimated_repair_cost",
        "تخمینی مرمت خرچ",
        "Estimated repair cost",
        "number"
      ),
      f("location", "جگہ", "Location"),
      f("source", "ذریعہ", "Source"),
      f("notes", "نوٹس", "Notes", "textarea"),
    ],
    columns: [
      "code",
      "name",
      "condition",
      "availability",
      "quantity",
      "selling_price",
    ],
  },
  workers: {
    path: "workers",
    ur: "کاریگر",
    en: "Workers",
    editable: true,
    ownerOnly: true,
    fields: [
      f("code", "کاریگر کوڈ", "Worker code", "text", true),
      f("name", "نام", "Name", "text", true),
      f("phone", "فون", "Phone"),
      f("specialization", "مہارت", "Specialization", "text", true),
      f("joining_date", "شمولیت کی تاریخ", "Joining date", "date", true),
      {
        key: "active",
        ur: "حالت",
        en: "Status",
        type: "select",
        options: [
          { value: "true", ur: "فعال", en: "Active" },
          { value: "false", ur: "غیر فعال", en: "Inactive" },
        ],
      },
      f("notes", "نوٹس", "Notes", "textarea"),
    ],
    columns: ["code", "name", "specialization", "phone", "active"],
  },
}
export const labels: Record<string, [string, string]> = {
  quantity: ["تعداد", "Quantity"],
  status: ["حالت", "Status"],
  created_at: ["تاریخ", "Date"],
  kind: ["حرکت", "Movement"],
  cost: ["لاگت", "Cost"],
  amount: ["رقم", "Amount"],
  payment_date: ["ادائیگی کی تاریخ", "Payment date"],
  method: ["طریقہ", "Method"],
  reference: ["حوالہ", "Reference"],
  notes: ["نوٹس", "Notes"],
  earned: ["کمائی", "Earned"],
  paid: ["ادا شدہ", "Paid"],
  payable: ["واجب الادا", "Payable"],
}
