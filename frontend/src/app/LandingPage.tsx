import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, Loader2, XCircle } from "lucide-react";
import { Link } from "react-router-dom";

import { apiFetch } from "@/lib/api-client";

interface HealthResponse {
  status: string;
  db: string;
}

function useBackendHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: async (): Promise<HealthResponse> => {
      const response = await apiFetch("/health");
      if (!response.ok) throw new Error(`Backend returned ${response.status}`);
      return response.json();
    },
    retry: false,
  });
}

function HealthStatus() {
  const { data, isPending, isError } = useBackendHealth();

  if (isPending) {
    return (
      <span className="inline-flex items-center gap-2 text-muted-foreground">
        <Loader2 className="animate-spin" /> Checking backend...
      </span>
    );
  }

  if (isError) {
    return (
      <span className="inline-flex items-center gap-2 text-destructive">
        <XCircle /> Backend unreachable — is `docker compose up` running?
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-2">
      <CheckCircle2 className="text-emerald-600" />
      Backend {data.status}, database {data.db}
    </span>
  );
}

export function LandingPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col items-start justify-center gap-6 p-8">
      <h1 className="text-2xl font-semibold">Mining Waste-to-Value Platform</h1>
      <p className="text-muted-foreground">
        Phase 0 scaffold. This page proves the frontend can reach the FastAPI backend.
      </p>
      <div className="rounded-md border border-border p-4">
        <HealthStatus />
      </div>
      <nav className="flex gap-4 text-sm">
        <Link className="underline hover:text-primary" to="/mine">
          Mine portal
        </Link>
        <Link className="underline hover:text-primary" to="/buyer">
          Buyer portal
        </Link>
        <Link className="underline hover:text-primary" to="/admin">
          Admin portal
        </Link>
      </nav>
    </main>
  );
}
