import { defineConfig } from "vite";
import solid from "vite-plugin-solid";

export default defineConfig({
  plugins: [solid()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:5040",
      "/login": "http://localhost:5040",
      "/signup": "http://localhost:5040",
      "/logout": "http://localhost:5040",
      "/confirm": "http://localhost:5040",
    },
  },
});
