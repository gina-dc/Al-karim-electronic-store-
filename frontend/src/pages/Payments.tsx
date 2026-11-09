import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { api } from "@/lib/api"
import type { Page, Row, User } from "@/lib/types"
import { money } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { Empty, ErrorMessage, PageHeading, Modal } from "@/components/shared"
import { PaymentForm } from "./Receipts"
export default function Payments({
  english,
  user,
}: {
  english: boolean
  user: User
}) {
  const cache = useQueryClient()
  const [correcting, setCorrecting] = useState<Row | null>(null)
  const [reason, setReason] = useState("")
  const reverse = useMutation({
    mutationFn: () =>
      api(`/payments/${correcting?.id}/reverse`, {
        method: "POST",
        body: JSON.stringify({ reason }),
      }),
    onSuccess: () => {
      void cache.invalidateQueries()
      setCorrecting(null)
      setReason("")
    },
  })
  const [adding, setAdding] = useState(false)
  const [offset, setOffset] = useState(0)
  const query = useQuery({
    queryKey: ["payments", offset],
    queryFn: () => api<Page<Row>>(`/payments?offset=${offset}&limit=25`),
  })
  return (
    <>
      <PageHeading title={english ? "Payment ledger" : "ادائیگیوں کا ریکارڈ"}>
        <Button onClick={() => setAdding(true)}>
          {english ? "Record payment" : "ادائیگی درج کریں"}
        </Button>
      </PageHeading>
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
                      "Direction",
                      "Amount",
                      "Method",
                      "Reference",
                      "Notes",
                    ]
                  : ["بلٹی", "تاریخ", "سمت", "رقم", "طریقہ", "حوالہ", "نوٹس"]
                ).map((h) => (
                  <th key={h}>{h}</th>
                ))}
                {user.role === "owner" && (
                  <th>{english ? "Correction" : "تصحیح"}</th>
                )}
              </tr>
            </thead>
            <tbody>
              {query.data.items.map((r) => (
                <tr key={r.id}>
                  <td>
                    <Link
                      className="text-link"
                      to={`/receipts/${r.receipt_id}`}
                    >
                      {String(r.receipt_number ?? "—")}
                    </Link>
                  </td>
                  <td>{String(r.payment_date)}</td>
                  <td>
                    {r.transaction_type === "purchase"
                      ? english
                        ? "Paid to seller"
                        : "فروخت کنندہ کو ادائیگی"
                      : english
                        ? "Received"
                        : "وصولی"}
                  </td>
                  <td>{money(r.amount)}</td>
                  <td>
                    {r.method === "cash"
                      ? english
                        ? "Cash"
                        : "نقد"
                      : r.method === "bank_transfer"
                        ? english
                          ? "Bank"
                          : "بینک"
                        : english
                          ? "Other"
                          : "دیگر"}
                  </td>
                  <td>{String(r.reference)}</td>
                  <td>{String(r.notes)}</td>
                  {user.role === "owner" && (
                    <td>
                      {Number(r.amount) > 0 && (
                        <Button
                          variant="outline"
                          onClick={() => setCorrecting(r)}
                        >
                          {english ? "Correct entry" : "تصحیح"}
                        </Button>
                      )}
                    </td>
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
        <span>{query.data?.total ?? 0}</span>
        <Button
          variant="outline"
          disabled={offset + 25 >= (query.data?.total ?? 0)}
          onClick={() => setOffset(offset + 25)}
        >
          {english ? "Next" : "اگلا"}
        </Button>
      </div>
      {correcting && (
        <Modal
          title={
            english ? "Correct an erroneous payment" : "غلط ادائیگی کی تصحیح"
          }
          close={() => setCorrecting(null)}
        >
          <p className="muted">
            {english
              ? "Use this only to correct an incorrect ledger entry. It does not issue a refund."
              : "صرف غلط اندراج کی تصحیح کے لیے استعمال کریں۔ اس سے رقم واپس نہیں کی جاتی۔"}
          </p>
          <form
            className="form-stack"
            onSubmit={(e) => {
              e.preventDefault()
              reverse.mutate()
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
            <ErrorMessage error={reverse.error} />
            <Button type="submit" disabled={reverse.isPending}>
              {english ? "Confirm correction" : "تصحیح کی تصدیق"}
            </Button>
          </form>
        </Modal>
      )}
      {adding && (
        <PaymentForm english={english} close={() => setAdding(false)} />
      )}
    </>
  )
}
