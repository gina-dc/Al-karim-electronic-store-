from datetime import date
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

Money = Annotated[Decimal, Field(ge=0, max_digits=14, decimal_places=2)]
PositiveMoney = Annotated[Decimal, Field(gt=0, max_digits=14, decimal_places=2)]
Text = Annotated[str, Field(max_length=5000)]


class ValidatedInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class CustomerInput(ValidatedInput):
    name: str = Field(min_length=1, max_length=150)
    phone: str = Field(default="", max_length=30)
    address: Text = ""
    notes: Text = ""


class ItemInput(ValidatedInput):
    inventory_id: UUID | None = None
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(default="", max_length=100)
    brand: str = Field(default="", max_length=100)
    model: str = Field(default="", max_length=100)
    serial_number: str = Field(default="", max_length=100)
    quantity: int = Field(gt=0, le=100000)
    unit_price: Money


class ReceiptInput(ValidatedInput):
    post: bool = False
    initial_payment: Money = Decimal(0)
    payment_method: Literal["cash", "bank_transfer", "other"] = "cash"
    customer_id: UUID | None = None
    transaction_type: Literal["sale", "repair", "purchase"]
    transaction_date: date
    notes: Text = ""
    work_description: Text = ""
    items: list[ItemInput] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def check_items(self):
        if self.initial_payment and not self.post:
            raise ValueError("Drafts cannot have initial payments")
        if self.initial_payment > sum(i.unit_price * i.quantity for i in self.items):
            raise ValueError("Initial payment exceeds receipt total")
        if self.transaction_type in {"sale", "purchase"} and any(
            not i.inventory_id for i in self.items
        ):
            raise ValueError("Sales and purchases require linked inventory items")
        if sum(i.unit_price * i.quantity for i in self.items) > Decimal(
            "999999999999.99"
        ):
            raise ValueError("Receipt total exceeds supported amount")
        return self


class PaymentInput(ValidatedInput):
    receipt_id: UUID
    amount: PositiveMoney
    payment_date: date
    method: Literal["cash", "bank_transfer", "other"]
    reference: str = Field(default="", max_length=150)
    notes: Text = ""


class ReasonInput(ValidatedInput):
    reason: str = Field(min_length=5, max_length=5000)


class InventoryInput(ValidatedInput):
    availability: Literal["available", "reserved", "sold", "unavailable"] = "available"
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=100)
    brand: str = Field(default="", max_length=100)
    model: str = Field(default="", max_length=100)
    serial_number: str | None = Field(default=None, max_length=100)
    condition: Literal["new", "used", "damaged", "under_repair", "repaired", "scrap"]
    selling_price: Money
    estimated_repair_cost: Money = Decimal(0)
    location: str = Field(default="", max_length=150)
    source: str = Field(default="", max_length=200)
    notes: Text = ""


class WorkerInput(ValidatedInput):
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=150)
    phone: str = Field(default="", max_length=30)
    specialization: str = Field(min_length=1, max_length=150)
    joining_date: date
    active: bool = True
    notes: Text = ""


class JobInput(ValidatedInput):
    receipt_item_id: UUID
    worker_id: UUID
    description: str = Field(min_length=1, max_length=5000)
    assigned_date: date
    expected_date: date | None = None
    labor_amount: Money
    notes: Text = ""

    @model_validator(mode="after")
    def dates(self):
        if self.expected_date and self.expected_date < self.assigned_date:
            raise ValueError("Completion date cannot precede assignment")
        return self


class JobStatusInput(ValidatedInput):
    status: Literal["in_progress", "completed", "cancelled"]


class WorkerPaymentInput(ValidatedInput):
    worker_id: UUID
    amount: PositiveMoney
    payment_date: date
    method: Literal["cash", "bank_transfer", "other"]
    reference: str = Field(default="", max_length=150)
    notes: Text = ""


class ExpenseInput(ValidatedInput):
    description: str = Field(min_length=1, max_length=250)
    category: Literal["operating", "repair"]
    amount: PositiveMoney
    expense_date: date
    receipt_id: UUID | None = None


class SettingsInput(ValidatedInput):
    name_ur: str = Field(default="", max_length=200)
    address_ur: Text = ""
    language: Literal["ur", "en"] = "ur"
    theme: Literal["light", "dark"] = "light"
    name: str = Field(min_length=1, max_length=200)
    address: Text = ""
    phone: str = Field(default="", max_length=40)
    receipt_header: Text = ""
    receipt_footer: Text = ""
    print_format: Literal["a4", "thermal"] = "a4"
    currency: Literal["PKR", "Rs."] = "PKR"
