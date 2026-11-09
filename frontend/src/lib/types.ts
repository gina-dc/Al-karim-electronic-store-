export type User = {
  id: string
  username: string
  display_name: string
  role: string
}
export type Row = Record<string, unknown> & { id: string }
export type Page<T> = { total: number; items: T[] }
export type Field = {
  key: string
  ur: string
  en: string
  type?: "text" | "number" | "date" | "textarea" | "select"
  required?: boolean
  options?: { value: string; ur: string; en: string }[]
  initial?: string
}
export type Resource = {
  path: string
  ur: string
  en: string
  fields: Field[]
  columns: string[]
  editable?: boolean
  ownerOnly?: boolean
}
export const localDate = () =>
  new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Karachi",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date())
export const money = (value: unknown) =>
  `Rs. ${new Intl.NumberFormat("en-PK", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Number(value ?? 0))}`
