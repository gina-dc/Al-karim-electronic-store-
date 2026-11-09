import { printDocument } from "@/lib/printing"
import { useState } from "react"
import { Link } from "react-router-dom"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Plus, Search, Pencil, History } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Empty, ErrorMessage, Modal, PageHeading } from "@/components/shared"
import { api } from "@/lib/api"
import { labels } from "@/lib/resources"
import { localDate, money } from "@/lib/types"
import type { Page, Resource, Row, User } from "@/lib/types"
const formSchema = z.record(z.string(), z.string())
function Editor({
  config,
  english,
  existing,
  close,
}: {
  config: Resource
  english: boolean
  existing: Row | null
  close: () => void
}) {
  const cache = useQueryClient()
  const defaults = Object.fromEntries(
    config.fields.map((f) => [
      f.key,
      String(
        existing?.[f.key] ??
          f.initial ??
          (f.type === "date"
            ? localDate()
            : (f.options?.[0]?.value ?? (f.type === "number" ? "0" : "")))
      ),
    ])
  )
  const form = useForm<Record<string, string>>({
    resolver: zodResolver(formSchema),
    defaultValues: defaults,
  })
  const save = useMutation({
    mutationFn: (data: Record<string, string>) => {
      const payload: Record<string, unknown> = { ...data }
      if ("serial_number" in payload && !payload.serial_number)
        payload.serial_number = null
      if ("active" in payload) payload.active = payload.active === "true"
      return api(`/${config.path}${existing ? `/${existing.id}` : ""}`, {
        method: existing ? "PATCH" : "POST",
        body: JSON.stringify(payload),
      })
    },
    onSuccess: () => {
      void cache.invalidateQueries()
      close()
    },
  })
  return (
    <Modal title={english ? "Record details" : "ریکارڈ کی تفصیل"} close={close}>
      <form
        onSubmit={form.handleSubmit((data) => save.mutate(data))}
        className="editor-grid"
      >
        {config.fields.map((f) => (
          <label key={f.key}>
            {english ? f.en : f.ur}
            {f.required && " *"}
            {f.type === "select" ? (
              <select {...form.register(f.key)}>
                {f.options?.map((o) => (
                  <option value={o.value} key={o.value}>
                    {english ? o.en : o.ur}
                  </option>
                ))}
              </select>
            ) : f.type === "textarea" ? (
              <textarea {...form.register(f.key)} />
            ) : (
              <input
                type={f.type ?? "text"}
                required={f.required}
                min={f.type === "number" ? 0 : undefined}
                step={f.type === "number" ? "0.01" : undefined}
                {...form.register(f.key)}
              />
            )}
          </label>
        ))}
        <div className="form-footer">
          <ErrorMessage error={save.error} />
          <Button disabled={save.isPending} type="submit">
            {save.isPending
              ? english
                ? "Saving…"
                : "محفوظ ہو رہا ہے…"
              : english
                ? "Save"
                : "محفوظ کریں"}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
export default function ResourcePage({
  config,
  english,
  user,
}: {
  config: Resource
  english: boolean
  user: User
}) {
  const [search, setSearch] = useState("")
  const [offset, setOffset] = useState(0)
  const [editing, setEditing] = useState<Row | null | undefined>(undefined)
  const [history, setHistory] = useState<Row | null>(null)
  const [period, setPeriod] = useState(localDate().slice(0, 7))
  const records = useQuery({
    queryKey: [config.path, search, offset],
    queryFn: () =>
      api<Page<Row>>(
        `/${config.path}?search=${encodeURIComponent(search)}&offset=${offset}&limit=25`
      ),
  })
  const historyQuery = useQuery({
    queryKey: [config.path, "history", history?.id, period],
    queryFn: () =>
      api<unknown>(
        `/${config.path}/${history?.id}/${config.path === "inventory" ? "movements" : config.path === "workers" ? `statement?start=${period}-01&end=${new Date(Number(period.slice(0, 4)), Number(period.slice(5, 7)), 0).toLocaleDateString("en-CA")}` : "history"}`
      ),
    enabled: !!history,
  })
  const editable = !config.ownerOnly || user.role !== "staff"
  const label = (key: string) => {
    const f = config.fields.find((f) => f.key === key)
    return f ? (english ? f.en : f.ur) : (labels[key]?.[english ? 1 : 0] ?? key)
  }
  const display = (key: string, value: unknown) => {
    if (key.includes("price") || key.includes("cost")) return money(value)
    if (key === "active")
      return value
        ? english
          ? "Active"
          : "فعال"
        : english
          ? "Inactive"
          : "غیر فعال"
    const options = config.fields.find((f) => f.key === key)?.options
    const option = options?.find((o) => o.value === value)
    return option ? (english ? option.en : option.ur) : String(value ?? "—")
  }
  return (
    <>
      <PageHeading
        title={english ? config.en : config.ur}
        description={
          config.path === "inventory"
            ? english
              ? "Register equipment here, then receive stock through a purchase receipt."
              : "سامان درج کریں، پھر خریداری کی بلٹی سے اسٹاک شامل کریں۔"
            : undefined
        }
      >
        {editable && (
          <Button onClick={() => setEditing(null)}>
            <Plus size={16} />
            {english ? "New record" : "نیا ریکارڈ"}
          </Button>
        )}
      </PageHeading>
      <div className="search-bar">
        <Search size={17} />
        <input
          value={search}
          onChange={(e) => {
            setSearch(e.target.value)
            setOffset(0)
          }}
          placeholder={english ? "Search records…" : "ریکارڈ تلاش کریں…"}
        />
      </div>
      <ErrorMessage error={records.error} />
      {records.isPending ? (
        <p role="status">{english ? "Loading…" : "انتظار فرمائیں…"}</p>
      ) : !records.data?.items.length ? (
        <Empty english={english} />
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {config.columns.map((c) => (
                  <th key={c}>{label(c)}</th>
                ))}
                <th>{english ? "Actions" : "عمل"}</th>
              </tr>
            </thead>
            <tbody>
              {records.data.items.map((r) => (
                <tr key={r.id}>
                  {config.columns.map((c) => (
                    <td key={c}>{display(c, r[c])}</td>
                  ))}
                  <td className="table-actions">
                    {editable && config.editable && (
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => setEditing(r)}
                        aria-label={english ? "Edit" : "ترمیم"}
                      >
                        <Pencil size={16} />
                      </Button>
                    )}
                    {(config.path !== "inventory" || user.role !== "staff") &&
                      (config.path !== "workers" || user.role === "owner") && (
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setHistory(r)}
                          aria-label={english ? "History" : "تفصیل"}
                        >
                          <History size={16} />
                        </Button>
                      )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="pagination">
        <Button
          variant="outline"
          disabled={!offset}
          onClick={() => setOffset(Math.max(0, offset - 25))}
        >
          {english ? "Previous" : "پچھلا"}
        </Button>
        <span>
          {records.data?.total ?? 0} {english ? "records" : "ریکارڈ"}
        </span>
        <Button
          variant="outline"
          disabled={offset + 25 >= (records.data?.total ?? 0)}
          onClick={() => setOffset(offset + 25)}
        >
          {english ? "Next" : "اگلا"}
        </Button>
      </div>
      {editing !== undefined && (
        <Editor
          key={editing?.id ?? "new"}
          config={config}
          english={english}
          existing={editing}
          close={() => setEditing(undefined)}
        />
      )}{" "}
      {history && (
        <Modal
          title={String(history.name ?? "")}
          close={() => setHistory(null)}
        >
          {config.path === "workers" && (
            <div className="filter-bar no-print">
              <label>
                {english ? "Month" : "مہینہ"}
                <input
                  type="month"
                  value={period}
                  onChange={(e) => setPeriod(e.target.value)}
                />
              </label>
              <Button variant="outline" onClick={() => printDocument()}>
                {english ? "Print" : "پرنٹ"}
              </Button>
              <Button
                nativeButton={false}
                role="link"
                render={
                  <a
                    href={`/api/v1/workers/${history.id}/statement.pdf?start=${period}-01&end=${new Date(Number(period.slice(0, 4)), Number(period.slice(5, 7)), 0).toLocaleDateString("en-CA")}`}
                    download
                  />
                }
              >
                {english ? "Statement PDF" : "بیان PDF"}
              </Button>
            </div>
          )}
          <ErrorMessage error={historyQuery.error} />
          {historyQuery.isPending ? (
            <p role="status">{english ? "Loading…" : "انتظار فرمائیں…"}</p>
          ) : (
            <HistoryView data={historyQuery.data} english={english} />
          )}
        </Modal>
      )}
    </>
  )
}
function HistoryView({ data, english }: { data: unknown; english: boolean }) {
  const obj = data as Record<string, unknown>
  if (!obj) return null
  const movement = Array.isArray(data)
  const customer = Array.isArray(obj.receipts)
  const payroll = Array.isArray(obj.jobs)
  const rows = (
    movement ? data : customer ? obj.receipts : payroll ? obj.jobs : []
  ) as Row[]
  const columns = movement
    ? ["created_at", "kind", "quantity", "cost", "notes"]
    : customer
      ? [
          "number",
          "transaction_date",
          "transaction_type",
          "total",
          "paid",
          "balance",
        ]
      : [
          "description",
          "assigned_date",
          "completed_at",
          "status",
          "labor_amount",
        ]
  const titles: Record<string, [string, string]> = {
    created_at: ["تاریخ", "Date"],
    kind: ["حرکت", "Movement"],
    quantity: ["تعداد", "Quantity"],
    cost: ["لاگت", "Cost"],
    notes: ["نوٹس", "Notes"],
    number: ["بلٹی", "Receipt"],
    transaction_date: ["تاریخ", "Date"],
    transaction_type: ["قسم", "Type"],
    total: ["کل رقم", "Total"],
    paid: ["ادا شدہ", "Paid"],
    balance: ["بقایا", "Dues"],
    description: ["کام", "Work"],
    assigned_date: ["تفویض کی تاریخ", "Assigned"],
    completed_at: ["تکمیل", "Completed"],
    status: ["حالت", "Status"],
    labor_amount: ["مزدوری", "Labor"],
  }
  return (
    <div className="history-content">
      {payroll && (
        <div className="summary-strip">
          <span>
            {english ? "Earned" : "کمائی"}: {money(obj.earned)}
          </span>
          <span>
            {english ? "Previous unpaid" : "پچھلا بقایا"}:{" "}
            {money(obj.previous_unpaid)}
          </span>
          <span>
            {english ? "Paid" : "ادا شدہ"}: {money(obj.paid)}
          </span>
          <span>
            {english ? "Payable" : "واجب الادا"}: {money(obj.payable)}
          </span>
        </div>
      )}
      {!rows.length ? (
        <Empty english={english} />
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {columns.map((k) => (
                  <th key={k}>{titles[k]?.[english ? 1 : 0] ?? k}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  {columns.map((k) => (
                    <td key={k}>
                      {k === "number" ? (
                        <Link className="text-link" to={`/receipts/${r.id}`}>
                          {String(r[k])}
                        </Link>
                      ) : [
                          "cost",
                          "total",
                          "paid",
                          "balance",
                          "labor_amount",
                        ].includes(k) ? (
                        money(r[k])
                      ) : (
                        String(r[k] ?? "—")
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {payroll && (
        <>
          <h2>{english ? "Payment history" : "ادائیگیوں کی تفصیل"}</h2>
          <div className="table-wrap">
            <table>
              <tbody>
                {(obj.payments as Row[]).map((p) => (
                  <tr key={p.id}>
                    <td>{String(p.payment_date)}</td>
                    <td>{money(p.amount)}</td>
                    <td>{String(p.method)}</td>
                    <td>
                      <a
                        className="text-link"
                        href={`/api/v1/worker-payments/${p.id}/pdf`}
                        download
                      >
                        {english
                          ? "Payment receipt PDF"
                          : "ادائیگی کی رسید PDF"}
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}
