import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type { Page, Row } from "@/lib/types"
export function RecordSelect({
  path,
  value,
  onChange,
  english,
  required = false,
  label,
}: {
  path: string
  value: string
  onChange: (id: string, row?: Row) => void
  english: boolean
  required?: boolean
  label?: string
}) {
  const [search, setSearch] = useState("")
  const records = useQuery({
    queryKey: [path, "select", search],
    queryFn: () =>
      api<Page<Row>>(`/${path}?search=${encodeURIComponent(search)}&limit=100`),
  })
  return (
    <div className="record-select">
      <input
        aria-label={`${label ?? ""} ${english ? "search" : "تلاش"}`}
        placeholder={english ? "Search…" : "تلاش کریں…"}
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      <select
        aria-label={label ?? (english ? "Select record" : "ریکارڈ منتخب کریں")}
        required={required}
        value={value}
        onChange={(e) =>
          onChange(
            e.target.value,
            records.data?.items.find((r) => r.id === e.target.value)
          )
        }
      >
        <option value="">
          {english ? "Select / walk-in" : "منتخب کریں / واک اِن"}
        </option>
        {value && !records.data?.items.some((r) => r.id === value) && (
          <option value={value}>
            {english ? "Selected record" : "منتخب ریکارڈ"}
          </option>
        )}
        {records.data?.items.map((r) => (
          <option key={r.id} value={r.id}>
            {String(r.number ?? r.code ?? "")} {String(r.name ?? "")}{" "}
            {r.customer ? String((r.customer as Row).name) : ""}
          </option>
        ))}
      </select>
      {records.error && (
        <small role="alert" className="error">
          {records.error.message}
        </small>
      )}
    </div>
  )
}
