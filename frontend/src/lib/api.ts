export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}
export async function api<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const csrf = document.cookie
    .split("; ")
    .find((c) => c.startsWith("shop_csrf="))
    ?.split("=")[1]
  const response = await fetch(`/api/v1${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(csrf ? { "X-CSRF-Token": decodeURIComponent(csrf) } : {}),
      ...options.headers,
    },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new ApiError(
      response.status,
      typeof body.detail === "string"
        ? body.detail
        : "درخواست مکمل نہیں ہو سکی / Request failed"
    )
  }
  return response.status === 204 ? (undefined as T) : response.json()
}
