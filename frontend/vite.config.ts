import { resolve } from "node:path"
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig, loadEnv } from "vite"

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "VITE_")
  return {
    plugins: [react(), tailwindcss()],
    server: {
      proxy: {
        "/api":
          process.env.VITE_API_PROXY ??
          env.VITE_API_PROXY ??
          "http://127.0.0.1:8000",
      },
    },
    resolve: {
      alias: {
        "@": resolve(import.meta.dirname, "./src"),
      },
    },
  }
})
