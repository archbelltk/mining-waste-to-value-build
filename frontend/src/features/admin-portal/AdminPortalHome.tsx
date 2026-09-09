import { ShieldCheck } from "lucide-react";

export function AdminPortalHome() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col items-start justify-center gap-3 p-8">
      <ShieldCheck className="text-muted-foreground" />
      <h1 className="text-xl font-semibold">Admin portal</h1>
      <p className="text-muted-foreground">
        Org verification and the applications taxonomy arrive alongside Phases 1–2.
      </p>
    </main>
  );
}
