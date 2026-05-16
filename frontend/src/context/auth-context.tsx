import React, { createContext, useContext, useEffect, useState } from "react";
import type { Session, User } from "@supabase/supabase-js";

import { supabase } from "@/lib/supabase";
const disableAuth = (import.meta.env.VITE_DISABLE_AUTH as string | undefined) === "true";

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(
    disableAuth
      ? ({ id: (import.meta.env.VITE_DEV_USER_ID as string | undefined) || "dev-user", email: "dev@local", app_metadata: {}, user_metadata: {}, aud: "authenticated", created_at: new Date().toISOString() } as unknown as User)
      : null,
  );
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (disableAuth) {
      setLoading(false);
      return;
    }
    supabase.auth.getSession().then(({ data, error }) => {
      if (!error) {
        setSession(data.session ?? null);
        setUser(data.session?.user ?? null);
      }
      setLoading(false);
    });

    const { data } = supabase.auth.onAuthStateChange((_event, currentSession) => {
      setSession(currentSession ?? null);
      setUser(currentSession?.user ?? null);
      setLoading(false);
    });

    return () => data.subscription.unsubscribe();
  }, []);

  const signInWithGoogle = async () => {
    if (disableAuth) return;
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${window.location.origin}/onboarding`,
      },
    });
    if (error) throw error;
  };

  const signOut = async () => {
    if (disableAuth) return;
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
  };

  return (
    <AuthContext.Provider value={{ user, session, loading, signInWithGoogle, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
