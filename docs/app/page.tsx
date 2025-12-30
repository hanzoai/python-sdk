import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="max-w-2xl text-center">
        <h1 className="mb-4 text-4xl font-bold">Hanzo Python SDK</h1>
        <p className="mb-8 text-lg text-fd-muted-foreground">
          The official Python SDK for Hanzo AI - Unified access to 100+ LLM providers
          through a single OpenAI-compatible API.
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/docs"
            className="rounded-lg bg-fd-primary px-6 py-3 font-medium text-fd-primary-foreground transition-colors hover:bg-fd-primary/90"
          >
            Get Started
          </Link>
          <a
            href="https://github.com/hanzoai/python-sdk"
            className="rounded-lg border border-fd-border px-6 py-3 font-medium transition-colors hover:bg-fd-accent"
            target="_blank"
            rel="noopener noreferrer"
          >
            GitHub
          </a>
        </div>
      </div>
    </main>
  );
}
