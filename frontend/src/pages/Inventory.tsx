import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { resources } from "@/lib/resources"
import { money } from "@/lib/types"
import type { User } from "@/lib/types"
import { ErrorMessage } from "@/components/shared"
import ResourcePage from "./ResourcePage"
type Summary = {
  records: number
  units: number
  conditions: Record<string, number>
  availability: Record<string, number>
  sold_units: number
  acquisition_cost?: string
  estimated_selling_value?: string
}
export default function Inventory({
  english,
  user,
}: {
  english: boolean
  user: User
}) {
  const query = useQuery({
    queryKey: ["inventory-summary"],
    queryFn: () => api<Summary>("/inventory-summary"),
  })
  const data = query.data
  const cards: [string, string, number | string | undefined, boolean?][] = data
    ? [
        ["کل سامان", "Total units", data.units],
        ["نیا", "New", data.conditions.new ?? 0],
        ["استعمال شدہ", "Used", data.conditions.used ?? 0],
        ["خراب", "Damaged", data.conditions.damaged ?? 0],
        ["زیر مرمت", "Under repair", data.conditions.under_repair ?? 0],
        ["مرمت شدہ", "Repaired", data.conditions.repaired ?? 0],
        ["دستیاب", "Available", data.availability.available ?? 0],
        ["محفوظ", "Reserved", data.availability.reserved ?? 0],
        ["فروخت شدہ", "Sold units", data.sold_units],
      ]
    : []
  if (data?.acquisition_cost !== undefined)
    cards.push(
      ["اسٹاک کی اصل لاگت", "Current stock cost", data.acquisition_cost, true],
      [
        "تخمینی فروخت قیمت",
        "Estimated selling value",
        data.estimated_selling_value,
        true,
      ]
    )
  return (
    <>
      <ErrorMessage error={query.error} />
      <div className="kpi-grid">
        {cards.map(([ur, en, value, currency]) => (
          <section className="kpi" key={en}>
            <span>{english ? en : ur}</span>
            <strong>{currency ? money(value) : value}</strong>
          </section>
        ))}
      </div>
      <ResourcePage
        config={resources.inventory}
        english={english}
        user={user}
      />
    </>
  )
}
