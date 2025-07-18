// dashboard/vite.config.ts  (create)
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/ws": "ws://localhost:8000",
      "/registry": "http://localhost:8000",
      "/analyzer": "http://localhost:8000",
      "/metrics": "http://localhost:8000",
    },
  },
});
