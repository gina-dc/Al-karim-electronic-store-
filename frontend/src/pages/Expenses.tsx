import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { localDate } from "@/lib/types"
import { Modal, ErrorMessage } from "@/components/shared"
import { Button } from "@/components/ui/button"
export function ExpenseForm({
  english,
  close,
}: {
  english: boolean
  close: () => void
}) {
  const cache = useQueryClient()
  const [key] = useState(() => crypto.randomUUID())
  const [description, setDescription] = useState("")
  const [category, setCategory] = useState("operating")
  const [amount, setAmount] = useState("")
  const [date, setDate] = useState(localDate())
  const save = useMutation({
    mutationFn: () =>
      api("/expenses", {
        method: "POST",
        headers: { "Idempotency-Key": key },
        body: JSON.stringify({
          description,
          category,
          amount,
          expense_date: date,
        }),
      }),
    onSuccess: () => {
      void cache.invalidateQueries()
      close()
    },
  })
  return (
    <Modal title={english ? "Record expense" : "خرچ درج کریں"} close={close}>
      <form
        className="form-stack"
        onSubmit={(e) => {
          e.preventDefault()
          save.mutate()
        }}
      >
        <label>
          {english ? "Description" : "تفصیل"}
          <input
            required
            maxLength={250}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </label>
        <label>
          {english ? "Category" : "قسم"}
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            <option value="operating">
              {english ? "Operating" : "دکان کا خرچ"}
            </option>
            <option value="repair">{english ? "Repair" : "مرمت کا خرچ"}</option>
          </select>
        </label>
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
          {english ? "Date" : "تاریخ"}
          <input
            required
            type="date"
            max={localDate()}
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
        </label>
        <ErrorMessage error={save.error} />
        <Button type="submit" disabled={save.isPending}>
          {english ? "Save" : "محفوظ کریں"}
        </Button>
      </form>
    </Modal>
  )
}
