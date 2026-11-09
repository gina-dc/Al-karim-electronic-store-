import uuid

from tortoise import fields, models


class Entity(models.Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Customer(Entity):
    name = fields.CharField(max_length=150, db_index=True)
    phone = fields.CharField(max_length=30, default="", db_index=True)
    address = fields.TextField(default="")
    notes = fields.TextField(default="")


class InventoryItem(Entity):
    code = fields.CharField(max_length=30, unique=True)
    name = fields.CharField(max_length=200, db_index=True)
    category = fields.CharField(max_length=100)
    brand = fields.CharField(max_length=100, default="")
    model = fields.CharField(max_length=100, default="")
    serial_number = fields.CharField(max_length=100, null=True, unique=True)
    condition = fields.CharField(max_length=20)
    availability = fields.CharField(max_length=20, default="available")
    quantity = fields.IntField(default=0)
    selling_price = fields.DecimalField(max_digits=16, decimal_places=2)
    estimated_repair_cost = fields.DecimalField(
        max_digits=16, decimal_places=2, default=0
    )
    location = fields.CharField(max_length=150, default="")
    source = fields.CharField(max_length=200, default="")
    notes = fields.TextField(default="")


class ReceiptSequence(models.Model):
    name = fields.CharField(primary_key=True, max_length=30)
    value = fields.BigIntField(default=0)


class Receipt(Entity):
    number = fields.CharField(max_length=20, unique=True)
    customer = fields.ForeignKeyField(
        "models.Customer", null=True, on_delete=fields.RESTRICT
    )
    transaction_type = fields.CharField(max_length=20, db_index=True)
    transaction_date = fields.DateField(db_index=True)
    status = fields.CharField(max_length=20, default="draft", db_index=True)
    total = fields.DecimalField(max_digits=16, decimal_places=2)
    notes = fields.TextField(default="")
    work_description = fields.TextField(default="")
    created_by = fields.ForeignKeyField("models.User", on_delete=fields.RESTRICT)
    idempotency_key = fields.UUIDField(unique=True)
    request_hash = fields.CharField(max_length=64)
    posted_at = fields.DatetimeField(null=True)
    completed_at = fields.DatetimeField(null=True)
    void_reason = fields.TextField(default="")


class ReceiptItem(Entity):
    cost_allocations = fields.JSONField(default=list)
    receipt = fields.ForeignKeyField(
        "models.Receipt", related_name="items", on_delete=fields.RESTRICT
    )
    inventory = fields.ForeignKeyField(
        "models.InventoryItem", null=True, on_delete=fields.RESTRICT
    )
    name = fields.CharField(max_length=200)
    category = fields.CharField(max_length=100, default="")
    brand = fields.CharField(max_length=100, default="")
    model = fields.CharField(max_length=100, default="")
    serial_number = fields.CharField(max_length=100, default="")
    quantity = fields.IntField()
    unit_price = fields.DecimalField(max_digits=16, decimal_places=2)
    cost_total = fields.DecimalField(max_digits=16, decimal_places=2, default=0)


class Payment(Entity):
    receipt = fields.ForeignKeyField(
        "models.Receipt", related_name="payments", on_delete=fields.RESTRICT
    )
    amount = fields.DecimalField(max_digits=16, decimal_places=2)
    payment_date = fields.DateField(db_index=True)
    method = fields.CharField(max_length=40)
    reference = fields.CharField(max_length=150, default="")
    notes = fields.TextField(default="")
    recorded_by = fields.ForeignKeyField("models.User", on_delete=fields.RESTRICT)
    idempotency_key = fields.UUIDField(unique=True)
    request_hash = fields.CharField(max_length=64)


class StockLot(Entity):
    inventory = fields.ForeignKeyField(
        "models.InventoryItem", related_name="lots", on_delete=fields.RESTRICT
    )
    receipt_item = fields.ForeignKeyField(
        "models.ReceiptItem", null=True, on_delete=fields.RESTRICT
    )
    quantity = fields.IntField()
    unit_cost = fields.DecimalField(max_digits=16, decimal_places=2)
    purchase_date = fields.DateField()


class StockMovement(Entity):
    inventory = fields.ForeignKeyField(
        "models.InventoryItem", related_name="movements", on_delete=fields.RESTRICT
    )
    receipt_item = fields.ForeignKeyField(
        "models.ReceiptItem", null=True, on_delete=fields.RESTRICT
    )
    kind = fields.CharField(max_length=30)
    quantity = fields.IntField()
    cost = fields.DecimalField(max_digits=16, decimal_places=2, default=0)
    notes = fields.TextField(default="")
    recorded_by = fields.ForeignKeyField("models.User", on_delete=fields.RESTRICT)


class Worker(Entity):
    code = fields.CharField(max_length=30, unique=True)
    name = fields.CharField(max_length=150)
    phone = fields.CharField(max_length=30, default="")
    specialization = fields.CharField(max_length=150)
    joining_date = fields.DateField()
    active = fields.BooleanField(default=True)
    notes = fields.TextField(default="")


class WorkerJob(Entity):
    receipt_item = fields.ForeignKeyField(
        "models.ReceiptItem", related_name="jobs", on_delete=fields.RESTRICT
    )
    worker = fields.ForeignKeyField(
        "models.Worker", related_name="jobs", on_delete=fields.RESTRICT
    )
    description = fields.TextField()
    status = fields.CharField(max_length=20, default="assigned", db_index=True)
    assigned_date = fields.DateField()
    expected_date = fields.DateField(null=True)
    completed_at = fields.DatetimeField(null=True)
    labor_amount = fields.DecimalField(max_digits=16, decimal_places=2)
    notes = fields.TextField(default="")


class WorkerEarning(Entity):
    job = fields.OneToOneField(
        "models.WorkerJob", on_delete=fields.RESTRICT, related_name="earning"
    )
    worker = fields.ForeignKeyField(
        "models.Worker", related_name="earnings", on_delete=fields.RESTRICT
    )
    amount = fields.DecimalField(max_digits=16, decimal_places=2)
    earned_date = fields.DateField(db_index=True)


class WorkerPayment(Entity):
    worker = fields.ForeignKeyField(
        "models.Worker", related_name="payments", on_delete=fields.RESTRICT
    )
    amount = fields.DecimalField(max_digits=16, decimal_places=2)
    payment_date = fields.DateField(db_index=True)
    method = fields.CharField(max_length=40)
    reference = fields.CharField(max_length=150, default="")
    notes = fields.TextField(default="")
    recorded_by = fields.ForeignKeyField("models.User", on_delete=fields.RESTRICT)
    idempotency_key = fields.UUIDField(unique=True)
    request_hash = fields.CharField(max_length=64)


class Expense(Entity):
    description = fields.CharField(max_length=250)
    category = fields.CharField(max_length=30)
    amount = fields.DecimalField(max_digits=16, decimal_places=2)
    expense_date = fields.DateField(db_index=True)
    receipt = fields.ForeignKeyField(
        "models.Receipt", null=True, on_delete=fields.RESTRICT
    )
    recorded_by = fields.ForeignKeyField("models.User", on_delete=fields.RESTRICT)
    idempotency_key = fields.UUIDField(unique=True)
    request_hash = fields.CharField(max_length=64)


class ShopSettings(models.Model):
    name_ur = fields.CharField(max_length=200, default="")
    address_ur = fields.TextField(default="")
    logo = fields.BinaryField(null=True)
    language = fields.CharField(max_length=5, default="ur")
    theme = fields.CharField(max_length=10, default="light")
    id = fields.IntField(primary_key=True, default=1)
    name = fields.CharField(max_length=200, default="Electronics Shop")
    address = fields.TextField(default="")
    phone = fields.CharField(max_length=40, default="")
    receipt_header = fields.TextField(default="")
    receipt_footer = fields.TextField(default="")
    print_format = fields.CharField(max_length=20, default="a4")
    currency = fields.CharField(max_length=10, default="PKR")


class PaymentReversal(Entity):
    original = fields.OneToOneField(
        "models.Payment", on_delete=fields.RESTRICT, related_name="reversed_by"
    )
    correction = fields.OneToOneField(
        "models.Payment", on_delete=fields.RESTRICT, related_name="correction_for"
    )
    reason = fields.TextField()
