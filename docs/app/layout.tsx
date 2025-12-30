import 'fumadocs-ui/style.css';
import './global.css';
import { RootProvider } from 'fumadocs-ui/provider/next';
import type { ReactNode } from 'react';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: {
    default: 'Hanzo Python SDK',
    template: '%s | Hanzo Python SDK',
  },
  description: 'The official Python SDK for Hanzo AI - 100+ LLM providers through a single OpenAI-compatible API',
  icons: {
    icon: [
      { url: '/python-sdk/favicon.svg', type: 'image/svg+xml' },
      { url: '/python-sdk/favicon.png', type: 'image/png', sizes: '32x32' },
    ],
    apple: '/python-sdk/apple-touch-icon.png',
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning className="dark">
      <body>
        <RootProvider
          theme={{
            defaultTheme: 'dark',
            attribute: 'class',
          }}
        >
          {children}
        </RootProvider>
      </body>
    </html>
  );
}
