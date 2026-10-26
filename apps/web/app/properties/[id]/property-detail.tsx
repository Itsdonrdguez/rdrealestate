'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { apiFetch } from '@/lib/api';

type FactSource = { source: string; source_identifier: string; observed_at: string };
type PropertyDetailData = {
  id: string; state: string; county: string | null; property_type: string | null; year_built: number | null;
  bedrooms: number | null; bathrooms: number | null; square_feet: number | null; is_active: boolean;
  address: null | { raw_address: string | null; normalized_address: string | null; city: string | null; state: string | null; postal_code: string | null; latitude: number | null; longitude: number | null };
  identifiers: { source: string; source_identifier: string }[];
  assessments: (FactSource & { id: string; assessment_year: number | null; assessed_value: string | null; confidence: number | null })[];
  sales: (FactSource & { id: string; sale_date: string | null; sale_price: string | null; deed_type: string | null })[];
  provenance: FactSource & { source_record_id: string | null; created_at: string; updated_at: string };
};

const money = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });
const value = (input: string | number | null | undefined, suffix = '') => input === null || input === undefined || input === '' ? 'Not available' : `${input}${suffix}`;
const date = (input: string | null | undefined) => input ? new Date(input).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : 'Not available';

export default function PropertyDetail() {
  const { id } = useParams<{ id: string }>();
  const [property, setProperty] = useState<PropertyDetailData | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    apiFetch<PropertyDetailData>(`/api/properties/${id}`, controller.signal).then(setProperty).catch((reason) => {
      if (reason.name !== 'AbortError') setError('This property could not be loaded.');
    });
    return () => controller.abort();
  }, [id]);

  if (error) return <main className="page"><div className="empty-state"><span>Property unavailable</span><h1>We could not open this record.</h1><p>{error}</p><Link className="button button-secondary" href="/properties">Back to property search</Link></div></main>;
  if (!property) return <main className="page property-detail-page"><div className="detail-loading"><span/><span/><span/></div></main>;

  const assessment = property.assessments[0];
  const latestSale = property.sales[0];
  const accountId = property.identifiers[0]?.source_identifier ?? property.provenance.source_identifier;
  const address = property.address?.normalized_address ?? property.address?.raw_address ?? 'Address unavailable';
  return <main className="page property-detail-page">
    <div className="detail-breadcrumb"><Link href="/properties">Property search</Link><span>/</span><span>{accountId}</span></div>
    <header className="detail-header">
      <div><div className="detail-label-row"><span className="status-pill succeeded">Active public record</span><span>Account {accountId}</span></div><h1>{address}</h1><p>{property.county} County, {property.state} {property.address?.postal_code}</p></div>
      <div className="detail-actions"><Link href="/properties" className="button button-secondary">Back to search</Link></div>
    </header>
    <section className="detail-kpis">
      <article><small>Assessed value</small><strong>{assessment?.assessed_value ? money.format(Number(assessment.assessed_value)) : 'Not available'}</strong><span>{assessment?.assessment_year ? `${assessment.assessment_year} assessment` : 'No assessment on file'}</span></article>
      <article><small>Last recorded sale</small><strong>{latestSale?.sale_price ? money.format(Number(latestSale.sale_price)) : 'Not available'}</strong><span>{date(latestSale?.sale_date)}</span></article>
      <article><small>Property type</small><strong>{value(property.property_type)}</strong><span>{property.square_feet ? `${property.square_feet.toLocaleString()} square feet` : 'Area unavailable'}</span></article>
      <article><small>Year built</small><strong>{value(property.year_built)}</strong><span>{property.year_built ? `${new Date().getFullYear() - property.year_built} years old` : 'Age unavailable'}</span></article>
    </section>
    <div className="detail-layout">
      <div className="detail-main">
        <section className="detail-section"><div className="section-heading"><div><span>Property record</span><h2>Characteristics</h2></div><small>Public Maryland data</small></div><dl className="attribute-grid"><div><dt>Property type</dt><dd>{value(property.property_type)}</dd></div><div><dt>Year built</dt><dd>{value(property.year_built)}</dd></div><div><dt>Living area</dt><dd>{property.square_feet ? property.square_feet.toLocaleString() + ' sq ft' : 'Not available'}</dd></div><div><dt>Bedrooms</dt><dd>{value(property.bedrooms)}</dd></div><div><dt>Bathrooms</dt><dd>{value(property.bathrooms)}</dd></div><div><dt>County</dt><dd>{value(property.county)}</dd></div></dl></section>
        <section className="detail-section"><div className="section-heading"><div><span>Value history</span><h2>Assessments</h2></div><small>{property.assessments.length} record{property.assessments.length === 1 ? '' : 's'}</small></div>{property.assessments.length ? <div className="history-table"><div className="history-head"><span>Year</span><span>Assessed value</span><span>Observed</span><span>Source</span></div>{property.assessments.map((item) => <div className="history-row" key={item.id}><strong>{value(item.assessment_year)}</strong><span>{item.assessed_value ? money.format(Number(item.assessed_value)) : 'Not available'}</span><span>{date(item.observed_at)}</span><code>{item.source}</code></div>)}</div> : <p className="no-data">No assessment history is available.</p>}</section>
        <section className="detail-section"><div className="section-heading"><div><span>Transaction history</span><h2>Recorded sales</h2></div><small>{property.sales.length} record{property.sales.length === 1 ? '' : 's'}</small></div>{property.sales.length ? <div className="history-table"><div className="history-head"><span>Sale date</span><span>Sale price</span><span>Deed type</span><span>Source</span></div>{property.sales.map((item) => <div className="history-row" key={item.id}><strong>{date(item.sale_date)}</strong><span>{item.sale_price ? money.format(Number(item.sale_price)) : 'Not available'}</span><span>{value(item.deed_type)}</span><code>{item.source}</code></div>)}</div> : <p className="no-data">No qualifying sale history is available for this property.</p>}</section>
      </div>
      <aside className="detail-aside">
        <section className="location-card"><div className="location-grid"/><span className="location-pin"/><div><small>Recorded coordinates</small><strong>{property.address?.latitude && property.address?.longitude ? `${property.address.latitude.toFixed(5)}, ${property.address.longitude.toFixed(5)}` : 'Not available'}</strong><p>A full interactive PostGIS map is planned for the next frontend phase.</p></div></section>
        <section className="aside-card"><div className="section-heading"><div><span>Source evidence</span><h2>Provenance</h2></div></div><dl className="provenance-list"><div><dt>Source</dt><dd>{property.provenance.source}</dd></div><div><dt>Source identifier</dt><dd><code>{property.provenance.source_identifier}</code></dd></div><div><dt>Observed</dt><dd>{date(property.provenance.observed_at)}</dd></div><div><dt>Raw source record</dt><dd><code>{property.provenance.source_record_id ?? 'Not available'}</code></dd></div><div><dt>Canonical property ID</dt><dd><code>{property.id}</code></dd></div></dl></section>
        <section className="owner-pending"><span>Owner intelligence</span><h3>Awaiting authorized data</h3><p>Ownership, mailing address, absentee status, and portfolio analysis will appear here after the licensed owner-name source is connected.</p></section>
      </aside>
    </div>
  </main>;
}
