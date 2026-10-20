import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Property Intelligence',
  description: 'Maryland property and owner intelligence workspace',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
