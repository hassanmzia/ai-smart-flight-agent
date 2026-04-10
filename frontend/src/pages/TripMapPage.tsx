import { useState, useEffect, useCallback, lazy, Suspense } from 'react';
import { useAuth } from '@/hooks/useAuth';
import api from '@/services/api';
import type { MapItinerary } from '@/components/map/TripMapVisualization';

const TripMapVisualization = lazy(
  () => import('@/components/map/TripMapVisualization'),
);
const ImmersiveTripViewer = lazy(
  () => import('@/components/map/ImmersiveTripViewer'),
);
const TripStoryView = lazy(
  () => import('@/components/trip/TripStoryView'),
);

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface RecommendationItem {
  title: string;
  destination: string;
  reason: string;
  match_score: number;
  based_on: string;
}

type Tab = 'immersive' | 'map' | 'story' | 'trips' | 'dna' | 'recs';

// ---------------------------------------------------------------------------
// TripMapPage
// ---------------------------------------------------------------------------

const TripMapPage = () => {
  const { isAuthenticated } = useAuth();
  const [itineraries, setItineraries] = useState<MapItinerary[]>([]);
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  const [travelDna, setTravelDna] = useState<Record<string, any> | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>('immersive');
  const [selectedTrip, setSelectedTrip] = useState<MapItinerary | null>(null);
  const [isGeocoding, setIsGeocoding] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      loadData();
    }
  }, [isAuthenticated]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [itinRes, dnaRes, recsRes] = await Promise.allSettled([
        api.get('/api/itineraries/itineraries/'),
        api.get('/api/agents/travel-dna'),
        api.get('/api/agents/recommendations?limit=5'),
      ]);

      if (itinRes.status === 'fulfilled') {
        const data = itinRes.value.data;
        const list: MapItinerary[] = Array.isArray(data)
          ? data
          : data.items || data.results || [];
        setItineraries(list);
        // Auto-select first itinerary that has geo data
        const first = list.find((it) =>
          it.days?.some((d) =>
            d.items?.some((i) => i.latitude != null && i.longitude != null),
          ),
        );
        if (first) setSelectedTrip(first);
        else if (list.length > 0) setSelectedTrip(list[0]);

        // Auto-geocode itineraries that have items with names/titles but no coordinates
        // Uses browser-side Nominatim (no Docker network dependency)
        for (const trip of list) {
          const needsGeocode = trip.days?.some((d) =>
            d.items?.some(
              (i) =>
                (i.latitude == null || i.longitude == null) &&
                (i.location_name || i.title),
            ),
          );
          if (needsGeocode) {
            geocodeTrip(trip.id);
            break; // geocode one at a time to respect rate limits
          }
        }
      }
      if (dnaRes.status === 'fulfilled' && dnaRes.value.data.travel_dna) {
        setTravelDna(dnaRes.value.data.travel_dna);
      }
      if (recsRes.status === 'fulfilled' && recsRes.value.data.recommendations) {
        setRecommendations(recsRes.value.data.recommendations);
      }
    } catch {
      // Errors are handled individually above
    } finally {
      setLoading(false);
    }
  };

  // ---- helpers ----

  const statusColor = (s: string) => {
    const colors: Record<string, string> = {
      draft: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
      planned: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
      active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
      completed: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
    };
    return colors[s] || colors.draft;
  };

  const dnaLabel = (key: string) => {
    const labels: Record<string, string> = {
      budget: 'Budget Traveler',
      moderate: 'Mid-Range Explorer',
      premium: 'Premium Traveler',
      luxury: 'Luxury Connoisseur',
      weekend_warrior: 'Weekend Warrior',
      week_tripper: 'Week Tripper',
      extended_traveler: 'Extended Traveler',
      balanced: 'Balanced Traveler',
    };
    return labels[key] || key;
  };

  const hasGeoData = (trip: MapItinerary) =>
    trip.days?.some((d) => d.items?.some((i) => i.latitude != null && i.longitude != null));

  // Geocode via backend endpoint (avoids CORS issues with Nominatim)
  const geocodeTrip = useCallback(
    async (itineraryId: string | number) => {
      setIsGeocoding(true);
      try {
        const res = await api.post(`/api/itineraries/itineraries/${itineraryId}/geocode-items/`);
        if (res.data?.itinerary) {
          const updated: MapItinerary = res.data.itinerary;
          setItineraries((prev) =>
            prev.map((it) => (String(it.id) === String(itineraryId) ? updated : it)),
          );
          setSelectedTrip(updated);
        }
      } catch {
        // Geocoding is best-effort
      } finally {
        setIsGeocoding(false);
      }
    },
    [],
  );

  const handleGeocode = useCallback(
    async (itineraryId: string | number) => {
      await geocodeTrip(itineraryId);
    },
    [geocodeTrip],
  );

  // ---- auth guard ----

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <p className="text-gray-600 dark:text-gray-400">Please sign in to view your trip map.</p>
      </div>
    );
  }

  // ---- tab config ----

  const TABS: { key: Tab; label: string; icon: string }[] = [
    { key: 'immersive', label: 'Immersive View', icon: '\uD83C\uDF0D' },
    { key: 'story', label: 'Trip Story', icon: '\uD83D\uDCD6' },
    { key: 'map', label: 'Classic Map', icon: '\uD83D\uDDFA\uFE0F' },
    { key: 'trips', label: 'My Trips', icon: '\u2708\uFE0F' },
    { key: 'dna', label: 'Travel DNA', icon: '\uD83E\uDDEC' },
    { key: 'recs', label: 'For You', icon: '\uD83C\uDFAF' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Hero */}
      <div className="bg-gradient-to-br from-teal-600 via-cyan-600 to-blue-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-20">
          <h1 className="text-lg sm:text-xl lg:text-2xl font-bold mb-4">
            My Travel World
          </h1>
          <p className="text-lg sm:text-xl text-teal-100 max-w-2xl">
            Visualize your trips on an interactive map, explore your Travel DNA,
            and discover personalized recommendations.
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 -mt-6">
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-1 sm:flex sm:gap-2">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-2 sm:px-4 py-2 sm:py-3 rounded-t-xl font-semibold text-xs sm:text-sm text-center transition-all flex items-center justify-center gap-1.5 ${
                activeTab === tab.key
                  ? 'bg-white dark:bg-gray-800 text-teal-600 dark:text-teal-400 shadow-lg'
                  : 'bg-white/60 dark:bg-gray-800/60 text-gray-600 dark:text-gray-400 hover:bg-white dark:hover:bg-gray-800'
              }`}
            >
              <span className="hidden sm:inline">{tab.icon}</span> {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-teal-500 border-t-transparent" />
          </div>
        ) : (
          <>
            {/* ============================================================ */}
            {/* IMMERSIVE VIEW TAB */}
            {/* ============================================================ */}
            {activeTab === 'immersive' && (
              <div className="space-y-6">
                {/* Trip selector */}
                {itineraries.length > 1 && (
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Itinerary:
                    </span>
                    {itineraries.map((trip) => (
                      <button
                        key={trip.id}
                        onClick={() => setSelectedTrip(trip)}
                        className={`px-4 py-2 rounded-xl text-sm font-medium transition-all border ${
                          selectedTrip?.id === trip.id
                            ? 'border-teal-500 bg-teal-50 dark:bg-teal-900/20 text-teal-700 dark:text-teal-300'
                            : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:border-teal-300'
                        }`}
                      >
                        {trip.title || trip.destination}
                        {hasGeoData(trip) && (
                          <span className="ml-1.5 inline-block w-2 h-2 rounded-full bg-teal-500" />
                        )}
                      </button>
                    ))}
                  </div>
                )}

                {selectedTrip ? (
                  <Suspense
                    fallback={
                      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg flex items-center justify-center" style={{ height: 600 }}>
                        <div className="text-center">
                          <div className="animate-spin rounded-full h-10 w-10 border-4 border-teal-500 border-t-transparent mx-auto mb-3" />
                          <p className="text-sm text-gray-500 dark:text-gray-400">Loading immersive view...</p>
                        </div>
                      </div>
                    }
                  >
                    <ImmersiveTripViewer
                      itinerary={selectedTrip}
                      onGeocode={handleGeocode}
                      isGeocoding={isGeocoding}
                    />
                  </Suspense>
                ) : (
                  <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-12 text-center">
                    <p className="text-5xl mb-4">{'\uD83C\uDF0D'}</p>
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                      No Trips Yet
                    </h3>
                    <p className="text-gray-500 dark:text-gray-400 max-w-md mx-auto">
                      Create an itinerary with the AI Trip Planner to experience the immersive fly-through view.
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* ============================================================ */}
            {/* TRIP STORY TAB */}
            {/* ============================================================ */}
            {activeTab === 'story' && (
              <div className="space-y-6">
                {/* Trip selector */}
                {itineraries.length > 1 && (
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Itinerary:
                    </span>
                    {itineraries.map((trip) => (
                      <button
                        key={trip.id}
                        onClick={() => setSelectedTrip(trip)}
                        className={`px-4 py-2 rounded-xl text-sm font-medium transition-all border ${
                          selectedTrip?.id === trip.id
                            ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300'
                            : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:border-purple-300'
                        }`}
                      >
                        {trip.title || trip.destination}
                      </button>
                    ))}
                  </div>
                )}

                {selectedTrip ? (
                  <Suspense
                    fallback={
                      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg flex items-center justify-center" style={{ height: 300 }}>
                        <div className="text-center">
                          <div className="animate-spin rounded-full h-10 w-10 border-4 border-purple-500 border-t-transparent mx-auto mb-3" />
                          <p className="text-sm text-gray-500 dark:text-gray-400">Loading story view...</p>
                        </div>
                      </div>
                    }
                  >
                    <TripStoryView
                      itineraryId={selectedTrip.id}
                      itineraryTitle={selectedTrip.title}
                      destination={selectedTrip.destination}
                    />
                  </Suspense>
                ) : (
                  <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-12 text-center">
                    <p className="text-5xl mb-4">{'\uD83D\uDCD6'}</p>
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                      No Trips Yet
                    </h3>
                    <p className="text-gray-500 dark:text-gray-400 max-w-md mx-auto">
                      Create an itinerary with the AI Trip Planner to generate your trip story.
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* ============================================================ */}
            {/* MAP TAB */}
            {/* ============================================================ */}
            {activeTab === 'map' && (
              <div className="space-y-6">
                {/* Trip selector */}
                {itineraries.length > 1 && (
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Itinerary:
                    </span>
                    {itineraries.map((trip) => (
                      <button
                        key={trip.id}
                        onClick={() => setSelectedTrip(trip)}
                        className={`px-4 py-2 rounded-xl text-sm font-medium transition-all border ${
                          selectedTrip?.id === trip.id
                            ? 'border-teal-500 bg-teal-50 dark:bg-teal-900/20 text-teal-700 dark:text-teal-300'
                            : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:border-teal-300'
                        }`}
                      >
                        {trip.title || trip.destination}
                        {hasGeoData(trip) && (
                          <span className="ml-1.5 inline-block w-2 h-2 rounded-full bg-teal-500" />
                        )}
                      </button>
                    ))}
                  </div>
                )}

                {/* Map visualization */}
                {selectedTrip ? (
                  <Suspense
                    fallback={
                      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg flex items-center justify-center" style={{ height: 520 }}>
                        <div className="text-center">
                          <div className="animate-spin rounded-full h-10 w-10 border-4 border-teal-500 border-t-transparent mx-auto mb-3" />
                          <p className="text-sm text-gray-500 dark:text-gray-400">Loading map...</p>
                        </div>
                      </div>
                    }
                  >
                    <TripMapVisualization
                      itinerary={selectedTrip}
                      onGeocode={handleGeocode}
                      isGeocoding={isGeocoding}
                    />
                  </Suspense>
                ) : (
                  <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-12 text-center">
                    <p className="text-5xl mb-4">{'\uD83C\uDF0D'}</p>
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                      No Trips Yet
                    </h3>
                    <p className="text-gray-500 dark:text-gray-400 max-w-md mx-auto">
                      Create an itinerary with the AI Trip Planner to see your
                      destinations on an interactive map.
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* ============================================================ */}
            {/* TRIPS TAB (original) */}
            {/* ============================================================ */}
            {activeTab === 'trips' && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Trip List */}
                <div className="lg:col-span-1 space-y-3">
                  <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-3">
                    Your Itineraries
                  </h2>
                  {itineraries.length === 0 ? (
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 text-center">
                      <p className="text-4xl mb-3">{'\uD83D\uDDFA\uFE0F'}</p>
                      <p className="text-gray-500 dark:text-gray-400">
                        No trips yet. Create one to get started!
                      </p>
                    </div>
                  ) : (
                    itineraries.map((trip) => (
                      <button
                        key={trip.id}
                        onClick={() => setSelectedTrip(trip)}
                        className={`w-full text-left bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm hover:shadow-md transition-all border-2 ${
                          selectedTrip?.id === trip.id
                            ? 'border-teal-500 dark:border-teal-400'
                            : 'border-transparent'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="font-semibold text-gray-900 dark:text-white">
                              {trip.title || trip.destination}
                            </h3>
                            <p className="text-sm text-gray-500 dark:text-gray-400">
                              {trip.destination}
                            </p>
                          </div>
                          <span
                            className={`text-xs px-2 py-1 rounded-full ${statusColor(trip.status)}`}
                          >
                            {trip.status}
                          </span>
                        </div>
                        <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
                          {trip.start_date} &mdash; {trip.end_date}
                        </p>
                      </button>
                    ))
                  )}
                </div>

                {/* Trip Detail */}
                <div className="lg:col-span-2">
                  {selectedTrip ? (
                    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-1">
                            {selectedTrip.title || selectedTrip.destination}
                          </h2>
                          <p className="text-gray-500 dark:text-gray-400 text-sm">
                            {selectedTrip.destination} | {selectedTrip.start_date} &mdash;{' '}
                            {selectedTrip.end_date}
                          </p>
                        </div>
                        {hasGeoData(selectedTrip) && (
                          <button
                            onClick={() => setActiveTab('map')}
                            className="px-4 py-2 rounded-lg bg-teal-50 dark:bg-teal-900/20 text-teal-700 dark:text-teal-300 text-sm font-medium hover:bg-teal-100 dark:hover:bg-teal-900/40 transition-colors"
                          >
                            {'\uD83D\uDDFA\uFE0F'} View on Map
                          </button>
                        )}
                      </div>

                      {selectedTrip.days && selectedTrip.days.length > 0 ? (
                        <div className="space-y-6">
                          {selectedTrip.days.map((day) => (
                            <div
                              key={day.day_number}
                              className="relative pl-8 border-l-2 border-teal-300 dark:border-teal-600"
                            >
                              <div className="absolute -left-2.5 top-0 w-5 h-5 rounded-full bg-teal-500 border-2 border-white dark:border-gray-800" />
                              <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                                Day {day.day_number} &mdash; {day.date}
                              </h4>
                              <div className="space-y-2">
                                {day.items.map((item, idx) => (
                                  <div
                                    key={idx}
                                    className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3"
                                  >
                                    <div className="flex items-center gap-2">
                                      <span className="text-xs px-2 py-0.5 rounded-full bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-300">
                                        {item.item_type}
                                      </span>
                                      {item.start_time && (
                                        <span className="text-xs text-gray-500 dark:text-gray-400">
                                          {item.start_time}
                                        </span>
                                      )}
                                      {item.latitude != null && item.longitude != null && (
                                        <span className="text-xs text-teal-500" title="Has map coordinates">
                                          {'\uD83D\uDCCD'}
                                        </span>
                                      )}
                                    </div>
                                    <p className="font-medium text-gray-900 dark:text-white mt-1">
                                      {item.title}
                                    </p>
                                    {item.location_name && (
                                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                                        {item.location_name}
                                      </p>
                                    )}
                                    {item.notes && (
                                      <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                                        {item.notes}
                                      </p>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-10 text-gray-500 dark:text-gray-400">
                          <p className="text-3xl mb-2">{'\uD83D\uDCCB'}</p>
                          <p>No day-by-day plan available for this trip.</p>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 flex items-center justify-center min-h-[400px]">
                      <div className="text-center text-gray-500 dark:text-gray-400">
                        <p className="text-5xl mb-4">{'\uD83C\uDF0D'}</p>
                        <p className="text-lg">Select a trip to view details</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* ============================================================ */}
            {/* TRAVEL DNA TAB */}
            {/* ============================================================ */}
            {activeTab === 'dna' && (
              <div className="space-y-6">
                {travelDna ? (
                  <>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                      {/* Destinations */}
                      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                        <h3 className="font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                          <span className="text-2xl">{'\uD83D\uDDFA\uFE0F'}</span> Destinations
                        </h3>
                        {travelDna.destinations?.favorite_destinations?.length > 0 ? (
                          <div className="space-y-2">
                            {travelDna.destinations.favorite_destinations.map(
                              (d: string, i: number) => (
                                <div key={i} className="flex items-center gap-2">
                                  <span className="w-6 h-6 rounded-full bg-teal-100 dark:bg-teal-900/30 flex items-center justify-center text-xs font-bold text-teal-700 dark:text-teal-300">
                                    {i + 1}
                                  </span>
                                  <span className="text-gray-700 dark:text-gray-300">{d}</span>
                                </div>
                              ),
                            )}
                          </div>
                        ) : (
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            Book trips to build your destination profile.
                          </p>
                        )}
                        <p className="text-xs text-gray-400 dark:text-gray-500 mt-3">
                          {travelDna.destinations?.total_destinations || 0} destinations visited
                        </p>
                      </div>

                      {/* Budget Profile */}
                      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                        <h3 className="font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                          <span className="text-2xl">{'\uD83D\uDCB0'}</span> Budget Profile
                        </h3>
                        <div className="space-y-3">
                          <div>
                            <p className="text-sm text-gray-500 dark:text-gray-400">Range</p>
                            <p className="text-lg font-semibold text-teal-600 dark:text-teal-400">
                              {dnaLabel(travelDna.budget?.range || 'unknown')}
                            </p>
                          </div>
                          {travelDna.budget?.average_spend > 0 && (
                            <div>
                              <p className="text-sm text-gray-500 dark:text-gray-400">
                                Average Spend
                              </p>
                              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                                ${travelDna.budget.average_spend.toFixed(0)}
                              </p>
                            </div>
                          )}
                          {travelDna.budget?.booking_count > 0 && (
                            <p className="text-xs text-gray-400 dark:text-gray-500">
                              Based on {travelDna.budget.booking_count} bookings
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Travel Style */}
                      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                        <h3 className="font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                          <span className="text-2xl">{'\u2728'}</span> Travel Style
                        </h3>
                        <div className="space-y-3">
                          <div>
                            <p className="text-sm text-gray-500 dark:text-gray-400">Style</p>
                            <p className="text-lg font-semibold text-teal-600 dark:text-teal-400">
                              {dnaLabel(travelDna.style?.style || 'balanced')}
                            </p>
                          </div>
                          {travelDna.style?.avg_trip_duration > 0 && (
                            <div>
                              <p className="text-sm text-gray-500 dark:text-gray-400">
                                Avg Trip Duration
                              </p>
                              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                                {travelDna.style.avg_trip_duration} days
                              </p>
                            </div>
                          )}
                          {travelDna.style?.top_interests?.length > 0 && (
                            <div>
                              <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
                                Interests
                              </p>
                              <div className="flex flex-wrap gap-1">
                                {travelDna.style.top_interests.map((t: string, i: number) => (
                                  <span
                                    key={i}
                                    className="text-xs px-2 py-1 rounded-full bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-300"
                                  >
                                    {t}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Timing & Preferences */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                        <h3 className="font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                          <span className="text-2xl">{'\uD83D\uDCC5'}</span> Timing Patterns
                        </h3>
                        {travelDna.timing?.preferred_booking_months?.length > 0 ? (
                          <div className="flex flex-wrap gap-2">
                            {travelDna.timing.preferred_booking_months.map(
                              (m: string, i: number) => (
                                <span
                                  key={i}
                                  className="px-3 py-1.5 rounded-full bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300 text-sm font-medium"
                                >
                                  {m}
                                </span>
                              ),
                            )}
                          </div>
                        ) : (
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            No booking pattern detected yet.
                          </p>
                        )}
                        <p className="text-xs text-gray-400 dark:text-gray-500 mt-3">
                          Avg advance booking: {travelDna.timing?.avg_advance_days || 14} days
                        </p>
                      </div>

                      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                        <h3 className="font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                          <span className="text-2xl">{'\u2699\uFE0F'}</span> Preferences
                        </h3>
                        {travelDna.preferences &&
                        Object.keys(travelDna.preferences).length > 0 ? (
                          <div className="space-y-2 text-sm">
                            {travelDna.preferences.preferred_airlines?.length > 0 && (
                              <p className="text-gray-700 dark:text-gray-300">
                                <strong>Airlines:</strong>{' '}
                                {travelDna.preferences.preferred_airlines.join(', ')}
                              </p>
                            )}
                            {travelDna.preferences.preferred_hotel_chains?.length > 0 && (
                              <p className="text-gray-700 dark:text-gray-300">
                                <strong>Hotels:</strong>{' '}
                                {travelDna.preferences.preferred_hotel_chains.join(', ')}
                              </p>
                            )}
                            {travelDna.preferences.trip_style && (
                              <p className="text-gray-700 dark:text-gray-300">
                                <strong>Style:</strong> {travelDna.preferences.trip_style}
                              </p>
                            )}
                          </div>
                        ) : (
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            Set your preferences in your profile.
                          </p>
                        )}
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-12 text-center">
                    <p className="text-5xl mb-4">{'\uD83E\uDDEC'}</p>
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                      Your Travel DNA
                    </h3>
                    <p className="text-gray-500 dark:text-gray-400 max-w-md mx-auto">
                      Book trips and search for destinations to build your personalized Travel DNA
                      profile.
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* ============================================================ */}
            {/* RECOMMENDATIONS TAB */}
            {/* ============================================================ */}
            {activeTab === 'recs' && (
              <div className="space-y-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                  Personalized For You
                </h2>
                {recommendations.length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                    {recommendations.map((rec, i) => (
                      <div
                        key={i}
                        className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow"
                      >
                        <div className="h-3 bg-gradient-to-r from-teal-500 via-cyan-500 to-blue-500" />
                        <div className="p-6">
                          <div className="flex items-center justify-between mb-3">
                            <h3 className="font-bold text-gray-900 dark:text-white">{rec.title}</h3>
                            <span className="text-xs font-bold text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-900/20 px-2 py-1 rounded-full">
                              {rec.match_score}% match
                            </span>
                          </div>
                          <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
                            {rec.destination}
                          </p>
                          <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">
                            {rec.reason}
                          </p>
                          <p className="text-xs text-gray-400 dark:text-gray-500 italic">
                            {rec.based_on}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-12 text-center">
                    <p className="text-5xl mb-4">{'\uD83C\uDFAF'}</p>
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                      Recommendations Coming Soon
                    </h3>
                    <p className="text-gray-500 dark:text-gray-400 max-w-md mx-auto">
                      Use the app more to receive personalized trip recommendations based on your
                      travel style.
                    </p>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default TripMapPage;
