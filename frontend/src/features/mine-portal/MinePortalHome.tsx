import { Pickaxe } from "lucide-react";

export function MinePortalHome() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col items-start justify-center gap-3 p-8">
      <Pickaxe className="text-muted-foreground" />
      <h1 className="text-xl font-semibold">Mine portal</h1>
      <p className="text-muted-foreground">
        Waste-stream listing, lab data, and verification arrive in Phase 1.
      </p>
    </main>
  );
}
