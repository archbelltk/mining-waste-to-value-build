import { LogIn } from "lucide-react";

export function LoginPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col items-start justify-center gap-3 p-8">
      <LogIn className="text-muted-foreground" />
      <h1 className="text-xl font-semibold">Sign in</h1>
      <p className="text-muted-foreground">
        Wired to Supabase Auth once a real project's URL/anon key are set in .env — see
        docs/how-it-works.md.
      </p>
    </main>
  );
}
