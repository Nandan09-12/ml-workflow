const supabaseUrl = process.env.EXPO_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY;

export const hasSupabaseEnv = Boolean(
  supabaseUrl && supabaseAnonKey && !supabaseUrl.includes("your-project"),
);

export const supabaseConfig = {
  url: supabaseUrl ?? "",
  anonKey: supabaseAnonKey ?? "",
};
