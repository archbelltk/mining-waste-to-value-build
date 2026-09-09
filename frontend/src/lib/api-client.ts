import { supabase } from "@/lib/supabase-client";

const API_URL = import.meta.env.VITE_API_URL;

/** Fetch wrapper that calls FastAPI and attaches the Supabase JWT when a session exists. */
export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  if (session?.access_token) {
    headers.set("Authorization", `Bearer ${session.access_token}`);
  }

  return fetch(`${API_URL}${path}`, { ...init, headers });
}
