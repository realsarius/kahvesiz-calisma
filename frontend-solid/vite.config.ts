import { defineConfig } from "vite";
import solid from "vite-plugin-solid";

const apiProxyTarget = process.env.VITE_API_PROXY_TARGET || "http://127.0.0.1:8000";

export default defineConfig(({ command }) => ({
  base: command === "serve" ? "/" : "/solid/",
  plugins: [solid()],
  server: {
    port: 5173,
    proxy: {
      "/api": apiProxyTarget,
      "/login": apiProxyTarget,
      "/signup": apiProxyTarget,
      "/logout": apiProxyTarget,
      "/confirm": apiProxyTarget,
    },
  },
}));
