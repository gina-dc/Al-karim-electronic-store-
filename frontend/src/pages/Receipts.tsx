import { printDocument } from "@/lib/printing"
import { useState, useEffect } from "react"
import { useNavigate, useParams, Link } from "react-router-dom"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Plus, Trash2, Printer, Download, Search } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Empty, ErrorMessage, PageHeading, Modal } from "@/components/shared"
import { RecordSelect } from "@/components/RecordSelect"
import { api } from "@/lib/api"
import { localDate, money } from "@/lib/types"
import type { Page, Row, User } from "@/lib/types"
type Line = {
  inventory_id: string | null
  name: string
  category: string
  brand: string
  model: string
  serial_number: string
  quantity: number
  unit_price: string
}
export type Receipt = Row & {
  number: string
  status: string
  transaction_type: string
  transaction_date: string
  customer_id: string | null
  customer: Row | null
  total: string
  paid: string
  balance: string
  payment_status: string
  notes: string
  work_description: string
  completed_at: string | null
  items: (Line & { id: string })[]
}
const blank = (): Line => ({
  inventory_id: null,
  name: "",
  category: "",
  brand: "",
  model: "",
  serial_number: "",
  quantity: 1,
  unit_price: "0",
})
const typeName = (type: string, en: boolean) =>
  ({
    sale: en ? "Sale" : "فروخت",
    repair: en ? "Repair service" : "مرمت",
    purchase: en ? "Purchase" : "خریداری",
  })[type] ?? type
const partyLabel = (type: string, english: boolean) =>
  type === "purchase"
    ? english
      ? "Seller"
      : "فروخت کنندہ"
    : type === "sale"
      ? english
        ? "Buyer"
        : "خریدار"
      : english
        ? "Customer"
        : "گاہک"
export function ReceiptList({ english }: { english: boolean }) {
  const [search, setSearch] = useState("")
  const [offset, setOffset] = useState(0)
  const [type, setType] = useState("")
  const [paymentStatus, setPaymentStatus] = useState("")
  const [sort, setSort] = useState("-created_at")
  const [start, setStart] = useState("")
  const [end, setEnd] = useState("")
  const query = useQuery({
    queryKey: [
      "receipts",
      search,
      offset,
      type,
      start,
      end,
      paymentStatus,
      sort,
    ],
    queryFn: () =>
      api<Page<Receipt>>(
        `/receipts?search=${encodeURIComponent(search)}&offset=${offset}&limit=25&sort=${sort}${paymentStatus ? `&payment_status=${paymentStatus}` : ""}${type ? `&transaction_type=${type}` : ""}${start ? `&start=${start}` : ""}${end ? `&end=${end}` : ""}`
      ),
  })
  return (
    <>
      <PageHeading title={english ? "Receipt records" : "بلٹی کا ریکارڈ"}>
        <Button
          nativeButton={false}
          role="link"
          render={<Link to="/new-receipt" />}
        >
          <Plus size={16} />
          {english ? "New receipt" : "نئی بلٹی"}
        </Button>
      </PageHeading>
      <div className="filter-bar">
        <div className="search-bar">
          <Search size={16} />
          <input
            placeholder={
              english ? "Receipt number or customer…" : "بلٹی نمبر یا گاہک…"
            }
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setOffset(0)
            }}
          />
        </div>
        <select
          aria-label={english ? "Transaction type" : "لین دین کی قسم"}
          value={type}
          onChange={(e) => {
            setType(e.target.value)
            setOffset(0)
          }}
        >
          <option value="">{english ? "All types" : "تمام اقسام"}</option>
          {["sale", "repair", "purchase"].map((t) => (
            <option value={t} key={t}>
              {typeName(t, english)}
            </option>
          ))}
        </select>
        <select
          aria-label={english ? "Payment status" : "ادائیگی کی حالت"}
          value={paymentStatus}
          onChange={(e) => {
            setPaymentStatus(e.target.value)
            setOffset(0)
          }}
        >
          <option value="">
            {english ? "All payment statuses" : "ادائیگی کی تمام حالتیں"}
          </option>
          <option value="unpaid">{english ? "Unpaid" : "غیر ادا شدہ"}</option>
          <option value="partial">
            {english ? "Partial payment" : "جزوی ادائیگی"}
          </option>
          <option value="paid">
            {english ? "Fully paid" : "مکمل ادائیگی"}
          </option>
        </select>
        <select
          aria-label={english ? "Sort receipts" : "ترتیب"}
          value={sort}
          onChange={(e) => {
            setSort(e.target.value)
            setOffset(0)
          }}
        >
          <option value="-created_at">
            {english ? "Newest first" : "نئی پہلے"}
          </option>
          <option value="transaction_date">
            {english ? "Date: oldest first" : "تاریخ: پرانی پہلے"}
          </option>
          <option value="-total">
            {english ? "Highest amount first" : "زیادہ رقم پہلے"}
          </option>
          <option value="total">
            {english ? "Lowest amount first" : "کم رقم پہلے"}
          </option>
        </select>
        <label>
          {english ? "From" : "سے"}
          <input
            type="date"
            value={start}
            onChange={(e) => {
              setStart(e.target.value)
              setOffset(0)
            }}
          />
        </label>
        <label>
          {english ? "To" : "تک"}
          <input
            type="date"
            value={end}
            onChange={(e) => {
              setEnd(e.target.value)
              setOffset(0)
            }}
          />
        </label>
      </div>
      <ErrorMessage error={query.error} />
      {query.isPending ? (
        <p role="status">{english ? "Loading…" : "انتظار فرمائیں…"}</p>
      ) : !query.data?.items.length ? (
        <Empty english={english} />
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {(english
                  ? [
                      "Receipt",
                      "Date",
                      "Customer",
                      "Type",
                      "Total",
                      "Paid",
                      "Dues",
                      "Status",
                    ]
                  : [
                      "بلٹی",
                      "تاریخ",
                      "گاہک",
                      "قسم",
                      "کل رقم",
                      "ادا شدہ",
                      "بقایا",
                      "حالت",
                    ]
                ).map((h) => (
                  <th key={h}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {query.data.items.map((r) => (
                <tr key={r.id}>
                  <td>
                    <Link className="text-link" to={`/receipts/${r.id}`}>
                      {r.number}
                    </Link>
                  </td>
                  <td>{r.transaction_date}</td>
                  <td>
                    {String(
                      r.customer?.name ?? (english ? "Walk-in" : "واک اِن")
                    )}
                  </td>
                  <td>{typeName(r.transaction_type, english)}</td>
                  <td>{money(r.total)}</td>
                  <td>{money(r.paid)}</td>
                  <td>{money(r.balance)}</td>
                  <td>
                    <span className={`badge ${r.status}`}>
                      {r.status === "draft"
                        ? english
                          ? "Draft"
                          : "مسودہ"
                        : r.status === "void"
                          ? english
                            ? "Void"
                            : "منسوخ"
                          : r.payment_status === "paid"
                            ? english
                              ? "Paid"
                              : "مکمل ادائیگی"
                            : english
                              ? "Dues"
                              : "بقایا"}
                    </span>
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
          onClick={() => setOffset(offset - 25)}
        >
          {english ? "Previous" : "پچھلا"}
        </Button>
        <span>{query.data?.total ?? 0}</span>
        <Button
          variant="outline"
          disabled={offset + 25 >= (query.data?.total ?? 0)}
          onClick={() => setOffset(offset + 25)}
        >
          {english ? "Next" : "اگلا"}
        </Button>
      </div>
    </>
  )
}
export function ReceiptEditor({
  english,
  user,
}: {
  english: boolean
  user: User
}) {
  const { id } = useParams()
  const query = useQuery({
    queryKey: ["receipt", id],
    queryFn: () => api<Receipt>(`/receipts/${id}`),
    enabled: !!id,
  })
  if (id && query.isPending)
    return <p role="status">{english ? "Loading…" : "انتظار فرمائیں…"}</p>
  if (query.error) return <ErrorMessage error={query.error} />
  return (
    <ReceiptForm
      key={id ?? "new"}
      english={english}
      user={user}
      existing={query.data}
    />
  )
}
function ReceiptForm({
  english,
  user,
  existing,
}: {
  english: boolean
  user: User
  existing?: Receipt
}) {
  const navigate = useNavigate()
  const cache = useQueryClient()
  const [key] = useState(() => crypto.randomUUID())
  const [customer, setCustomer] = useState(existing?.customer_id ?? "")
  const [type, setType] = useState(existing?.transaction_type ?? "repair")
  const [date, setDate] = useState(existing?.transaction_date ?? localDate())
  const [items, setItems] = useState<Line[]>(existing?.items ?? [blank()])
  const [notes, setNotes] = useState(existing?.notes ?? "")
  const [description, setDescription] = useState(
    existing?.work_description ?? ""
  )
  const [advance, setAdvance] = useState("0")
  const [method, setMethod] = useState("cash")
  const save = useMutation({
    mutationFn: ({ post, print }: { post: boolean; print: boolean }) =>
      api<Receipt>(existing ? `/receipts/${existing.id}` : "/receipts", {
        method: existing ? "PUT" : "POST",
        headers: { "Idempotency-Key": key },
        body: JSON.stringify({
          customer_id: customer || null,
          transaction_type: type,
          transaction_date: date,
          items: items.map(
            ({
              inventory_id,
              name,
              category,
              brand,
              model,
              serial_number,
              quantity,
              unit_price,
            }) => ({
              inventory_id,
              name,
              category,
              brand,
              model,
              serial_number,
              quantity,
              unit_price,
            })
          ),
          notes,
          work_description: description,
          post,
          initial_payment: post ? advance : "0",
          payment_method: method,
        }),
      }).then((r) => ({ r, print })),
    onSuccess: ({ r, print }) => {
      void cache.invalidateQueries()
      navigate(`/receipts/${r.id}${print ? "?print=1" : ""}`)
    },
  })
  const change = (i: number, patch: Partial<Line>) =>
    setItems(items.map((r, index) => (index === i ? { ...r, ...patch } : r)))
  return (
    <>
      <PageHeading
        title={
          existing
            ? english
              ? `Edit draft ${existing.number}`
              : `مسودہ ${existing.number} میں ترمیم`
            : english
              ? "New receipt"
              : "نئی بلٹی"
        }
        description={
          english
            ? "Save a draft, or post the receipt to record the transaction."
            : "مسودہ محفوظ کریں یا لین دین مکمل کرنے کے لیے بلٹی حتمی کریں۔"
        }
      />
      <form
        className="receipt-form"
        onSubmit={(e) => {
          e.preventDefault()
          const submitter = (e.nativeEvent as SubmitEvent)
            .submitter as HTMLButtonElement
          save.mutate({
            post: submitter?.value !== "draft",
            print: submitter?.value === "print",
          })
        }}
      >
        <section className="panel editor-grid">
          <label>
            {partyLabel(type, english)} {english ? "(optional)" : "(اختیاری)"}
            <RecordSelect
              label={partyLabel(type, english)}
              path="customers"
              value={customer}
              onChange={setCustomer}
              english={english}
            />
          </label>
          <label>
            {english ? "Transaction type" : "لین دین کی قسم"}
            <select
              aria-label={english ? "Transaction type" : "لین دین کی قسم"}
              value={type}
              onChange={(e) => setType(e.target.value)}
            >
              {(user.role === "staff"
                ? ["sale", "repair"]
                : ["sale", "repair", "purchase"]
              ).map((t) => (
                <option key={t} value={t}>
                  {typeName(t, english)}
                </option>
              ))}
            </select>
          </label>
          <label>
            {english ? "Date" : "تاریخ"}
            <input
              type="date"
              required
              max={localDate()}
              value={date}
              onChange={(e) => setDate(e.target.value)}
            />
          </label>
        </section>
        <section className="panel">
          <h2>{english ? "Equipment and services" : "سامان اور خدمات"}</h2>
          {items.map((item, i) => (
            <div className="line-item" key={i}>
              {type !== "repair" && (
                <label>
                  {english ? "Inventory item" : "اسٹاک کا سامان"}
                  <RecordSelect
                    label={english ? "Inventory item" : "اسٹاک کا سامان"}
                    path="inventory"
                    value={item.inventory_id ?? ""}
                    required
                    onChange={(id, r) =>
                      change(i, {
                        inventory_id: id || null,
                        ...(r
                          ? {
                              name: String(r.name),
                              category: String(r.category),
                              brand: String(r.brand),
                              model: String(r.model),
                              serial_number: String(r.serial_number ?? ""),
                              unit_price:
                                type === "sale"
                                  ? String(r.selling_price)
                                  : item.unit_price,
                            }
                          : {}),
                      })
                    }
                    english={english}
                  />
                </label>
              )}
              <label>
                {english ? "Equipment / service" : "سامان / خدمت"}
                <input
                  required
                  maxLength={200}
                  value={item.name}
                  onChange={(e) => change(i, { name: e.target.value })}
                />
              </label>
              <label>
                {english ? "Category" : "قسم"}
                <input
                  value={item.category}
                  maxLength={100}
                  onChange={(e) => change(i, { category: e.target.value })}
                />
              </label>
              <label>
                {english ? "Brand / model" : "برانڈ / ماڈل"}
                <input
                  value={item.brand}
                  maxLength={100}
                  onChange={(e) => change(i, { brand: e.target.value })}
                />
                <input
                  aria-label={english ? "Model" : "ماڈل"}
                  value={item.model}
                  maxLength={100}
                  onChange={(e) => change(i, { model: e.target.value })}
                />
              </label>
              <label>
                {english ? "Serial number" : "سیریل نمبر"}
                <input
                  value={item.serial_number}
                  maxLength={100}
                  onChange={(e) => change(i, { serial_number: e.target.value })}
                />
              </label>
              <label>
                {english ? "Quantity" : "تعداد"}
                <input
                  type="number"
                  required
                  min={1}
                  max={100000}
                  step={1}
                  value={item.quantity}
                  onChange={(e) =>
                    change(i, { quantity: Number(e.target.value) })
                  }
                />
              </label>
              <label>
                {english ? "Unit price (Rs.)" : "فی عدد قیمت (روپے)"}
                <input
                  type="number"
                  required
                  min={0}
                  step="0.01"
                  value={item.unit_price}
                  onChange={(e) => change(i, { unit_price: e.target.value })}
                />
              </label>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                disabled={items.length === 1}
                onClick={() => setItems(items.filter((_, n) => n !== i))}
                aria-label={english ? "Remove item" : "آئٹم ہٹائیں"}
              >
                <Trash2 size={16} />
              </Button>
            </div>
          ))}
          <Button
            type="button"
            variant="outline"
            onClick={() => setItems([...items, blank()])}
          >
            <Plus size={16} />
            {english ? "Add item" : "آئٹم شامل کریں"}
          </Button>
        </section>
        <section className="panel editor-grid">
          <label>
            {english ? "Work description" : "کام کی تفصیل"}
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </label>
          <label>
            {english ? "Notes" : "نوٹس"}
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </label>
          {!existing && (
            <>
              <label>
                {type === "purchase"
                  ? english
                    ? "Amount paid to seller"
                    : "فروخت کنندہ کو ادا شدہ رقم"
                  : english
                    ? "Initial amount received"
                    : "وصول شدہ رقم / ایڈوانس"}
                <input
                  type="number"
                  min={0}
                  step="0.01"
                  value={advance}
                  onChange={(e) => setAdvance(e.target.value)}
                />
              </label>
              <label>
                {english ? "Payment method" : "ادائیگی کا طریقہ"}
                <select
                  value={method}
                  onChange={(e) => setMethod(e.target.value)}
                >
                  <option value="cash">{english ? "Cash" : "نقد"}</option>
                  <option value="bank_transfer">
                    {english ? "Bank transfer" : "بینک ٹرانسفر"}
                  </option>
                  <option value="other">{english ? "Other" : "دیگر"}</option>
                </select>
              </label>
            </>
          )}
        </section>
        <ErrorMessage error={save.error} />
        <div className="form-actions">
          <Button
            type="submit"
            name="action"
            value="draft"
            variant="outline"
            disabled={save.isPending}
          >
            {english ? "Save draft" : "مسودہ محفوظ کریں"}
          </Button>
          {!existing && (
            <>
              <Button
                type="submit"
                name="action"
                value="post"
                disabled={save.isPending}
              >
                {english ? "Save and post" : "محفوظ اور حتمی کریں"}
              </Button>
              <Button
                type="submit"
                name="action"
                value="print"
                disabled={save.isPending}
              >
                <Printer size={16} />
                {english ? "Save and print" : "محفوظ اور پرنٹ کریں"}
              </Button>
            </>
          )}
        </div>
      </form>
    </>
  )
}
export function ReceiptDetail({
  english,
  user,
}: {
  english: boolean
  user: User
}) {
  const { id } = useParams()
  const cache = useQueryClient()
  const [voiding, setVoiding] = useState(false)
  const [reason, setReason] = useState("")
  const [payment, setPayment] = useState(false)
  const query = useQuery({
    queryKey: ["receipt", id],
    queryFn: () => api<Receipt>(`/receipts/${id}`),
  })
  const settings = useQuery({
    queryKey: ["settings"],
    queryFn: () => api<Row>("/settings"),
  })
  const action = useMutation({
    mutationFn: (name: string) =>
      api(`/receipts/${id}/${name}`, {
        method: "POST",
        body: name === "void" ? JSON.stringify({ reason }) : undefined,
      }),
    onSuccess: () => {
      void cache.invalidateQueries()
      setVoiding(false)
    },
  })
  useEffect(() => {
    if (
      query.data &&
      settings.data &&
      new URLSearchParams(window.location.search).get("print") === "1"
    ) {
      window.history.replaceState(null, "", window.location.pathname)
      const timer = setTimeout(() => printDocument(), 150)
      return () => clearTimeout(timer)
    }
  }, [query.data, settings.data])
  const r = query.data
  if (query.isPending)
    return <p role="status">{english ? "Loading…" : "انتظار فرمائیں…"}</p>
  if (!r) return <ErrorMessage error={query.error} />
  return (
    <>
      <div className="no-print">
        <PageHeading title={`${english ? "Receipt" : "بلٹی"} ${r.number}`}>
          <Button variant="outline" onClick={() => printDocument()}>
            <Printer size={16} />
            {english ? "Print" : "پرنٹ"}
          </Button>
          <Button
            nativeButton={false}
            role="link"
            render={<a href={`/api/v1/receipts/${r.id}/pdf`} download />}
          >
            <Download size={16} />
            {english ? "Download PDF" : "پی ڈی ایف"}
          </Button>
        </PageHeading>
        <ErrorMessage error={action.error} />
        <div className="form-actions">
          {r.status === "draft" && (
            <>
              <Button
                nativeButton={false}
                role="link"
                render={<Link to={`/receipts/${r.id}/edit`} />}
              >
                {english ? "Edit draft" : "مسودے میں ترمیم"}
              </Button>
              <Button
                disabled={action.isPending}
                onClick={() => {
                  if (
                    window.confirm(
                      english
                        ? "Post this receipt? Stock and financial records will be committed."
                        : "بلٹی حتمی کریں؟ اسٹاک اور مالی ریکارڈ محفوظ ہو جائیں گے۔"
                    )
                  )
                    action.mutate("post")
                }}
              >
                {english ? "Post receipt" : "بلٹی حتمی کریں"}
              </Button>
              {user.role === "owner" && (
                <Button variant="outline" onClick={() => setVoiding(true)}>
                  {english ? "Void draft" : "مسودہ منسوخ کریں"}
                </Button>
              )}
            </>
          )}
          {r.status === "posted" && (
            <>
              {user.role === "owner" && (
                <Button variant="outline" onClick={() => setVoiding(true)}>
                  {english ? "Void incorrect receipt" : "غلط بلٹی منسوخ کریں"}
                </Button>
              )}
              <Button
                onClick={() => setPayment(true)}
                disabled={Number(r.balance) <= 0}
              >
                {english ? "Record payment" : "ادائیگی درج کریں"}
              </Button>
              {r.transaction_type === "repair" && !r.completed_at && (
                <Button
                  variant="outline"
                  disabled={action.isPending}
                  onClick={() => action.mutate("complete")}
                >
                  {english ? "Mark repair complete" : "مرمت مکمل کریں"}
                </Button>
              )}
            </>
          )}
        </div>
      </div>
      <article className="print-receipt panel">
        <div className="receipt-shop">
          {Boolean(settings.data?.has_logo) && (
            <img
              className="shop-logo receipt-logo"
              src="/api/v1/settings/logo"
              alt={english ? "Shop logo" : "دکان کا لوگو"}
            />
          )}
          {Boolean(settings.data?.name_ur) && (
            <h1 lang="ur" dir="rtl">
              {String(settings.data?.name_ur)}
            </h1>
          )}
          <h1>{String(settings.data?.name ?? "")}</h1>
          {Boolean(settings.data?.address_ur) && (
            <p lang="ur" dir="rtl">
              {String(settings.data?.address_ur)}
            </p>
          )}
          <p>{String(settings.data?.address ?? "")}</p>
          <p dir="ltr">{String(settings.data?.phone ?? "")}</p>
          <p>{String(settings.data?.receipt_header ?? "")}</p>
        </div>
        <div className="receipt-meta">
          <strong>
            {english ? "Receipt" : "بلٹی"}: {r.number}
          </strong>
          <span>{r.transaction_date}</span>
          <span>{typeName(r.transaction_type, english)}</span>
          <span>
            {r.status === "draft"
              ? english
                ? "DRAFT"
                : "مسودہ"
              : r.status === "void"
                ? english
                  ? "VOID"
                  : "منسوخ"
                : english
                  ? "POSTED"
                  : "حتمی"}
          </span>
        </div>
        <h2>{partyLabel(r.transaction_type, english)}</h2>
        <p>
          <strong>{english ? "Name" : "نام"}: </strong>
          {String(r.customer?.name ?? (english ? "Walk-in" : "واک اِن"))}
        </p>
        <p>
          <strong>{english ? "Phone" : "فون"}: </strong>
          <bdi dir="ltr">{String(r.customer?.phone || "—")}</bdi>
        </p>
        <p>
          <strong>{english ? "Address" : "پتہ"}: </strong>
          {String(r.customer?.address || "—")}
        </p>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {(english
                  ? ["Description", "Quantity", "Unit price"]
                  : ["تفصیل", "تعداد", "فی عدد قیمت"]
                ).map((h) => (
                  <th key={h}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {r.items.map((i) => (
                <tr key={i.id}>
                  <td>
                    {i.name} {i.brand} {i.model}
                    <small className="muted"> {i.serial_number}</small>
                  </td>
                  <td>{i.quantity}</td>
                  <td>{money(i.unit_price)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="receipt-totals">
          <p>
            {english ? "Total" : "کل رقم"}
            <strong>{money(r.total)}</strong>
          </p>
          <p>
            {english ? "Paid" : "ادا شدہ"}
            <strong>{money(r.paid)}</strong>
          </p>
          <p>
            {english ? "Remaining balance" : "بقایا رقم"}
            <strong>{money(r.balance)}</strong>
          </p>
        </div>
        <p>{r.work_description}</p>
        <p>{r.notes}</p>
        <div className="signature">
          {english ? "Authorized signature" : "مجاز دستخط"}: __________________
        </div>
        <p className="muted">{String(settings.data?.receipt_footer ?? "")}</p>
      </article>
      {voiding && (
        <Modal
          title={english ? "Void incorrect receipt" : "غلط بلٹی منسوخ کریں"}
          close={() => setVoiding(false)}
        >
          <form
            className="form-stack"
            onSubmit={(e) => {
              e.preventDefault()
              action.mutate("void")
            }}
          >
            <label>
              {english ? "Reason" : "وجہ"}
              <textarea
                required
                minLength={5}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              />
            </label>
            <ErrorMessage error={action.error} />
            <Button type="submit" disabled={action.isPending}>
              {english ? "Confirm cancellation" : "منسوخی کی تصدیق"}
            </Button>
          </form>
        </Modal>
      )}
      {payment && (
        <PaymentForm
          receiptId={r.id}
          english={english}
          close={() => setPayment(false)}
        />
      )}
    </>
  )
}
export function PaymentForm({
  receiptId,
  english,
  close,
}: {
  receiptId?: string
  english: boolean
  close: () => void
}) {
  const cache = useQueryClient()
  const [key] = useState(() => crypto.randomUUID())
  const [id, setId] = useState(receiptId ?? "")
  const [amount, setAmount] = useState("")
  const [date, setDate] = useState(localDate())
  const [method, setMethod] = useState("cash")
  const [reference, setReference] = useState("")
  const [notes, setNotes] = useState("")
  const save = useMutation({
    mutationFn: () =>
      api("/payments", {
        method: "POST",
        headers: { "Idempotency-Key": key },
        body: JSON.stringify({
          receipt_id: id,
          amount,
          payment_date: date,
          method,
          reference,
          notes,
        }),
      }),
    onSuccess: () => {
      void cache.invalidateQueries()
      close()
    },
  })
  return (
    <Modal
      title={english ? "Record payment" : "ادائیگی درج کریں"}
      close={close}
    >
      <form
        className="form-stack"
        onSubmit={(e) => {
          e.preventDefault()
          save.mutate()
        }}
      >
        {!receiptId && (
          <label>
            {english ? "Receipt" : "بلٹی"}
            <RecordSelect
              label={english ? "Receipt" : "بلٹی"}
              path="receipts"
              value={id}
              onChange={setId}
              english={english}
              required
            />
          </label>
        )}
        <label>
          {english ? "Amount" : "رقم"}
          <input
            type="number"
            required
            min="0.01"
            step="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />
        </label>
        <label>
          {english ? "Date" : "تاریخ"}
          <input
            type="date"
            required
            max={localDate()}
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
        </label>
        <label>
          {english ? "Method" : "طریقہ"}
          <select value={method} onChange={(e) => setMethod(e.target.value)}>
            <option value="cash">{english ? "Cash" : "نقد"}</option>
            <option value="bank_transfer">
              {english ? "Bank transfer" : "بینک ٹرانسفر"}
            </option>
            <option value="other">{english ? "Other" : "دیگر"}</option>
          </select>
        </label>
        <label>
          {english ? "Reference" : "حوالہ"}
          <input
            value={reference}
            onChange={(e) => setReference(e.target.value)}
          />
        </label>
        <label>
          {english ? "Notes" : "نوٹس"}
          <textarea value={notes} onChange={(e) => setNotes(e.target.value)} />
        </label>
        <ErrorMessage error={save.error} />
        <Button type="submit" disabled={save.isPending}>
          {english ? "Save payment" : "ادائیگی محفوظ کریں"}
        </Button>
      </form>
    </Modal>
  )
}
