import { printDocument } from "@/lib/printing"
import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { ArrowUpRight, Plus, Download, Printer } from "lucide-react"
import { api } from "@/lib/api"
import { localDate, money } from "@/lib/types"
import type { User, Row, Page } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { ErrorMessage, PageHeading, Empty } from "@/components/shared"
import type { Receipt } from "./Receipts"
import { ExpenseForm } from "./Expenses"
type Point = Record<string, string | number>
type Report = {
  start: string
  end: string
  kpis: Record<string, string | number>
  dues: Point[]
  payroll: Point[]
  expenses: Row[]
  inventory: Row[]
  movements: Row[]
  jobs: Row[]
  worker_payments: Row[]
  pending_repairs: Row[]
  low_stock: Row[]
}
const metrics: [string, string, string, boolean][] = [
  ["revenue", "کل آمدنی", "Recognized revenue", true],
  ["costs", "کل اخراجات", "Total costs", true],
  ["gross_profit", "مجموعی منافع", "Gross profit", true],
  ["sales_count", "کل فروخت", "Sales receipts", false],
  ["customers", "کل گاہک", "Customers", false],
  ["inventory_items", "کل اسٹاک آئٹمز", "Inventory records", false],
  ["available_stock", "دستیاب سامان", "Available units", false],
  ["under_repair", "زیر مرمت سامان", "Units under repair", false],
  ["dues", "گاہکوں کی بقایا رقم", "Customer dues", true],
  ["worker_due", "کاریگروں کی واجب الادا رقم", "Worker payments due", true],
]
const shifted = (days: number) => {
  const d = new Date(`${localDate()}T12:00:00Z`)
  d.setUTCDate(d.getUTCDate() + days)
  return d.toISOString().slice(0, 10)
}
export default function Dashboard({
  english,
  user,
  reports = false,
}: {
  english: boolean
  user: User
  reports?: boolean
}) {
  const [start, setStart] = useState(localDate().slice(0, 7) + "-01")
  const [end, setEnd] = useState(localDate())
  const [expense, setExpense] = useState(false)
  const query = useQuery({
    queryKey: [reports ? "reports" : "dashboard", start, end],
    queryFn: () =>
      api<Report & { drafts: number }>(
        `/${reports ? "reports" : "dashboard"}?start=${start}&end=${end}`
      ),
  })
  const recent = useQuery({
    queryKey: ["receipts", "recent"],
    queryFn: () => api<Page<Receipt>>("/receipts?limit=5"),
  })
  const payments = useQuery({
    queryKey: ["payments", "recent"],
    queryFn: () => api<Page<Row>>("/payments?limit=5"),
    enabled: user.role === "owner",
  })
  if (query.isPending)
    return (
      <p role="status">
        {english ? "Loading shop records…" : "دکان کا ریکارڈ لوڈ ہو رہا ہے…"}
      </p>
    )
  if (query.error) return <ErrorMessage error={query.error} />
  const data = query.data
  if (!data) return null
  if (user.role !== "owner")
    return (
      <>
        <PageHeading title={english ? "Dashboard" : "ڈیش بورڈ"}>
          <Button
            nativeButton={false}
            role="link"
            render={<Link to="/new-receipt" />}
          >
            <Plus size={16} />
            {english ? "New receipt" : "نئی بلٹی"}
          </Button>
        </PageHeading>
        <div className="kpi-grid">
          <div className="kpi">
            <span>{english ? "Pending repairs" : "نامکمل مرمت"}</span>
            <strong>{String(data.pending_repairs)}</strong>
          </div>
          <div className="kpi">
            <span>{english ? "Draft receipts" : "مسودہ بلٹیاں"}</span>
            <strong>{data.drafts}</strong>
          </div>
        </div>
        <Recent receipts={recent.data?.items ?? []} english={english} />
      </>
    )
  return (
    <>
      <PageHeading
        title={
          reports
            ? english
              ? "Reports"
              : "رپورٹس"
            : english
              ? "Business overview"
              : "کاروبار کا جائزہ"
        }
        description={
          english
            ? "Accrual revenue and cash collections are shown separately. Stock figures reflect current inventory."
            : "آمدنی اور نقد وصولیاں الگ ہیں۔ اسٹاک کے اعداد موجودہ حالت دکھاتے ہیں۔"
        }
      >
        <Button
          nativeButton={false}
          role="link"
          render={<Link to="/new-receipt" />}
        >
          <Plus size={16} />
          {english ? "New receipt" : "نئی بلٹی"}
        </Button>
      </PageHeading>
      <div className="filter-bar no-print">
        <select
          aria-label={english ? "Date preset" : "مدت"}
          defaultValue="month"
          onChange={(e) => {
            const p = e.target.value
            if (p === "custom") return
            setEnd(p === "yesterday" ? shifted(-1) : localDate())
            setStart(
              p === "today"
                ? localDate()
                : p === "yesterday"
                  ? shifted(-1)
                  : p === "week"
                    ? shifted(-6)
                    : localDate().slice(0, 7) + "-01"
            )
          }}
        >
          <option value="today">{english ? "Today" : "آج"}</option>
          <option value="yesterday">{english ? "Yesterday" : "کل"}</option>
          <option value="week">{english ? "Last 7 days" : "گزشتہ ۷ دن"}</option>
          <option value="month">
            {english ? "Current month" : "موجودہ مہینہ"}
          </option>
          <option value="custom">
            {english ? "Custom range" : "اپنی مدت"}
          </option>
        </select>
        <label>
          {english ? "From" : "سے"}
          <input
            type="date"
            value={start}
            max={end}
            onChange={(e) => setStart(e.target.value)}
          />
        </label>
        <label>
          {english ? "To" : "تک"}
          <input
            type="date"
            value={end}
            min={start}
            max={localDate()}
            onChange={(e) => setEnd(e.target.value)}
          />
        </label>
        {reports && (
          <>
            <Button variant="outline" onClick={() => setExpense(true)}>
              <Plus size={16} />
              {english ? "Record expense" : "خرچ درج کریں"}
            </Button>
            <Button variant="outline" onClick={() => printDocument()}>
              <Printer size={16} />
              {english ? "Print report" : "رپورٹ پرنٹ کریں"}
            </Button>
          </>
        )}
      </div>
      <div className="kpi-grid">
        {metrics.map(([key, ur, en, currency]) => (
          <section className="kpi" key={key}>
            <div>
              <span>{english ? en : ur}</span>
              <ArrowUpRight size={16} />
            </div>
            <strong dir="ltr">
              {currency ? money(data.kpis[key]) : data.kpis[key]}
            </strong>
            <small>
              {[
                "customers",
                "inventory_items",
                "available_stock",
                "under_repair",
              ].includes(key)
                ? english
                  ? "Current records"
                  : "موجودہ ریکارڈ"
                : `${data.start} — ${data.end}`}
            </small>
          </section>
        ))}
      </div>
      <div className="summary-strip">
        <span>
          {english ? "Cash received" : "نقد وصولیاں"}:{" "}
          <strong>{money(data.kpis.cash_received)}</strong>
        </span>
        <span>
          {english ? "Customer advances" : "گاہکوں کے ایڈوانس"}:{" "}
          <strong>{money(data.kpis.advances)}</strong>
        </span>
        <span>
          {english ? "Net profit" : "خالص منافع"}:{" "}
          <strong>{money(data.kpis.net_profit)}</strong>
        </span>
      </div>
      {reports && (
        <>
          <section className="panel">
            <h2>
              {english ? "Financial reconciliation" : "مالی حساب کی تفصیل"}
            </h2>
            <div className="financial-grid">
              {Object.entries(data.kpis)
                .filter(
                  ([k]) =>
                    ![
                      "customers",
                      "inventory_items",
                      "available_stock",
                      "under_repair",
                      "sales_count",
                    ].includes(k)
                )
                .map(([key, value]) => (
                  <div key={key}>
                    <span>
                      {financialLabels[key]?.[english ? 1 : 0] ?? key}
                    </span>
                    <strong>{money(value)}</strong>
                  </div>
                ))}
            </div>
            <div className="form-actions no-print">
              <Button
                variant="outline"
                nativeButton={false}
                role="link"
                render={
                  <a
                    href={`/api/v1/reports/export.pdf?start=${start}&end=${end}`}
                    download
                  />
                }
              >
                <Download size={16} />
                {english ? "Report PDF" : "رپورٹ PDF"}
              </Button>
              {[
                "summary",
                "dues",
                "payroll",
                "expenses",
                "inventory",
                "jobs",
                "movements",
                "worker_payments",
              ].map((kind) => (
                <Button
                  key={kind}
                  variant="outline"
                  nativeButton={false}
                  role="link"
                  render={
                    <a
                      href={`/api/v1/reports/export.csv?kind=${kind}&start=${start}&end=${end}`}
                      download
                    />
                  }
                >
                  <Download size={16} />
                  {
                    {
                      summary: english ? "Summary CSV" : "خلاصہ CSV",
                      dues: english ? "Dues CSV" : "بقایا CSV",
                      payroll: english ? "Payroll CSV" : "کاریگر CSV",
                      expenses: english ? "Expenses CSV" : "اخراجات CSV",
                      inventory: english ? "Inventory CSV" : "اسٹاک CSV",
                      jobs: english ? "Jobs CSV" : "مرمت CSV",
                      movements: english
                        ? "Stock movements CSV"
                        : "اسٹاک کی حرکت CSV",
                      worker_payments: english
                        ? "Worker payments CSV"
                        : "کاریگر ادائیگیاں CSV",
                    }[kind]
                  }
                </Button>
              ))}
            </div>
          </section>
        </>
      )}
      {reports && <ReportTables data={data} english={english} />}
      <div className="tables-grid">
        <Recent receipts={recent.data?.items ?? []} english={english} />
        <section className="panel">
          <h2>{english ? "Outstanding customer dues" : "گاہکوں کا بقایا"}</h2>
          {!data.dues.length ? (
            <Empty english={english} />
          ) : (
            <div className="table-wrap">
              <table>
                <tbody>
                  {data.dues.map((r) => (
                    <tr key={String(r.id)}>
                      <td>
                        <Link className="text-link" to={`/receipts/${r.id}`}>
                          {r.number}
                        </Link>
                      </td>
                      <td>{r.customer}</td>
                      <td>{money(r.balance)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
        <section className="panel">
          <h2>
            {english ? "Worker payment summary" : "کاریگروں کی ادائیگیاں"}
          </h2>
          {!data.payroll.length ? (
            <Empty english={english} />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    {(english
                      ? ["Worker", "Earned", "Paid", "Due"]
                      : ["کاریگر", "کمائی", "ادا شدہ", "بقایا"]
                    ).map((t) => (
                      <th key={t}>{t}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.payroll.map((r) => (
                    <tr key={String(r.id)}>
                      <td>{r.name}</td>
                      <td>{money(r.earned)}</td>
                      <td>{money(r.paid)}</td>
                      <td>{money(r.payable)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
        <section className="panel">
          <h2>{english ? "Pending repairs" : "نامکمل مرمت"}</h2>
          {data.pending_repairs.length ? (
            data.pending_repairs.map((r) => (
              <p key={r.id}>
                <Link className="text-link" to={`/receipts/${r.id}`}>
                  {String(r.number)}
                </Link>{" "}
                — {String(r.work_description)}
              </p>
            ))
          ) : (
            <Empty english={english} />
          )}
        </section>
        <section className="panel">
          <h2>
            {english
              ? "Low stock alerts (2 units or fewer)"
              : "کم اسٹاک (۲ یا کم)"}
          </h2>
          {data.low_stock.length ? (
            data.low_stock.map((r) => (
              <p key={r.id}>
                {String(r.name)} — {String(r.quantity)}
              </p>
            ))
          ) : (
            <Empty english={english} />
          )}
        </section>
        <section className="panel">
          <h2>{english ? "Recent payments" : "حالیہ ادائیگیاں"}</h2>
          {payments.data?.items.length ? (
            payments.data.items.map((r) => (
              <div className="list-line" key={r.id}>
                <span>{String(r.payment_date)}</span>
                <strong>{money(r.amount)}</strong>
              </div>
            ))
          ) : (
            <Empty english={english} />
          )}
        </section>
      </div>
      {expense && (
        <ExpenseForm english={english} close={() => setExpense(false)} />
      )}
    </>
  )
}
function Recent({
  receipts,
  english,
}: {
  receipts: Receipt[]
  english: boolean
}) {
  return (
    <section className="panel">
      <h2>{english ? "Recent receipts" : "حالیہ بلٹیاں"}</h2>
      {!receipts.length ? (
        <Empty english={english} />
      ) : (
        receipts.map((r) => (
          <div className="list-line" key={r.id}>
            <Link className="text-link" to={`/receipts/${r.id}`}>
              {r.number}
            </Link>
            <span>
              {String(r.customer?.name ?? (english ? "Walk-in" : "واک اِن"))}
            </span>
            <strong>{money(r.total)}</strong>
          </div>
        ))
      )}
    </section>
  )
}
const financialLabels: Record<string, [string, string]> = {
  revenue: ["تسلیم شدہ آمدنی", "Recognized revenue"],
  sales_revenue: ["فروخت کی آمدنی", "Sales revenue"],
  repair_revenue: ["مکمل مرمت کی آمدنی", "Completed repair revenue"],
  costs: ["کل اخراجات", "Total costs"],
  gross_profit: ["مجموعی منافع", "Gross profit"],
  net_profit: ["خالص منافع", "Net profit"],
  stock_cost: ["فروخت شدہ سامان کی لاگت", "Cost of goods sold"],
  repair_cost: ["مرمت کے اخراجات", "Repair expenses"],
  labor_cost: ["کاریگر کی مزدوری", "Worker labor cost"],
  operating_expenses: ["دکان کے اخراجات", "Operating expenses"],
  cash_received: ["وصول شدہ رقم", "Cash received"],
  advances: ["نامکمل مرمت کے ایڈوانس", "Unrecognized repair advances"],
  dues: ["گاہکوں کی بقایا رقم", "Customer dues"],
  worker_due: ["کاریگروں کا بقایا", "Worker payable"],
  acquisitions: ["خریداری کی لاگت", "Inventory acquisitions"],
  inventory_cost: ["موجودہ اسٹاک کی لاگت", "Current stock cost"],
  estimated_inventory_value: [
    "اسٹاک کی تخمینی فروخت قیمت",
    "Estimated stock selling value",
  ],
}

function ReportTables({ data, english }: { data: Report; english: boolean }) {
  const tables: [string, string, Row[], [string, string, string][]][] = [
    [
      "اسٹاک کی قدر",
      "Inventory valuation",
      data.inventory,
      [
        ["code", "کوڈ", "Code"],
        ["name", "سامان", "Equipment"],
        ["quantity", "تعداد", "Quantity"],
        ["cost", "اصل لاگت", "Cost"],
        [
          "estimated_selling_value",
          "تخمینی فروخت قیمت",
          "Estimated selling value",
        ],
      ],
    ],
    [
      "مرمت کے کام",
      "Repair jobs",
      data.jobs,
      [
        ["receipt_number", "بلٹی", "Receipt"],
        ["equipment", "سامان", "Equipment"],
        ["worker", "کاریگر", "Worker"],
        ["status", "حالت", "Status"],
        ["labor_amount", "مزدوری", "Labor"],
      ],
    ],
    [
      "اسٹاک کی حرکت",
      "Stock movements",
      data.movements,
      [
        ["code", "کوڈ", "Code"],
        ["name", "سامان", "Equipment"],
        ["kind", "حرکت", "Movement"],
        ["quantity", "تعداد", "Quantity"],
        ["cost", "لاگت", "Cost"],
        ["receipt_number", "بلٹی", "Receipt"],
      ],
    ],
    [
      "اخراجات",
      "Expenses",
      data.expenses,
      [
        ["expense_date", "تاریخ", "Date"],
        ["description", "تفصیل", "Description"],
        ["category", "قسم", "Category"],
        ["amount", "رقم", "Amount"],
      ],
    ],
  ]
  return (
    <>
      {tables.map(([ur, en, rows, columns]) => (
        <section className="panel" key={en}>
          <h2>{english ? en : ur}</h2>
          {!rows.length ? (
            <Empty english={english} />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    {columns.map(([key, ur, en]) => (
                      <th key={key}>{english ? en : ur}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, index) => (
                    <tr key={index}>
                      {columns.map(([key]) => (
                        <td key={key}>
                          {[
                            "cost",
                            "estimated_selling_value",
                            "labor_amount",
                            "amount",
                          ].includes(key)
                            ? money(row[key])
                            : String(row[key] ?? "—")}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      ))}
    </>
  )
}
