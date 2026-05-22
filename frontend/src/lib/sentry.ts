/**
 * Sentry browser init. No-op when VITE_SENTRY_DSN is unset (local dev) or
 * during SSR. Imported once from __root.tsx.
 */
import * as Sentry from "@sentry/react";

const dsn = import.meta.env.VITE_SENTRY_DSN as string | undefined;

if (typeof document !== "undefined" && dsn) {
  Sentry.init({
    dsn,
    environment: (import.meta.env.MODE as string) || "production",
    tracesSampleRate: 0.2,
    sendDefaultPii: true,
  });
}

export { Sentry };
