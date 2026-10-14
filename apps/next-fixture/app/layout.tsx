import { BloxwapSans } from '@bloxwap/font/sans';
import { BloxwapMono } from '@bloxwap/font/mono';
import type { ReactNode } from 'react';
import './global.css';
export default function Layout({ children }: { children: ReactNode }) {
 return <html lang="en" className={`${BloxwapSans.variable} ${BloxwapMono.variable}`}><body>{children}</body></html>;
}
