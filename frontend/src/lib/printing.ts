export function printDocument() {
  try {
    window.print()
    return true
  } catch {
    window.dispatchEvent(new Event("shop:print-error"))
    return false
  }
}
