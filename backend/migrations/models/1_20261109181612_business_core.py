from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "customer" (
    "id" UUID NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL,
    "name" VARCHAR(150) NOT NULL,
    "phone" VARCHAR(30) NOT NULL,
    "address" TEXT NOT NULL,
    "notes" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "idx_customer_name_0aae8f" ON "customer" ("name");
CREATE INDEX IF NOT EXISTS "idx_customer_phone_8f0dcc" ON "customer" ("phone");
        CREATE TABLE IF NOT EXISTS "inventoryitem" (
    "id" UUID NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL,
    "code" VARCHAR(30) NOT NULL UNIQUE,
    "name" VARCHAR(200) NOT NULL,
    "category" VARCHAR(100) NOT NULL,
    "brand" VARCHAR(100) NOT NULL,
    "model" VARCHAR(100) NOT NULL,
    "serial_number" VARCHAR(100) UNIQUE,
    "condition" VARCHAR(20) NOT NULL,
    "availability" VARCHAR(20) NOT NULL,
    "quantity" INT NOT NULL,
    "selling_price" DECIMAL(16,2) NOT NULL,
    "estimated_repair_cost" DECIMAL(16,2) NOT NULL,
    "location" VARCHAR(150) NOT NULL,
    "source" VARCHAR(200) NOT NULL,
    "notes" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "idx_inventoryit_name_8748ef" ON "inventoryitem" ("name");
        CREATE TABLE IF NOT EXISTS "receiptsequence" (
    "name" VARCHAR(30) NOT NULL PRIMARY KEY,
    "value" BIGINT NOT NULL
);
        CREATE TABLE IF NOT EXISTS "shopsettings" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(200) NOT NULL,
    "address" TEXT NOT NULL,
    "phone" VARCHAR(40) NOT NULL,
    "receipt_header" TEXT NOT NULL,
    "receipt_footer" TEXT NOT NULL,
    "print_format" VARCHAR(20) NOT NULL,
    "currency" VARCHAR(10) NOT NULL
);
        CREATE TABLE IF NOT EXISTS "worker" (
    "id" UUID NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL,
    "code" VARCHAR(30) NOT NULL UNIQUE,
    "name" VARCHAR(150) NOT NULL,
    "phone" VARCHAR(30) NOT NULL,
    "specialization" VARCHAR(150) NOT NULL,
    "joining_date" DATE NOT NULL,
    "active" BOOL NOT NULL,
    "notes" TEXT NOT NULL
);
        CREATE TABLE IF NOT EXISTS "receipt" (
    "id" UUID NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL,
    "number" VARCHAR(20) NOT NULL UNIQUE,
    "transaction_type" VARCHAR(20) NOT NULL,
    "transaction_date" DATE NOT NULL,
    "status" VARCHAR(20) NOT NULL,
    "total" DECIMAL(16,2) NOT NULL,
    "notes" TEXT NOT NULL,
    "work_description" TEXT NOT NULL,
    "idempotency_key" UUID NOT NULL UNIQUE,
    "request_hash" VARCHAR(64) NOT NULL,
    "posted_at" TIMESTAMPTZ,
    "completed_at" TIMESTAMPTZ,
    "void_reason" TEXT NOT NULL,
    "created_by_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE RESTRICT,
    "customer_id" UUID REFERENCES "customer" ("id") ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS "idx_receipt_transac_c59d4f" ON "receipt" ("transaction_type");
CREATE INDEX IF NOT EXISTS "idx_receipt_transac_6f9d7a" ON "receipt" ("transaction_date");
CREATE INDEX IF NOT EXISTS "idx_receipt_status_41523d" ON "receipt" ("status");
        CREATE TABLE IF NOT EXISTS "expense" (
    "id" UUID NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL,
    "description" VARCHAR(250) NOT NULL,
    "category" VARCHAR(30) NOT NULL,
    "amount" DECIMAL(16,2) NOT NULL,
    "expense_date" DATE NOT NULL,
    "idempotency_key" UUID NOT NULL UNIQUE,
    "request_hash" VARCHAR(64) NOT NULL,
    "receipt_id" UUID REFERENCES "receipt" ("id") ON DELETE RESTRICT,
    "recorded_by_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS "idx_expense_expense_b04f25" ON "expense" ("expense_date");
        CREATE TABLE IF NOT EXISTS "payment" (
    "id" UUID NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL,
    "amount" DECIMAL(16,2) NOT NULL,
    "payment_date" DATE NOT NULL,
    "method" VARCHAR(40) NOT NULL,
    "reference" VARCHAR(150) NOT NULL,
    "notes" TEXT NOT NULL,
    "idempotency_key" UUID NOT NULL UNIQUE,
    "request_hash" VARCHAR(64) NOT NULL,
    "receipt_id" UUID NOT NULL REFERENCES "receipt" ("id") ON DELETE RESTRICT,
    "recorded_by_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS "idx_payment_payment_2b4468" ON "payment" ("payment_date");
        CREATE TABLE IF NOT EXISTS "paymentreversal" (
    "id" UUID NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL,
    "reason" TEXT NOT NULL,
    "original_id" UUID NOT NULL UNIQUE REFERENCES "payment" ("id") ON DELETE RESTRICT,
    "correction_id" UUID NOT NULL UNIQUE REFERENCES "payment" ("id") ON DELETE RESTRICT
);
        CREATE TABLE IF NOT EXISTS "receiptitem" (
    "id" UUID NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL,
    "name" VARCHAR(200) NOT NULL,
    "category" VARCHAR(100) NOT NULL,
    "brand" VARCHAR(100) NOT NULL,
    "model" VARCHAR(100) NOT NULL,
    "serial_number" VARCHAR(100) NOT NULL,
    "quantity" INT NOT NULL,
    "unit_price" DECIMAL(16,2) NOT NULL,
    "cost_total" DECIMAL(16,2) NOT NULL,
    "inventory_id" UUID REFERENCES "inventoryitem" ("id") ON DELETE RESTRICT,
    "receipt_id" UUID NOT NULL REFERENCES "receipt" ("id") ON DELETE RESTRICT
);
        CREATE TABLE IF NOT EXISTS "stocklot" (
    "id" UUID NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL,
    "quantity" INT NOT NULL,
    "unit_cost" DECIMAL(16,2) NOT NULL,
    "purchase_date" DATE NOT NULL,
    "inventory_id" UUID NOT NULL REFERENCES "inventoryitem" ("id") ON DELETE RESTRICT,
    "receipt_item_id" UUID REFERENCES "receiptitem" ("id") ON DELETE RESTRICT
);
        CREATE TABLE IF NOT EXISTS "stockmovement" (
    "id" UUID NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL,
    "kind" VARCHAR(30) NOT NULL,
    "quantity" INT NOT NULL,
    "cost" DECIMAL(16,2) NOT NULL,
    "notes" TEXT NOT NULL,
    "inventory_id" UUID NOT NULL REFERENCES "inventoryitem" ("id") ON DELETE RESTRICT,
    "receipt_item_id" UUID REFERENCES "receiptitem" ("id") ON DELETE RESTRICT,
    "recorded_by_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE RESTRICT
);
        CREATE TABLE IF NOT EXISTS "workerjob" (
    "id" UUID NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL,
    "description" TEXT NOT NULL,
    "status" VARCHAR(20) NOT NULL,
    "assigned_date" DATE NOT NULL,
    "expected_date" DATE,
    "completed_at" TIMESTAMPTZ,
    "labor_amount" DECIMAL(16,2) NOT NULL,
    "notes" TEXT NOT NULL,
    "receipt_item_id" UUID NOT NULL REFERENCES "receiptitem" ("id") ON DELETE RESTRICT,
    "worker_id" UUID NOT NULL REFERENCES "worker" ("id") ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS "idx_workerjob_status_ab5b3c" ON "workerjob" ("status");
        CREATE TABLE IF NOT EXISTS "workerearning" (
    "id" UUID NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL,
    "amount" DECIMAL(16,2) NOT NULL,
    "earned_date" DATE NOT NULL,
    "worker_id" UUID NOT NULL REFERENCES "worker" ("id") ON DELETE RESTRICT,
    "job_id" UUID NOT NULL UNIQUE REFERENCES "workerjob" ("id") ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS "idx_workerearni_earned__5fddb3" ON "workerearning" ("earned_date");
        CREATE TABLE IF NOT EXISTS "workerpayment" (
    "id" UUID NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL,
    "amount" DECIMAL(16,2) NOT NULL,
    "payment_date" DATE NOT NULL,
    "method" VARCHAR(40) NOT NULL,
    "reference" VARCHAR(150) NOT NULL,
    "notes" TEXT NOT NULL,
    "idempotency_key" UUID NOT NULL UNIQUE,
    "request_hash" VARCHAR(64) NOT NULL,
    "recorded_by_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE RESTRICT,
    "worker_id" UUID NOT NULL REFERENCES "worker" ("id") ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS "idx_workerpayme_payment_2d15c6" ON "workerpayment" ("payment_date");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "receipt";
        DROP TABLE IF EXISTS "stockmovement";
        DROP TABLE IF EXISTS "expense";
        DROP TABLE IF EXISTS "workerpayment";
        DROP TABLE IF EXISTS "workerjob";
        DROP TABLE IF EXISTS "stocklot";
        DROP TABLE IF EXISTS "payment";
        DROP TABLE IF EXISTS "paymentreversal";
        DROP TABLE IF EXISTS "workerearning";
        DROP TABLE IF EXISTS "shopsettings";
        DROP TABLE IF EXISTS "worker";
        DROP TABLE IF EXISTS "receiptsequence";
        DROP TABLE IF EXISTS "customer";
        DROP TABLE IF EXISTS "inventoryitem";
        DROP TABLE IF EXISTS "receiptitem";"""


MODELS_STATE = (
    "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"
)
