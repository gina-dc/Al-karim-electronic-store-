import { useEffect, useRef } from "react"
import type { ReactNode } from "react"
import { X } from "lucide-react"
import { Button } from "@/components/ui/button"
export function Modal({
  title,
  close,
  children,
}: {
  title: string
  close: () => void
  children: ReactNode
}) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    ref.current?.showModal()
  }, [])
  return (
    <dialog ref={ref} className="modal" onCancel={close}>
      <div className="modal-heading">
        <h2>{title}</h2>
        <Button variant="ghost" size="icon" onClick={close} aria-label="Close">
          <X size={18} />
        </Button>
      </div>
      {children}
    </dialog>
  )
}
export function ErrorMessage({ error }: { error: unknown }) {
  return error ? (
    <p role="alert" className="error">
      {error instanceof Error ? error.message : String(error)}
    </p>
  ) : null
}
export function Empty({ english }: { english: boolean }) {
  return (
    <div className="empty-state">
      {english
        ? "No records yet. Add your first record to get started."
        : "ابھی کوئی ریکارڈ موجود نہیں۔ نیا ریکارڈ شامل کریں۔"}
    </div>
  )
}
export function PageHeading({
  title,
  description,
  children,
}: {
  title: string
  description?: string
  children?: ReactNode
}) {
  return (
    <div className="page-heading">
      <div>
        <h1>{title}</h1>
        {description && <p className="muted">{description}</p>}
      </div>
      <div className="heading-actions">{children}</div>
    </div>
  )
}
