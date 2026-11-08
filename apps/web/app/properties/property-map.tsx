'use client';

import Link from 'next/link';
import { GeoJSONSource, Map as MapLibreMap, MapMouseEvent, NavigationControl } from 'maplibre-gl';
import { useCallback, useEffect, useRef, useState } from 'react';
import { API_URL } from '@/lib/api';

type MapProperty = { id: string; address: string | null; city: string | null; postal_code: string | null; property_type: string | null; year_built: number | null; account_id: string | null; assessed_value: number | null };
type MapResponse = GeoJSON.FeatureCollection<GeoJSON.Point, MapProperty> & { count: number; limit: number; truncated: boolean };
type Props = { filters: string };
const empty: GeoJSON.FeatureCollection<GeoJSON.Point, MapProperty> = { type: 'FeatureCollection', features: [] };
const money = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });

export default function PropertyMap({ filters }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<MapLibreMap | null>(null);
  const loadViewportRef = useRef<() => void>(() => undefined);
  const [selected, setSelected] = useState<MapProperty | null>(null);
  const [status, setStatus] = useState({ count: 0, truncated: false, loading: true, error: '' });

  const loadViewport = useCallback(async () => {
    if (!map.current || !map.current.isStyleLoaded()) return;
    const bounds = map.current.getBounds();
    const params = new URLSearchParams(filters);
    params.set('west', String(bounds.getWest())); params.set('south', String(bounds.getSouth()));
    params.set('east', String(bounds.getEast())); params.set('north', String(bounds.getNorth())); params.set('limit', '1500');
    setStatus((current) => ({ ...current, loading: true, error: '' }));
    try {
      const response = await fetch(`${API_URL}/api/properties/map?${params}`, { cache: 'no-store' });
      if (!response.ok) throw new Error(String(response.status));
      const data = await response.json() as MapResponse;
      (map.current.getSource('properties') as GeoJSONSource | undefined)?.setData(data);
      setStatus({ count: data.count, truncated: data.truncated, loading: false, error: '' });
    } catch {
      (map.current.getSource('properties') as GeoJSONSource | undefined)?.setData(empty);
      setStatus({ count: 0, truncated: false, loading: false, error: 'Map records could not be loaded.' });
    }
  }, [filters]);
  loadViewportRef.current = loadViewport;

  useEffect(() => {
    if (!container.current || map.current) return;
    const instance = new MapLibreMap({
      container: container.current,
      center: [-77.01, 38.53], zoom: 9.3, minZoom: 7, maxZoom: 18,
      style: { version: 8, sources: { osm: { type: 'raster', tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize: 256, attribution: '&copy; OpenStreetMap contributors' } }, layers: [{ id: 'osm', type: 'raster', source: 'osm' }] },
    });
    map.current = instance;
    instance.addControl(new NavigationControl({ showCompass: false }), 'top-right');
    instance.on('load', () => {
      instance.addSource('properties', { type: 'geojson', data: empty, cluster: true, clusterMaxZoom: 14, clusterRadius: 48 });
      instance.addLayer({ id: 'clusters', type: 'circle', source: 'properties', filter: ['has', 'point_count'], paint: { 'circle-color': ['step', ['get', 'point_count'], '#65d493', 100, '#48b77b', 750, '#2b8556'], 'circle-radius': ['step', ['get', 'point_count'], 17, 100, 23, 750, 30], 'circle-stroke-width': 2, 'circle-stroke-color': '#102019' } });
      instance.addLayer({ id: 'cluster-count', type: 'symbol', source: 'properties', filter: ['has', 'point_count'], layout: { 'text-field': ['get', 'point_count_abbreviated'], 'text-size': 11 }, paint: { 'text-color': '#07150d' } });
      instance.addLayer({ id: 'property-points', type: 'circle', source: 'properties', filter: ['!', ['has', 'point_count']], paint: { 'circle-color': '#8aefb0', 'circle-radius': 5, 'circle-stroke-width': 2, 'circle-stroke-color': '#102019' } });
      loadViewportRef.current();
    });
    instance.on('moveend', () => loadViewportRef.current());
    instance.on('click', 'clusters', async (event: MapMouseEvent) => {
      const feature = instance.queryRenderedFeatures(event.point, { layers: ['clusters'] })[0];
      const clusterId = Number(feature?.properties?.cluster_id);
      const source = instance.getSource('properties') as GeoJSONSource;
      const zoom = await source.getClusterExpansionZoom(clusterId);
      const coordinates = (feature.geometry as GeoJSON.Point).coordinates as [number, number];
      instance.easeTo({ center: coordinates, zoom });
    });
    instance.on('click', 'property-points', (event: MapMouseEvent) => {
      const feature = instance.queryRenderedFeatures(event.point, { layers: ['property-points'] })[0];
      if (feature?.properties) setSelected(feature.properties as MapProperty);
    });
    ['clusters', 'property-points'].forEach((layer) => { instance.on('mouseenter', layer, () => { instance.getCanvas().style.cursor = 'pointer'; }); instance.on('mouseleave', layer, () => { instance.getCanvas().style.cursor = ''; }); });
    return () => { instance.remove(); map.current = null; };
  }, []);

  useEffect(() => {
    loadViewport();
  }, [filters, loadViewport]);

  return <div className="property-map-shell">
    <div ref={container} className="property-map" aria-label="Map of filtered Charles County properties" />
    <div className="map-result-status"><span className={status.loading ? 'map-loading-dot' : 'status-dot'} />{status.error || (status.loading ? 'Loading this viewport...' : `${status.count.toLocaleString()} mapped properties`)}{status.truncated && <strong>Zoom in to see all results</strong>}</div>
    {selected && <aside className="map-summary"><button aria-label="Close property summary" onClick={() => setSelected(null)}>x</button><span>{selected.property_type ?? 'Property'} · {selected.account_id}</span><h3>{selected.address ?? 'Address unavailable'}</h3><p>{selected.city}, MD {selected.postal_code}</p><dl><div><dt>Assessment</dt><dd>{selected.assessed_value ? money.format(selected.assessed_value) : 'Not available'}</dd></div><div><dt>Year built</dt><dd>{selected.year_built ?? 'Not available'}</dd></div></dl><Link href={`/properties/${selected.id}`}>Open property profile <b>→</b></Link></aside>}
  </div>;
}
