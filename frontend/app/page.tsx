import Image from "next/image";
import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-4">Flowwatch</h1>
        <p className="text-muted-foreground mb-8">
          Monitor n8n workflow runs and alert on failures
        </p>
        <div className="space-y-4">
          <Link
            href="/api/health"
            className="inline-block px-6 py-3 bg-primary text-primary-foreground rounded hover:bg-secondary/80">
            Check API Health
          </Link>
          <Link
            href="/dashboard"
            className="inline-block px-6 py-3 bg-secondary text-secondary-foreground rounded hover:bg-secondary/80">
            Go to Dashboard
          </Link>
        </div>
      </div>
    </main>
  );
}