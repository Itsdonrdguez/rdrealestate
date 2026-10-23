'use client';

import { useEffect, useState } from 'react';
import { apiFetch } from '@/lib/api';

type Health = { status: string; database_bytes: number; raw_directory_bytes: number; latest_sync: null | { id: string; source: string; status: string; started_at: string; finished_at: string; records_seen: number; records_created: number; records_updated: number; records_failed: number; records_validated: number; pages_fetched: number; api_retries: number; raw_bytes: number; elapsed_seconds: number }; capacity_preflight: null | { host_free_bytes: number; minimum_free_bytes: number; statewide_records: number; preflight_passed: boolean }; capacity: null | { host_free_bytes: number; projected_raw_bytes: number; projected_database_bytes: number; required_bytes_at_2x: number; statewide_go: boolean } };
const bytes = (value: number) => new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(value / 1_000_000_000) + ' GB';

export default function DataHealth() {
  const [data, setData] = useState<Health | null>(null); const [error, setError] = useState('');
  useEffect(() => { apiFetch<Health>('/api/system/health').then(setData).catch(() => setError('The system health API is unavailable.')); }, []);
  const sync = data?.latest_sync;
  const capacity = data?.capacity;
  const capacityPercent = capacity ? Math.min(100, capacity.host_free_bytes / capacity.required_bytes_at_2x * 100) : 0;
  return <main className="page health-page">
    <div className="page-heading compact"><div><span className="eyebrow">Operations</span><h1>System & data health</h1></div><p>Live database, ingestion, and capacity signals for the local intelligence stack.</p></div>
    {error && <div className="error-banner">{error}</div>}
    <section className="health-summary">
      <article><span className="metric-icon green">✓</span><div><small>API status</small><strong>{data?.status ?? 'Checking…'}</strong><em>Local service</em></div></article>
      <article><span className="metric-icon">DB</span><div><small>Database size</small><strong>{data ? bytes(data.database_bytes) : '—'}</strong><em>PostgreSQL / PostGIS</em></div></article>
      <article><span className="metric-icon">RAW</span><div><small>Raw evidence</small><strong>{data ? bytes(data.raw_directory_bytes) : '—'}</strong><em>Append-only snapshots</em></div></article>
      <article><span className="metric-icon amber">!</span><div><small>Statewide capacity</small><strong>{capacity?.statewide_go ? 'Go' : 'Hold'}</strong><em>{capacity?.statewide_go ? 'Capacity gate passed' : 'More headroom required'}</em></div></article>
    </section>
    <div className="health-grid">
      <section className="detail-card"><div className="card-heading"><div><span className="status-dot"/><h2>Latest Maryland sync</h2></div><span className={`status-pill ${sync?.status}`}>{sync?.status ?? 'Loading'}</span></div>
        <div className="sync-hero"><div><small>Records processed</small><strong>{sync?.records_seen.toLocaleString() ?? '—'}</strong></div><div><small>Elapsed time</small><strong>{sync ? `${Math.floor(sync.elapsed_seconds / 60)}m ${Math.round(sync.elapsed_seconds % 60)}s` : '—'}</strong></div></div>
        <dl className="metric-list"><div><dt>Validated</dt><dd>{sync?.records_validated.toLocaleString() ?? '—'}</dd></div><div><dt>Created</dt><dd>{sync?.records_created.toLocaleString() ?? '—'}</dd></div><div><dt>Updated</dt><dd>{sync?.records_updated.toLocaleString() ?? '—'}</dd></div><div><dt>Failed</dt><dd className={sync?.records_failed ? 'bad' : ''}>{sync?.records_failed.toLocaleString() ?? '—'}</dd></div><div><dt>API pages</dt><dd>{sync?.pages_fetched ?? '—'}</dd></div><div><dt>Recovered retries</dt><dd>{sync?.api_retries ?? '—'}</dd></div></dl>
        <footer>Run ID <code>{sync?.id ?? '—'}</code><span>{sync?.finished_at ? new Date(sync.finished_at).toLocaleString() : ''}</span></footer>
      </section>
      <section className="detail-card capacity-card"><div className="card-heading"><h2>Capacity gate</h2><span className={`status-pill ${capacity?.statewide_go ? 'succeeded' : 'hold'}`}>{capacity?.statewide_go ? 'Go' : 'No-go'}</span></div><div className="capacity-visual"><div className="capacity-ring"><strong>{capacity ? (capacity.host_free_bytes / 1_000_000_000).toFixed(1) : '—'}</strong><small>GB free</small></div><div><small>Statewide 2× target</small><strong>{capacity ? bytes(capacity.required_bytes_at_2x) : '—'}</strong><p>Measured county storage projects beyond current safe operating capacity.</p></div></div><div className="progress-track"><span style={{width: `${capacityPercent}%`}}/></div><div className="progress-labels"><span>Current free space</span><span>Required headroom</span></div><div className="recommendation"><strong>Next action</strong><p>Add 40–60 GB of usable space and optimize canonical upserts before the next scale test.</p></div></section>
    </div>
  </main>;
}
