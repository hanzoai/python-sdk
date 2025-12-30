import { DocsLayout } from 'fumadocs-ui/layouts/docs';
import type { ReactNode } from 'react';
import { source } from '@/lib/source';

function HanzoLogo() {
  return (
    <svg viewBox="0 0 67 67" width="24" height="24" xmlns="http://www.w3.org/2000/svg">
      <path d="M22.21 67V44.6369H0V67H22.21Z" fill="currentColor"/>
      <path d="M0 44.6369L22.21 46.8285V44.6369H0Z" fill="currentColor" opacity="0.7"/>
      <path d="M66.7038 22.3184H22.2534L0.0878906 44.6367H44.4634L66.7038 22.3184Z" fill="currentColor"/>
      <path d="M22.21 0H0V22.3184H22.21V0Z" fill="currentColor"/>
      <path d="M66.7198 0H44.5098V22.3184H66.7198V0Z" fill="currentColor"/>
      <path d="M66.6753 22.3185L44.5098 20.0822V22.3185H66.6753Z" fill="currentColor" opacity="0.7"/>
      <path d="M66.7198 67V44.6369H44.5098V67H66.7198Z" fill="currentColor"/>
    </svg>
  );
}

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <DocsLayout
      tree={source.pageTree}
      nav={{
        title: (
          <div className="flex items-center gap-2">
            <HanzoLogo />
            <span className="font-semibold">Hanzo Python SDK</span>
          </div>
        ),
        url: '/docs',
      }}
      sidebar={{
        defaultOpenLevel: 1,
      }}
    >
      {children}
    </DocsLayout>
  );
}
