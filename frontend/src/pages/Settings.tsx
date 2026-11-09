import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type { Row } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { ErrorMessage, PageHeading, Modal } from "@/components/shared"
export default function Settings({ english }: { english: boolean }) {
  const [account, setAccount] = useState<Row | null | undefined>(undefined)
  const settings = useQuery({
    queryKey: ["settings"],
    queryFn: () => api<Row>("/settings"),
  })
  const users = useQuery({
    queryKey: ["users"],
    queryFn: () => api<Row[]>("/users"),
  })
  return (
    <>
      <PageHeading title={english ? "Settings" : "ترتیبات"} />
      <ErrorMessage error={settings.error} />
      {settings.data && (
        <SettingsForm initial={settings.data} english={english} />
      )}
      <section className="panel">
        <PageHeading title={english ? "Authorized accounts" : "مجاز اکاؤنٹس"}>
          <Button onClick={() => setAccount(null)}>
            {english ? "Create account" : "اکاؤنٹ بنائیں"}
          </Button>
        </PageHeading>
        <ErrorMessage error={users.error} />
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {(english
                  ? ["Name", "Username", "Role", "Status", "Actions"]
                  : ["نام", "صارف کا نام", "کردار", "حالت", "عمل"]
                ).map((h) => (
                  <th key={h}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {users.data?.map((u) => (
                <tr key={u.id}>
                  <td>{String(u.display_name)}</td>
                  <td>{String(u.username)}</td>
                  <td>
                    {u.role === "owner"
                      ? english
                        ? "Owner"
                        : "مالک"
                      : u.role === "manager"
                        ? english
                          ? "Manager"
                          : "منیجر"
                        : english
                          ? "Staff"
                          : "عملہ"}
                  </td>
                  <td>
                    {u.active
                      ? english
                        ? "Active"
                        : "فعال"
                      : english
                        ? "Inactive"
                        : "غیر فعال"}
                  </td>
                  <td>
                    <Button variant="outline" onClick={() => setAccount(u)}>
                      {english ? "Manage" : "انتظام"}
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      {account !== undefined && (
        <AccountForm
          english={english}
          existing={account}
          close={() => setAccount(undefined)}
        />
      )}
    </>
  )
}
function SettingsForm({
  initial,
  english,
}: {
  initial: Row
  english: boolean
}) {
  const cache = useQueryClient()
  const [values, setValues] = useState({ ...initial })
  const [saved, setSaved] = useState(false)
  const save = useMutation({
    mutationFn: () =>
      api("/settings", { method: "PUT", body: JSON.stringify(values) }),
    onSuccess: () => {
      setSaved(true)
      void cache.invalidateQueries({ queryKey: ["settings"] })
    },
  })
  const upload = useMutation({
    mutationFn: (file: File) =>
      api("/settings/logo", {
        method: "PUT",
        headers: { "Content-Type": file.type },
        body: file,
      }),
    onSuccess: () => {
      void cache.invalidateQueries({ queryKey: ["settings"] })
    },
  })
  const fields = [
    { key: "name_ur", ur: "دکان کا نام (اردو)", en: "Shop name (Urdu)" },
    { key: "address_ur", ur: "پتہ (اردو)", en: "Address (Urdu)" },
    { key: "name", ur: "دکان کا نام", en: "Shop name" },
    { key: "address", ur: "پتہ", en: "Address" },
    { key: "phone", ur: "فون", en: "Phone" },
    { key: "receipt_header", ur: "بلٹی کا ہیڈر", en: "Receipt header" },
    { key: "receipt_footer", ur: "بلٹی کا فوٹر", en: "Receipt footer" },
  ]
  return (
    <section className="panel">
      <form
        className="editor-grid"
        onSubmit={(e) => {
          e.preventDefault()
          save.mutate()
        }}
      >
        {fields.map((f) => (
          <label key={f.key}>
            {english ? f.en : f.ur}
            <input
              required={f.key === "name"}
              value={String(values[f.key] ?? "")}
              onChange={(e) => {
                setSaved(false)
                setValues({ ...values, [f.key]: e.target.value })
              }}
            />
          </label>
        ))}
        <label>
          {english ? "Receipt format" : "بلٹی کا سائز"}
          <select
            value={String(values.print_format)}
            onChange={(e) =>
              setValues({ ...values, print_format: e.target.value })
            }
          >
            <option value="a4">A4</option>
            <option value="thermal">
              {english ? "Thermal 80 mm" : "تھرمل ۸۰ ملی میٹر"}
            </option>
          </select>
        </label>
        <label>
          {english ? "Currency display" : "کرنسی"}
          <select
            value={String(values.currency)}
            onChange={(e) => setValues({ ...values, currency: e.target.value })}
          >
            <option value="PKR">PKR</option>
            <option value="Rs.">Rs.</option>
          </select>
        </label>
        <label>
          {english ? "Default language" : "بنیادی زبان"}
          <select
            value={String(values.language)}
            onChange={(e) => setValues({ ...values, language: e.target.value })}
          >
            <option value="ur">اردو</option>
            <option value="en">English</option>
          </select>
        </label>
        <label>
          {english ? "Theme" : "تھیم"}
          <select
            value={String(values.theme)}
            onChange={(e) => setValues({ ...values, theme: e.target.value })}
          >
            <option value="light">{english ? "Light" : "روشن"}</option>
            <option value="dark">{english ? "Dark" : "تاریک"}</option>
          </select>
        </label>
        <div className="form-footer">
          <ErrorMessage error={save.error} />
          {saved && (
            <p role="status">
              {english ? "Settings saved" : "ترتیبات محفوظ ہو گئیں"}
            </p>
          )}
          <Button type="submit" disabled={save.isPending}>
            {english ? "Save settings" : "ترتیبات محفوظ کریں"}
          </Button>
        </div>
      </form>
      <div className="logo-upload">
        <label>
          {english
            ? "Shop logo (PNG/JPEG, up to 1 MB)"
            : "دکان کا لوگو (PNG/JPEG، زیادہ سے زیادہ 1 MB)"}
          <input
            type="file"
            accept="image/png,image/jpeg"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) upload.mutate(file)
            }}
            disabled={upload.isPending}
          />
        </label>
        {Boolean(initial.has_logo) && (
          <img
            className="shop-logo"
            src="/api/v1/settings/logo"
            alt={english ? "Shop logo" : "دکان کا لوگو"}
          />
        )}
        <ErrorMessage error={upload.error} />
      </div>
    </section>
  )
}
function AccountForm({
  english,
  existing,
  close,
}: {
  english: boolean
  existing: Row | null
  close: () => void
}) {
  const cache = useQueryClient()
  const [username, setUsername] = useState(String(existing?.username ?? ""))
  const [name, setName] = useState(String(existing?.display_name ?? ""))
  const [role, setRole] = useState(String(existing?.role ?? "staff"))
  const [password, setPassword] = useState("")
  const [active, setActive] = useState(existing?.active !== false)
  const save = useMutation({
    mutationFn: () =>
      api(existing ? `/users/${existing.id}` : "/auth/users", {
        method: existing ? "PATCH" : "POST",
        body: JSON.stringify({
          username,
          display_name: name,
          role,
          password: password || undefined,
          active,
        }),
      }),
    onSuccess: () => {
      void cache.invalidateQueries()
      close()
    },
  })
  return (
    <Modal
      title={english ? "Account details" : "اکاؤنٹ کی تفصیل"}
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
          {english ? "Username" : "صارف کا نام"}
          <input
            required
            disabled={!!existing}
            pattern="[a-zA-Z0-9_.@-]+"
            dir="ltr"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </label>
        <label>
          {english ? "Display name" : "نام"}
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </label>
        <label>
          {english ? "Role" : "کردار"}
          <select value={role} onChange={(e) => setRole(e.target.value)}>
            <option value="owner">{english ? "Owner" : "مالک"}</option>
            <option value="manager">{english ? "Manager" : "منیجر"}</option>
            <option value="staff">{english ? "Staff" : "عملہ"}</option>
          </select>
        </label>
        <label>
          {existing
            ? english
              ? "New password (leave blank to keep)"
              : "نیا پاس ورڈ (تبدیلی نہ ہو تو خالی چھوڑیں)"
            : english
              ? "Password (12+ characters)"
              : "پاس ورڈ (کم از کم ۱۲ حروف)"}
          <input
            type="password"
            autoComplete="new-password"
            minLength={12}
            required={!existing}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        {existing && (
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={active}
              onChange={(e) => setActive(e.target.checked)}
            />
            {english ? "Active account" : "فعال اکاؤنٹ"}
          </label>
        )}
        <ErrorMessage error={save.error} />
        <Button type="submit" disabled={save.isPending}>
          {english ? "Save account" : "اکاؤنٹ محفوظ کریں"}
        </Button>
      </form>
    </Modal>
  )
}
