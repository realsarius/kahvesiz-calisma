import { createEffect, ErrorBoundary, Suspense, lazy, type JSX } from "solid-js";
import { Route, type RouteSectionProps, useLocation, useNavigate } from "@solidjs/router";
import { useAuth } from "./auth/AuthContext";
import { AppLayout } from "./components/layout/AppLayout";
import { GlobalErrorFallback } from "./components/GlobalErrorFallback";
import { RouteLoader } from "./components/RouteLoader";

const HomePage = lazy(() => import("./pages/HomePage"));
const CafesPage = lazy(() => import("./pages/CafesPage"));
const CafeDetailPage = lazy(() => import("./pages/CafeDetailPage"));
const AboutPage = lazy(() => import("./pages/AboutPage"));
const PrivacyPage = lazy(() => import("./pages/PrivacyPage"));
const LicensePage = lazy(() => import("./pages/LicensePage"));
const ContactPage = lazy(() => import("./pages/ContactPage"));
const AdminPage = lazy(() => import("./pages/AdminPage"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const SignupPage = lazy(() => import("./pages/SignupPage"));
const NotFoundPage = lazy(() => import("./pages/NotFoundPage"));

export function AppRoot(props: RouteSectionProps): JSX.Element {
  const auth = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  createEffect(() => {
    if (!auth.state.sessionExpired) {
      return;
    }

    if (location.pathname === "/login") {
      return;
    }

    const returnTo = `${location.pathname}${location.search}`;
    auth.clearSession(false);
    void navigate(`/login?reason=session_expired&redirect=${encodeURIComponent(returnTo)}`, {
      replace: true,
    });
  });

  return (
    <ErrorBoundary fallback={(error, reset) => <GlobalErrorFallback error={error} reset={reset} />}>
      <AppLayout>
        <Suspense fallback={<RouteLoader />}>{props.children}</Suspense>
      </AppLayout>
    </ErrorBoundary>
  );
}

export function AppRoutes() {
  return (
    <>
      <Route path="/" component={HomePage} />
      <Route path="/cafes" component={CafesPage} />
      <Route path="/cafes/:id" component={CafeDetailPage} />
      <Route path="/about" component={AboutPage} />
      <Route path="/privacy" component={PrivacyPage} />
      <Route path="/license" component={LicensePage} />
      <Route path="/contact" component={ContactPage} />
      <Route path="/admin" component={AdminPage} />
      <Route path="/login" component={LoginPage} />
      <Route path="/signup" component={SignupPage} />
      <Route path="*" component={NotFoundPage} />
    </>
  );
}
