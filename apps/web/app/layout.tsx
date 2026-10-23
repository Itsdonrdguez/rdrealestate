import './globals.css';
import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'RD Real Estate Intelligence',
  description: 'Maryland property and owner intelligence workspace',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="app-frame">
          <aside className="sidebar">
            <Link href="/" className="brand" aria-label="RD Real Estate Intelligence home">
              <span className="brand-mark">RD</span>
              <span><strong>Real Estate</strong><small>Intelligence</small></span>
            </Link>
            <nav className="primary-nav" aria-label="Primary navigation">
              <Link href="/properties"><span>PS</span> Property search</Link>
              <span className="nav-disabled" title="Available after owner-name data"><span>OW</span> Owners <em>later</em></span>
              <span className="nav-disabled" title="Available after scoring data"><span>OP</span> Opportunities <em>later</em></span>
              <Link href="/data-health"><span>DH</span> Data health</Link>
            </nav>
            <div className="source-card">
              <span className="status-dot" />
              <div><strong>Maryland public data</strong><small>Charles County loaded</small></div>
            </div>
          </aside>
          <div className="app-content">
            <header className="topbar">
              <div><span className="eyebrow">Private workspace</span></div>
              <div className="topbar-meta"><span className="status-dot" /> Local system</div>
            </header>
            {children}
          </div>
        </div>
      </body>
    </html>
  );
}
