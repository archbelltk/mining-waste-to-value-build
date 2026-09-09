import { ShoppingCart } from "lucide-react";

export function BuyerPortalHome() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col items-start justify-center gap-3 p-8">
      <ShoppingCart className="text-muted-foreground" />
      <h1 className="text-xl font-semibold">Buyer portal</h1>
      <p className="text-muted-foreground">
        Browsing listings and posting requirements arrive in Phase 3.
      </p>
    </main>
  );
}
