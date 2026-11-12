import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="page dashboard-home">
      <div className="page-heading">
        <div><span className="eyebrow">Maryland intelligence workspace</span><h1>See the market beneath the listings.</h1></div>
        <p>Explore the verified public property backbone now. Owner intelligence and opportunity scoring will activate when authorized owner-name data is connected.</p>
      </div>
      <section className="hero-panel">
        <div className="hero-copy">
          <span className="hero-kicker">The Maryland backbone is growing</span>
          <h2>391,382 properties.<br/>Clear, verified records.</h2>
          <p>Search assessments, sale history, property characteristics, and source identifiers from the completed Charles and Prince George&apos;s County pilots.</p>
          <div className="button-row">
            <Link href="/properties" className="button button-primary">Browse properties <span>→</span></Link>
            <Link href="/data-health" className="button button-secondary">View data health</Link>
          </div>
        </div>
        <div className="county-graphic" aria-hidden="true">
          <div className="map-grid" />
          <span className="map-pin pin-one"/><span className="map-pin pin-two"/><span className="map-pin pin-three"/><span className="map-pin pin-four"/>
          <div className="map-label"><strong>Charles County</strong><small>Public backbone loaded</small></div>
        </div>
      </section>
      <section className="stat-grid">
        <article><span>Properties loaded</span><strong>391,382</strong><small>Validated public records</small></article>
        <article><span>Duplicate rate</span><strong>0%</strong><small>Canonical source IDs</small></article>
        <article><span>Latest benchmark</span><strong>262.6 <i>rec/s</i></strong><small>Prince George&apos;s pilot</small></article>
        <article><span>Data scope</span><strong>Public</strong><small>Owner names pending</small></article>
      </section>
      <section className="roadmap-panel">
        <div><span className="eyebrow">Build sequence</span><h2>A useful system, layer by layer.</h2></div>
        <ol>
          <li className="done"><span>01</span><div><strong>Property backbone</strong><small>Search, assessments, sales, provenance</small></div></li>
          <li className="done"><span>02</span><div><strong>Query and map stack</strong><small>Search, profiles, and clustered map live</small></div></li>
          <li className="active"><span>03</span><div><strong>Owner intelligence</strong><small>Waiting on authorized source data</small></div></li>
          <li><span>04</span><div><strong>Opportunity engine</strong><small>Explainable signals after owner resolution</small></div></li>
        </ol>
      </section>
    </main>
  );
}
