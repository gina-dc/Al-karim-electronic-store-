# Accounting and operational policy

## Scope

One owner and one or two authorized operators. Owner/manager/staff roles are supported. Workers are workforce records, not login accounts. No tax, customer credit account, returns, exchanges or opening balances. New stock enters through posted purchase receipts; existing opening stock import is deliberately absent.

## Receipt lifecycle

Creation allocates a visible sequential number using a transaction-locked PostgreSQL counter. Drafts are editable and have no stock or payment effects. Posting validates stock and preserves historical cost. Saving with an initial payment posts the receipt, updates stock and records payment within one database transaction. PDF generation and printing are outside that transaction.

Committed visible numbers are never reused. A rolled-back allocation is not a committed receipt. A UUID is the relationship key; the visible number is a business reference.

## Money and recognition

Money uses Python Decimal and PostgreSQL NUMERIC. Frontend values never determine authoritative totals. Only posted receipts contribute to reports.

- Sale revenue: line totals on the transaction date.
- Repair revenue: line totals on explicit repair completion, after assigned jobs finish or are cancelled.
- Repair collections before completion: advances, not revenue.
- Cash received: signed incoming payment entries within the selected dates. Purchase settlements are outgoing and excluded.
- Customer dues: posted sales/repair total less signed payments as of the report end date. These are contractual receipt dues, including unfinished repair orders; they are not additional recognized revenue.
- Inventory acquisitions: posted purchases, capitalized into stock cost lots, not charged again as operating expenses.
- Cost of goods sold: FIFO lot cost consumed by posted sales. Serialized catalog entries hold at most one unit, giving specific-unit cost.
- Direct period costs: cost of goods sold, recorded repair expenses and completed worker earnings.
- Gross profit: recognized revenue minus direct period costs.
- Net profit: gross profit minus recorded operating expenses.
- Worker cash payments settle liabilities; they do not charge labor cost a second time.

Repair expenses and labor are recognized when incurred/completed, including work on repairs whose revenue has not yet been recognized. This conservative period policy can produce negative profit before a repair is completed. There is no separate work-in-progress capitalization module.

Financial flows use date-range filters. Advances, receivables and worker payable are balances as of the end date. Inventory quantity, condition, acquisition valuation and estimated selling valuation show the current stock snapshot, explicitly identified in the UI. Estimated selling values are not actual revenue. Reports read a consistent PostgreSQL snapshot.

## Stock

Condition and availability are separate. Reserving a catalog entry reserves its entire remaining quantity; partial bulk reservations are not provided. Stock counts change only through transactional purchase/sale posting or explicit correction. Physical condition changes create zero-quantity history entries. Sold-out catalog entries are marked sold and become available again upon a new purchase or an erroneous-sale correction.

Each sale stores original FIFO lot allocations. A void restores those exact lots. A purchased lot cannot be voided after consumption. Stock movements are append-only. Normal customer returns are outside this application.

## Worker jobs and payments

Each job references a specific receipt item and a worker. Multiple jobs/workers can serve one receipt through separate assignments. Assigned and in-progress jobs are pending work and earn nothing. Completing a job creates one uniquely linked earning. Repeated completion cannot duplicate earnings.

Completed and cancelled jobs are locked. Reopening or changing a completed job's compensation is not available in this release; additional authorized work must be recorded as a separate job. This avoids silently changing earned or paid compensation. An unfinished job may be cancelled without earnings.

Worker payable = accumulated completed earnings - recorded payments. Monthly statements include earned, previous unpaid, paid and payable values; payroll recalculation creates no ledger records. Payments cannot exceed eligible earnings, be dated before the latest worker payment, or have future dates. Partial and full settlement use idempotency keys.

## Corrections

Only the owner can reverse a mistaken payment entry. A reversal is a separate negative payment linked uniquely to the original, dated when corrected, with a reason and audit event. This is an accounting-entry correction, not a cash refund.

Only the owner can void an incorrect receipt. It must have zero net recorded settlement and no active or earned worker jobs. Stock and original costs must be restorable; consumed purchases are blocked. The original receipt, number, items, payment records and movements remain. A correction restates that erroneous receipt's earlier revenue reports; its correction audit timestamp and movement remain visible. There is no closing-period or tax-reporting system.

Posted receipts cannot be silently edited. Draft changes have audit events. No endpoint deletes completed financial records.

## Dates and roles

Timestamps are stored in UTC. Reporting boundaries and display use Asia/Karachi and Gregorian dates. Staff can enter only today's transactions. Owner/manager may backdate valid dates; future financial entries are rejected. Backdated sales cannot consume lots acquired after their sale date.

The owner controls financial reports, payroll payments, corrections, settings and accounts. Managers can manage operational records, inventory, purchases and assignments; staff can create sales/repairs, record their collections, and view operational records. All checks run on the backend.
