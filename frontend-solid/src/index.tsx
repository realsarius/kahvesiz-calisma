/* @refresh reload */
import { render } from "solid-js/web";
import { Router } from "@solidjs/router";
import { AppRoot, AppRoutes } from "./App";
import { AuthProvider } from "./auth/AuthContext";
import "./index.css";

const root = document.getElementById("root");

if (!root) {
  throw new Error("Root element not found.");
}

render(
  () => (
    <AuthProvider>
      <Router root={AppRoot}>
        <AppRoutes />
      </Router>
    </AuthProvider>
  ),
  root,
);
