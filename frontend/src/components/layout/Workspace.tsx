import Inventory from "@/pages/Inventory"
import { useEffect, useState, lazy, Suspense } from "react"
import { NavLink, Routes, Route, Navigate, Link } from "react-router-dom"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  LayoutDashboard,
  FilePlus2,
  ReceiptText,
  UsersRound,
  Boxes,
  ContactRound,
  Wallet,
  ChartNoAxesCombined,
  Settings as SettingsIcon,
  LogOut,
  Menu,
  Bell,
  Sun,
  Moon,
  Wrench,
} from "lucide-react"
import { api } from "@/lib/api"
import type { Row, User, Page } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { ErrorMessage } from "@/components/shared"
import { useTheme } from "@/components/theme-provider"
import ResourcePage from "@/pages/ResourcePage"
import { resources } from "@/lib/resources"
import { ReceiptList, ReceiptEditor, ReceiptDetail } from "@/pages/Receipts"
const Dashboard = lazy(() => import("@/pages/Dashboard"))
const Workforce = lazy(() => import("@/pages/Workforce"))
import Payments from "@/pages/Payments"
const Settings = lazy(() => import("@/pages/Settings"))
const nav = [
  { to: "/", ur: "ڈیش بورڈ", en: "Dashboard", icon: LayoutDashboard },
  { to: "/new-receipt", ur: "نئی بلٹی", en: "New receipt", icon: FilePlus2 },
  {
    to: "/receipts",
    ur: "بلٹی کا ریکارڈ",
    en: "Receipt records",
    icon: ReceiptText,
  },
  { to: "/workers", ur: "کاریگر", en: "Workforce", icon: UsersRound },
  { to: "/inventory", ur: "اسٹاک", en: "Inventory", icon: Boxes },
  { to: "/customers", ur: "گاہک", en: "Customers", icon: ContactRound },
  { to: "/payments", ur: "ادائیگیاں", en: "Payments", icon: Wallet },
  {
    to: "/reports",
    ur: "رپورٹس",
    en: "Reports",
    icon: ChartNoAxesCombined,
    owner: true,
  },
  {
    to: "/settings",
    ur: "ترتیبات",
    en: "Settings",
    icon: SettingsIcon,
    owner: true,
  },
]
export default function Workspace({
  user,
  english,
  setEnglish,
}: {
  user: User
  english: boolean
  setEnglish: (value: boolean) => void
}) {
  const cache = useQueryClient()
  const [open, setOpen] = useState(false)
  const { theme, setTheme } = useTheme()
  const settings = useQuery({
    queryKey: ["settings"],
    queryFn: () => api<Row>("/settings"),
  })
  const notifications = useQuery({
    queryKey: ["notifications"],
    queryFn: () => api<Page<Row>>("/jobs?status=assigned&limit=1"),
  })
  const language = settings.data?.language
  const configuredTheme = settings.data?.theme
  useEffect(() => {
    if (language && !sessionStorage.getItem("shop_language"))
      setEnglish(language === "en")
  }, [language, setEnglish])
  useEffect(() => {
    if (configuredTheme === "dark" || configuredTheme === "light")
      setTheme(configuredTheme)
  }, [configuredTheme, setTheme])
  const logout = useMutation({
    mutationFn: () => api<void>("/auth/logout", { method: "POST" }),
    onSuccess: () => {
      cache.clear()
      cache.setQueryData(["me"], null)
    },
  })
  const role =
    user.role === "owner"
      ? english
        ? "Owner"
        : "مالک"
      : user.role === "manager"
        ? english
          ? "Manager"
          : "منیجر"
        : english
          ? "Staff"
          : "عملہ"
  return (
    <div className={`workspace ${open ? "menu-open" : ""}`}>
      <aside className="app-sidebar">
        <div className="sidebar-brand">
          {settings.data?.has_logo ? (
            <img src="/api/v1/settings/logo" alt="" className="shop-logo" />
          ) : (
            <Wrench size={24} />
          )}
          <strong>
            {String(
              settings.data?.name ??
                (english ? "Shop management" : "دکان کا انتظام")
            )}
          </strong>
        </div>
        <p className="sidebar-caption">
          {english ? "DAILY OPERATIONS" : "روزمرہ کاروبار"}
        </p>
        <nav>
          {nav
            .filter((n) => !n.owner || user.role === "owner")
            .map((n) => (
              <NavLink
                end={n.to === "/"}
                key={n.to}
                to={n.to}
                onClick={() => setOpen(false)}
                className={({ isActive }) =>
                  isActive ? "nav-item active" : "nav-item"
                }
              >
                <n.icon size={18} />
                <span>{english ? n.en : n.ur}</span>
              </NavLink>
            ))}
        </nav>
        <div className="sidebar-footer">
          <div className="user-avatar">{user.display_name.slice(0, 1)}</div>
          <strong>{user.display_name}</strong>
          <span>{role}</span>
          <Button
            variant="outline"
            disabled={logout.isPending}
            onClick={() => logout.mutate()}
          >
            <LogOut size={16} />
            {english ? "Sign out" : "لاگ آؤٹ"}
          </Button>
          <ErrorMessage error={logout.error} />
        </div>
      </aside>
      <div className="app-body">
        <header className="app-topbar">
          <div className="topbar-start">
            <Button
              className="mobile-menu"
              variant="ghost"
              size="icon"
              onClick={() => setOpen(!open)}
              aria-label={english ? "Toggle navigation" : "مینو کھولیں"}
            >
              <Menu size={20} />
            </Button>
            <span>
              {new Intl.DateTimeFormat(english ? "en-PK" : "ur-PK", {
                dateStyle: "full",
                timeZone: "Asia/Karachi",
              }).format(new Date())}
            </span>
          </div>
          <div className="topbar-actions">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              aria-label={english ? "Toggle theme" : "تھیم تبدیل کریں"}
            >
              {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
            </Button>
            <Link
              className="notification-link"
              to="/workers?tab=jobs"
              aria-label={english ? "Assigned jobs" : "تفویض شدہ کام"}
            >
              <Bell size={19} />
              {!!notifications.data?.total && (
                <span>{notifications.data.total}</span>
              )}
            </Link>
            <span className="role-badge">{role}</span>
          </div>
        </header>
        <main className="workspace-main">
          <Suspense
            fallback={
              <p role="status">{english ? "Loading…" : "انتظار فرمائیں…"}</p>
            }
          >
            <Routes>
              <Route
                path="/"
                element={<Dashboard english={english} user={user} />}
              />
              <Route
                path="/new-receipt"
                element={<ReceiptEditor english={english} user={user} />}
              />
              <Route
                path="/receipts"
                element={<ReceiptList english={english} />}
              />
              <Route
                path="/receipts/:id"
                element={<ReceiptDetail english={english} user={user} />}
              />
              <Route
                path="/receipts/:id/edit"
                element={<ReceiptEditor english={english} user={user} />}
              />
              <Route
                path="/customers"
                element={
                  <ResourcePage
                    config={resources.customers}
                    english={english}
                    user={user}
                  />
                }
              />
              <Route
                path="/inventory"
                element={<Inventory english={english} user={user} />}
              />
              <Route
                path="/workers"
                element={<Workforce english={english} user={user} />}
              />
              <Route
                path="/payments"
                element={<Payments english={english} user={user} />}
              />
              <Route
                path="/reports"
                element={
                  user.role === "owner" ? (
                    <Dashboard english={english} user={user} reports />
                  ) : (
                    <Navigate to="/" replace />
                  )
                }
              />
              <Route
                path="/settings"
                element={
                  user.role === "owner" ? (
                    <Settings english={english} />
                  ) : (
                    <Navigate to="/" replace />
                  )
                }
              />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </main>
      </div>
    </div>
  )
}
