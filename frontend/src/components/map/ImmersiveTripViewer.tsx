import { useState, useMemo, useEffect, useCallback, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import { motion, AnimatePresence } from 'framer-motion';
import 'leaflet/dist/leaflet.css';
import type { MapItinerary, MapItineraryDay, MapItineraryItem } from './TripMapVisualization';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const DAY_COLORS = [
  '#8b5cf6', '#06b6d4', '#f59e0b', '#10b981', '#ef4444',
  '#3b82f6', '#ec4899', '#84cc16', '#f97316', '#6366f1',
];

const ITEM_TYPE_ICONS: Record<string, string> = {
  flight: '\u2708\uFE0F', hotel: '\uD83C\uDFE8', restaurant: '\uD83C\uDF7D\uFE0F',
  attraction: '\uD83C\uDFDB\uFE0F', activity: '\uD83C\uDFC4',
  transport: '\uD83D\uDE95', note: '\uD83D\uDCDD',
};

const ITEM_TYPE_VERBS: Record<string, string> = {
  flight: 'Fly to', hotel: 'Check into', restaurant: 'Dine at',
  attraction: 'Explore', activity: 'Experience', transport: 'Travel via',
};

const TILE_LAYERS: Record<string, { url: string; attribution: string; name: string }> = {
  streets: {
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; OpenStreetMap',
    name: 'Streets',
  },
  satellite: {
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: '&copy; Esri',
    name: 'Satellite',
  },
  topo: {
    url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
    attribution: '&copy; OpenTopoMap',
    name: 'Terrain',
  },
  dark: {
    url: 'https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png',
    attribution: '&copy; Stadia Maps',
    name: 'Dark',
  },
};

// Time-of-day atmosphere presets
const TIME_OF_DAY_PRESETS: Record<string, { gradient: string; opacity: number; label: string }> = {
  dawn: { gradient: 'linear-gradient(to bottom, rgba(255,140,66,0.25), rgba(255,200,120,0.1), transparent)', opacity: 0.3, label: 'Dawn' },
  morning: { gradient: 'linear-gradient(to bottom, rgba(135,206,250,0.08), transparent)', opacity: 0.08, label: 'Morning' },
  noon: { gradient: 'linear-gradient(to bottom, rgba(255,255,200,0.05), transparent)', opacity: 0.05, label: 'Noon' },
  afternoon: { gradient: 'linear-gradient(to bottom, rgba(255,220,100,0.12), transparent)', opacity: 0.12, label: 'Afternoon' },
  sunset: { gradient: 'linear-gradient(to bottom, rgba(255,100,50,0.3), rgba(255,160,80,0.15), transparent)', opacity: 0.3, label: 'Sunset' },
  night: { gradient: 'linear-gradient(to bottom, rgba(10,10,40,0.4), rgba(20,20,60,0.25), transparent)', opacity: 0.4, label: 'Night' },
};

// ---------------------------------------------------------------------------
// Marker icon
// ---------------------------------------------------------------------------

function createImmersiveMarker(dayNumber: number, color: string, itemType: string, isActive: boolean): L.DivIcon {
  const emoji = ITEM_TYPE_ICONS[itemType] || '\uD83D\uDCCD';
  const size = isActive ? 48 : 36;
  const glow = isActive ? `box-shadow: 0 0 20px ${color}80, 0 4px 12px rgba(0,0,0,0.3);` : 'box-shadow: 0 2px 8px rgba(0,0,0,0.3);';
  return L.divIcon({
    className: 'immersive-map-marker',
    html: `
      <div style="position:relative;width:${size}px;height:${size}px;transition:all 0.3s ease;">
        <div style="width:${size}px;height:${size}px;background:${color};border:3px solid white;border-radius:50%;${glow}display:flex;align-items:center;justify-content:center;font-size:${isActive ? 22 : 16}px;line-height:1;">${emoji}</div>
        <div style="position:absolute;top:-8px;right:-8px;width:20px;height:20px;background:${color};border:2px solid white;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;color:white;box-shadow:0 1px 4px rgba(0,0,0,0.3);">${dayNumber}</div>
      </div>
    `,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
  });
}

// ---------------------------------------------------------------------------
// Map controller (smooth fly-to)
// ---------------------------------------------------------------------------

interface FlyControllerProps {
  target: { lat: number; lng: number; zoom?: number } | null;
  bounds: L.LatLngBoundsExpression | null;
}

function FlyController({ target, bounds }: FlyControllerProps) {
  const map = useMap();

  useEffect(() => {
    if (target) {
      map.flyTo([target.lat, target.lng], target.zoom ?? 15, { duration: 1.5, easeLinearity: 0.25 });
    } else if (bounds) {
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 14 });
    }
  }, [map, target, bounds]);

  return null;
}

// ---------------------------------------------------------------------------
// Geo item type
// ---------------------------------------------------------------------------

interface GeoItem {
  item: MapItineraryItem;
  day: MapItineraryDay;
  dayNumber: number;
  color: string;
  lat: number;
  lng: number;
  globalIndex: number;
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

interface ImmersiveTripViewerProps {
  itinerary: MapItinerary;
  onGeocode?: (itineraryId: string) => Promise<void>;
  isGeocoding?: boolean;
}

export default function ImmersiveTripViewer({ itinerary, onGeocode, isGeocoding }: ImmersiveTripViewerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const [selectedDay, setSelectedDay] = useState<number | null>(null);
  const [tileLayer, setTileLayer] = useState<keyof typeof TILE_LAYERS>('streets');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [is3DMode, setIs3DMode] = useState(false);
  const [timeOfDay, setTimeOfDay] = useState<keyof typeof TIME_OF_DAY_PRESETS>('morning');
  const [show360Panel, setShow360Panel] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const playTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Collect all geo items
  const geoItems = useMemo<GeoItem[]>(() => {
    const items: GeoItem[] = [];
    let idx = 0;
    for (const day of itinerary.days) {
      const color = DAY_COLORS[(day.day_number - 1) % DAY_COLORS.length];
      for (const item of day.items) {
        if (item.latitude != null && item.longitude != null) {
          items.push({
            item, day, dayNumber: day.day_number, color,
            lat: Number(item.latitude), lng: Number(item.longitude),
            globalIndex: idx++,
          });
        }
      }
    }
    return items;
  }, [itinerary]);

  // Filter by day
  const visibleItems = useMemo(
    () => selectedDay ? geoItems.filter(g => g.dayNumber === selectedDay) : geoItems,
    [geoItems, selectedDay],
  );

  // Route polylines
  const routeLines = useMemo(() => {
    const lines: Array<{ positions: [number, number][]; color: string }> = [];
    const days = selectedDay ? itinerary.days.filter(d => d.day_number === selectedDay) : itinerary.days;
    for (const day of days) {
      const color = DAY_COLORS[(day.day_number - 1) % DAY_COLORS.length];
      const coords: [number, number][] = [];
      for (const item of day.items) {
        if (item.latitude != null && item.longitude != null) {
          coords.push([Number(item.latitude), Number(item.longitude)]);
        }
      }
      if (coords.length >= 2) lines.push({ positions: coords, color });
    }
    return lines;
  }, [itinerary, selectedDay]);

  // Bounds
  const bounds = useMemo<L.LatLngBoundsExpression | null>(() => {
    if (visibleItems.length === 0) return null;
    const lats = visibleItems.map(g => g.lat);
    const lngs = visibleItems.map(g => g.lng);
    return [[Math.min(...lats), Math.min(...lngs)], [Math.max(...lats), Math.max(...lngs)]];
  }, [visibleItems]);

  // Fly target
  const flyTarget = useMemo(() => {
    if (activeIndex == null) return null;
    const g = visibleItems[activeIndex];
    return g ? { lat: g.lat, lng: g.lng, zoom: 16 } : null;
  }, [activeIndex, visibleItems]);

  // Active item
  const activeItem = activeIndex != null ? visibleItems[activeIndex] : null;

  // Days with coordinates
  const daysWithCoords = useMemo(
    () => [...new Set(geoItems.map(g => g.dayNumber))].sort((a, b) => a - b),
    [geoItems],
  );

  // Missing coords count
  const missingCoords = useMemo(() => {
    let count = 0;
    for (const day of itinerary.days) {
      for (const item of day.items) {
        if ((item.latitude == null || item.longitude == null) && (item.location_name || item.title)) count++;
      }
    }
    return count;
  }, [itinerary]);

  // Fly-through playback
  const playFlyThrough = useCallback(() => {
    setIsPlaying(true);
    setActiveIndex(0);
  }, []);

  const stopFlyThrough = useCallback(() => {
    setIsPlaying(false);
    if (playTimerRef.current) clearTimeout(playTimerRef.current);
  }, []);

  useEffect(() => {
    if (!isPlaying || activeIndex == null) return;
    if (activeIndex >= visibleItems.length - 1) {
      playTimerRef.current = setTimeout(() => {
        setIsPlaying(false);
        setActiveIndex(null);
      }, 3000);
      return;
    }
    playTimerRef.current = setTimeout(() => {
      setActiveIndex(prev => (prev != null ? prev + 1 : 0));
    }, 3500);
    return () => { if (playTimerRef.current) clearTimeout(playTimerRef.current); };
  }, [isPlaying, activeIndex, visibleItems.length]);

  // Fullscreen toggle
  const toggleFullscreen = useCallback(() => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().then(() => setIsFullscreen(true)).catch(() => {});
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(() => {});
    }
  }, []);

  useEffect(() => {
    const handler = () => setIsFullscreen(!!document.fullscreenElement);
    document.addEventListener('fullscreenchange', handler);
    return () => document.removeEventListener('fullscreenchange', handler);
  }, []);

  // Generate narrative text for an item
  const getNarrative = (g: GeoItem): string => {
    const verb = ITEM_TYPE_VERBS[g.item.item_type] || 'Visit';
    const name = g.item.location_name || g.item.title;
    const time = g.item.start_time ? ` at ${g.item.start_time}` : '';
    const cost = g.item.estimated_cost ? ` ($${Number(g.item.estimated_cost).toFixed(0)})` : '';
    return `${verb} ${name}${time}${cost}`;
  };

  // Empty state
  if (geoItems.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8 text-center">
        <p className="text-5xl mb-4">{'\uD83D\uDDFA\uFE0F'}</p>
        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">No Map Data Available</h3>
        <p className="text-gray-500 dark:text-gray-400 max-w-md mx-auto mb-4">
          This itinerary doesn't have location coordinates yet.
          {missingCoords > 0 && ` ${missingCoords} item${missingCoords !== 1 ? 's' : ''} can be geocoded.`}
        </p>
        {missingCoords > 0 && onGeocode && (
          <button
            onClick={() => onGeocode(itinerary.id)}
            disabled={isGeocoding}
            className="px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-medium text-sm transition-colors disabled:opacity-50"
          >
            {isGeocoding ? 'Geocoding...' : `Geocode ${missingCoords} Location${missingCoords !== 1 ? 's' : ''}`}
          </button>
        )}
      </div>
    );
  }

  return (
    <div ref={containerRef} className={`relative ${isFullscreen ? 'bg-gray-900' : ''}`}>
      {/* Top control bar */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-3 mb-3">
        <div className="flex flex-wrap items-center gap-2">
          {/* Fly-through controls */}
          <div className="flex items-center gap-2">
            {!isPlaying ? (
              <button
                onClick={playFlyThrough}
                className="px-4 py-2 rounded-lg bg-gradient-to-r from-violet-600 to-indigo-600 text-white text-sm font-semibold hover:from-violet-700 hover:to-indigo-700 transition-all flex items-center gap-2 shadow-md"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" /></svg>
                Fly Through
              </button>
            ) : (
              <button
                onClick={stopFlyThrough}
                className="px-4 py-2 rounded-lg bg-red-500 text-white text-sm font-semibold hover:bg-red-600 transition-all flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><rect x="5" y="4" width="10" height="12" rx="1" /></svg>
                Stop
              </button>
            )}

            {/* Step controls */}
            <button
              onClick={() => setActiveIndex(prev => Math.max(0, (prev ?? 0) - 1))}
              disabled={activeIndex === 0 || activeIndex == null}
              className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-30 transition-colors"
              title="Previous stop"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" /></svg>
            </button>
            <button
              onClick={() => setActiveIndex(prev => Math.min(visibleItems.length - 1, (prev ?? -1) + 1))}
              disabled={activeIndex === visibleItems.length - 1}
              className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-30 transition-colors"
              title="Next stop"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" /></svg>
            </button>
            <button
              onClick={() => { setActiveIndex(null); setSelectedDay(null); }}
              className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              title="Reset view"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
            </button>
          </div>

          {/* Day filter chips */}
          <div className="flex items-center gap-1.5 ml-2">
            <button
              onClick={() => { setSelectedDay(null); setActiveIndex(null); }}
              className={`px-2.5 py-1 rounded-full text-xs font-semibold transition-all ${
                selectedDay === null
                  ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900'
                  : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'
              }`}
            >
              All
            </button>
            {daysWithCoords.map(d => {
              const color = DAY_COLORS[(d - 1) % DAY_COLORS.length];
              return (
                <button
                  key={d}
                  onClick={() => { setSelectedDay(selectedDay === d ? null : d); setActiveIndex(null); }}
                  className="px-2.5 py-1 rounded-full text-xs font-semibold transition-all border-2"
                  style={{
                    borderColor: color,
                    backgroundColor: selectedDay === d ? color : 'transparent',
                    color: selectedDay === d ? 'white' : color,
                  }}
                >
                  D{d}
                </button>
              );
            })}
          </div>

          {/* Right controls */}
          <div className="ml-auto flex items-center gap-2">
            {/* 3D Mode Toggle */}
            <button
              onClick={() => setIs3DMode(!is3DMode)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                is3DMode
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
              }`}
              title="Toggle 3D perspective"
            >
              3D
            </button>

            {/* Time of Day Selector */}
            <select
              value={timeOfDay}
              onChange={e => setTimeOfDay(e.target.value as keyof typeof TIME_OF_DAY_PRESETS)}
              className="text-xs rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-2 py-1.5"
              title="Time-of-day lighting"
            >
              {Object.entries(TIME_OF_DAY_PRESETS).map(([key, val]) => (
                <option key={key} value={key}>{val.label}</option>
              ))}
            </select>

            {/* 360° Street View Toggle */}
            <button
              onClick={() => setShow360Panel(!show360Panel)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                show360Panel
                  ? 'bg-teal-600 text-white shadow-md'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
              }`}
              title="Toggle 360° Street View panel"
            >
              360°
            </button>

            {/* Map style selector */}
            <select
              value={tileLayer}
              onChange={e => setTileLayer(e.target.value as keyof typeof TILE_LAYERS)}
              className="text-xs rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-2 py-1.5"
            >
              {Object.entries(TILE_LAYERS).map(([key, val]) => (
                <option key={key} value={key}>{val.name}</option>
              ))}
            </select>

            <button
              onClick={() => setShowSidebar(!showSidebar)}
              className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              title="Toggle sidebar"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h7" /></svg>
            </button>

            <button
              onClick={toggleFullscreen}
              className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
            >
              {isFullscreen ? (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 9V4.5M9 9H4.5M9 9L3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5l5.25 5.25" /></svg>
              ) : (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" /></svg>
              )}
            </button>
          </div>
        </div>

        {/* Progress bar for fly-through */}
        {isPlaying && activeIndex != null && (
          <div className="mt-2">
            <div className="h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-violet-500 to-indigo-500 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${((activeIndex + 1) / visibleItems.length) * 100}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 text-center">
              Stop {activeIndex + 1} of {visibleItems.length}
            </p>
          </div>
        )}
      </div>

      {/* Main map area with sidebar */}
      <div className={`flex gap-3 ${isFullscreen ? 'h-screen pt-0' : ''}`}>
        {/* Sidebar: day-by-day narrative */}
        <AnimatePresence>
          {showSidebar && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 320, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="flex-shrink-0 overflow-hidden"
            >
              <div className="w-80 bg-white dark:bg-gray-800 rounded-2xl shadow-lg overflow-y-auto max-h-[520px] lg:max-h-[600px]">
                <div className="p-4 border-b border-gray-100 dark:border-gray-700 sticky top-0 bg-white dark:bg-gray-800 z-10">
                  <h3 className="font-bold text-gray-900 dark:text-white text-sm">
                    {itinerary.title}
                  </h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                    {itinerary.destination} &middot; {itinerary.start_date} to {itinerary.end_date}
                  </p>
                </div>

                <div className="p-3 space-y-1">
                  {visibleItems.map((g, idx) => {
                    const isActive = activeIndex === idx;
                    return (
                      <button
                        key={`${g.dayNumber}-${g.item.id}`}
                        onClick={() => setActiveIndex(isActive ? null : idx)}
                        className={`w-full text-left rounded-xl p-3 transition-all border-l-4 ${
                          isActive
                            ? 'bg-gradient-to-r from-gray-50 to-white dark:from-gray-700 dark:to-gray-750 shadow-md'
                            : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
                        }`}
                        style={{ borderLeftColor: isActive ? g.color : 'transparent' }}
                      >
                        <div className="flex items-start gap-2">
                          <span className="text-lg flex-shrink-0 mt-0.5">
                            {ITEM_TYPE_ICONS[g.item.item_type] || '\uD83D\uDCCD'}
                          </span>
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-1.5 mb-0.5">
                              <span
                                className="text-[10px] px-1.5 py-0.5 rounded-full text-white font-bold flex-shrink-0"
                                style={{ backgroundColor: g.color }}
                              >
                                Day {g.dayNumber}
                              </span>
                              {g.item.start_time && (
                                <span className="text-[10px] text-gray-400">{g.item.start_time}</span>
                              )}
                            </div>
                            <p className={`text-xs font-medium truncate ${isActive ? 'text-gray-900 dark:text-white' : 'text-gray-700 dark:text-gray-300'}`}>
                              {g.item.title}
                            </p>
                            {isActive && (
                              <motion.p
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                className="text-[11px] text-gray-500 dark:text-gray-400 mt-1 leading-relaxed"
                              >
                                {getNarrative(g)}
                                {g.item.notes && <span className="block mt-1 italic">{g.item.notes}</span>}
                              </motion.p>
                            )}
                          </div>
                          {g.item.estimated_cost != null && Number(g.item.estimated_cost) > 0 && (
                            <span className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 flex-shrink-0">
                              ${Number(g.item.estimated_cost).toFixed(0)}
                            </span>
                          )}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Map */}
        <div
          className={`flex-1 bg-white dark:bg-gray-800 rounded-2xl shadow-lg overflow-hidden ${isFullscreen ? 'h-full' : 'h-[520px] lg:h-[600px]'}`}
          style={is3DMode ? {
            perspective: '1200px',
            perspectiveOrigin: '50% 50%',
          } : undefined}
        >
          <div
            className="h-full w-full relative"
            style={is3DMode ? {
              transform: 'rotateX(45deg) scale(1.15)',
              transformOrigin: '50% 80%',
              transition: 'transform 0.6s ease-in-out',
            } : { transition: 'transform 0.6s ease-in-out' }}
          >
          {/* Time-of-day atmosphere overlay */}
          <div
            className="absolute inset-0 z-[400] pointer-events-none"
            style={{
              background: TIME_OF_DAY_PRESETS[timeOfDay].gradient,
              opacity: TIME_OF_DAY_PRESETS[timeOfDay].opacity,
              transition: 'all 0.8s ease',
            }}
          />
          <MapContainer
            center={[visibleItems[0]?.lat ?? 0, visibleItems[0]?.lng ?? 0]}
            zoom={12}
            className="h-full w-full z-0"
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              attribution={TILE_LAYERS[tileLayer].attribution}
              url={TILE_LAYERS[tileLayer].url}
            />
            <FlyController target={flyTarget} bounds={activeIndex == null ? bounds : null} />

            {/* Route polylines */}
            {routeLines.map((line, idx) => (
              <Polyline
                key={`route-${idx}`}
                positions={line.positions}
                pathOptions={{ color: line.color, weight: 4, opacity: 0.7, dashArray: '8, 8' }}
              />
            ))}

            {/* Markers */}
            {visibleItems.map((g, idx) => (
              <Marker
                key={`${g.dayNumber}-${g.item.id}`}
                position={[g.lat, g.lng]}
                icon={createImmersiveMarker(g.dayNumber, g.color, g.item.item_type, activeIndex === idx)}
                eventHandlers={{ click: () => setActiveIndex(activeIndex === idx ? null : idx) }}
              >
                <Popup maxWidth={300}>
                  <div className="p-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs px-2 py-0.5 rounded-full text-white font-bold" style={{ backgroundColor: g.color }}>
                        Day {g.dayNumber}
                      </span>
                      <span className="text-xs text-gray-500">{g.item.item_type}</span>
                    </div>
                    <h4 className="font-bold text-gray-900 text-sm mb-1">{g.item.title}</h4>
                    {g.item.location_name && <p className="text-xs text-gray-500 mb-1">{g.item.location_name}</p>}
                    <div className="flex items-center gap-3 text-xs text-gray-500 mb-2">
                      {g.item.start_time && <span>{g.item.start_time}</span>}
                      {g.item.estimated_cost != null && Number(g.item.estimated_cost) > 0 && (
                        <span className="font-medium text-emerald-600">${Number(g.item.estimated_cost).toFixed(0)}</span>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-1.5 pt-2 border-t border-gray-100">
                      <a
                        href={`https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${g.lat},${g.lng}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs px-2 py-1 rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 font-medium"
                      >
                        Street View
                      </a>
                      <a
                        href={`https://www.google.com/maps/search/?api=1&query=${g.lat},${g.lng}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs px-2 py-1 rounded-lg bg-teal-50 text-teal-700 hover:bg-teal-100 font-medium"
                      >
                        Google Maps
                      </a>
                    </div>
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>
          </div>
        </div>

        {/* 360° Street View Panel */}
        <AnimatePresence>
          {show360Panel && activeItem && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 400, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="flex-shrink-0 overflow-hidden"
            >
              <div className="w-[400px] bg-white dark:bg-gray-800 rounded-2xl shadow-lg overflow-hidden h-full flex flex-col">
                <div className="p-3 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
                  <div>
                    <h4 className="font-bold text-sm text-gray-900 dark:text-white">360° Street View</h4>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{activeItem.item.title}</p>
                  </div>
                  <a
                    href={`https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${activeItem.lat},${activeItem.lng}&heading=0&pitch=0&fov=90`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs px-2 py-1 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded-lg hover:bg-indigo-200 dark:hover:bg-indigo-800/40"
                  >
                    Open Full
                  </a>
                </div>
                <div className="flex-1 min-h-[300px]">
                  <iframe
                    src={`https://www.google.com/maps/embed?pb=!4v0!6m8!1m7!1s!2m2!1d${activeItem.lat}!2d${activeItem.lng}!3f0!4f0!5f0.7820865974627469&output=svembed`}
                    width="100%"
                    height="100%"
                    style={{ border: 0, minHeight: '300px' }}
                    allowFullScreen
                    loading="lazy"
                    referrerPolicy="no-referrer-when-downgrade"
                    title="360° Street View"
                  />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        {show360Panel && !activeItem && (
          <div className="w-[400px] flex-shrink-0 bg-white dark:bg-gray-800 rounded-2xl shadow-lg flex items-center justify-center">
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center px-6">
              Click a marker on the map to view its 360° Street View
            </p>
          </div>
        )}
      </div>

      {/* Active stop narrative overlay (during fly-through) */}
      <AnimatePresence>
        {isPlaying && activeItem && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="absolute bottom-4 left-1/2 -translate-x-1/2 z-[1000] pointer-events-none"
          >
            <div className="bg-white/95 dark:bg-gray-800/95 backdrop-blur-md rounded-2xl shadow-2xl px-6 py-4 max-w-lg border border-gray-200/50 dark:border-gray-700/50">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-2xl">{ITEM_TYPE_ICONS[activeItem.item.item_type] || '\uD83D\uDCCD'}</span>
                <div>
                  <span
                    className="text-xs px-2 py-0.5 rounded-full text-white font-bold"
                    style={{ backgroundColor: activeItem.color }}
                  >
                    Day {activeItem.dayNumber}
                  </span>
                  {activeItem.item.start_time && (
                    <span className="text-xs text-gray-500 dark:text-gray-400 ml-2">{activeItem.item.start_time}</span>
                  )}
                </div>
              </div>
              <h3 className="font-bold text-gray-900 dark:text-white text-lg mb-1">
                {activeItem.item.title}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                {getNarrative(activeItem)}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
