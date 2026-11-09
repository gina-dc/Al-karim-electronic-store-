import { useState, useEffect } from "react"
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"
import {
  QueryClient,
  MutationCache,
  QueryClientProvider,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Eye, EyeOff, ShieldCheck, Wrench, Languages } from "lucide-react"
import { Button } from "@/components/ui/button"
import { api, ApiError } from "@/lib/api"

import type { User } from "@/lib/types"
import Workspace from "@/components/layout/Workspace"
import Toast from "@/components/Toast"
const client = new QueryClient({
  mutationCache: new MutationCache({
    onSuccess: () => window.dispatchEvent(new Event("shop:saved")),
  }),
  defaultOptions: { queries: { retry: false, staleTime: 30_000 } },
})
const schema = z.object({
  username: z.string().min(1, "صارف کا نام درج کریں"),
  password: z.string().min(1, "پاس ورڈ درج کریں"),
})
type LoginData = z.infer<typeof schema>

function Login({ english }: { english: boolean }) {
  const [show, setShow] = useState(false)
  const cache = useQueryClient()
  const form = useForm<LoginData>({ resolver: zodResolver(schema) })
  const login = useMutation({
    mutationFn: (data: LoginData) =>
      api<User>("/auth/login", { method: "POST", body: JSON.stringify(data) }),
    onSuccess: (user) => cache.setQueryData(["me"], user),
  })
  return (
    <main className="login-wrap">
      <section className="login-card">
        <div className="brand-mark">
          <Wrench size={28} />
        </div>
        <p className="eyebrow">ELECTRONICS SHOP MANAGEMENT</p>
        <h1>{english ? "Welcome back" : "خوش آمدید"}</h1>
        <p className="muted">
          {english
            ? "Sign in to manage your shop securely."
            : "اپنی دکان کا انتظام کرنے کے لیے لاگ اِن کریں۔"}
        </p>
        <form
          onSubmit={form.handleSubmit((data) => login.mutate(data))}
          className="form-stack"
        >
          <label>
            {english ? "Username" : "صارف کا نام"}
            <input
              autoComplete="username"
              dir="ltr"
              {...form.register("username")}
              aria-invalid={!!form.formState.errors.username}
            />
          </label>
          {form.formState.errors.username && (
            <p className="error" role="alert">
              {form.formState.errors.username.message}
            </p>
          )}
          <label>
            {english ? "Password" : "پاس ورڈ"}
            <div className="password-field">
              <input
                type={show ? "text" : "password"}
                autoComplete="current-password"
                dir="ltr"
                {...form.register("password")}
              />
              <button
                type="button"
                onClick={() => setShow(!show)}
                aria-label={
                  english
                    ? "Toggle password visibility"
                    : "پاس ورڈ دکھائیں یا چھپائیں"
                }
              >
                {show ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </label>
          {form.formState.errors.password && (
            <p className="error" role="alert">
              {form.formState.errors.password.message}
            </p>
          )}
          {login.error && (
            <p className="error" role="alert">
              {login.error instanceof ApiError && login.error.status === 401
                ? english
                  ? "Incorrect username or password."
                  : "صارف کا نام یا پاس ورڈ درست نہیں۔"
                : login.error.message}
            </p>
          )}
          <Button type="submit" disabled={login.isPending}>
            {login.isPending
              ? english
                ? "Signing in…"
                : "لاگ اِن ہو رہا ہے…"
              : english
                ? "Sign in"
                : "لاگ اِن کریں"}
          </Button>
        </form>
        <p className="secure-note">
          <ShieldCheck size={16} />
          {english
            ? "Access is managed by the shop owner."
            : "اکاؤنٹس دکان کا مالک بناتا ہے۔"}
        </p>
      </section>
    </main>
  )
}

function Application() {
  const [english, setEnglish] = useState(
    () => sessionStorage.getItem("shop_language") === "en"
  )
  useEffect(() => {
    document.documentElement.lang = english ? "en" : "ur"
    document.documentElement.dir = english ? "ltr" : "rtl"
  }, [english])
  const me = useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      try {
        return await api<User>("/auth/me")
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) return null
        throw error
      }
    },
  })
  return (
    <div dir={english ? "ltr" : "rtl"} lang={english ? "en" : "ur"}>
      <Toast />
      <button
        className="language-toggle"
        onClick={() => {
          sessionStorage.setItem("shop_language", english ? "ur" : "en")
          setEnglish(!english)
        }}
      >
        <Languages size={16} />
        {english ? "اردو" : "English"}
      </button>
      {me.isPending ? (
        <main className="login-wrap" role="status">
          {english ? "Loading…" : "انتظار فرمائیں…"}
        </main>
      ) : me.error ? (
        <main className="login-wrap">
          <section className="login-card">
            <h1>
              {english ? "Connection unavailable" : "سرور سے رابطہ نہیں ہو سکا"}
            </h1>
            <p className="muted">
              {english
                ? "Please try again or contact the shop owner."
                : "دوبارہ کوشش کریں یا دکان کے مالک سے رابطہ کریں۔"}
            </p>
            <Button onClick={() => void me.refetch()}>
              {english ? "Try again" : "دوبارہ کوشش کریں"}
            </Button>
          </section>
        </main>
      ) : (
        <Routes>
          <Route
            path="/*"
            element={
              me.data ? (
                <Workspace
                  user={me.data}
                  english={english}
                  setEnglish={setEnglish}
                />
              ) : (
                <Login english={english} />
              )
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      )}
    </div>
  )
}
export default function App() {
  return (
    <QueryClientProvider client={client}>
      <BrowserRouter>
        <Application />
      </BrowserRouter>
    </QueryClientProvider>
  )
}
