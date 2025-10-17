// frontend/vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:18081",
        changeOrigin: true,
        secure: false,
        ws: true,
      },
      "/ws": {
        target: "ws://localhost:18081",
        ws: true,
        changeOrigin: true,
      },
    },
  },
});