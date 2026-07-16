import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // Listens on all local IP addresses (needed for Docker)
    port: 5173,
    watch: {
      usePolling: true,
    },
  },
});
