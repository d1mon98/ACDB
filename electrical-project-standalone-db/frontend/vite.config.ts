import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// During development the Vite dev server (port 5173) proxies every /api request
// to the FastAPI backend (port 8000), so the frontend can use plain relative
// URLs and there is no cross-origin concern.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
