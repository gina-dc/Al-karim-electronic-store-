from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
ALTER TABLE "users" ADD CONSTRAINT "user_role" CHECK (role IN ('owner','manager','staff'));
ALTER TABLE "receipt" ADD CONSTRAINT "receipt_total_nonnegative" CHECK (total >= 0);
ALTER TABLE "receipt" ADD CONSTRAINT "receipt_status" CHECK (status IN ('draft','posted','void'));
ALTER TABLE "receipt" ADD CONSTRAINT "receipt_type" CHECK (transaction_type IN ('sale','repair','purchase'));
ALTER TABLE "receiptitem" ADD CONSTRAINT "line_quantity_positive" CHECK (quantity > 0);
ALTER TABLE "receiptitem" ADD CONSTRAINT "line_price_nonnegative" CHECK (unit_price >= 0);
ALTER TABLE "receiptitem" ADD CONSTRAINT "line_cost_nonnegative" CHECK (cost_total >= 0);
ALTER TABLE "inventoryitem" ADD CONSTRAINT "stock_nonnegative" CHECK (quantity >= 0);
ALTER TABLE "inventoryitem" ADD CONSTRAINT "serialized_single_unit" CHECK (serial_number IS NULL OR quantity <= 1);
ALTER TABLE "inventoryitem" ADD CONSTRAINT "stock_price_nonnegative" CHECK (selling_price >= 0);
ALTER TABLE "inventoryitem" ADD CONSTRAINT "sold_stock_empty" CHECK (availability <> 'sold' OR quantity = 0);
ALTER TABLE "inventoryitem" ADD CONSTRAINT "stock_availability" CHECK (availability IN ('available','reserved','sold','unavailable'));
ALTER TABLE "inventoryitem" ADD CONSTRAINT "stock_condition" CHECK (condition IN ('new','used','damaged','under_repair','repaired','scrap'));
ALTER TABLE "stocklot" ADD CONSTRAINT "lot_quantity_nonnegative" CHECK (quantity >= 0);
ALTER TABLE "stocklot" ADD CONSTRAINT "lot_cost_nonnegative" CHECK (unit_cost >= 0);
ALTER TABLE "payment" ADD CONSTRAINT "payment_nonzero" CHECK (amount <> 0);
ALTER TABLE "workerjob" ADD CONSTRAINT "labor_nonnegative" CHECK (labor_amount >= 0);
ALTER TABLE "workerjob" ADD CONSTRAINT "job_status" CHECK (status IN ('assigned','in_progress','completed','cancelled'));
ALTER TABLE "workerearning" ADD CONSTRAINT "earning_nonnegative" CHECK (amount >= 0);
ALTER TABLE "workerpayment" ADD CONSTRAINT "worker_payment_positive" CHECK (amount > 0);
ALTER TABLE "expense" ADD CONSTRAINT "expense_positive" CHECK (amount > 0);
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
ALTER TABLE "users" DROP CONSTRAINT "user_role";
ALTER TABLE "receipt" DROP CONSTRAINT "receipt_total_nonnegative";
ALTER TABLE "receipt" DROP CONSTRAINT "receipt_status";
ALTER TABLE "receipt" DROP CONSTRAINT "receipt_type";
ALTER TABLE "receiptitem" DROP CONSTRAINT "line_quantity_positive";
ALTER TABLE "receiptitem" DROP CONSTRAINT "line_price_nonnegative";
ALTER TABLE "receiptitem" DROP CONSTRAINT "line_cost_nonnegative";
ALTER TABLE "inventoryitem" DROP CONSTRAINT "stock_nonnegative";
ALTER TABLE "inventoryitem" DROP CONSTRAINT "serialized_single_unit";
ALTER TABLE "inventoryitem" DROP CONSTRAINT "stock_price_nonnegative";
ALTER TABLE "inventoryitem" DROP CONSTRAINT "sold_stock_empty";
ALTER TABLE "inventoryitem" DROP CONSTRAINT "stock_availability";
ALTER TABLE "inventoryitem" DROP CONSTRAINT "stock_condition";
ALTER TABLE "stocklot" DROP CONSTRAINT "lot_quantity_nonnegative";
ALTER TABLE "stocklot" DROP CONSTRAINT "lot_cost_nonnegative";
ALTER TABLE "payment" DROP CONSTRAINT "payment_nonzero";
ALTER TABLE "workerjob" DROP CONSTRAINT "labor_nonnegative";
ALTER TABLE "workerjob" DROP CONSTRAINT "job_status";
ALTER TABLE "workerearning" DROP CONSTRAINT "earning_nonnegative";
ALTER TABLE "workerpayment" DROP CONSTRAINT "worker_payment_positive";
ALTER TABLE "expense" DROP CONSTRAINT "expense_positive";
    """


MODELS_STATE = (
    "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"
    "xi9u3/jlHuwA=="
)
