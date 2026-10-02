import { DocsLayout } from 'fumadocs-ui/layouts/docs';
import type { ReactNode } from 'react';
import { ArrowUpRight } from 'lucide-react';
import { baseOptions } from '@/lib/layout.shared';
import { source } from '@/lib/source';
import { assetUrl } from '@/lib/site';
import { Toaster } from '@/components/ui/toast';

export default function Layout({ children }: { children: ReactNode }) {
  const { links: _links, ...options } = baseOptions();
  return <DocsLayout {...options} tree={source.getPageTree()} sidebar={{
    defaultOpenLevel: 1,
    footer: <div className="docs-sidebar-footer" key="sidebar-footer">
      <a href={assetUrl('/#tester')} className="docs-app-link">Open the type tester <ArrowUpRight className="size-4" aria-hidden="true" /></a>
    </div>,
  }}>{children}<Toaster /></DocsLayout>;
}
