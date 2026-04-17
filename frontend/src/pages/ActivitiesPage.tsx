import { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useToast } from '@/hooks/useNotifications';
import activityService, {
  ActivityPlace,
  RoadTripWaypoint,
  INTEREST_CATEGORIES,
} from '@/services/activityService';

// ------------------------------------------------------------------ //
//  Marker icons                                                       //
// ------------------------------------------------------------------ //

function placeIcon(emoji: string) {
  return L.divIcon({
    html: `<span style="font-size:24px;line-height:1">${emoji}</span>`,
    className: 'activity-marker',
    iconSize: [28, 28],
    iconAnchor: [14, 28],
    popupAnchor: [0, -24],
  });
}

const cityIcon = L.divIcon({
  html: '<span style="font-size:30px;line-height:1">\u{1F3AF}</span>',
  className: 'city-marker',
  iconSize: [34, 34],
  iconAnchor: [17, 34],
  popupAnchor: [0, -30],
});

// ------------------------------------------------------------------ //
//  Component                                                          //
// ------------------------------------------------------------------ //

export default function ActivitiesPage() {
  const { showError } = useToast();

  // Search state
  const [city, setCity] = useState('');
  const [selectedInterest, setSelectedInterest] = useState('');
  const [customInterest, setCustomInterest] = useState('');
  const [loading, setLoading] = useState(false);

  // Results
  const [places, setPlaces] = useState<ActivityPlace[]>([]);
  const [resultMeta, setResultMeta] = useState<{
    city: string; interest_label: string; icon: string;
    city_lat: number | null; city_lng: number | null;
  } | null>(null);

  // Road trip state
  const [fromCity, setFromCity] = useState('');
  const [toCity, setToCity] = useState('');
  const [waypoints, setWaypoints] = useState<RoadTripWaypoint[]>([]);
  const [tripEndpoints, setTripEndpoints] = useState<{
    from_lat: number; from_lng: number; to_lat: number; to_lng: number;
    from_city: string; to_city: string;
  } | null>(null);
  const [loadingTrip, setLoadingTrip] = useState(false);

  const activeInterest = selectedInterest || customInterest;

  // ---- handlers -------------------------------------------------- //

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!city.trim() || !activeInterest.trim()) {
      showError('Please enter a city and select an interest');
      return;
    }
    setLoading(true);
    setPlaces([]);
    setResultMeta(null);
    try {
      const data = await activityService.searchActivities(city.trim(), activeInterest.trim());
      if (data.success) {
        setPlaces(data.results);
        setResultMeta({
          city: data.city,
          interest_label: data.interest_label,
          icon: data.icon,
          city_lat: data.city_lat,
          city_lng: data.city_lng,
        });
      } else {
        showError(data.error || 'Search failed');
      }
    } catch {
      showError('Failed to search activities');
    } finally {
      setLoading(false);
    }
  };

  const handleRoadTrip = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fromCity.trim() || !toCity.trim()) {
      showError('Enter both starting and destination cities');
      return;
    }
    setLoadingTrip(true);
    setWaypoints([]);
    setTripEndpoints(null);
    try {
      const data = await activityService.roadTripWaypoints(fromCity.trim(), toCity.trim());
      if (data.success) {
        setWaypoints(data.waypoints);
        setTripEndpoints({
          from_lat: data.from_lat, from_lng: data.from_lng,
          to_lat: data.to_lat, to_lng: data.to_lng,
          from_city: data.from_city, to_city: data.to_city,
        });
      } else {
        showError(data.error || 'Road trip planning failed');
      }
    } catch {
      showError('Failed to generate road trip');
    } finally {
      setLoadingTrip(false);
    }
  };

  // ---- map data -------------------------------------------------- //

  const mapPins = places.filter((p) => p.latitude && p.longitude);
  const mapCenter: [number, number] = resultMeta?.city_lat
    ? [resultMeta.city_lat, resultMeta.city_lng!]
    : mapPins.length > 0
      ? [mapPins[0].latitude!, mapPins[0].longitude!]
      : [40, -3];

  // Road trip polyline
  const tripPolyline: [number, number][] = tripEndpoints
    ? [
        [tripEndpoints.from_lat, tripEndpoints.from_lng],
        ...waypoints.map((w) => [w.latitude, w.longitude] as [number, number]),
        [tripEndpoints.to_lat, tripEndpoints.to_lng],
      ]
    : [];

  const tripCenter: [number, number] | null = tripEndpoints
    ? [
        (tripEndpoints.from_lat + tripEndpoints.to_lat) / 2,
        (tripEndpoints.from_lng + tripEndpoints.to_lng) / 2,
      ]
    : null;

  // ---- render ---------------------------------------------------- //

  const inputCls =
    'w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500';

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8 px-4 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <span className="text-4xl">{'\u{1F3DE}\uFE0F'}</span> Activities & Interests
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Find birding spots, hiking trails, campgrounds, golf courses, and more near any destination.
        </p>
      </div>

      {/* ---- Interest Picker + City Search ---- */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 space-y-5">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">What are you interested in?</h2>

        {/* Category grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
          {INTEREST_CATEGORIES.map((cat) => (
            <button
              key={cat.key}
              type="button"
              onClick={() => { setSelectedInterest(cat.key); setCustomInterest(''); }}
              className={`flex items-center gap-2 px-3 py-2.5 rounded-lg border text-sm font-medium transition-all ${
                selectedInterest === cat.key
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 ring-2 ring-blue-300'
                  : 'border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600'
              }`}
            >
              <span className="text-xl">{cat.icon}</span>
              {cat.label}
            </button>
          ))}
        </div>

        {/* Custom interest */}
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500 dark:text-gray-400 whitespace-nowrap">Or type your own:</span>
          <input
            value={customInterest}
            onChange={(e) => { setCustomInterest(e.target.value); setSelectedInterest(''); }}
            className={inputCls}
            placeholder="e.g. surfing, wine tasting, rock climbing..."
          />
        </div>

        {/* City + Search */}
        <form onSubmit={handleSearch} className="flex gap-3 items-end">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Destination City</label>
            <input value={city} onChange={(e) => setCity(e.target.value)} className={inputCls} placeholder="e.g. Denver" required />
          </div>
          <button
            type="submit"
            disabled={loading || !activeInterest}
            className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition-colors disabled:opacity-50 whitespace-nowrap"
          >
            {loading ? 'Searching...' : 'Find Places'}
          </button>
        </form>
      </div>

      {/* ---- Results: map + list ---- */}
      {resultMeta && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 space-y-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <span className="text-2xl">{resultMeta.icon}</span>
            {resultMeta.interest_label} near {resultMeta.city}
            <span className="text-sm font-normal text-gray-500 dark:text-gray-400">({places.length} places)</span>
          </h2>

          {/* Map */}
          {(mapPins.length > 0 || resultMeta.city_lat) && (
            <div className="rounded-xl overflow-hidden border border-gray-200 dark:border-gray-700" style={{ height: 420 }}>
              <MapContainer
                key={`${mapCenter[0]}-${mapCenter[1]}-${activeInterest}`}
                center={mapCenter}
                zoom={12}
                scrollWheelZoom
                style={{ height: '100%', width: '100%' }}
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                {resultMeta.city_lat && (
                  <Marker position={[resultMeta.city_lat, resultMeta.city_lng!]} icon={cityIcon}>
                    <Popup><strong>{resultMeta.city}</strong></Popup>
                  </Marker>
                )}
                {mapPins.map((p, i) => (
                  <Marker key={i} position={[p.latitude!, p.longitude!]} icon={placeIcon(p.icon)}>
                    <Popup>
                      <div className="text-sm" style={{ maxWidth: 220 }}>
                        <strong>{p.name}</strong>
                        {p.description && <div className="text-gray-500 mt-0.5">{p.description}</div>}
                        {p.rating > 0 && <div className="mt-1">{'\u2B50'} {p.rating} ({p.reviews} reviews)</div>}
                        {p.address && <div className="mt-0.5 text-xs text-gray-400">{p.address}</div>}
                        {p.website && (
                          <a href={p.website} target="_blank" rel="noopener noreferrer" className="text-blue-600 text-xs hover:underline block mt-1">
                            {'\u{1F517}'} Visit Website
                          </a>
                        )}
                      </div>
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>
            </div>
          )}

          {/* Place cards */}
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {places.map((p, i) => (
              <div key={i} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow transition-shadow">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">{p.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold text-gray-900 dark:text-white truncate">{p.name}</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{p.description}</div>
                  </div>
                  {p.rating > 0 && (
                    <div className="text-sm font-semibold text-yellow-600 dark:text-yellow-400 whitespace-nowrap">
                      {'\u2B50'} {p.rating}
                    </div>
                  )}
                </div>
                {p.address && <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">{'\u{1F4CD}'} {p.address}</div>}
                {p.hours && <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">{'\u{1F552}'} {p.hours}</div>}
                <div className="flex gap-2 mt-3 pt-2 border-t border-gray-100 dark:border-gray-700">
                  {p.website ? (
                    <a href={p.website} target="_blank" rel="noopener noreferrer" className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors">
                      {'\u{1F517}'} Visit Website
                    </a>
                  ) : (
                    <a
                      href={`https://www.google.com/search?q=${encodeURIComponent(p.name + ' ' + (resultMeta?.city || ''))}`}
                      target="_blank" rel="noopener noreferrer"
                      className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
                    >
                      {'\u{1F50D}'} Find Online
                    </a>
                  )}
                  {p.latitude && p.longitude && (
                    <a
                      href={`https://www.google.com/maps/search/?api=1&query=${p.latitude},${p.longitude}`}
                      target="_blank" rel="noopener noreferrer"
                      className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-primary-600 dark:text-primary-400 bg-primary-50 dark:bg-primary-900/20 hover:bg-primary-100 dark:hover:bg-primary-900/30 rounded-lg transition-colors"
                    >
                      {'\u{1F5FA}\uFE0F'} Map
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ---- Cross-Country Road Trip Planner ---- */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <span className="text-2xl">{'\u{1F697}'}</span> Cross-Country Drive Planner
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Plan a road trip with scenic stops, rest areas, and campgrounds along your route.
        </p>
        <form onSubmit={handleRoadTrip} className="flex flex-wrap gap-3 items-end">
          <div className="flex-1 min-w-[140px]">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">From</label>
            <input value={fromCity} onChange={(e) => setFromCity(e.target.value)} className={inputCls} placeholder="e.g. New York" required />
          </div>
          <div className="flex-1 min-w-[140px]">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">To</label>
            <input value={toCity} onChange={(e) => setToCity(e.target.value)} className={inputCls} placeholder="e.g. Los Angeles" required />
          </div>
          <button type="submit" disabled={loadingTrip} className="px-5 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-semibold rounded-lg transition-colors disabled:opacity-50 whitespace-nowrap">
            {loadingTrip ? 'Planning...' : 'Plan Route'}
          </button>
        </form>

        {/* Road trip map + waypoints */}
        {tripEndpoints && (
          <>
            <div className="rounded-xl overflow-hidden border border-gray-200 dark:border-gray-700" style={{ height: 400 }}>
              <MapContainer
                key={`trip-${tripEndpoints.from_lat}-${tripEndpoints.to_lat}`}
                center={tripCenter!}
                zoom={5}
                scrollWheelZoom
                style={{ height: '100%', width: '100%' }}
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <Polyline positions={tripPolyline} color="#3b82f6" weight={3} dashArray="8 6" />
                <Marker position={[tripEndpoints.from_lat, tripEndpoints.from_lng]} icon={placeIcon('\u{1F7E2}')}>
                  <Popup><strong>Start:</strong> {tripEndpoints.from_city}</Popup>
                </Marker>
                <Marker position={[tripEndpoints.to_lat, tripEndpoints.to_lng]} icon={placeIcon('\u{1F3C1}')}>
                  <Popup><strong>Destination:</strong> {tripEndpoints.to_city}</Popup>
                </Marker>
                {waypoints.map((w) => (
                  <Marker key={w.stop_number} position={[w.latitude, w.longitude]} icon={placeIcon(w.icon)}>
                    <Popup>
                      <div className="text-sm">
                        <strong>Stop {w.stop_number}: {w.name}</strong>
                        <div className="text-gray-500 mt-0.5">{w.description}</div>
                      </div>
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>
            </div>

            {/* Waypoint list */}
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-white">
                {'\u{1F7E2}'} {tripEndpoints.from_city} {'\u2192'} {'\u{1F3C1}'} {tripEndpoints.to_city}
                <span className="text-gray-400 font-normal">({waypoints.length} stops)</span>
              </div>
              {waypoints.map((w) => (
                <div key={w.stop_number} className="flex items-center gap-3 p-3 border border-gray-200 dark:border-gray-700 rounded-lg">
                  <span className="text-2xl">{w.icon}</span>
                  <div className="flex-1">
                    <div className="font-medium text-gray-900 dark:text-white text-sm">{w.name}</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">{w.description}</div>
                  </div>
                  <a
                    href={`https://www.google.com/maps/search/?api=1&query=${w.latitude},${w.longitude}`}
                    target="_blank" rel="noopener noreferrer"
                    className="text-xs text-blue-600 dark:text-blue-400 hover:underline whitespace-nowrap"
                  >
                    {'\u{1F5FA}\uFE0F'} Map
                  </a>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
