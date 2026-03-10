import { createContext, onCleanup, onMount, useContext, type JSX } from "solid-js";
import { createStore } from "solid-js/store";
import { AUTH_REQUIRED_EVENT, ApiRequestError, apiGet } from "../lib/api";

interface AuthBootstrapResponse {
  user: AuthUser | null;
}

export interface AuthUser {
  id: number;
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
  user?: AuthUser | null;
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

function isAuthUser(value: unknown): value is AuthUser {
  if (!value || typeof value !== "object") {
    return false;
  }

  const user = value as Record<string, unknown>;
  return (
    typeof user.id === "number" &&
    typeof user.name === "string" &&
    typeof user.email === "string" &&
    typeof user.isAdmin === "boolean"
  );
}

function readWindowBootstrap() {
  const payload = window.__KAHVESIZ_AUTH__;
  if (!payload) {
    return null;
  }

  const user = isAuthUser(payload.user) ? payload.user : null;
  const isAuthenticated = typeof payload.isAuthenticated === "boolean" ? payload.isAuthenticated : Boolean(user);

  return {
    user,
    isAuthenticated,
  };
}

async function readEndpointBootstrap() {
  const endpoint = import.meta.env.VITE_AUTH_BOOTSTRAP_ENDPOINT?.trim();
  if (!endpoint) {
    return null;
  }

  try {
    const response = await apiGet<AuthBootstrapResponse>(endpoint, {
      retries: 0,
      emitAuthEvent: false,
      timeoutMs: 8_000,
    });

    const user = response && isAuthUser(response.user) ? response.user : null;

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
      if (endpointBootstrap) {
        setState({
          user: endpointBootstrap.user,
          isAuthenticated: endpointBootstrap.isAuthenticated,
          sessionExpired: false,
          loading: false,
        });
        return;
      }

      clearSession(false);
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
