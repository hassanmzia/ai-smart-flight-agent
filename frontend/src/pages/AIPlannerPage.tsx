import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Loading from '@/components/common/Loading';
import { useToast } from '@/hooks/useNotifications';
import { useAuth } from '@/hooks/useAuth';
import api from '@/services/api';
import {
  parseItineraryNarrative,
  saveAiPlanAsItinerary,
} from '@/utils/aiItinerarySaver';
import TravelChat from '@/components/TravelChat';
import AirportAutocomplete from '@/components/common/AirportAutocomplete';
import SmartTripPreview from '@/components/SmartTripPreview';
import { ROUTES } from '@/utils/constants';

type OrderMode = 'form' | 'chat' | 'voice';
type ResultTab = 'itinerary' | 'flights' | 'hotels' | 'rentals' | 'cars' | 'dining' | 'intelligence';

// Parser/saver helpers (parseItineraryNarrative, extractPlaceName, guessItemType,
// saveAiPlanAsItinerary) live in @/utils/aiItinerarySaver so the Collaborate
// page can produce the same rich itinerary for shared trips.

const ITEM_TYPE_CONFIG: Record<string, { icon: string; color: string; bg: string }> = {
  flight: { icon: '✈️', color: 'text-blue-700 dark:text-blue-300', bg: 'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-800' },
  hotel: { icon: '🏨', color: 'text-purple-700 dark:text-purple-300', bg: 'bg-purple-50 dark:bg-purple-900/30 border-purple-200 dark:border-purple-800' },
  restaurant: { icon: '🍽️', color: 'text-orange-700 dark:text-orange-300', bg: 'bg-orange-50 dark:bg-orange-900/30 border-orange-200 dark:border-orange-800' },
  attraction: { icon: '🏛️', color: 'text-emerald-700 dark:text-emerald-300', bg: 'bg-emerald-50 dark:bg-emerald-900/30 border-emerald-200 dark:border-emerald-800' },
  activity: { icon: '🎯', color: 'text-indigo-700 dark:text-indigo-300', bg: 'bg-indigo-50 dark:bg-indigo-900/30 border-indigo-200 dark:border-indigo-800' },
  transport: { icon: '🚕', color: 'text-cyan-700 dark:text-cyan-300', bg: 'bg-cyan-50 dark:bg-cyan-900/30 border-cyan-200 dark:border-cyan-800' },
  note: { icon: '📝', color: 'text-gray-700 dark:text-gray-300', bg: 'bg-gray-50 dark:bg-gray-900/30 border-gray-200 dark:border-gray-800' },
};

const TAB_CONFIG: { key: ResultTab; label: string; icon: string }[] = [
  { key: 'itinerary', label: 'Itinerary', icon: '📅' },
  { key: 'flights', label: 'Flights', icon: '✈️' },
  { key: 'hotels', label: 'Hotels', icon: '🏨' },
  { key: 'rentals', label: 'Rentals', icon: '🏡' },
  { key: 'cars', label: 'Cars', icon: '🚗' },
  { key: 'dining', label: 'Dining', icon: '🍽️' },
  { key: 'intelligence', label: 'Intelligence', icon: '🧠' },
];

/**
 * Pull a booking / partner URL off an item regardless of which field the
 * upstream provider populated. SerpAPI flights use bookingUrl, hotel
 * results use link or website_url, rentals use booking_url, restaurants
 * use website, etc. Returning null lets callers skip rendering cleanly.
 */
const getBookingUrl = (item: any): string | null => {
  if (!item) return null;
  const url =
    item.bookingUrl ||
    item.booking_url ||
    item.link ||
    item.website_url ||
    item.website ||
    item.url ||
    item.reservation_url ||
    item.source_url ||
    null;
  return typeof url === 'string' && url.trim() ? url : null;
};

/**
 * Renders a small "Book / Visit" external-link button. Used in every
 * AI Planner result tab so users can jump straight to the partner site
 * the same way the dedicated search pages already let them.
 */
const BookingLinkButton = ({
  item,
  label = 'Book on Partner Site',
  tone = 'blue',
  size = 'md',
}: {
  item: any;
  label?: string;
  tone?: 'blue' | 'green' | 'teal' | 'orange' | 'rose' | 'indigo';
  size?: 'sm' | 'md';
}) => {
  const url = getBookingUrl(item);
  if (!url) return null;
  const toneClasses: Record<string, string> = {
    blue: 'border-blue-500 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20',
    green: 'border-green-500 text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20',
    teal: 'border-teal-500 text-teal-600 dark:text-teal-400 hover:bg-teal-50 dark:hover:bg-teal-900/20',
    orange: 'border-orange-500 text-orange-600 dark:text-orange-400 hover:bg-orange-50 dark:hover:bg-orange-900/20',
    rose: 'border-rose-500 text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-900/20',
    indigo: 'border-indigo-500 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20',
  };
  const sizeClasses = size === 'sm'
    ? 'px-2 py-1 text-[11px]'
    : 'px-3 py-2 text-xs';
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      onClick={(e) => e.stopPropagation()}
      className={`inline-flex items-center gap-1.5 rounded-lg border font-semibold whitespace-nowrap transition-colors ${toneClasses[tone]} ${sizeClasses}`}
      title="Opens the partner booking site in a new tab"
    >
      <span>🔗</span> {label}
    </a>
  );
};

const AIPlannerPage = () => {
  const navigate = useNavigate();
  const { showSuccess, showError } = useToast();
  const { isAuthenticated, user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [orderMode, setOrderMode] = useState<OrderMode>('form');
  const [activeTab, setActiveTab] = useState<ResultTab>('itinerary');
  const [expandedDay, setExpandedDay] = useState<number | null>(1);

  // Form state — kept blank on every fresh navigation to the AI Travel
  // Planner page so the user always starts from a clean slate. Within a
  // single visit, React state alone is enough to survive tab switches
  // inside the page; we deliberately do NOT persist to localStorage so
  // last-week's "Washington DC → Jessore" search isn't pre-filled when
  // the user comes back tomorrow.
  //
  // Historical note: an earlier version stored these under
  // ``aiPlannerFormV1``. Wipe that key on mount so existing users with a
  // stale value also see an empty form.
  useEffect(() => {
    try { localStorage.removeItem('aiPlannerFormV1'); } catch { /* ignore */ }
  }, []);

  const [originCity, setOriginCity] = useState<string>('');
  const [originCountry, setOriginCountry] = useState<string>('');
  const [destinationCity, setDestinationCity] = useState<string>('');
  const [destinationCountry, setDestinationCountry] = useState<string>('');
  const [departureDate, setDepartureDate] = useState<string>('');
  const [returnDate, setReturnDate] = useState<string>('');
  const [passengers, setPassengers] = useState<number>(1);
  const [budget, setBudget] = useState<string>('');
  const [cuisine, setCuisine] = useState<string>('');
  const [travelStyle, setTravelStyle] = useState<string>('');
  const [interests, setInterests] = useState<string>('');
  const [accommodationPref, setAccommodationPref] = useState<string>('');
  const [chatParams, setChatParams] = useState<any>({});

  // Compose display labels from city/country
  const originLabel = originCountry ? `${originCity}, ${originCountry}` : originCity;
  const destinationLabel = destinationCountry ? `${destinationCity}, ${destinationCountry}` : destinationCity;

  const handlePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const response = await api.post('/api/agents/plan', {
        query: `Plan a trip from ${originLabel} to ${destinationLabel}`,
        origin_city: originCity,
        origin_country: originCountry || undefined,
        destination_city: destinationCity,
        destination_country: destinationCountry || undefined,
        departure_date: departureDate,
        return_date: returnDate || undefined,
        passengers: Number(passengers),
        budget: budget ? Number(budget) : undefined,
        cuisine: cuisine || undefined,
        travel_style: travelStyle || undefined,
        interests: interests || undefined,
        accommodation_preference: accommodationPref || undefined,
      }, { timeout: 300000 });
      const data = response.data;
      if (data.success) {
        setResult(data);
        setActiveTab('itinerary');
        setExpandedDay(1);
        showSuccess('AI travel planning complete!');
      } else {
        showError(data.error || 'Planning failed');
      }
    } catch (error: any) {
      showError(error.response?.data?.error || error.message || 'Failed to connect to AI agent');
    } finally {
      setLoading(false);
    }
  };

  const handleChatPlanReady = (planResult: any) => {
    const merged = { ...planResult, success: planResult.success !== false };
    setResult(merged);
    setActiveTab('itinerary');
    setExpandedDay(1);
    if (chatParams.origin_city) setOriginCity(chatParams.origin_city);
    if (chatParams.origin_country) setOriginCountry(chatParams.origin_country);
    if (chatParams.origin) setOriginCity(chatParams.origin);
    if (chatParams.destination_city) setDestinationCity(chatParams.destination_city);
    if (chatParams.destination_country) setDestinationCountry(chatParams.destination_country);
    if (chatParams.destination) setDestinationCity(chatParams.destination);
    if (chatParams.departure_date) setDepartureDate(chatParams.departure_date);
    if (chatParams.return_date) setReturnDate(chatParams.return_date);
    if (chatParams.passengers) setPassengers(chatParams.passengers);
    if (chatParams.budget) setBudget(String(chatParams.budget));
    if (chatParams.cuisine) setCuisine(chatParams.cuisine);
    showSuccess('AI travel planning complete!');
  };

  const handleSaveAsItinerary = async () => {
    let token = localStorage.getItem('auth_token');
    if (!result || !user) {
      showError('Please log in to save itineraries');
      return;
    }

    // Ensure we have a valid token — try refreshing if missing/expired
    if (!token) {
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const parsed = JSON.parse(refreshToken);
          const resp = await api.post('/api/auth/refresh', { refreshToken: parsed });
          const newToken = resp.data.accessToken;
          if (newToken) {
            localStorage.setItem('auth_token', JSON.stringify(newToken));
            token = JSON.stringify(newToken);
          }
        }
      } catch {
        // refresh failed
      }
    }

    if (!token) {
      showError('Your session has expired. Please log in again to save itineraries.');
      return;
    }

    setSaving(true);
    try {
      const itinerary = await saveAiPlanAsItinerary(result, {
        origin_city: originCity,
        origin_country: originCountry || '',
        destination_city: destinationCity,
        destination_country: destinationCountry || '',
        departure_date: departureDate,
        return_date: returnDate || departureDate,
        passengers,
        budget: budget || undefined,
        cuisine: cuisine || undefined,
        travel_style: travelStyle || undefined,
        interests: interests || undefined,
        accommodation_preference: accommodationPref || undefined,
      });
      showSuccess('Itinerary saved! Redirecting...');
      setTimeout(() => navigate(`/itineraries/${itinerary.id}`), 500);
    } catch (err: any) {
      console.error('Failed to save itinerary:', err);
      showError(err.response?.data?.detail || 'Failed to save itinerary. Make sure you are logged in.');
    } finally {
      setSaving(false);
    }
  };

  // Parse itinerary for structured display
  const parsedDays = result?.itinerary_text ? parseItineraryNarrative(result.itinerary_text) : [];

  // Extract budget table from narrative
  const extractBudgetTable = (text: string) => {
    if (!text) return [];
    const rows: { category: string; cost: string }[] = [];
    const tableMatch = text.match(/\|.*Category.*Cost.*\|[\s\S]*?(?=\n\n|\n#|$)/i);
    if (tableMatch) {
      const lines = tableMatch[0].split('\n').filter(l => l.trim().startsWith('|'));
      for (const line of lines) {
        const cells = line.split('|').map(c => c.trim()).filter(Boolean);
        if (cells.length >= 2 && !/^[-:]+$/.test(cells[0]) && !/Category/i.test(cells[0])) {
          rows.push({ category: cells[0].replace(/\*\*/g, ''), cost: cells[1].replace(/\*\*/g, '') });
        }
      }
    }
    return rows;
  };

  const budgetRows = extractBudgetTable(result?.itinerary_text || '');

  const rec = result?.recommendation;
  const intel = result?.enhanced_data?.destination_intelligence;
  const intelError = result?.enhanced_data?._intel_error;

  // Use the budget table total if available (more accurate, includes all categories),
  // otherwise fall back to the recommendation's estimated cost
  const budgetTotal = budgetRows.find(r => /total/i.test(r.category))?.cost;
  const displayTotal = budgetTotal || (rec?.total_estimated_cost ? `$${rec.total_estimated_cost}` : 'N/A');

  // Compute trip date range string
  const formatDateRange = () => {
    if (!departureDate) return '';
    const opts: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric', year: 'numeric' };
    const d1 = new Date(departureDate + 'T12:00:00');
    const d2 = returnDate ? new Date(returnDate + 'T12:00:00') : d1;
    return `${d1.toLocaleDateString('en-US', opts)} - ${d2.toLocaleDateString('en-US', opts)}`;
  };

  const numNights = (() => {
    if (!departureDate || !returnDate) return 0;
    const d1 = new Date(departureDate);
    const d2 = new Date(returnDate);
    return Math.max(1, Math.ceil((d2.getTime() - d1.getTime()) / (1000 * 60 * 60 * 24)));
  })();

  return (
    <div className="min-h-screen">
      {/* Hero Header */}
      <div className="relative overflow-hidden bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-700 dark:from-blue-800 dark:via-indigo-800 dark:to-purple-900">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 -right-40 w-80 h-80 bg-white rounded-full blur-3xl"></div>
          <div className="absolute -bottom-20 -left-20 w-60 h-60 bg-purple-300 rounded-full blur-3xl"></div>
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
          <h1 className="text-2xl md:text-3xl font-bold text-white mb-2">
            AI Travel Planner
          </h1>
          <p className="text-blue-100 text-lg">
            Let our AI agents find and evaluate the best travel options for you
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6 relative z-10 pb-12">
      {/* Order Mode Switcher */}
      <div className="flex gap-2 mb-6">
        {[
          { mode: 'form' as OrderMode, icon: '📝', label: 'Form' },
          { mode: 'chat' as OrderMode, icon: '💬', label: 'Chat' },
          { mode: 'voice' as OrderMode, icon: '🎙️', label: 'Voice' },
        ].map(({ mode, icon, label }) => (
          <button
            key={mode}
            onClick={() => setOrderMode(mode)}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 ${
              orderMode === mode
                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/25'
                : 'bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm text-gray-700 dark:text-gray-300 border border-gray-200/60 dark:border-gray-700/50 hover:bg-white dark:hover:bg-gray-700 shadow-sm'
            }`}
          >
            {icon} {label}
          </button>
        ))}
      </div>

      {/* MODE 1: Form */}
      {orderMode === 'form' && (
        <Card variant="glass" className="mb-8">
          <div className="p-6 md:p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-lg">📝</div>
              <div>
                <h2 className="text-lg font-bold text-gray-900 dark:text-white">Travel Details</h2>
                <p className="text-xs text-gray-500 dark:text-gray-400">Fill in your trip preferences and let AI do the rest</p>
              </div>
            </div>
            <form onSubmit={handlePlan} className="space-y-5">
              {/* Origin & Destination with Autocomplete */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <AirportAutocomplete
                  label="From (Origin)"
                  value={originCity}
                  onChange={(val, airport) => {
                    setOriginCity(airport ? airport.city : val);
                    if (airport) setOriginCountry(airport.country);
                  }}
                  placeholder="Search city or airport..."
                  required
                />
                <AirportAutocomplete
                  label="To (Destination)"
                  value={destinationCity}
                  onChange={(val, airport) => {
                    setDestinationCity(airport ? airport.city : val);
                    if (airport) setDestinationCountry(airport.country);
                  }}
                  placeholder="Search city or airport..."
                  required
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <Input label="Departure Date" type="date" value={departureDate} onChange={(e) => setDepartureDate(e.target.value)} required />
                <Input label="Return Date (Optional)" type="date" value={returnDate} onChange={(e) => setReturnDate(e.target.value)} />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <Input label="Travelers" type="number" min="1" value={passengers} onChange={(e) => setPassengers(Number(e.target.value))} required />
                <Input label="Budget (USD, Optional)" type="number" value={budget} onChange={(e) => setBudget(e.target.value)} placeholder="e.g., 2000" />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1.5">Preferred Cuisine (Optional)</label>
                  <select value={cuisine} onChange={(e) => setCuisine(e.target.value)} className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow">
                    <option value="">Any Cuisine</option>
                    {['American','Italian','Mexican','Chinese','Japanese','Indian','Thai','French','Mediterranean','Seafood','Korean','Vietnamese'].map(c => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1.5">Travel Style (Optional)</label>
                  <select value={travelStyle} onChange={(e) => setTravelStyle(e.target.value)} className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow">
                    <option value="">Any Style</option>
                    {['Budget','Comfort','Luxury','Adventure','Cultural','Family','Romantic','Business'].map(s => (
                      <option key={s} value={s.toLowerCase()}>{s}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1.5">Accommodation (Optional)</label>
                  <select value={accommodationPref} onChange={(e) => setAccommodationPref(e.target.value)} className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow">
                    <option value="">Auto (Hotels + Rentals for 4+)</option>
                    <option value="hotel">Hotels Only</option>
                    <option value="rental">Vacation Rentals Only</option>
                    <option value="both">Both Hotels & Rentals</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1.5">Your Interests (Optional)</label>
                <textarea
                  value={interests}
                  onChange={(e) => setInterests(e.target.value)}
                  rows={3}
                  placeholder="Tell us what you enjoy: e.g., historical sites, museums, local street food, hiking, beach activities, nightlife, photography, art galleries, natural beauty, adventure sports..."
                  className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1.5">
                  AI will personalize your itinerary based on your interests.
                </p>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                AI will automatically find the nearest airports, best hotels, restaurants, and attractions based on your city.
              </p>
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold text-base shadow-lg shadow-blue-500/25 hover:shadow-xl hover:shadow-blue-500/30 transition-all duration-200 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    AI Agents Working...
                  </span>
                ) : '🤖 Plan My Trip with AI'}
              </button>
            </form>
          </div>
        </Card>
      )}

      {/* MODE 2: Chat */}
      {orderMode === 'chat' && (
        <div className="mb-8">
          <TravelChat onPlanReady={handleChatPlanReady} onParamsExtracted={setChatParams} />
        </div>
      )}

      {/* MODE 3: Voice */}
      {orderMode === 'voice' && (
        <div className="mb-8">
          <Card variant="glass" padding="none" className="overflow-hidden">
            <div className="relative bg-gradient-to-r from-purple-500/10 via-fuchsia-500/10 to-pink-500/10 dark:from-purple-500/20 dark:via-fuchsia-500/20 dark:to-pink-500/20 border-b border-purple-200/50 dark:border-purple-700/50">
              <div className="py-8 text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500 to-fuchsia-600 text-white text-3xl mb-4 shadow-lg shadow-purple-500/25">🎙️</div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">Voice-Powered Trip Planning</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 max-w-md mx-auto px-4">
                  Speak naturally to plan your trip. The AI will listen, understand your requirements, ask follow-up questions by voice, and create your itinerary.
                </p>
                <span className="inline-flex items-center gap-1.5 text-xs text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/30 px-3 py-1 rounded-full">
                  <span className="w-1.5 h-1.5 bg-purple-500 rounded-full animate-pulse"></span>
                  Web Speech API + OpenAI TTS
                </span>
              </div>
            </div>
          </Card>
          <div className="mt-4">
            <TravelChat onPlanReady={handleChatPlanReady} onParamsExtracted={setChatParams} initialVoiceEnabled={true} key="voice-chat" />
          </div>
        </div>
      )}

      {/* Smart Trip Preview — inline live insights (weather, safety, budget,
          crowds, "a day in your trip") as soon as a destination is entered.
          Deep-dive chips open specialty pages in new tabs so form entries
          on this page are never lost. */}
      {!loading && destinationCity && (
        <SmartTripPreview
          destination={destinationLabel}
          startDate={departureDate}
          endDate={returnDate}
          travelers={passengers}
        />
      )}

      {/* Loading State */}
      {loading && (
        <Card variant="glass">
          <div className="py-12 px-6">
            <Loading size="lg" text="AI agents are analyzing your request..." />
            <div className="mt-6 grid grid-cols-2 md:grid-cols-3 gap-3 max-w-lg mx-auto">
              {[
                { icon: '✈️', text: 'Searching flights' },
                { icon: '🏨', text: 'Finding hotels' },
                { icon: '🚗', text: 'Checking rentals' },
                { icon: '🍽️', text: 'Finding restaurants' },
                { icon: '💰', text: 'Optimizing budget' },
                { icon: '🎯', text: 'Compiling results' },
              ].map(({ icon, text }) => (
                <div key={text} className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 bg-white/60 dark:bg-gray-800/60 backdrop-blur-sm rounded-xl px-3 py-2.5 border border-gray-200/50 dark:border-gray-700/50">
                  <span className="animate-pulse">{icon}</span> {text}
                </div>
              ))}
            </div>
          </div>
        </Card>
      )}

      {/* ═══════════════════ RESULTS ═══════════════════ */}
      {result && result.success && (
        <div className="space-y-6">

          {/* ── Personalization Banner ── */}
          {result.personalization?.applied && (
            <div className="rounded-2xl bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-900/20 dark:to-teal-900/20 border border-emerald-200 dark:border-emerald-800/40 p-4 md:p-5">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div className="flex items-start gap-3">
                  <span className="text-2xl leading-none" aria-hidden>✨</span>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-bold text-emerald-900 dark:text-emerald-100 flex items-center gap-1.5">
                      Personalized for you
                      <span className="text-emerald-600 dark:text-emerald-400">✓</span>
                    </h3>
                    <p className="text-sm text-emerald-800/80 dark:text-emerald-200/80 mt-0.5">
                      This plan honors your Travel DNA, dietary needs, faith, and past trip signals.
                    </p>
                    {result.personalization.signals?.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {result.personalization.signals.slice(0, 6).map((sig: string, i: number) => (
                          <span
                            key={i}
                            className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-white/80 dark:bg-emerald-900/40 text-emerald-900 dark:text-emerald-100 border border-emerald-200 dark:border-emerald-700/50"
                          >
                            {sig}
                          </span>
                        ))}
                        {result.personalization.signals.length > 6 && (
                          <span className="text-xs text-emerald-700 dark:text-emerald-300 self-center">
                            +{result.personalization.signals.length - 6} more
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
                <a
                  href={ROUTES.TRAVEL_PROFILE}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-white dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-200 border border-emerald-300 dark:border-emerald-700/50 hover:bg-emerald-50 dark:hover:bg-emerald-900/60 transition-colors"
                  title="Opens in a new tab"
                >
                  Edit preferences
                  <span aria-hidden className="opacity-60">↗</span>
                </a>
              </div>
            </div>
          )}

          {/* Not-yet-personalized nudge for signed-in users with empty profiles */}
          {result.personalization && !result.personalization.applied && isAuthenticated && (
            <div className="rounded-2xl bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 border border-amber-200 dark:border-amber-800/40 p-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div className="flex items-start gap-3">
                  <span className="text-xl leading-none" aria-hidden>💡</span>
                  <p className="text-sm text-amber-900 dark:text-amber-100">
                    <span className="font-semibold">Want a more tailored plan?</span>{' '}
                    Set your Travel DNA, dietary needs, and faith preferences so future trips honor them.
                  </p>
                </div>
                <a
                  href={ROUTES.TRAVEL_PROFILE}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-white dark:bg-amber-900/40 text-amber-800 dark:text-amber-200 border border-amber-300 dark:border-amber-700/50 hover:bg-amber-50 dark:hover:bg-amber-900/60 transition-colors"
                >
                  Set up profile
                  <span aria-hidden className="opacity-60">↗</span>
                </a>
              </div>
            </div>
          )}

          {/* ── Trip Overview Banner ── */}
          <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-primary-600 via-primary-700 to-indigo-800 text-white p-4 md:p-6 lg:p-8 shadow-xl">
            <div className="absolute inset-0 opacity-10">
              <div className="absolute -right-20 -top-20 w-80 h-80 rounded-full bg-white/20"></div>
              <div className="absolute -left-10 -bottom-10 w-60 h-60 rounded-full bg-white/10"></div>
            </div>
            <div className="relative z-10">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                  <p className="text-primary-200 text-sm font-medium uppercase tracking-wider mb-1">AI-Planned Trip</p>
                  <h2 className="text-2xl md:text-3xl font-bold">
                    {originLabel || 'Origin'} &rarr; {destinationLabel || 'Destination'}
                  </h2>
                  <p className="text-primary-100 mt-1">{formatDateRange()}{passengers > 1 ? ` · ${passengers} travelers` : ''}</p>
                </div>
                <div className="flex gap-4 flex-wrap">
                  {/* Save Button in Banner */}
                  <button
                    onClick={handleSaveAsItinerary}
                    disabled={saving || !isAuthenticated}
                    className="px-5 py-2.5 bg-white/20 hover:bg-white/30 backdrop-blur rounded-xl text-sm font-medium transition-all border border-white/30 disabled:opacity-50"
                  >
                    {saving ? 'Saving...' : 'Save as Itinerary'}
                  </button>
                </div>
              </div>

              {/* Key Stats Row */}
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2 md:gap-3 mt-4 md:mt-6">
                {[
                  { label: 'Est. Total', value: displayTotal, accent: true },
                  { label: 'Flights', value: rec?.summary?.flights_found || 0 },
                  { label: 'Hotels', value: rec?.summary?.hotels_found || 0 },
                  { label: 'Cars', value: rec?.summary?.cars_found || 0 },
                  { label: 'Restaurants', value: rec?.summary?.restaurants_found || 0 },
                ].map(({ label, value, accent }) => (
                  <div key={label} className={`rounded-xl p-3 ${accent ? 'bg-white/20 backdrop-blur' : 'bg-white/10'}`}>
                    <p className="text-xs text-primary-200">{label}</p>
                    <p className={`text-xl font-bold ${accent ? 'text-white' : 'text-primary-100'}`}>{value}</p>
                  </div>
                ))}
              </div>
              {!isAuthenticated && (
                <p className="text-xs text-primary-200 mt-3">Sign in to save itineraries</p>
              )}
            </div>
          </div>

          {/* ── Tab Navigation ── */}
          <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1">
            {TAB_CONFIG.map(({ key, label, icon }) => {
              // Show badge count
              let count: number | null = null;
              if (key === 'flights') count = rec?.summary?.flights_found || 0;
              if (key === 'hotels') count = rec?.summary?.hotels_found || 0;
              if (key === 'cars') count = rec?.summary?.cars_found || 0;
              if (key === 'dining') count = rec?.summary?.restaurants_found || 0;
              if (key === 'itinerary') count = parsedDays.length || null;

              return (
                <button
                  key={key}
                  onClick={() => setActiveTab(key)}
                  className={`flex items-center gap-1.5 px-4 py-2.5 rounded-xl font-medium text-sm whitespace-nowrap transition-all duration-200 ${
                    activeTab === key
                      ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/25'
                      : 'bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm text-gray-700 dark:text-gray-300 hover:bg-white dark:hover:bg-gray-700 shadow-sm border border-gray-200/60 dark:border-gray-700/50'
                  }`}
                >
                  <span>{icon}</span>
                  {label}
                  {count !== null && count > 0 && (
                    <span className={`ml-1 px-1.5 py-0.5 rounded-full text-xs font-semibold ${
                      activeTab === key
                        ? 'bg-white/20 text-white'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                    }`}>
                      {count}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* ══════ TAB: ITINERARY ══════ */}
          {activeTab === 'itinerary' && (
            <div className="space-y-4">
              {/* Budget Summary Table */}
              {budgetRows.length > 0 && (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                  <div className="px-5 py-3 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                      💰 Budget Summary
                    </h3>
                  </div>
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-100 dark:border-gray-700">
                        <th className="text-left px-3 md:px-5 py-2.5 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Category</th>
                        <th className="text-right px-3 md:px-5 py-2.5 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Cost</th>
                      </tr>
                    </thead>
                    <tbody>
                      {budgetRows.map((row, i) => {
                        const isTotal = /total/i.test(row.category);
                        const isBudget = /budget/i.test(row.category);
                        const isRemaining = /remaining|over/i.test(row.category);
                        return (
                          <tr key={i} className={`border-b border-gray-50 dark:border-gray-800 ${isTotal || isBudget ? 'bg-gray-50 dark:bg-gray-900' : ''}`}>
                            <td className={`px-3 md:px-5 py-2.5 ${isTotal || isBudget ? 'font-semibold text-gray-900 dark:text-white' : 'text-gray-700 dark:text-gray-300'}`}>
                              {row.category}
                            </td>
                            <td className={`px-3 md:px-5 py-2.5 text-right font-medium ${
                              isTotal ? 'text-primary-600 dark:text-primary-400 text-base font-bold' :
                              isRemaining ? (row.cost.includes('-') ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400') :
                              'text-gray-900 dark:text-white'
                            }`}>
                              {row.cost}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Day-by-Day Timeline */}
              {parsedDays.length > 0 ? (
                <div className="space-y-4">
                  {parsedDays.map((day) => {
                    const isExpanded = expandedDay === day.dayNumber;
                    const dayTotal = day.activities.reduce((sum, a) => sum + (a.estimatedCost || 0), 0);
                    // Calculate the actual date for this day
                    const dayDate = departureDate ? (() => {
                      const d = new Date(departureDate);
                      d.setDate(d.getDate() + day.dayNumber - 1);
                      return d.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric', year: 'numeric' });
                    })() : '';
                    const isFirstDay = day.dayNumber === 1;
                    const isLastDay = day.dayNumber === parsedDays.length;

                    return (
                      <div key={day.dayNumber} className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden transition-all">
                        {/* Day Header */}
                        <button
                          onClick={() => setExpandedDay(isExpanded ? null : day.dayNumber)}
                          className="w-full flex items-center justify-between px-4 md:px-6 py-4 md:py-5 text-left hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
                        >
                          <div className="flex items-center gap-3 md:gap-4">
                            <div className={`w-12 h-12 md:w-14 md:h-14 rounded-2xl flex flex-col items-center justify-center font-bold text-xs md:text-sm ${
                              isFirstDay ? 'bg-green-100 dark:bg-green-900/50 text-green-700 dark:text-green-300' :
                              isLastDay ? 'bg-red-100 dark:bg-red-900/50 text-red-700 dark:text-red-300' :
                              'bg-primary-100 dark:bg-primary-900/50 text-primary-700 dark:text-primary-300'
                            }`}>
                              <span className="text-[10px] uppercase tracking-wide opacity-70">Day</span>
                              <span className="text-lg md:text-xl font-extrabold leading-none">{day.dayNumber}</span>
                            </div>
                            <div>
                              <h3 className="font-bold text-gray-900 dark:text-white text-sm md:text-base">
                                {day.title}
                                {isFirstDay && <span className="ml-2 text-xs font-medium text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/30 px-2 py-0.5 rounded-full">Arrival</span>}
                                {isLastDay && <span className="ml-2 text-xs font-medium text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/30 px-2 py-0.5 rounded-full">Departure</span>}
                              </h3>
                              <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                                {dayDate && <span className="text-xs text-gray-500 dark:text-gray-400">{dayDate}</span>}
                                <span className="text-xs text-gray-400 dark:text-gray-500">|</span>
                                <span className="text-xs text-gray-500 dark:text-gray-400">
                                  {day.activities.length} activit{day.activities.length === 1 ? 'y' : 'ies'}
                                </span>
                                {dayTotal > 0 && (
                                  <>
                                    <span className="text-xs text-gray-400 dark:text-gray-500">|</span>
                                    <span className="text-xs font-semibold text-primary-600 dark:text-primary-400">~${dayTotal.toFixed(0)}</span>
                                  </>
                                )}
                              </div>
                            </div>
                          </div>
                          <svg className={`w-5 h-5 text-gray-400 transition-transform flex-shrink-0 ${isExpanded ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        </button>

                        {/* Day Activities - Timeline Layout */}
                        {isExpanded && (
                          <div className="border-t border-gray-100 dark:border-gray-700">
                            <div className="relative px-4 md:px-6 py-4 md:py-5">
                              {/* Vertical timeline line */}
                              <div className="absolute left-[2.15rem] md:left-[2.65rem] top-4 bottom-4 w-px bg-gray-200 dark:bg-gray-700" />

                              <div className="space-y-1">
                                {day.activities.map((activity, idx) => {
                                  const config = ITEM_TYPE_CONFIG[activity.itemType] || ITEM_TYPE_CONFIG.activity;
                                  // Check if this is a sub-item (directions/tips starting with arrow)
                                  const isSubItem = activity.title.startsWith('→') || activity.title.startsWith('Getting there') || activity.title.startsWith('Tip:');

                                  if (isSubItem) {
                                    return (
                                      <div key={idx} className="ml-10 md:ml-12 pl-4 py-1">
                                        <p className="text-xs text-gray-500 dark:text-gray-400 italic">{activity.title}</p>
                                      </div>
                                    );
                                  }

                                  return (
                                    <div key={idx} className="flex items-start gap-3 md:gap-4 py-2 group">
                                      {/* Time Column */}
                                      <div className="flex-shrink-0 w-14 md:w-16 text-right pt-2.5">
                                        {activity.time ? (
                                          <span className="text-xs font-bold text-gray-900 dark:text-white tracking-tight">
                                            {activity.time}
                                          </span>
                                        ) : (
                                          <span className="text-xs text-gray-400">--:--</span>
                                        )}
                                      </div>

                                      {/* Timeline dot */}
                                      <div className="flex-shrink-0 relative z-10 mt-2">
                                        <div className={`w-7 h-7 md:w-8 md:h-8 rounded-full flex items-center justify-center text-sm shadow-sm border-2 border-white dark:border-gray-800 ${
                                          activity.itemType === 'flight' ? 'bg-blue-100 dark:bg-blue-900' :
                                          activity.itemType === 'hotel' ? 'bg-purple-100 dark:bg-purple-900' :
                                          activity.itemType === 'restaurant' ? 'bg-orange-100 dark:bg-orange-900' :
                                          activity.itemType === 'transport' ? 'bg-cyan-100 dark:bg-cyan-900' :
                                          activity.itemType === 'attraction' ? 'bg-emerald-100 dark:bg-emerald-900' :
                                          'bg-indigo-100 dark:bg-indigo-900'
                                        }`}>
                                          {config.icon}
                                        </div>
                                      </div>

                                      {/* Activity Card */}
                                      <div className={`flex-1 min-w-0 rounded-xl p-3 md:p-4 border ${config.bg} group-hover:shadow-md transition-shadow`}>
                                        <div className="flex items-start justify-between gap-2">
                                          <p className={`text-sm md:text-base font-medium ${config.color} leading-snug`}>
                                            {activity.title}
                                          </p>
                                          {activity.estimatedCost !== undefined && activity.estimatedCost > 0 && (
                                            <span className="flex-shrink-0 text-xs font-bold text-gray-800 dark:text-gray-200 bg-white/80 dark:bg-gray-700/80 px-2.5 py-1 rounded-lg shadow-sm">
                                              ${activity.estimatedCost}
                                            </span>
                                          )}
                                        </div>
                                        {(activity as any).url && (
                                          <div className="mt-2">
                                            <a
                                              href={(activity as any).url}
                                              target="_blank"
                                              rel="noopener noreferrer"
                                              onClick={(e) => e.stopPropagation()}
                                              className="inline-flex items-center gap-1 text-[11px] font-semibold text-blue-600 dark:text-blue-400 hover:underline"
                                              title="Opens the partner booking site in a new tab"
                                            >
                                              🔗 Book / View on Partner Site
                                            </a>
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>

                              {/* Day Total Footer */}
                              {dayTotal > 0 && (
                                <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700 ml-10 md:ml-12">
                                  <div className="flex items-center justify-between">
                                    <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Day {day.dayNumber} Total</span>
                                    <span className="text-sm font-bold text-primary-600 dark:text-primary-400">${dayTotal.toFixed(0)}</span>
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : result.itinerary_text ? (
                /* Fallback: raw narrative if parsing didn't extract days */
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm p-6">
                  <div
                    className="prose prose-sm dark:prose-invert max-w-none prose-headings:text-gray-900 dark:prose-headings:text-white prose-h2:text-lg prose-h2:font-bold prose-h2:mt-6 prose-h2:mb-2 prose-h3:text-base prose-h3:font-semibold prose-p:text-gray-700 dark:prose-p:text-gray-300 prose-p:my-1 prose-li:text-gray-700 dark:prose-li:text-gray-300 prose-strong:text-gray-900 dark:prose-strong:text-white prose-ul:my-1 prose-ol:my-1"
                    dangerouslySetInnerHTML={{
                      __html: (() => {
                        let html = result.itinerary_text;
                        html = html.replace(
                          /(?:^\|.+\|$\n?)+/gm,
                          (tableBlock: string) => {
                            const rows = tableBlock.trim().split('\n').filter((r: string) => r.trim());
                            if (rows.length < 2) return tableBlock;
                            let table = '<table class="w-full text-sm border-collapse my-3">';
                            rows.forEach((row: string, i: number) => {
                              if (/^\|[\s\-:|]+\|$/.test(row.trim())) return;
                              const cells = row.split('|').filter((c: string, ci: number, arr: string[]) => ci > 0 && ci < arr.length - 1);
                              const tag = i === 0 ? 'th' : 'td';
                              const cls = i === 0 ? 'bg-gray-100 dark:bg-gray-800 font-semibold' : '';
                              table += `<tr class="${cls}">`;
                              cells.forEach((cell: string) => {
                                table += `<${tag} class="border border-gray-200 dark:border-gray-700 px-3 py-1.5">${cell.trim()}</${tag}>`;
                              });
                              table += '</tr>';
                            });
                            table += '</table>';
                            return table;
                          }
                        );
                        html = html
                          .replace(/^### (.*$)/gm, '<h3>$1</h3>')
                          .replace(/^## (.*$)/gm, '<h2>$1</h2>')
                          .replace(/^# (.*$)/gm, '<h1>$1</h1>')
                          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                          .replace(/\*(.*?)\*/g, '<em>$1</em>')
                          .replace(/^- (.*$)/gm, '<li>$1</li>')
                          .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
                          .replace(/\n\n/g, '</p><p>')
                          .replace(/\n/g, '<br/>');
                        return html;
                      })()
                    }}
                  />
                </div>
              ) : null}
            </div>
          )}

          {/* ══════ TAB: FLIGHTS ══════ */}
          {activeTab === 'flights' && (
            <div className="space-y-6">
              {/* Hub Route Notice */}
              {result?.flights?.hub_route && result?.flights?.transit_notes?.length > 0 && (
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
                  <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-200 mb-2">Connecting Route via Hub Airport</h3>
                  <p className="text-sm text-blue-700 dark:text-blue-300 mb-2">
                    No direct international flights found to {destinationLabel}. Showing flights to the nearest major hub airport.
                    You will need to arrange onward transport from the hub to your final destination.
                  </p>
                  <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1.5">
                    {result.flights.transit_notes.map((note: string, i: number) => (
                      <li key={i} className="flex gap-2 items-start"><span className="mt-0.5">→</span> <span>{note}</span></li>
                    ))}
                  </ul>
                </div>
              )}
              {/* Recommended Flight */}
              {rec?.recommended_flight && (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                  <div className="px-5 py-3 bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/20 border-b border-blue-200 dark:border-blue-800 flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-200 flex items-center gap-2">
                      <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                      Top Pick - Best Value Flight
                    </h3>
                    <span className="text-2xl font-bold text-blue-700 dark:text-blue-300">${rec.recommended_flight.price}<span className="text-sm font-normal text-blue-500 dark:text-blue-400 ml-1">/person</span></span>
                  </div>
                  <div className="p-5">
                    {/* Airline Header */}
                    <div className="flex items-center gap-3 mb-5">
                      {rec.recommended_flight.airline_logo && (
                        <img src={rec.recommended_flight.airline_logo} alt="" className="h-10 w-10 object-contain rounded" />
                      )}
                      <div>
                        <p className="font-semibold text-gray-900 dark:text-white text-lg">{rec.recommended_flight.airline}</p>
                        {rec.recommended_flight.flight_number && (
                          <p className="text-sm text-gray-500">Flight {rec.recommended_flight.flight_number}</p>
                        )}
                      </div>
                    </div>
                    {/* Route Visual */}
                    <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2 md:gap-4 p-3 md:p-4 bg-gray-50 dark:bg-gray-900 rounded-xl mb-4 md:mb-5">
                      <div>
                        <p className="text-lg md:text-2xl font-bold text-gray-900 dark:text-white">
                          {rec.recommended_flight.departure_time?.split(' ')[1] || rec.recommended_flight.departure_time}
                        </p>
                        <p className="text-sm md:text-lg font-semibold text-gray-700 dark:text-gray-300">{rec.recommended_flight.departure_airport_code}</p>
                        <p className="text-xs text-gray-500 mt-0.5">{rec.recommended_flight.departure_airport}</p>
                      </div>
                      <div className="text-center px-1 md:px-4">
                        <p className="text-xs text-gray-500 mb-2">
                          {rec.recommended_flight.duration ? `${Math.floor(rec.recommended_flight.duration / 60)}h ${rec.recommended_flight.duration % 60}m` : ''}
                        </p>
                        <div className="flex items-center">
                          <div className="w-2 h-2 rounded-full bg-primary-500"></div>
                          <div className="h-px bg-gray-300 dark:bg-gray-600 flex-1 mx-1"></div>
                          <span className="text-base">✈️</span>
                          <div className="h-px bg-gray-300 dark:bg-gray-600 flex-1 mx-1"></div>
                          <div className="w-2 h-2 rounded-full bg-primary-500"></div>
                        </div>
                        <p className="text-xs text-gray-500 mt-2 font-medium">
                          {rec.recommended_flight.stops === 0 ? 'Nonstop' : `${rec.recommended_flight.stops} stop${rec.recommended_flight.stops > 1 ? 's' : ''}`}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg md:text-2xl font-bold text-gray-900 dark:text-white">
                          {rec.recommended_flight.arrival_time?.split(' ')[1] || rec.recommended_flight.arrival_time}
                        </p>
                        <p className="text-sm md:text-lg font-semibold text-gray-700 dark:text-gray-300">{rec.recommended_flight.arrival_airport_code}</p>
                        <p className="text-xs text-gray-500 mt-0.5">{rec.recommended_flight.arrival_airport}</p>
                      </div>
                    </div>
                    {/* Flight Details Grid */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      {[
                        rec.recommended_flight.aircraft && { label: 'Aircraft', value: rec.recommended_flight.aircraft },
                        rec.recommended_flight.travel_class && { label: 'Class', value: rec.recommended_flight.travel_class },
                        rec.recommended_flight.legroom && { label: 'Legroom', value: rec.recommended_flight.legroom },
                        rec.recommended_flight.carbon_emissions?.this_flight && { label: 'CO2', value: `${rec.recommended_flight.carbon_emissions.this_flight} kg` },
                      ].filter(Boolean).map((item: any, idx) => (
                        <div key={idx} className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3">
                          <p className="text-xs text-gray-500 uppercase tracking-wider">{item.label}</p>
                          <p className="text-sm font-semibold text-gray-900 dark:text-white mt-0.5">{item.value}</p>
                        </div>
                      ))}
                    </div>
                    {/* Hub Route Note on recommended flight */}
                    {result?.flights?.hub_route && (
                      <div className="mt-4 p-3 rounded-lg text-sm bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300">
                        This flight goes to the nearest hub airport. Onward transport to {destinationLabel} will be needed.
                      </div>
                    )}
                    {/* Budget Status */}
                    {rec.recommended_flight.goal_score !== undefined && (
                      <div className={`mt-4 p-3 rounded-lg text-sm ${
                        rec.recommended_flight.budget_status === 'within budget'
                          ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300'
                          : 'bg-orange-50 dark:bg-orange-900/20 text-orange-700 dark:text-orange-300'
                      }`}>
                        {rec.recommended_flight.budget_status === 'within budget'
                          ? `Within budget - saves $${rec.recommended_flight.savings}`
                          : `Over budget by $${rec.recommended_flight.budget_difference}`}
                        <span className="ml-3 text-xs opacity-75">Goal Score: {rec.recommended_flight.goal_score > 0 ? '+' : ''}{rec.recommended_flight.goal_score}</span>
                      </div>
                    )}
                    {/* Partner booking link */}
                    {getBookingUrl(rec.recommended_flight) && (
                      <div className="mt-4 flex justify-end">
                        <BookingLinkButton item={rec.recommended_flight} tone="blue" label="Book on Partner Site" />
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Alternative Flights Table */}
              {result.flights?.flights && result.flights.flights.length > 1 && (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                  <div className="px-5 py-3 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Alternative Flights</h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
                          <th className="text-left px-3 md:px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Airline</th>
                          <th className="text-left px-2 md:px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Route</th>
                          <th className="hidden sm:table-cell text-center px-2 md:px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Depart</th>
                          <th className="hidden sm:table-cell text-center px-2 md:px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Arrive</th>
                          <th className="text-center px-2 md:px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Stops</th>
                          <th className="hidden md:table-cell text-center px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Duration</th>
                          <th className="text-right px-3 md:px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Price/Person</th>
                          <th className="text-center px-3 md:px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Book</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.flights.flights.slice(1, 8).map((f: any, idx: number) => (
                          <tr key={idx} className="border-b border-gray-50 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors">
                            <td className="px-3 md:px-4 py-2.5">
                              <div className="flex items-center gap-2">
                                {f.airline_logo && <img src={f.airline_logo} alt="" className="h-4 w-4 md:h-5 md:w-5 object-contain" />}
                                <span className="font-medium text-gray-900 dark:text-white text-xs md:text-sm">{f.airline}</span>
                              </div>
                            </td>
                            <td className="px-2 md:px-4 py-2.5 text-gray-600 dark:text-gray-400 text-xs md:text-sm">{f.departure_airport_code} → {f.arrival_airport_code}</td>
                            <td className="hidden sm:table-cell px-2 md:px-4 py-2.5 text-center text-gray-900 dark:text-white font-medium text-xs md:text-sm">{f.departure_time?.split(' ')[1] || f.departure_time}</td>
                            <td className="hidden sm:table-cell px-2 md:px-4 py-2.5 text-center text-gray-900 dark:text-white font-medium text-xs md:text-sm">{f.arrival_time?.split(' ')[1] || f.arrival_time}</td>
                            <td className="px-2 md:px-4 py-2.5 text-center">
                              <span className={`px-1.5 md:px-2 py-0.5 rounded-full text-xs font-medium ${f.stops === 0 ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300' : 'bg-yellow-100 dark:bg-yellow-900 text-yellow-700 dark:text-yellow-300'}`}>
                                {f.stops === 0 ? 'Nonstop' : `${f.stops} stop${f.stops > 1 ? 's' : ''}`}
                              </span>
                            </td>
                            <td className="hidden md:table-cell px-4 py-2.5 text-center text-gray-600 dark:text-gray-400">
                              {f.duration ? `${Math.floor(f.duration / 60)}h ${f.duration % 60}m` : '-'}
                            </td>
                            <td className="px-3 md:px-4 py-2.5 text-right font-bold text-primary-600 dark:text-primary-400 text-xs md:text-sm">${f.price}</td>
                            <td className="px-3 md:px-4 py-2.5 text-center">
                              <BookingLinkButton item={f} tone="blue" label="Book" size="sm" />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {!rec?.recommended_flight && (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 md:p-8 text-center text-gray-500">
                  <p className="text-lg">No flight data available</p>
                  <p className="text-sm mt-1">Try adjusting your search parameters or dates</p>
                  {result?._search_debug && (
                    <p className="text-xs mt-3 text-gray-400">
                      Searched: {result._search_debug.resolved_origin} → {result._search_debug.resolved_destination}
                      {result._search_debug.hub_destination && result._search_debug.hub_destination !== result._search_debug.resolved_destination && (
                        <span> (also tried via hub: {result._search_debug.hub_destination})</span>
                      )}
                    </p>
                  )}
                </div>
              )}
            </div>
          )}

          {/* ══════ TAB: HOTELS ══════ */}
          {activeTab === 'hotels' && (
            <div className="space-y-6">
              {/* Fallback city notice */}
              {result?.hotels?.fallback_city && (
                <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl p-4">
                  <p className="text-sm text-amber-800 dark:text-amber-200">
                    <span className="font-semibold">Note:</span> No hotels found in {result.hotels.original_city || destinationLabel}.
                    Showing hotels in nearby <span className="font-semibold">{result.hotels.fallback_city}</span> instead.
                  </p>
                </div>
              )}
              {rec?.recommended_hotel && (() => {
                const h = rec.recommended_hotel;
                return (
                  <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                    <div className="px-5 py-3 bg-gradient-to-r from-green-50 to-emerald-100 dark:from-green-900/30 dark:to-emerald-800/20 border-b border-green-200 dark:border-green-800 flex items-center justify-between">
                      <h3 className="text-sm font-semibold text-green-900 dark:text-green-200 flex items-center gap-2">
                        <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                        Top Pick - Best Value Hotel
                      </h3>
                      <div className="text-right">
                        {(h.price || h.price_per_night) ? (
                          <>
                            <span className="text-2xl font-bold text-green-700 dark:text-green-300">${h.price || h.price_per_night}</span>
                            <span className="text-sm text-green-600 dark:text-green-400 ml-1">/night</span>
                          </>
                        ) : (
                          <span className="text-sm font-medium text-gray-500 dark:text-gray-400">Price on request</span>
                        )}
                      </div>
                    </div>
                    <div className="p-5">
                      <div className="flex flex-col md:flex-row gap-5">
                        {/* Hotel Image */}
                        {h.images?.[0] && (
                          <img src={h.images[0]} alt={h.name || h.hotel_name} className="w-full md:w-72 h-52 object-cover rounded-xl shadow-sm" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                        )}
                        <div className="flex-1 space-y-4">
                          <div>
                            <h3 className="text-xl font-bold text-gray-900 dark:text-white">{h.name || h.hotel_name}</h3>
                            <div className="flex items-center gap-2 mt-1">
                              <span className="text-yellow-500">{'⭐'.repeat(Math.round(h.stars || h.star_rating || 0))}</span>
                              {h.guest_rating > 0 && (
                                <span className="text-sm text-gray-500">({h.guest_rating} guest rating)</span>
                              )}
                            </div>
                          </div>
                          {/* Info Grid */}
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                            {[
                              h.check_in_time && { label: 'Check-in', value: h.check_in_time },
                              h.check_out_time && { label: 'Check-out', value: h.check_out_time },
                              h.distance_from_center && { label: 'Location', value: h.distance_from_center },
                              numNights > 0 && { label: 'Total Stay', value: `$${((h.price || h.price_per_night) * numNights).toFixed(0)} (${numNights} nights)` },
                            ].filter(Boolean).map((item: any, idx) => (
                              <div key={idx} className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3">
                                <p className="text-xs text-gray-500 uppercase tracking-wider">{item.label}</p>
                                <p className="text-sm font-semibold text-gray-900 dark:text-white mt-0.5">{item.value}</p>
                              </div>
                            ))}
                          </div>
                          {h.address && (
                            <p className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-1">
                              <span className="flex-shrink-0">📍</span> {h.address}
                            </p>
                          )}
                          {h.amenities && h.amenities.length > 0 && (
                            <div className="flex flex-wrap gap-1.5">
                              {h.amenities.slice(0, 10).map((a: string, idx: number) => (
                                <span key={idx} className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-2.5 py-1 rounded-full">{a}</span>
                              ))}
                              {h.amenities.length > 10 && <span className="text-xs text-gray-500 px-2 py-1">+{h.amenities.length - 10} more</span>}
                            </div>
                          )}
                          {h.recommendation && (
                            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 text-sm text-blue-700 dark:text-blue-300">
                              {h.recommendation}
                            </div>
                          )}
                          {getBookingUrl(h) && (
                            <div className="flex justify-end">
                              <BookingLinkButton item={h} tone="green" label="Visit / Book Direct" />
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* Alternative Hotels Table */}
              {rec?.top_5_hotels && rec.top_5_hotels.length > 1 && (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                  <div className="px-5 py-3 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Alternative Hotels</h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
                          <th className="text-left px-3 md:px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Hotel</th>
                          <th className="text-center px-2 md:px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Stars</th>
                          <th className="hidden md:table-cell text-center px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Rating</th>
                          <th className="hidden md:table-cell text-center px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Score</th>
                          <th className="text-right px-2 md:px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Price/Nt</th>
                          <th className="text-right px-3 md:px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Total</th>
                          <th className="text-center px-3 md:px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Book</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rec.top_5_hotels.slice(1, 8).map((h: any, idx: number) => (
                          <tr key={idx} className="border-b border-gray-50 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors">
                            <td className="px-3 md:px-4 py-2.5">
                              <div className="flex items-center gap-2 md:gap-3">
                                {h.images?.[0] ? (
                                  <img src={h.images[0]} alt="" className="hidden sm:block w-10 h-10 md:w-12 md:h-12 rounded-lg object-cover flex-shrink-0" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                                ) : (
                                  <div className="hidden sm:flex w-10 h-10 md:w-12 md:h-12 rounded-lg bg-gray-100 dark:bg-gray-700 items-center justify-center text-base md:text-lg flex-shrink-0">🏨</div>
                                )}
                                <span className="font-medium text-gray-900 dark:text-white text-xs md:text-sm">{h.name || h.hotel_name}</span>
                              </div>
                            </td>
                            <td className="px-2 md:px-4 py-2.5 text-center text-yellow-500 text-xs">{'⭐'.repeat(Math.min(Math.round(h.stars || h.star_rating || 0), 5))}</td>
                            <td className="hidden md:table-cell px-4 py-2.5 text-center text-gray-700 dark:text-gray-300">{h.guest_rating || '-'}</td>
                            <td className="hidden md:table-cell px-4 py-2.5 text-center">
                              <span className="px-2 py-0.5 bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-full text-xs font-medium">
                                {h.utility_score || h.combined_utility_score || '-'}
                              </span>
                            </td>
                            <td className="px-2 md:px-4 py-2.5 text-right font-bold text-primary-600 dark:text-primary-400 text-xs md:text-sm">
                              {(h.price || h.price_per_night) ? `$${h.price || h.price_per_night}` : 'N/A'}
                            </td>
                            <td className="px-3 md:px-4 py-2.5 text-right text-gray-600 dark:text-gray-400 text-xs md:text-sm">
                              {(h.price || h.price_per_night) && numNights > 0 ? `$${((h.price || h.price_per_night) * numNights).toFixed(0)}` : '-'}
                            </td>
                            <td className="px-3 md:px-4 py-2.5 text-center">
                              <BookingLinkButton item={h} tone="green" label="Book" size="sm" />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {!rec?.recommended_hotel && (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 md:p-8 text-center text-gray-500">
                  <p className="text-lg">No hotel data available</p>
                  <p className="text-sm mt-1">Hotels at this destination don't have current pricing data</p>
                  {result?.hotels?.fallback_city && (
                    <p className="text-xs mt-2 text-gray-400">Also searched nearby: {result.hotels.fallback_city}</p>
                  )}
                </div>
              )}
            </div>
          )}

          {/* ══════ TAB: RENTALS ══════ */}
          {activeTab === 'rentals' && (
            <div className="space-y-6">
              {rec?.recommended_rental && (() => {
                const r = rec.recommended_rental;
                return (
                  <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                    <div className="px-5 py-3 bg-gradient-to-r from-teal-50 to-cyan-100 dark:from-teal-900/30 dark:to-cyan-800/20 border-b border-teal-200 dark:border-teal-800 flex items-center justify-between">
                      <h3 className="text-sm font-semibold text-teal-900 dark:text-teal-200 flex items-center gap-2">
                        <span className="w-2 h-2 bg-teal-500 rounded-full"></span>
                        Top Pick - Best Value Rental
                      </h3>
                      <div className="text-right">
                        {(r.price || r.price_per_night) ? (
                          <>
                            <span className="text-2xl font-bold text-teal-700 dark:text-teal-300">${r.price || r.price_per_night}</span>
                            <span className="text-sm text-teal-600 dark:text-teal-400 ml-1">/night</span>
                          </>
                        ) : (
                          <span className="text-sm font-medium text-gray-500 dark:text-gray-400">Price on request</span>
                        )}
                      </div>
                    </div>
                    <div className="p-5">
                      <h3 className="text-xl font-bold text-gray-900 dark:text-white">{r.name || r.hotel_name}</h3>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
                        {[
                          r.bedrooms && { label: 'Bedrooms', value: r.bedrooms },
                          r.max_guests && { label: 'Max Guests', value: r.max_guests },
                          r.cleaning_fee && { label: 'Cleaning Fee', value: `$${r.cleaning_fee}` },
                          numNights > 0 && (r.price || r.price_per_night) && { label: 'Total Stay', value: `$${((r.price || r.price_per_night) * numNights + (r.cleaning_fee || 0)).toFixed(0)} (${numNights} nights)` },
                        ].filter(Boolean).map((item: any, idx) => (
                          <div key={idx} className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3">
                            <p className="text-xs text-gray-500 uppercase tracking-wider">{item.label}</p>
                            <p className="text-sm font-semibold text-gray-900 dark:text-white mt-0.5">{item.value}</p>
                          </div>
                        ))}
                      </div>
                      {r.amenities && r.amenities.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mt-4">
                          {r.amenities.slice(0, 10).map((a: string, idx: number) => (
                            <span key={idx} className="text-xs bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300 px-2.5 py-1 rounded-full">{a}</span>
                          ))}
                        </div>
                      )}
                      {getBookingUrl(r) && (
                        <div className="flex justify-end mt-4">
                          <BookingLinkButton item={r} tone="teal" label="View Listing" />
                        </div>
                      )}
                    </div>
                  </div>
                );
              })()}
              {/* Other rental results */}
              {(() => {
                const allRentals = result?.rentals?.rentals || result?.recommendation?.top_rentals || [];
                return allRentals.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {allRentals.map((r: any, idx: number) => (
                      <div key={idx} className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm p-4 hover:shadow-md transition-shadow">
                        <div className="flex items-start gap-3">
                          {r.images?.[0] && (
                            <img src={r.images[0]} alt={r.name} className="w-24 h-24 object-cover rounded-lg flex-shrink-0" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                          )}
                          <div className="flex-1 min-w-0">
                            <h4 className="font-semibold text-gray-900 dark:text-white truncate">{r.name || r.hotel_name}</h4>
                            {r.type && <p className="text-xs text-teal-600 dark:text-teal-400 mt-0.5">{r.type}</p>}
                            <div className="flex items-center gap-3 mt-2 text-sm">
                              {(r.price || r.price_per_night) && (
                                <span className="font-bold text-teal-700 dark:text-teal-300">${r.price || r.price_per_night}/night</span>
                              )}
                              {r.guest_rating > 0 && (
                                <span className="text-gray-500">{r.guest_rating} rating</span>
                              )}
                            </div>
                            {getBookingUrl(r) && (
                              <div className="mt-3">
                                <BookingLinkButton item={r} tone="teal" label="View Listing" size="sm" />
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                    <p className="text-5xl mb-3">🏡</p>
                    <p className="font-medium">No vacation rental results</p>
                    <p className="text-sm mt-1">Try setting Accommodation to "Vacation Rentals Only" or "Both" with 4+ travelers</p>
                  </div>
                );
              })()}
            </div>
          )}

          {/* ══════ TAB: CARS ══════ */}
          {activeTab === 'cars' && (
            <div className="space-y-6">
              {rec?.recommended_car && (() => {
                const c = rec.recommended_car;
                return (
                  <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                    <div className="px-5 py-3 bg-gradient-to-r from-orange-50 to-amber-100 dark:from-orange-900/30 dark:to-amber-800/20 border-b border-orange-200 dark:border-orange-800 flex items-center justify-between">
                      <h3 className="text-sm font-semibold text-orange-900 dark:text-orange-200 flex items-center gap-2">
                        <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                        Top Pick - Best Value Car Rental
                      </h3>
                      <div className="text-right">
                        <span className="text-2xl font-bold text-orange-700 dark:text-orange-300">${c.price_per_day}</span>
                        <span className="text-sm text-orange-600 dark:text-orange-400 ml-1">/day</span>
                      </div>
                    </div>
                    <div className="p-5 space-y-4">
                      <div className="flex items-center gap-4">
                        <div className="w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-xl flex items-center justify-center text-3xl">🚗</div>
                        <div>
                          <h3 className="text-xl font-bold text-gray-900 dark:text-white">{c.rental_company}</h3>
                          <p className="text-gray-500">{c.vehicle || c.car_type}</p>
                        </div>
                        {c.rating > 0 && (
                          <div className="ml-auto text-right">
                            <div className="flex items-center gap-1">
                              <span className="text-yellow-500">⭐</span>
                              <span className="font-semibold">{c.rating.toFixed(1)}</span>
                            </div>
                            {c.reviews > 0 && <p className="text-xs text-gray-500">{c.reviews} reviews</p>}
                          </div>
                        )}
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                        {[
                          { label: 'Type', value: c.car_type },
                          { label: 'Total', value: `$${c.total_price}` },
                          { label: 'Days', value: `${c.rental_days} days` },
                          { label: 'Mileage', value: c.mileage },
                          c.deposit > 0 && { label: 'Deposit', value: `$${c.deposit}` },
                        ].filter(Boolean).map((item: any, idx) => (
                          <div key={idx} className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3">
                            <p className="text-xs text-gray-500 uppercase tracking-wider">{item.label}</p>
                            <p className="text-sm font-semibold text-gray-900 dark:text-white mt-0.5">{item.value}</p>
                          </div>
                        ))}
                      </div>
                      {c.features && c.features.length > 0 && (
                        <div className="flex flex-wrap gap-1.5">
                          {c.features.slice(0, 8).map((f: string, idx: number) => (
                            <span key={idx} className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-2.5 py-1 rounded-full">{f}</span>
                          ))}
                        </div>
                      )}
                      {c.pickup_location && (
                        <p className="text-sm text-gray-600 dark:text-gray-400"><span className="font-medium">Pickup:</span> {c.pickup_location}</p>
                      )}
                      {c.recommendation && (
                        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 text-sm text-blue-700 dark:text-blue-300">{c.recommendation}</div>
                      )}
                      {getBookingUrl(c) && (
                        <div className="flex justify-end">
                          <BookingLinkButton item={c} tone="orange" label="Reserve on Partner Site" />
                        </div>
                      )}
                    </div>
                  </div>
                );
              })()}

              {/* Alternative Cars Table */}
              {rec?.top_5_cars && rec.top_5_cars.length > 1 && (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                  <div className="px-5 py-3 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Alternative Car Rentals</h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
                          <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Company</th>
                          <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Vehicle</th>
                          <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Type</th>
                          <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Rating</th>
                          <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Score</th>
                          <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Per Day</th>
                          <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Total</th>
                          <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Book</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rec.top_5_cars.slice(1, 8).map((c: any, idx: number) => (
                          <tr key={idx} className="border-b border-gray-50 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors">
                            <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">{c.rental_company}</td>
                            <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{c.vehicle || c.car_type}</td>
                            <td className="px-4 py-3 text-center">
                              <span className="px-2 py-0.5 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full text-xs font-medium capitalize">{c.car_type}</span>
                            </td>
                            <td className="px-4 py-3 text-center">{c.rating > 0 ? `⭐ ${c.rating.toFixed(1)}` : '-'}</td>
                            <td className="px-4 py-3 text-center">
                              {c.utility_score !== undefined && (
                                <span className="px-2 py-0.5 bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-full text-xs font-medium">{c.utility_score}</span>
                              )}
                            </td>
                            <td className="px-4 py-3 text-right font-bold text-primary-600 dark:text-primary-400">${c.price_per_day}</td>
                            <td className="px-4 py-3 text-right text-gray-600 dark:text-gray-400">${c.total_price}</td>
                            <td className="px-4 py-3 text-center">
                              <BookingLinkButton item={c} tone="orange" label="Book" size="sm" />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {!rec?.recommended_car && (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-8 text-center text-gray-500">
                  <p className="text-lg">No car rental data available</p>
                  <p className="text-sm mt-1">Car rentals at this location don't have current pricing data</p>
                </div>
              )}
            </div>
          )}

          {/* ══════ TAB: DINING ══════ */}
          {activeTab === 'dining' && (
            <div className="space-y-6">
              {rec?.recommended_restaurant && (() => {
                const r = rec.recommended_restaurant;
                return (
                  <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                    <div className="px-5 py-3 bg-gradient-to-r from-rose-50 to-pink-100 dark:from-rose-900/30 dark:to-pink-800/20 border-b border-rose-200 dark:border-rose-800 flex items-center justify-between">
                      <h3 className="text-sm font-semibold text-rose-900 dark:text-rose-200 flex items-center gap-2">
                        <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                        Top Pick - Best Restaurant
                      </h3>
                      <span className="text-sm font-bold text-rose-700 dark:text-rose-300">~${r.average_cost_per_person}/person</span>
                    </div>
                    <div className="p-5">
                      <div className="flex flex-col md:flex-row gap-5">
                        {(r.thumbnail || r.primary_image) && (
                          <img src={r.thumbnail || r.primary_image} alt={r.name} className="w-full md:w-72 h-52 object-cover rounded-xl shadow-sm" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                        )}
                        <div className="flex-1 space-y-4">
                          <div>
                            <h3 className="text-xl font-bold text-gray-900 dark:text-white">{r.name}</h3>
                            <p className="text-gray-500">{r.cuisine_type}{r.city ? ` · ${r.city}` : ''}</p>
                          </div>
                          <div className="flex items-center gap-4 flex-wrap">
                            {r.rating > 0 && (
                              <div className="flex items-center gap-1">
                                <span className="text-yellow-500">⭐</span>
                                <span className="font-semibold">{r.rating.toFixed(1)}</span>
                                {r.review_count > 0 && <span className="text-sm text-gray-500">({r.review_count} reviews)</span>}
                              </div>
                            )}
                            <span className="text-lg font-semibold text-green-600 dark:text-green-400">{r.price_range}</span>
                            {r.utility_score !== undefined && (
                              <span className="px-2.5 py-1 bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-full text-xs font-semibold">
                                Score: {r.utility_score}
                              </span>
                            )}
                          </div>
                          <div className="grid grid-cols-2 gap-3">
                            {[
                              r.address && { label: 'Address', value: r.address },
                              r.hours && { label: 'Hours', value: r.hours },
                            ].filter(Boolean).map((item: any, idx) => (
                              <div key={idx} className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3">
                                <p className="text-xs text-gray-500 uppercase tracking-wider">{item.label}</p>
                                <p className="text-sm text-gray-900 dark:text-white mt-0.5">{item.value}</p>
                              </div>
                            ))}
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {r.has_delivery && <span className="text-xs px-3 py-1.5 bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full border border-green-200 dark:border-green-800">Delivery</span>}
                            {r.has_takeout && <span className="text-xs px-3 py-1.5 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full border border-blue-200 dark:border-blue-800">Takeout</span>}
                            {r.has_reservation && <span className="text-xs px-3 py-1.5 bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full border border-purple-200 dark:border-purple-800">Reservations</span>}
                          </div>
                          <div className="flex gap-4 text-sm items-center flex-wrap">
                            {r.phone && <a href={`tel:${r.phone}`} className="text-primary-600 dark:text-primary-400 hover:underline">{r.phone}</a>}
                            {r.website && <a href={r.website} target="_blank" rel="noopener noreferrer" className="text-primary-600 dark:text-primary-400 hover:underline">Website</a>}
                            <BookingLinkButton item={r} tone="rose" label={r.has_reservation ? 'Reserve Table' : 'Visit / Order'} size="sm" />
                          </div>
                          {r.recommendation && (
                            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 text-sm text-blue-700 dark:text-blue-300">{r.recommendation}</div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* Alternative Restaurants Table */}
              {rec?.top_5_restaurants && rec.top_5_restaurants.length > 1 && (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                  <div className="px-5 py-3 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Alternative Restaurants</h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
                          <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Restaurant</th>
                          <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Cuisine</th>
                          <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Rating</th>
                          <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Price Range</th>
                          <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Score</th>
                          <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Per Person</th>
                          <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Book</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rec.top_5_restaurants.slice(1, 8).map((r: any, idx: number) => (
                          <tr key={idx} className="border-b border-gray-50 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors">
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-3">
                                {(r.thumbnail || r.primary_image) ? (
                                  <img src={r.thumbnail || r.primary_image} alt="" className="w-10 h-10 rounded-lg object-cover flex-shrink-0" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                                ) : (
                                  <div className="w-10 h-10 rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center flex-shrink-0">🍽️</div>
                                )}
                                <span className="font-medium text-gray-900 dark:text-white">{r.name}</span>
                              </div>
                            </td>
                            <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{r.cuisine_type}</td>
                            <td className="px-4 py-3 text-center">{r.rating > 0 ? `⭐ ${r.rating.toFixed(1)}` : '-'}</td>
                            <td className="px-4 py-3 text-center font-medium text-green-600 dark:text-green-400">{r.price_range}</td>
                            <td className="px-4 py-3 text-center">
                              {r.utility_score !== undefined && (
                                <span className="px-2 py-0.5 bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-full text-xs font-medium">{r.utility_score}</span>
                              )}
                            </td>
                            <td className="px-4 py-3 text-right font-bold text-primary-600 dark:text-primary-400">${r.average_cost_per_person}</td>
                            <td className="px-4 py-3 text-center">
                              <BookingLinkButton item={r} tone="rose" label="Visit" size="sm" />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {!rec?.recommended_restaurant && (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-8 text-center text-gray-500">
                  <p className="text-lg">No restaurant data available</p>
                  <p className="text-sm mt-1">Try adjusting your cuisine preferences</p>
                </div>
              )}
            </div>
          )}

          {/* ══════ TAB: INTELLIGENCE ══════ */}
          {activeTab === 'intelligence' && (
            <div className="space-y-4">
              {intel ? (
                <>
                  <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-2">
                    <span className="inline-block w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                    10+ AI agents analyzed {destinationLabel} for your travel dates
                  </div>
                  {intelError && (
                    <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3 mb-2 text-sm text-yellow-800 dark:text-yellow-200">
                      <span className="font-medium">AI intelligence limited:</span> {intelError}. Showing basic data instead.
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Weather */}
                    {intel.weather_by_day && intel.weather_by_day.length > 0 && (
                      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                        <div className="px-5 py-3 bg-amber-50 dark:bg-amber-900/20 border-b border-amber-200 dark:border-amber-800">
                          <h3 className="text-sm font-semibold text-amber-900 dark:text-amber-200">Weather Forecast</h3>
                        </div>
                        <div className="p-4">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="text-xs text-gray-500 uppercase tracking-wider">
                                <th className="text-left pb-2">Date</th>
                                <th className="text-left pb-2">Condition</th>
                                <th className="text-right pb-2">Temp</th>
                                <th className="text-right pb-2">Rain</th>
                              </tr>
                            </thead>
                            <tbody>
                              {intel.weather_by_day.map((day: any, i: number) => (
                                <tr key={i} className="border-t border-gray-50 dark:border-gray-800">
                                  <td className="py-2 text-gray-700 dark:text-gray-300">{day.date}</td>
                                  <td className="py-2 text-gray-600 dark:text-gray-400">{day.condition}</td>
                                  <td className="py-2 text-right font-medium text-gray-900 dark:text-white">{day.high_c}°/{day.low_c}°C</td>
                                  <td className="py-2 text-right">
                                    {day.rain_chance_pct > 30
                                      ? <span className="text-blue-600 dark:text-blue-400 font-medium">{day.rain_chance_pct}%</span>
                                      : <span className="text-gray-400">{day.rain_chance_pct || 0}%</span>}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    {/* Safety */}
                    {intel.safety && (
                      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                        <div className="px-5 py-3 bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800">
                          <h3 className="text-sm font-semibold text-red-900 dark:text-red-200">Safety Intel</h3>
                        </div>
                        <div className="p-4 space-y-3">
                          <div className="flex items-center gap-3">
                            <div className="w-14 h-14 rounded-xl bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                              <span className="text-2xl font-bold text-gray-900 dark:text-white">{intel.safety.overall_score}</span>
                            </div>
                            <div>
                              <p className="text-sm font-medium text-gray-900 dark:text-white">/10 Safety Score</p>
                              <span className={`text-xs px-2 py-0.5 rounded-full ${
                                intel.safety.crime_level === 'low' ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' :
                                intel.safety.crime_level === 'moderate' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300' :
                                'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
                              }`}>{intel.safety.crime_level} crime</span>
                            </div>
                          </div>
                          {intel.safety.areas_to_avoid?.length > 0 && (
                            <div>
                              <p className="text-xs font-semibold text-red-600 dark:text-red-400 uppercase tracking-wider mb-1">Areas to Avoid</p>
                              <p className="text-sm text-gray-600 dark:text-gray-400">{intel.safety.areas_to_avoid.join(', ')}</p>
                            </div>
                          )}
                          {intel.safety.scam_warnings?.length > 0 && (
                            <div>
                              <p className="text-xs font-semibold text-orange-600 dark:text-orange-400 uppercase tracking-wider mb-1">Scam Warnings</p>
                              <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-0.5">
                                {intel.safety.scam_warnings.slice(0, 3).map((s: string, i: number) => <li key={i} className="flex gap-1"><span className="text-orange-400">!</span> {s}</li>)}
                              </ul>
                            </div>
                          )}
                          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-gray-100 dark:border-gray-700 text-xs">
                            <p className="text-gray-500">Emergency: <span className="font-medium text-gray-900 dark:text-white">{intel.safety.emergency_number}</span></p>
                            <p className="text-gray-500">Tap water: <span className="font-medium text-gray-900 dark:text-white">{intel.safety.tap_water_safe ? 'Safe' : 'Not safe'}</span></p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Transport */}
                    {intel.best_transport && (
                      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                        <div className="px-5 py-3 bg-indigo-50 dark:bg-indigo-900/20 border-b border-indigo-200 dark:border-indigo-800">
                          <h3 className="text-sm font-semibold text-indigo-900 dark:text-indigo-200">Transport Decision</h3>
                        </div>
                        <div className="p-4 space-y-3">
                          <div className={`inline-block px-3 py-1 rounded-lg text-sm font-bold ${
                            intel.best_transport.recommendation === 'public_transit'
                              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                              : intel.best_transport.recommendation === 'car_rental'
                                ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                                : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                          }`}>
                            {intel.best_transport.recommendation === 'public_transit' ? 'USE PUBLIC TRANSIT' :
                             intel.best_transport.recommendation === 'car_rental' ? 'RENT A CAR' : 'MIXED TRANSPORT'}
                          </div>
                          <p className="text-sm text-gray-600 dark:text-gray-400">{intel.best_transport.reason}</p>
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            {intel.best_transport.daily_transit_pass_cost && (
                              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-2">
                                <p className="text-xs text-gray-500">Daily Pass</p>
                                <p className="font-medium text-gray-900 dark:text-white">{intel.best_transport.daily_transit_pass_cost}</p>
                              </div>
                            )}
                            {intel.best_transport.airport_to_city && (
                              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-2">
                                <p className="text-xs text-gray-500">Airport to City</p>
                                <p className="font-medium text-gray-900 dark:text-white">{intel.best_transport.airport_to_city}</p>
                              </div>
                            )}
                          </div>
                          <div className="flex flex-wrap gap-1.5 pt-1">
                            {intel.best_transport.metro_available && <span className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded-full">Metro</span>}
                            {intel.best_transport.bus_system && <span className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded-full">Bus</span>}
                            {intel.best_transport.ride_sharing && <span className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded-full">Uber/Lyft</span>}
                            {intel.best_transport.taxi_affordable && <span className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded-full">Taxi</span>}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Local Events */}
                    {intel.local_events && intel.local_events.length > 0 && (
                      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                        <div className="px-5 py-3 bg-purple-50 dark:bg-purple-900/20 border-b border-purple-200 dark:border-purple-800">
                          <h3 className="text-sm font-semibold text-purple-900 dark:text-purple-200">Local Events</h3>
                        </div>
                        <div className="p-4 space-y-3">
                          {intel.local_events.slice(0, 5).map((event: any, i: number) => (
                            <div key={i} className="flex items-start gap-3 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-750">
                              <div className="w-8 h-8 bg-purple-100 dark:bg-purple-900/40 rounded-lg flex items-center justify-center text-sm flex-shrink-0">🎉</div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center justify-between gap-2">
                                  <p className="font-medium text-sm text-gray-900 dark:text-white truncate">{event.name}</p>
                                  <span className="text-xs text-gray-500 flex-shrink-0">{event.date}</span>
                                </div>
                                <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">{event.description}</p>
                                <div className="flex gap-2 mt-1">
                                  <span className="text-xs bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 px-1.5 py-0.5 rounded">{event.type}</span>
                                  <span className="text-xs text-gray-500">{event.cost}</span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Food Scene */}
                    {intel.food_scene && (
                      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                        <div className="px-5 py-3 bg-orange-50 dark:bg-orange-900/20 border-b border-orange-200 dark:border-orange-800">
                          <h3 className="text-sm font-semibold text-orange-900 dark:text-orange-200">Food Scene</h3>
                        </div>
                        <div className="p-4 space-y-3">
                          {intel.food_scene.must_try_dishes?.length > 0 && (
                            <div>
                              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Must Try</p>
                              <div className="flex flex-wrap gap-1.5">
                                {intel.food_scene.must_try_dishes.map((d: string, i: number) => (
                                  <span key={i} className="text-xs bg-orange-50 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 px-2 py-1 rounded-full border border-orange-200 dark:border-orange-800">{d}</span>
                                ))}
                              </div>
                            </div>
                          )}
                          {intel.food_scene.food_markets?.length > 0 && (
                            <div>
                              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Food Markets</p>
                              <p className="text-sm text-gray-600 dark:text-gray-400">{intel.food_scene.food_markets.join(', ')}</p>
                            </div>
                          )}
                          <div className="grid grid-cols-3 gap-2 text-center">
                            {[
                              { label: 'Budget', value: intel.food_scene.budget_meal_cost, color: 'bg-green-50 dark:bg-green-900/20' },
                              { label: 'Mid-Range', value: intel.food_scene.mid_range_meal_cost, color: 'bg-yellow-50 dark:bg-yellow-900/20' },
                              { label: 'Fine Dining', value: intel.food_scene.fine_dining_cost, color: 'bg-red-50 dark:bg-red-900/20' },
                            ].map((tier) => (
                              <div key={tier.label} className={`${tier.color} rounded-lg p-2`}>
                                <p className="text-xs text-gray-500">{tier.label}</p>
                                <p className="text-sm font-semibold text-gray-900 dark:text-white">{tier.value}</p>
                              </div>
                            ))}
                          </div>
                          {intel.food_scene.street_food_safe !== undefined && (
                            <p className="text-xs text-gray-500">Street food: <span className="font-medium">{intel.food_scene.street_food_safe ? 'Safe to eat' : 'Be cautious'}</span></p>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Local Customs */}
                    {intel.local_customs && (
                      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                        <div className="px-5 py-3 bg-teal-50 dark:bg-teal-900/20 border-b border-teal-200 dark:border-teal-800">
                          <h3 className="text-sm font-semibold text-teal-900 dark:text-teal-200">Local Customs</h3>
                        </div>
                        <div className="p-4 space-y-2 text-sm">
                          {[
                            intel.local_customs.tipping && { label: 'Tipping', value: intel.local_customs.tipping },
                            intel.local_customs.language && { label: 'Language', value: intel.local_customs.language },
                            intel.local_customs.dress_code && { label: 'Dress Code', value: intel.local_customs.dress_code },
                            intel.local_customs.dining_etiquette && { label: 'Dining', value: intel.local_customs.dining_etiquette },
                          ].filter(Boolean).map((item: any, idx) => (
                            <div key={idx} className="flex gap-3 py-1.5 border-b border-gray-50 dark:border-gray-800 last:border-0">
                              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider w-20 flex-shrink-0 pt-0.5">{item.label}</span>
                              <span className="text-gray-700 dark:text-gray-300">{item.value}</span>
                            </div>
                          ))}
                          {intel.local_customs.useful_phrases?.length > 0 && (
                            <div className="pt-2 mt-2 border-t border-gray-100 dark:border-gray-700">
                              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Useful Phrases</p>
                              <div className="space-y-1">
                                {intel.local_customs.useful_phrases.slice(0, 4).map((p: string, i: number) => (
                                  <p key={i} className="text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-900 rounded px-3 py-1.5">{p}</p>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-8 text-center text-gray-500">
                  <p className="text-lg">No intelligence data available</p>
                  <p className="text-sm mt-1">Destination intelligence could not be gathered for this location</p>
                </div>
              )}
            </div>
          )}

        </div>
      )}
      </div>
    </div>
  );
};

export default AIPlannerPage;
