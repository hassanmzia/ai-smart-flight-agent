import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import api from '@/services/api';

interface ItineraryItem {
  id: string;
  title: string;
  destination: string;
  start_date: string;
  end_date: string;
  status: string;
  days?: Array<{
    day_number: number;
    date: string;
    items: Array<{
      name: string;
      type: string;
      time?: string;
      location?: string;
      notes?: string;
    }>;
  }>;
}

interface RecommendationItem {
  title: string;
  destination: string;
  reason: string;
  match_score: number;
  based_on: string;
}

const TripMapPage = () => {
  const { isAuthenticated } = useAuth();
  const [itineraries, setItineraries] = useState<ItineraryItem[]>([]);
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  const [travelDna, setTravelDna] = useState<Record<string, any> | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'trips' | 'dna' | 'recs'>('trips');
  const [selectedTrip, setSelectedTrip] = useState<ItineraryItem | null>(null);

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
        setItineraries(Array.isArray(data) ? data : data.results || []);
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

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <p className="text-gray-600 dark:text-gray-400">Please sign in to view your trip map.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Hero */}
      <div className="bg-gradient-to-br from-teal-600 via-cyan-600 to-blue-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-20">
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
            My Travel World
          </h1>
          <p className="text-lg sm:text-xl text-teal-100 max-w-2xl">
            Visualize your trips, explore your Travel DNA, and discover personalized recommendations.
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6">
        <div className="flex gap-2 overflow-x-auto pb-2">
          {(['trips', 'dna', 'recs'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-5 py-3 rounded-t-xl font-semibold text-sm whitespace-nowrap transition-all ${
                activeTab === tab
                  ? 'bg-white dark:bg-gray-800 text-teal-600 dark:text-teal-400 shadow-lg'
                  : 'bg-white/60 dark:bg-gray-800/60 text-gray-600 dark:text-gray-400 hover:bg-white dark:hover:bg-gray-800'
              }`}
            >
              {tab === 'trips' && 'My Trips'}
              {tab === 'dna' && 'Travel DNA'}
              {tab === 'recs' && 'Recommendations'}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-teal-500 border-t-transparent"></div>
          </div>
        ) : (
          <>
            {/* Trips Tab */}
            {activeTab === 'trips' && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Trip List */}
                <div className="lg:col-span-1 space-y-3">
                  <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-3">Your Itineraries</h2>
                  {itineraries.length === 0 ? (
                    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 text-center">
                      <p className="text-4xl mb-3">🗺️</p>
                      <p className="text-gray-500 dark:text-gray-400">No trips yet. Create one to get started!</p>
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
                            <p className="text-sm text-gray-500 dark:text-gray-400">{trip.destination}</p>
                          </div>
                          <span className={`text-xs px-2 py-1 rounded-full ${statusColor(trip.status)}`}>
                            {trip.status}
                          </span>
                        </div>
                        <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
                          {trip.start_date} — {trip.end_date}
                        </p>
                      </button>
                    ))
                  )}
                </div>

                {/* Trip Detail */}
                <div className="lg:col-span-2">
                  {selectedTrip ? (
                    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                      <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                        {selectedTrip.title || selectedTrip.destination}
                      </h2>
                      <p className="text-gray-500 dark:text-gray-400 mb-6">
                        {selectedTrip.destination} | {selectedTrip.start_date} — {selectedTrip.end_date}
                      </p>

                      {selectedTrip.days && selectedTrip.days.length > 0 ? (
                        <div className="space-y-6">
                          {selectedTrip.days.map((day) => (
                            <div key={day.day_number} className="relative pl-8 border-l-2 border-teal-300 dark:border-teal-600">
                              <div className="absolute -left-2.5 top-0 w-5 h-5 rounded-full bg-teal-500 border-2 border-white dark:border-gray-800" />
                              <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                                Day {day.day_number} — {day.date}
                              </h4>
                              <div className="space-y-2">
                                {day.items.map((item, idx) => (
                                  <div key={idx} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                                    <div className="flex items-center gap-2">
                                      <span className="text-xs px-2 py-0.5 rounded-full bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-300">
                                        {item.type}
                                      </span>
                                      {item.time && (
                                        <span className="text-xs text-gray-500 dark:text-gray-400">{item.time}</span>
                                      )}
                                    </div>
                                    <p className="font-medium text-gray-900 dark:text-white mt-1">{item.name}</p>
                                    {item.location && (
                                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{item.location}</p>
                                    )}
                                    {item.notes && (
                                      <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{item.notes}</p>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-10 text-gray-500 dark:text-gray-400">
                          <p className="text-3xl mb-2">📋</p>
                          <p>No day-by-day plan available for this trip.</p>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 flex items-center justify-center min-h-[400px]">
                      <div className="text-center text-gray-500 dark:text-gray-400">
                        <p className="text-5xl mb-4">🌍</p>
                        <p className="text-lg">Select a trip to view details</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Travel DNA Tab */}
            {activeTab === 'dna' && (
              <div className="space-y-6">
                {travelDna ? (
                  <>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                      {/* Destinations */}
                      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                        <h3 className="font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                          <span className="text-2xl">🗺️</span> Destinations
                        </h3>
                        {travelDna.destinations?.favorite_destinations?.length > 0 ? (
                          <div className="space-y-2">
                            {travelDna.destinations.favorite_destinations.map((d: string, i: number) => (
                              <div key={i} className="flex items-center gap-2">
                                <span className="w-6 h-6 rounded-full bg-teal-100 dark:bg-teal-900/30 flex items-center justify-center text-xs font-bold text-teal-700 dark:text-teal-300">
                                  {i + 1}
                                </span>
                                <span className="text-gray-700 dark:text-gray-300">{d}</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-sm text-gray-500 dark:text-gray-400">Book trips to build your destination profile.</p>
                        )}
                        <p className="text-xs text-gray-400 dark:text-gray-500 mt-3">
                          {travelDna.destinations?.total_destinations || 0} destinations visited
                        </p>
                      </div>

                      {/* Budget Profile */}
                      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                        <h3 className="font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                          <span className="text-2xl">💰</span> Budget Profile
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
                              <p className="text-sm text-gray-500 dark:text-gray-400">Average Spend</p>
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
                          <span className="text-2xl">✨</span> Travel Style
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
                              <p className="text-sm text-gray-500 dark:text-gray-400">Avg Trip Duration</p>
                              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                                {travelDna.style.avg_trip_duration} days
                              </p>
                            </div>
                          )}
                          {travelDna.style?.top_interests?.length > 0 && (
                            <div>
                              <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Interests</p>
                              <div className="flex flex-wrap gap-1">
                                {travelDna.style.top_interests.map((t: string, i: number) => (
                                  <span key={i} className="text-xs px-2 py-1 rounded-full bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-300">
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
                          <span className="text-2xl">📅</span> Timing Patterns
                        </h3>
                        {travelDna.timing?.preferred_booking_months?.length > 0 ? (
                          <div className="flex flex-wrap gap-2">
                            {travelDna.timing.preferred_booking_months.map((m: string, i: number) => (
                              <span key={i} className="px-3 py-1.5 rounded-full bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300 text-sm font-medium">
                                {m}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <p className="text-sm text-gray-500 dark:text-gray-400">No booking pattern detected yet.</p>
                        )}
                        <p className="text-xs text-gray-400 dark:text-gray-500 mt-3">
                          Avg advance booking: {travelDna.timing?.avg_advance_days || 14} days
                        </p>
                      </div>

                      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                        <h3 className="font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                          <span className="text-2xl">⚙️</span> Preferences
                        </h3>
                        {travelDna.preferences && Object.keys(travelDna.preferences).length > 0 ? (
                          <div className="space-y-2 text-sm">
                            {travelDna.preferences.preferred_airlines?.length > 0 && (
                              <p className="text-gray-700 dark:text-gray-300">
                                <strong>Airlines:</strong> {travelDna.preferences.preferred_airlines.join(', ')}
                              </p>
                            )}
                            {travelDna.preferences.preferred_hotel_chains?.length > 0 && (
                              <p className="text-gray-700 dark:text-gray-300">
                                <strong>Hotels:</strong> {travelDna.preferences.preferred_hotel_chains.join(', ')}
                              </p>
                            )}
                            {travelDna.preferences.trip_style && (
                              <p className="text-gray-700 dark:text-gray-300">
                                <strong>Style:</strong> {travelDna.preferences.trip_style}
                              </p>
                            )}
                          </div>
                        ) : (
                          <p className="text-sm text-gray-500 dark:text-gray-400">Set your preferences in your profile.</p>
                        )}
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-12 text-center">
                    <p className="text-5xl mb-4">🧬</p>
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Your Travel DNA</h3>
                    <p className="text-gray-500 dark:text-gray-400 max-w-md mx-auto">
                      Book trips and search for destinations to build your personalized Travel DNA profile.
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Recommendations Tab */}
            {activeTab === 'recs' && (
              <div className="space-y-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">Personalized For You</h2>
                {recommendations.length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                    {recommendations.map((rec, i) => (
                      <div key={i} className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow">
                        <div className="h-3 bg-gradient-to-r from-teal-500 via-cyan-500 to-blue-500" />
                        <div className="p-6">
                          <div className="flex items-center justify-between mb-3">
                            <h3 className="font-bold text-gray-900 dark:text-white">{rec.title}</h3>
                            <span className="text-xs font-bold text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-900/20 px-2 py-1 rounded-full">
                              {rec.match_score}% match
                            </span>
                          </div>
                          <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">{rec.destination}</p>
                          <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">{rec.reason}</p>
                          <p className="text-xs text-gray-400 dark:text-gray-500 italic">{rec.based_on}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-12 text-center">
                    <p className="text-5xl mb-4">🎯</p>
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Recommendations Coming Soon</h3>
                    <p className="text-gray-500 dark:text-gray-400 max-w-md mx-auto">
                      Use the app more to receive personalized trip recommendations based on your travel style.
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
