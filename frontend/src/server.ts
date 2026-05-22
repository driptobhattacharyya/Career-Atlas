/**
 * Cloudflare Worker server entry — wraps the TanStack Start SSR handler with
 * Sentry so server-side / Worker errors are captured (the browser SDK in
 * lib/sentry.ts only covers client-side errors).
 */
import * as Sentry from "@sentry/cloudflare";
import { wrapFetchWithSentry } from "@sentry/tanstackstart-react";
import handler from "@tanstack/react-start/server-entry";

export default Sentry.withSentry(
  () => ({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    environment: import.meta.env.MODE,
    sendDefaultPii: true,
    tracesSampleRate: 0.2,
  }),
  // @ts-expect-error - handler is not typed as a Cloudflare fetch handler
  wrapFetchWithSentry(handler),
);
