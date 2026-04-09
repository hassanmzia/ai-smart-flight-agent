import { useState, useMemo, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface MapItineraryItem {
  id: string;
  title: string;
  item_type: string;
  order: number;
  start_time?: string;
  end_time?: string;
  location_name: string;
  location_address: string;
  latitude: number | null;
  longitude: number | null;
  estimated_cost?: number | null;
  notes?: string;
  is_booked?: boolean;
}

export interface MapItineraryDay {
  id: string;
  day_number: number;
  date: string;
  title?: string;
  items: MapItineraryItem[];
}

export interface MapItinerary {
  id: string;
  title: string;
  destination: string;
  start_date: string;
  end_date: string;
  status: string;
  days: MapItineraryDay[];
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const DAY_COLORS = [
  '#8b5cf6', // violet
  '#06b6d4', // cyan
  '#f59e0b', // amber
  '#10b981', // emerald
  '#ef4444', // red
  '#3b82f6', // blue
  '#ec4899', // pink
  '#84cc16', // lime
  '#f97316', // orange
  '#6366f1', // indigo
];

const ITEM_TYPE_ICONS: Record<string, string> = {
  flight: '\u2708\uFE0F',
  hotel: '\uD83C\uDFE8',
  restaurant: '\uD83C\uDF7D\uFE0F',
  attraction: '\uD83C\uDFDB\uFE0F',
  activity: '\uD83C\uDFC4',
  transport: '\uD83D\uDE95',
  note: '\uD83D\uDCDD',
};

// ---------------------------------------------------------------------------
// Custom marker icons
// ---------------------------------------------------------------------------

function createDayMarkerIcon(dayNumber: number, color: string, itemType: string): L.DivIcon {
  const emoji = ITEM_TYPE_ICONS[itemType] || '\uD83D\uDCCD';
  return L.divIcon({
    className: 'custom-map-marker',
    html: `
      <div style="
        position: relative;
        width: 36px;
        height: 36px;
      ">
        <div style="
          width: 36px;
          height: 36px;
          background: ${color};
          border: 3px solid white;
          border-radius: 50%;
          box-shadow: 0 2px 8px rgba(0,0,0,0.3);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 16px;
          line-height: 1;
        ">${emoji}</div>
        <div style="
          position: absolute;
          top: -8px;
          right: -8px;
          width: 20px;
          height: 20px;
          background: ${color};
          border: 2px solid white;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 10px;
          font-weight: 700;
          color: white;
          box-shadow: 0 1px 4px rgba(0,0,0,0.3);
        ">${dayNumber}</div>
      </div>
    `,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
    popupAnchor: [0, -20],
  });
}

// ---------------------------------------------------------------------------
// Map auto-fit helper
// ---------------------------------------------------------------------------

function FitBounds({ bounds }: { bounds: L.LatLngBoundsExpression | null }) {
  const map = useMap();
  useEffect(() => {
    if (bounds) {
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 14 });
    }
  }, [map, bounds]);
  return null;
}

// ---------------------------------------------------------------------------
// Street View URL helper
// ---------------------------------------------------------------------------

function getStreetViewUrl(lat: number, lng: number): string {
  return `https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${lat},${lng}`;
}

function getGoogleMapsUrl(lat: number, lng: number, name: string): string {
  return `https://www.google.com/maps/search/?api=1&query=${lat},${lng}&query_place_id=${encodeURIComponent(name)}`;
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

interface TripMapVisualizationProps {
  itinerary: MapItinerary;
  onGeocode?: (itineraryId: string) => Promise<void>;
  isGeocoding?: boolean;
}

export default function TripMapVisualization({ itinerary, onGeocode, isGeocoding }: TripMapVisualizationProps) {
  const [selectedDay, setSelectedDay] = useState<number | null>(null);
  const [showRoutes, setShowRoutes] = useState(true);

  // Collect all items with valid coordinates
  const geoItems = useMemo(() => {
    const items: Array<{
      item: MapItineraryItem;
      dayNumber: number;
      dayDate: string;
      color: string;
      lat: number;
      lng: number;
    }> = [];

    for (const day of itinerary.days) {
      const color = DAY_COLORS[(day.day_number - 1) % DAY_COLORS.length];
      for (const item of day.items) {
        if (item.latitude != null && item.longitude != null) {
          items.push({
            item,
            dayNumber: day.day_number,
            dayDate: day.date,
            color,
            lat: Number(item.latitude),
            lng: Number(item.longitude),
          });
        }
      }
    }
    return items;
  }, [itinerary]);

  // Filter by selected day
  const visibleItems = useMemo(
    () => (selectedDay ? geoItems.filter((g) => g.dayNumber === selectedDay) : geoItems),
    [geoItems, selectedDay],
  );

  // Build route polylines (per day)
  const routeLines = useMemo(() => {
    const lines: Array<{ positions: [number, number][]; color: string; dayNumber: number }> = [];
    const daysToShow = selectedDay
      ? itinerary.days.filter((d) => d.day_number === selectedDay)
      : itinerary.days;

    for (const day of daysToShow) {
      const color = DAY_COLORS[(day.day_number - 1) % DAY_COLORS.length];
      const coords: [number, number][] = [];
      for (const item of day.items) {
        if (item.latitude != null && item.longitude != null) {
          coords.push([Number(item.latitude), Number(item.longitude)]);
        }
      }
      if (coords.length >= 2) {
        lines.push({ positions: coords, color, dayNumber: day.day_number });
      }
    }
    return lines;
  }, [itinerary, selectedDay]);

  // Compute map bounds
  const bounds = useMemo<L.LatLngBoundsExpression | null>(() => {
    if (visibleItems.length === 0) return null;
    const lats = visibleItems.map((g) => g.lat);
    const lngs = visibleItems.map((g) => g.lng);
    return [
      [Math.min(...lats), Math.min(...lngs)],
      [Math.max(...lats), Math.max(...lngs)],
    ];
  }, [visibleItems]);

  // Days that have geo-items
  const daysWithCoords = useMemo(
    () => [...new Set(geoItems.map((g) => g.dayNumber))].sort((a, b) => a - b),
    [geoItems],
  );

  // Count items that could be geocoded (have a name but no coords)
  const missingCoords = useMemo(() => {
    let count = 0;
    for (const day of itinerary.days) {
      for (const item of day.items) {
        if ((item.latitude == null || item.longitude == null) && item.location_name) {
          count++;
        }
      }
    }
    return count;
  }, [itinerary]);

  if (geoItems.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8 text-center">
        <p className="text-5xl mb-4">{'\uD83D\uDDFA\uFE0F'}</p>
        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
          No Map Data Available
        </h3>
        <p className="text-gray-500 dark:text-gray-400 max-w-md mx-auto mb-4">
          This itinerary doesn't have location coordinates yet.
          {missingCoords > 0
            ? ` ${missingCoords} item${missingCoords !== 1 ? 's' : ''} can be geocoded from their location names.`
            : ' Coordinates are added automatically when you use the AI Trip Planner.'}
        </p>
        {missingCoords > 0 && onGeocode && (
          <button
            onClick={() => onGeocode(itinerary.id)}
            disabled={isGeocoding}
            className="px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-medium text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isGeocoding ? (
              <span className="flex items-center gap-2">
                <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                Geocoding...
              </span>
            ) : (
              `Geocode ${missingCoords} Location${missingCoords !== 1 ? 's' : ''}`
            )}
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-4">
        <div className="flex flex-wrap items-center gap-3">
          {/* Day filter chips */}
          <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Filter:</span>
          <button
            onClick={() => setSelectedDay(null)}
            className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all ${
              selectedDay === null
                ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900'
                : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            All Days
          </button>
          {daysWithCoords.map((d) => {
            const color = DAY_COLORS[(d - 1) % DAY_COLORS.length];
            const isActive = selectedDay === d;
            return (
              <button
                key={d}
                onClick={() => setSelectedDay(isActive ? null : d)}
                className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all border-2 ${
                  isActive
                    ? 'text-white'
                    : 'bg-white dark:bg-gray-700 hover:opacity-80'
                }`}
                style={{
                  borderColor: color,
                  backgroundColor: isActive ? color : undefined,
                  color: isActive ? 'white' : color,
                }}
              >
                Day {d}
              </button>
            );
          })}

          {/* Route toggle */}
          <div className="ml-auto flex items-center gap-2">
            <label className="text-xs text-gray-500 dark:text-gray-400 cursor-pointer select-none flex items-center gap-1.5">
              <input
                type="checkbox"
                checked={showRoutes}
                onChange={(e) => setShowRoutes(e.target.checked)}
                className="rounded border-gray-300 text-teal-600 focus:ring-teal-500"
              />
              Show routes
            </label>
          </div>
        </div>
      </div>

      {/* Map */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg overflow-hidden" style={{ height: 520 }}>
        <MapContainer
          center={[visibleItems[0]?.lat ?? 0, visibleItems[0]?.lng ?? 0]}
          zoom={12}
          className="h-full w-full z-0"
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <FitBounds bounds={bounds} />

          {/* Route polylines */}
          {showRoutes &&
            routeLines.map((line, idx) => (
              <Polyline
                key={`route-${idx}`}
                positions={line.positions}
                pathOptions={{
                  color: line.color,
                  weight: 4,
                  opacity: 0.7,
                  dashArray: '8, 8',
                }}
              />
            ))}

          {/* Markers */}
          {visibleItems.map((g) => (
            <Marker
              key={`${g.dayNumber}-${g.item.id}`}
              position={[g.lat, g.lng]}
              icon={createDayMarkerIcon(g.dayNumber, g.color, g.item.item_type)}
            >
              <Popup maxWidth={280} className="trip-map-popup">
                <div className="p-1">
                  {/* Header */}
                  <div className="flex items-center gap-2 mb-2">
                    <span
                      className="text-xs px-2 py-0.5 rounded-full text-white font-bold"
                      style={{ backgroundColor: g.color }}
                    >
                      Day {g.dayNumber}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 font-medium">
                      {g.item.item_type}
                    </span>
                  </div>

                  {/* Title */}
                  <h4 className="font-bold text-gray-900 text-sm mb-1">{g.item.title}</h4>

                  {/* Location */}
                  {g.item.location_name && (
                    <p className="text-xs text-gray-500 mb-1">{g.item.location_name}</p>
                  )}

                  {/* Time & Cost */}
                  <div className="flex items-center gap-3 text-xs text-gray-500 mb-2">
                    {g.item.start_time && <span>{g.item.start_time}</span>}
                    {g.item.estimated_cost != null && g.item.estimated_cost > 0 && (
                      <span className="font-medium text-emerald-600">
                        ${Number(g.item.estimated_cost).toFixed(0)}
                      </span>
                    )}
                    {g.item.is_booked && (
                      <span className="text-green-600 font-medium">Booked</span>
                    )}
                  </div>

                  {/* Action links */}
                  <div className="flex gap-2 pt-2 border-t border-gray-100">
                    <a
                      href={getStreetViewUrl(g.lat, g.lng)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs px-2.5 py-1 rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 font-medium transition-colors"
                    >
                      {'\uD83D\uDC41\uFE0F'} 3D Street View
                    </a>
                    <a
                      href={getGoogleMapsUrl(g.lat, g.lng, g.item.location_name || g.item.title)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs px-2.5 py-1 rounded-lg bg-teal-50 text-teal-700 hover:bg-teal-100 font-medium transition-colors"
                    >
                      {'\uD83D\uDDFA\uFE0F'} Google Maps
                    </a>
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>

      {/* Legend / Day summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {(selectedDay ? itinerary.days.filter((d) => d.day_number === selectedDay) : itinerary.days)
          .filter((day) => day.items.some((i) => i.latitude != null && i.longitude != null))
          .map((day) => {
            const color = DAY_COLORS[(day.day_number - 1) % DAY_COLORS.length];
            const geoCount = day.items.filter(
              (i) => i.latitude != null && i.longitude != null,
            ).length;
            return (
              <button
                key={day.day_number}
                onClick={() => setSelectedDay(selectedDay === day.day_number ? null : day.day_number)}
                className={`text-left rounded-xl p-4 transition-all border-2 ${
                  selectedDay === day.day_number
                    ? 'shadow-md'
                    : 'bg-white dark:bg-gray-800 shadow-sm hover:shadow-md'
                }`}
                style={{
                  borderColor: color,
                  backgroundColor: selectedDay === day.day_number ? `${color}10` : undefined,
                }}
              >
                <div className="flex items-center gap-2 mb-2">
                  <div
                    className="w-3 h-3 rounded-full flex-shrink-0"
                    style={{ backgroundColor: color }}
                  />
                  <span className="font-bold text-sm text-gray-900 dark:text-white">
                    Day {day.day_number}
                  </span>
                  <span className="text-xs text-gray-400 dark:text-gray-500">
                    {day.date}
                  </span>
                </div>
                <div className="space-y-1">
                  {day.items
                    .filter((i) => i.latitude != null && i.longitude != null)
                    .map((item, idx) => (
                      <div key={idx} className="flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-400">
                        <span>{ITEM_TYPE_ICONS[item.item_type] || '\uD83D\uDCCD'}</span>
                        <span className="truncate">{item.title}</span>
                      </div>
                    ))}
                </div>
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
                  {geoCount} location{geoCount !== 1 ? 's' : ''} on map
                </p>
              </button>
            );
          })}
      </div>

      {/* Walking directions info */}
      {showRoutes && routeLines.length > 0 && (
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4 border border-blue-200 dark:border-blue-800">
          <div className="flex items-start gap-3">
            <span className="text-xl flex-shrink-0">{'\uD83D\uDEB6'}</span>
            <div>
              <h4 className="text-sm font-semibold text-blue-900 dark:text-blue-200 mb-1">
                Route Lines
              </h4>
              <p className="text-xs text-blue-700 dark:text-blue-300">
                Dashed lines connect your stops in order for each day. Click any
                marker and open <strong>Google Maps</strong> to get turn-by-turn
                walking or driving directions between locations.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
