import { createContext, onCleanup, onMount, useContext, type JSX } from "solid-js";
import { createStore } from "solid-js/store";
import { AUTH_REQUIRED_EVENT, ApiRequestError, apiGet } from "../lib/api";

interface AuthBootstrapUser {
  id: number | string;
  name?: string;
  display_name?: string;
  username?: string;
  email: string;
  role?: string;
  isAdmin?: boolean;
  is_admin?: boolean;
}

interface AuthBootstrapResponse {
  user: AuthBootstrapUser | null;
}

export interface AuthUser {
  id: number | string;
  name: string;
  email: string;
  isAdmin: boolean;
}

interface AuthState {
  user: AuthUser | null;
  isAuthenticated: boolean;
  loading: boolean;
  sessionExpired: boolean;
}

interface AuthContextValue {
  state: AuthState;
  bootstrap: () => Promise<void>;
  setUser: (user: AuthUser | null) => void;
  clearSession: (sessionExpired?: boolean) => void;
}

interface WindowAuthBootstrap {
  user?: AuthBootstrapUser | null;
  isAuthenticated?: boolean;
}

declare global {
  interface Window {
    __KAHVESIZ_AUTH__?: WindowAuthBootstrap;
  }

  interface ImportMetaEnv {
    readonly VITE_AUTH_BOOTSTRAP_ENDPOINT?: string;
  }
}

const AuthContext = createContext<AuthContextValue>();

function normalizeAuthUser(value: unknown): AuthUser | null {
  if (!value || typeof value !== "object") {
    return null;
  }

  const user = value as Record<string, unknown>;
  const id = user.id;
  const isIdValid = typeof id === "number" || typeof id === "string";

  const name =
    typeof user.name === "string"
      ? user.name
      : typeof user.display_name === "string"
        ? user.display_name
        : typeof user.username === "string"
          ? user.username
          : null;

  if (!isIdValid || !name || typeof user.email !== "string") {
    return null;
  }

  const isAdmin =
    typeof user.isAdmin === "boolean"
      ? user.isAdmin
      : typeof user.is_admin === "boolean"
        ? user.is_admin
        : user.role === "admin";

  return {
    id,
    name,
    email: user.email,
    isAdmin,
  };
}

function readWindowBootstrap() {
  const payload = window.__KAHVESIZ_AUTH__;
  if (!payload) {
    return null;
  }

  const user = normalizeAuthUser(payload.user);
  const isAuthenticated = typeof payload.isAuthenticated === "boolean" ? payload.isAuthenticated : Boolean(user);

  return {
    user,
    isAuthenticated,
  };
}

async function readEndpointBootstrap() {
  const endpoint = import.meta.env.VITE_AUTH_BOOTSTRAP_ENDPOINT?.trim() || "/api/v1/auth/session";

  try {
    const response = await apiGet<AuthBootstrapResponse | null>(endpoint, {
      retries: 0,
      emitAuthEvent: false,
      timeoutMs: 8_000,
    });

    const user = normalizeAuthUser(response?.user);

    return {
      user,
      isAuthenticated: Boolean(user),
    };
  } catch (error) {
    if (error instanceof ApiRequestError && [401, 403, 404].includes(error.status)) {
      return {
        user: null,
        isAuthenticated: false,
      };
    }

    throw error;
  }
}

export function AuthProvider(props: { children: JSX.Element }) {
  const [state, setState] = createStore<AuthState>({
    user: null,
    isAuthenticated: false,
    loading: true,
    sessionExpired: false,
  });

  const setUser = (user: AuthUser | null) => {
    setState({
      user,
      isAuthenticated: Boolean(user),
      sessionExpired: false,
    });
  };

  const clearSession = (sessionExpired = false) => {
    setState({
      user: null,
      isAuthenticated: false,
      sessionExpired,
    });
  };

  const bootstrap = async () => {
    setState("loading", true);

    try {
      const windowBootstrap = readWindowBootstrap();
      if (windowBootstrap) {
        setState({
          user: windowBootstrap.user,
          isAuthenticated: windowBootstrap.isAuthenticated,
          sessionExpired: false,
          loading: false,
        });
        return;
      }

      const endpointBootstrap = await readEndpointBootstrap();
      setState({
        user: endpointBootstrap.user,
        isAuthenticated: endpointBootstrap.isAuthenticated,
        sessionExpired: false,
        loading: false,
      });
    } catch {
      clearSession(false);
    } finally {
      setState("loading", false);
    }
  };

  const handleAuthRequired = () => {
    clearSession(true);
  };

  onMount(() => {
    void bootstrap();
    window.addEventListener(AUTH_REQUIRED_EVENT, handleAuthRequired);
  });

  onCleanup(() => {
    window.removeEventListener(AUTH_REQUIRED_EVENT, handleAuthRequired);
  });

  return (
    <AuthContext.Provider
      value={{
        state,
        bootstrap,
        setUser,
        clearSession,
      }}
    >
      {props.children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth hook must be used inside AuthProvider.");
  }

  return context;
}
