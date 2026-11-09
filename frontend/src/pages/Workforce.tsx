import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { Plus, CheckCircle2 } from "lucide-react"
import { api } from "@/lib/api"
import { localDate, money } from "@/lib/types"
import type { User, Page, Row } from "@/lib/types"
import type { Receipt } from "./Receipts"
import { resources } from "@/lib/resources"
import ResourcePage from "./ResourcePage"
import { RecordSelect } from "@/components/RecordSelect"
import { Modal, Empty, ErrorMessage, PageHeading } from "@/components/shared"
import { Button } from "@/components/ui/button"
export default function Workforce({
  english,
  user,
}: {
  english: boolean
  user: User
}) {
  const [tab, setTab] = useState(() => new URLSearchParams(window.location.search).get("tab") === "jobs" ? "jobs" : "workers")
  const [assign, setAssign] = useState(false)
  const [pay, setPay] = useState(false)
  return (
    <>
      <div className="tabs no-print">
        <Button
          variant={tab === "workers" ? "default" : "outline"}
          onClick={() => setTab("workers")}
        >
          {english ? "Workers" : "کاریگر"}
        </Button>
        <Button
          variant={tab === "jobs" ? "default" : "outline"}
          onClick={() => setTab("jobs")}
        >
          {english ? "Repair jobs" : "مرمت کے کام"}
        </Button>
        {user.role !== "staff" && (
          <Button variant="outline" onClick={() => setAssign(true)}>
            <Plus size={16} />
            {english ? "Assign job" : "کام تفویض کریں"}
          </Button>
        )}
        {user.role === "owner" && (
          <Button variant="outline" onClick={() => setPay(true)}>
            {english ? "Pay worker" : "کاریگر کو ادائیگی"}
          </Button>
        )}
      </div>
      {tab === "workers" ? (
        <ResourcePage
          config={resources.workers}
          english={english}
          user={user}
        />
      ) : (
        <Jobs english={english} user={user} />
      )}{" "}
      {assign && (
        <JobForm
          english={english}
          close={() => {
            setAssign(false)
            setTab("jobs")
          }}
        />
      )}
      {pay && <WorkerPay english={english} close={() => setPay(false)} />}
    </>
  )
}
function Jobs({ english, user }: { english: boolean; user: User }) {
  const cache = useQueryClient()
  const [offset, setOffset] = useState(0)
  const [status, setStatus] = useState("")
  const jobs = useQuery({
    queryKey: ["jobs", offset, status],
    queryFn: () =>
      api<Page<Row>>(
        `/jobs?offset=${offset}&limit=25${status ? `&status=${status}` : ""}`
      ),
  })
  const update = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      api(`/jobs/${id}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      }),
    onSuccess: () => {
      void cache.invalidateQueries()
    },
  })
  const statuses: Record<string, string> = {
    assigned: english ? "Assigned" : "تفویض شدہ",
    in_progress: english ? "In progress" : "جاری",
    completed: english ? "Completed" : "مکمل",
    cancelled: english ? "Cancelled" : "منسوخ",
  }
  return (
    <>
      <PageHeading title={english ? "Repair jobs" : "مرمت کے کام"} />
      <select
        className="status-filter"
        aria-label={english ? "Job status" : "کام کی حالت"}
        value={status}
        onChange={(e) => {
          setStatus(e.target.value)
          setOffset(0)
        }}
      >
        <option value="">{english ? "All statuses" : "تمام حالتیں"}</option>
        {Object.entries(statuses).map(([key, label]) => (
          <option value={key} key={key}>
            {label}
          </option>
        ))}
      </select>
      <ErrorMessage error={jobs.error ?? update.error} />
      {jobs.isPending ? (
        <p role="status">{english ? "Loading…" : "انتظار فرمائیں…"}</p>
      ) : !jobs.data?.items.length ? (
        <Empty english={english} />
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {(english
                  ? [
                      "Receipt",
                      "Equipment",
                      "Worker",
                      "Work",
                      "Due date",
                      "Status",
                    ]
                  : ["بلٹی", "سامان", "کاریگر", "کام", "متوقع تکمیل", "حالت"]
                ).map((h) => (
                  <th key={h}>{h}</th>
                ))}
                {user.role !== "staff" && (
                  <>
                    <th>{english ? "Labor" : "مزدوری"}</th>
                    <th>{english ? "Actions" : "عمل"}</th>
                  </>
                )}
              </tr>
            </thead>
            <tbody>
              {jobs.data.items.map((j) => (
                <tr key={j.id}>
                  <td>
                    <Link
                      className="text-link"
                      to={`/receipts/${j.receipt_id}`}
                    >
                      {String(j.receipt_number)}
                    </Link>
                  </td>
                  <td>{String(j.equipment)}</td>
                  <td>{String(j.worker_name)}</td>
                  <td>{String(j.description)}</td>
                  <td>{String(j.expected_date ?? "—")}</td>
                  <td>
                    <span className="badge">{statuses[String(j.status)]}</span>
                  </td>
                  {user.role !== "staff" && (
                    <>
                      <td>{money(j.labor_amount)}</td>
                      <td>
                        {!["completed", "cancelled"].includes(
                          String(j.status)
                        ) && (
                          <div className="table-actions">
                            {j.status === "assigned" && (
                              <Button
                                variant="outline"
                                disabled={update.isPending}
                                onClick={() =>
                                  update.mutate({
                                    id: j.id,
                                    status: "in_progress",
                                  })
                                }
                              >
                                {english ? "Start" : "شروع"}
                              </Button>
                            )}
                            <Button
                              disabled={update.isPending}
                              onClick={() => {
                                if (
                                  window.confirm(
                                    english
                                      ? "Complete this job and recognize worker earnings?"
                                      : "کام مکمل کرکے کاریگر کی مزدوری درج کریں؟"
                                  )
                                )
                                  update.mutate({
                                    id: j.id,
                                    status: "completed",
                                  })
                              }}
                            >
                              <CheckCircle2 size={15} />
                              {english ? "Complete" : "مکمل"}
                            </Button>
                            <Button
                              variant="ghost"
                              disabled={update.isPending}
                              onClick={() => {
                                if (
                                  window.confirm(
                                    english
                                      ? "Cancel this unfinished job?"
                                      : "نامکمل کام منسوخ کریں؟"
                                  )
                                )
                                  update.mutate({
                                    id: j.id,
                                    status: "cancelled",
                                  })
                              }}
                            >
                              {english ? "Cancel" : "منسوخ"}
                            </Button>
                          </div>
                        )}
                      </td>
                    </>
                  )}
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
        <span>{jobs.data?.total ?? 0}</span>
        <Button
          variant="outline"
          disabled={offset + 25 >= (jobs.data?.total ?? 0)}
          onClick={() => setOffset(offset + 25)}
        >
          {english ? "Next" : "اگلا"}
        </Button>
      </div>
    </>
  )
}
function JobForm({ english, close }: { english: boolean; close: () => void }) {
  const cache = useQueryClient()
  const [receipt, setReceipt] = useState<Receipt | null>(null)
  const [item, setItem] = useState("")
  const [worker, setWorker] = useState("")
  const [description, setDescription] = useState("")
  const [amount, setAmount] = useState("")
  const [assigned, setAssigned] = useState(localDate())
  const [expected, setExpected] = useState("")
  const save = useMutation({
    mutationFn: () =>
      api("/jobs", {
        method: "POST",
        body: JSON.stringify({
          receipt_item_id: item,
          worker_id: worker,
          description,
          labor_amount: amount,
          assigned_date: assigned,
          expected_date: expected || null,
        }),
      }),
    onSuccess: () => {
      void cache.invalidateQueries()
      close()
    },
  })
  return (
    <Modal
      title={english ? "Assign repair job" : "مرمت کا کام تفویض کریں"}
      close={close}
    >
      <form
        className="form-stack"
        onSubmit={(e) => {
          e.preventDefault()
          save.mutate()
        }}
      >
        <label>
          {english ? "Find receipt number" : "بلٹی نمبر تلاش کریں"}
          <RecordSelect
            label={english ? "Receipt" : "بلٹی"}
            path="receipts"
            value={receipt?.id ?? ""}
            onChange={(_, r) => {
              setReceipt((r as Receipt) ?? null)
              setItem("")
            }}
            english={english}
            required
          />
        </label>
        {receipt && (
          <>
            <p>
              {String(
                receipt.customer?.name ?? (english ? "Walk-in" : "واک اِن")
              )}{" "}
              — {receipt.number}
            </p>
            <label>
              {english ? "Equipment" : "سامان"}
              <select
                aria-label={english ? "Equipment" : "سامان"}
                required
                value={item}
                onChange={(e) => setItem(e.target.value)}
              >
                <option value="">
                  {english ? "Select equipment" : "سامان منتخب کریں"}
                </option>
                {receipt.items.map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.name}
                  </option>
                ))}
              </select>
            </label>
          </>
        )}
        <label>
          {english ? "Worker" : "کاریگر"}
          <RecordSelect
            label={english ? "Worker" : "کاریگر"}
            path="workers"
            value={worker}
            onChange={setWorker}
            english={english}
            required
          />
        </label>
        <label>
          {english ? "Work description" : "کام کی تفصیل"}
          <textarea
            required
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </label>
        <label>
          {english ? "Labor amount" : "مزدوری کی رقم"}
          <input
            required
            type="number"
            min={0}
            step="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />
        </label>
        <label>
          {english ? "Assigned date" : "تفویض کی تاریخ"}
          <input
            required
            type="date"
            max={localDate()}
            value={assigned}
            onChange={(e) => setAssigned(e.target.value)}
          />
        </label>
        <label>
          {english ? "Expected completion" : "متوقع تکمیل"}
          <input
            type="date"
            min={assigned}
            value={expected}
            onChange={(e) => setExpected(e.target.value)}
          />
        </label>
        <ErrorMessage error={save.error} />
        <Button type="submit" disabled={save.isPending}>
          {english ? "Assign job" : "کام تفویض کریں"}
        </Button>
      </form>
    </Modal>
  )
}
function WorkerPay({
  english,
  close,
}: {
  english: boolean
  close: () => void
}) {
  const cache = useQueryClient()
  const [key] = useState(() => crypto.randomUUID())
  const [worker, setWorker] = useState("")
  const [amount, setAmount] = useState("")
  const [date, setDate] = useState(localDate())
  const [method, setMethod] = useState("cash")
  const [reference, setReference] = useState("")
  const [notes, setNotes] = useState("")
  const statement = useQuery({
    queryKey: ["statement", worker],
    queryFn: () => api<Row>(`/workers/${worker}/statement`),
    enabled: !!worker,
  })
  const save = useMutation({
    mutationFn: () =>
      api("/worker-payments", {
        method: "POST",
        headers: { "Idempotency-Key": key },
        body: JSON.stringify({
          worker_id: worker,
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
      title={english ? "Worker payment" : "کاریگر کی ادائیگی"}
      close={close}
    >
      <form
        className="form-stack"
        onSubmit={(e) => {
          e.preventDefault()
          save.mutate()
        }}
      >
        <label>
          {english ? "Worker" : "کاریگر"}
          <RecordSelect
            label={english ? "Worker" : "کاریگر"}
            path="workers"
            value={worker}
            onChange={setWorker}
            english={english}
            required
          />
        </label>
        {statement.data && (
          <p className="summary-strip">
            {english ? "Current payable" : "موجودہ واجب الادا"}:{" "}
            {money(statement.data.payable)}
          </p>
        )}
        <ErrorMessage error={statement.error} />
        <label>
          {english ? "Amount" : "رقم"}
          <input
            required
            type="number"
            min="0.01"
            step="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />
        </label>
        <label>
          {english ? "Payment date" : "ادائیگی کی تاریخ"}
          <input
            required
            type="date"
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
