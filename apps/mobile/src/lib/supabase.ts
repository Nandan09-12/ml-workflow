import "react-native-url-polyfill/auto";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { AppState, Platform } from "react-native";
import { createClient, processLock, type SupabaseClient } from "@supabase/supabase-js";

import { hasSupabaseEnv, supabaseConfig } from "./env";

function createStubSupabaseClient(): SupabaseClient {
  const notConfigured = () => {
    throw new Error(
      "Supabase is not configured. Set EXPO_PUBLIC_SUPABASE_URL and EXPO_PUBLIC_SUPABASE_ANON_KEY in apps/mobile/.env to enable real auth.",
    );
  };

  return {
    auth: {
      getSession: async () => ({ data: { session: null }, error: null }),
      onAuthStateChange: () => ({
        data: { subscription: { unsubscribe: () => undefined } },
      }),
      signInWithPassword: notConfigured,
      signInWithOAuth: notConfigured,
      signUp: notConfigured,
      signOut: async () => ({ error: null }),
      exchangeCodeForSession: notConfigured,
    },
  } as unknown as SupabaseClient;
}

export const supabase: SupabaseClient = hasSupabaseEnv
  ? createClient(supabaseConfig.url, supabaseConfig.anonKey, {
      auth: {
        ...(Platform.OS !== "web" ? { storage: AsyncStorage } : {}),
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: false,
        lock: processLock,
      },
    })
  : createStubSupabaseClient();

if (hasSupabaseEnv && Platform.OS !== "web") {
  AppState.addEventListener("change", (state) => {
    if (state === "active") {
      supabase.auth.startAutoRefresh();
      return;
    }

    supabase.auth.stopAutoRefresh();
  });
}
