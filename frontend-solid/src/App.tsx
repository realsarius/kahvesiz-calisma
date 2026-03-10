import { ErrorBoundary, Suspense, lazy, type JSX } from "solid-js";
import { Route, type RouteSectionProps } from "@solidjs/router";
import { AppLayout } from "./components/layout/AppLayout";
import { GlobalErrorFallback } from "./components/GlobalErrorFallback";
import { RouteLoader } from "./components/RouteLoader";

const HomePage = lazy(() => import("./pages/HomePage"));
const AboutPage = lazy(() => import("./pages/AboutPage"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const SignupPage = lazy(() => import("./pages/SignupPage"));
const NotFoundPage = lazy(() => import("./pages/NotFoundPage"));

export function AppRoot(props: RouteSectionProps): JSX.Element {
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
      <Route path="/about" component={AboutPage} />
      <Route path="/login" component={LoginPage} />
      <Route path="/signup" component={SignupPage} />
      <Route path="*" component={NotFoundPage} />
    </>
  );
}
