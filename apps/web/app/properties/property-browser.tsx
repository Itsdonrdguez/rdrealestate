'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import { apiFetch } from '@/lib/api';

type Property = { id: string; account_id: string | null; normalized_address: string | null; city: string | null; postal_code: string | null; county: string | null; property_type: string | null; year_built: number | null; square_feet: number | null; assessment_value: string | null; assessment_date: number | null; sale_value: string | null; sale_date: string | null };
type Results = { items: Property[]; total: number; page: number; page_size: number; pages: number };
type Facets = { postal_codes: {value: string; count: number}[]; property_types: {value: string; count: number}[] };

const money = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });

export default function PropertyBrowser() {
  const [query, setQuery] = useState('');
  const [submittedQuery, setSubmittedQuery] = useState('');
  const [zip, setZip] = useState('');
  const [type, setType] = useState('');
  const [minValue, setMinValue] = useState('');
  const [maxValue, setMaxValue] = useState('');
  const [sort, setSort] = useState('address');
  const [page, setPage] = useState(1);
  const [results, setResults] = useState<Results | null>(null);
  const [facets, setFacets] = useState<Facets | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const params = useMemo(() => {
    const value = new URLSearchParams({ county: 'Charles', page: String(page), page_size: '25', sort, direction: sort === 'address' ? 'asc' : 'desc' });
    if (submittedQuery) value.set('query', submittedQuery);
    if (zip) value.set('postal_code', zip);
    if (type) value.set('property_type', type);
    if (minValue) value.set('min_assessed_value', minValue);
    if (maxValue) value.set('max_assessed_value', maxValue);
    return value;
  }, [submittedQuery, zip, type, minValue, maxValue, sort, page]);

  useEffect(() => { apiFetch<Facets>('/api/properties/facets?county=Charles').then(setFacets).catch(() => setError('Could not load filter options.')); }, []);
  useEffect(() => {
    const controller = new AbortController(); setLoading(true); setError('');
    apiFetch<Results>(`/api/properties?${params}`, controller.signal).then(setResults).catch((reason) => { if (reason.name !== 'AbortError') setError('The property API is unavailable. Start the local stack and try again.'); }).finally(() => setLoading(false));
    return () => controller.abort();
  }, [params]);

  function submit(event: FormEvent) { event.preventDefault(); setPage(1); setSubmittedQuery(query); }
  function reset() { setQuery(''); setSubmittedQuery(''); setZip(''); setType(''); setMinValue(''); setMaxValue(''); setSort('address'); setPage(1); }

  return (
    <main className="page property-page">
      <div className="page-heading compact"><div><span className="eyebrow">Public property backbone</span><h1>Charles County properties</h1></div><p>Search verified assessment, sale, and parcel facts. Owner intelligence is intentionally excluded until authorized data is available.</p></div>
      <div className="browser-layout">
        <aside className="filter-panel">
          <div className="panel-title"><div><span>Filters</span><small>Refine public records</small></div><button onClick={reset}>Reset</button></div>
          <form onSubmit={submit}>
            <label>Address search<input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Street, city, or ZIP" /></label>
            <label>County<select disabled><option>Charles</option></select></label>
            <label>ZIP code<select value={zip} onChange={(e) => {setZip(e.target.value); setPage(1)}}><option value="">All ZIP codes</option>{facets?.postal_codes.map((item) => <option key={item.value} value={item.value}>{item.value} ({item.count.toLocaleString()})</option>)}</select></label>
            <label>Property type<select value={type} onChange={(e) => {setType(e.target.value); setPage(1)}}><option value="">All property types</option>{facets?.property_types.map((item) => <option key={item.value} value={item.value}>{item.value} ({item.count.toLocaleString()})</option>)}</select></label>
            <fieldset><legend>Assessed value</legend><div className="range-fields"><input aria-label="Minimum assessed value" type="number" value={minValue} onChange={(e) => setMinValue(e.target.value)} placeholder="Min"/><input aria-label="Maximum assessed value" type="number" value={maxValue} onChange={(e) => setMaxValue(e.target.value)} placeholder="Max"/></div></fieldset>
            <button className="button button-primary filter-submit">Apply filters</button>
          </form>
          <div className="locked-filter"><span>Owner filters</span><strong>Available with authorized owner data</strong></div>
        </aside>
        <section className="results-panel">
          <div className="results-toolbar"><div><span className="result-count">{loading ? 'Loading…' : `${(results?.total ?? 0).toLocaleString()} properties`}</span><small>Maryland SDAT / MDP public source</small></div><label>Sort by <select value={sort} onChange={(e) => {setSort(e.target.value); setPage(1)}}><option value="address">Address</option><option value="assessed_value">Assessed value</option><option value="sale_date">Last sale date</option><option value="year_built">Year built</option></select></label></div>
          {error && <div className="error-banner">{error}</div>}
          <div className="table-wrap"><table><thead><tr><th>Property</th><th>Type</th><th>Year</th><th>Assessment</th><th>Last sale</th><th>Account ID</th></tr></thead><tbody>
            {!loading && results?.items.map((item) => <tr key={item.id}><td><strong>{item.normalized_address ?? 'Address unavailable'}</strong><small>{item.city}, MD {item.postal_code}</small></td><td>{item.property_type ?? '—'}<small>{item.square_feet ? `${item.square_feet.toLocaleString()} sq ft` : ''}</small></td><td>{item.year_built ?? '—'}</td><td><strong>{item.assessment_value ? money.format(Number(item.assessment_value)) : '—'}</strong><small>{item.assessment_date ? `${item.assessment_date} assessment` : ''}</small></td><td>{item.sale_value ? money.format(Number(item.sale_value)) : '—'}<small>{item.sale_date ? new Date(item.sale_date).toLocaleDateString() : ''}</small></td><td><code>{item.account_id ?? '—'}</code></td></tr>)}
            {loading && Array.from({length: 8}).map((_, index) => <tr className="skeleton-row" key={index}><td colSpan={6}><span/></td></tr>)}
          </tbody></table></div>
          <div className="pagination"><span>Page {results?.page ?? 1} of {Math.max(results?.pages ?? 1, 1)}</span><div><button disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>← Previous</button><button disabled={!results || page >= results.pages} onClick={() => setPage((value) => value + 1)}>Next →</button></div></div>
        </section>
      </div>
    </main>
  );
}
