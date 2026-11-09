import { useEffect, useState } from "react"
import { CheckCircle2 } from "lucide-react"
export default function Toast() {
  const [message, setMessage] = useState("")
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>
    const show = (printing: boolean) => {
      setMessage(
        printing
          ? document.documentElement.lang === "en"
            ? "Printing is unavailable. Download the PDF instead."
            : "پرنٹ دستیاب نہیں۔ پی ڈی ایف ڈاؤن لوڈ کریں۔"
          : document.documentElement.lang === "en"
            ? "Saved successfully"
            : "کامیابی سے محفوظ ہو گیا"
      )
      clearTimeout(timer)
      timer = setTimeout(() => setMessage(""), 5000)
    }
    const saved = () => show(false)
    const printing = () => show(true)
    window.addEventListener("shop:saved", saved)
    window.addEventListener("shop:print-error", printing)
    return () => {
      window.removeEventListener("shop:saved", saved)
      window.removeEventListener("shop:print-error", printing)
      clearTimeout(timer)
    }
  }, [])
  return message ? (
    <div className="toast no-print" role="status">
      <CheckCircle2 size={18} />
      {message}
    </div>
  ) : null
}
