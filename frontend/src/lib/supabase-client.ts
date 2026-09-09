import { createClient } from "@supabase/supabase-js";

// Placeholder values until a real Supabase project exists (see .env.example).
// The client still constructs successfully with placeholders — it just can't
// authenticate anyone until real values are supplied.
export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY,
);
