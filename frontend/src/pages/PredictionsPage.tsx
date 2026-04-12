import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import api from '@/services/api';

interface PricePrediction {
  current_estimate: number | null;
  trend: string;
  confidence: number;
  forecast?: Array<{
    days_from_now: number;
    estimated_price: number;
    range: [number, number];
  }>;
  recommendation: string;
  reasoning: string;
  best_booking_window?: string;
}

interface BestTimeResult {
  destination: string;
  best_months?: Array<{
    month: string;
    score: number;
    weather: string;
    crowds: string;
    prices: string;
    events?: string[];
  }>;
  peak_season?: { months: string[]; reason: string };
  shoulder_season?: { months: string[]; reason: string };
  off_season?: { months: string[]; reason: string };
  overall_recommendation: string;
  budget_tip?: string;
  weather_tip?: string;
}

interface TrendItem {
  destination: string;
  search_count: number;
  rank: number;
}

interface CrowdMonth {
  month: string;
  crowd_level: 'low' | 'moderate' | 'high' | 'very_high';
  score: number;
  notes: string;
}

interface CrowdLevels {
  destination: string;
  months?: CrowdMonth[];
  peak_periods?: string[];
  best_for_avoiding_crowds?: string;
  major_events_driving_crowds?: string[];
}

interface TripExperience {
  destination: string;
  tagline?: string;
  vibe_emoji?: string;
  weather_preview?: {
    summary: string;
    avg_temp_high_c: number;
    avg_temp_low_c: number;
    condition: string;
    what_to_wear: string;
  };
  crowd_forecast?: {
    level: string;
    description: string;
    tip: string;
  };
  daily_budget?: {
    budget_usd: number;
    mid_range_usd: number;
    luxury_usd: number;
    currency: string;
    exchange_note: string;
  };
  cultural_highlights?: Array<{ title: string; description: string; icon: string }>;
  food_scene?: {
    summary: string;
    must_try: Array<{ dish: string; description: string; price_range: string }>;
    dining_tip: string;
  };
  a_day_in_your_trip?: {
    morning: string;
    afternoon: string;
    evening: string;
  };
  hidden_gems?: Array<{ name: string; why: string; icon: string }>;
  local_phrases?: Array<{ phrase: string; meaning: string; pronunciation: string }>;
  packing_essentials?: string[];
  safety_wellness?: {
    safety_level: string;
    tips: string[];
    health_note: string;
  };
  trip_score?: {
    overall: number;
    adventure: number;
    relaxation: number;
    culture: number;
    food: number;
    value: number;
  };
}

const PredictionsPage = () => {
  const { isAuthenticated } = useAuth();

  // Price prediction state
  const [priceOrigin, setPriceOrigin] = useState('');
  const [priceDest, setPriceDest] = useState('');
  const [priceDate, setPriceDate] = useState('');
  const [pricePrediction, setPricePrediction] = useState<PricePrediction | null>(null);
  const [priceLoading, setPriceLoading] = useState(false);

  // Best time state
  const [btDest, setBtDest] = useState('');
  const [bestTime, setBestTime] = useState<BestTimeResult | null>(null);
  const [btLoading, setBtLoading] = useState(false);

  // Trends state
  const [trends, setTrends] = useState<TrendItem[]>([]);
  const [trendsLoading, setTrendsLoading] = useState(false);

  // Trip Experience state
  const [expDest, setExpDest] = useState('');
  const [expStart, setExpStart] = useState('');
  const [expEnd, setExpEnd] = useState('');
  const [expTravelers, setExpTravelers] = useState(2);
  const [tripExperience, setTripExperience] = useState<TripExperience | null>(null);
  const [expLoading, setExpLoading] = useState(false);

  // Crowd Levels state
  const [crowdDest, setCrowdDest] = useState('');
  const [crowdData, setCrowdData] = useState<CrowdLevels | null>(null);
  const [crowdLoading, setCrowdLoading] = useState(false);

  const [activeTab, setActiveTab] = useState<'experience' | 'prices' | 'besttime' | 'crowds' | 'trends'>('experience');

  // Deep-link: auto-fill forms and select tab from ?destination=...&start_date=...&end_date=...&travelers=...&tab=...
  const [searchParams] = useSearchParams();
  useEffect(() => {
    const dest = searchParams.get('destination') || '';
    const start = searchParams.get('start_date') || '';
    const end = searchParams.get('end_date') || '';
    const travelers = searchParams.get('travelers');
    const tab = searchParams.get('tab');

    if (dest) {
      setExpDest(dest);
      setCrowdDest(dest);
      setBtDest(dest);
      setPriceDest(dest);
    }
    if (start) setExpStart(start);
    if (end) setExpEnd(end);
    if (travelers) {
      const n = parseInt(travelers, 10);
      if (!isNaN(n) && n > 0) setExpTravelers(n);
    }
    if (tab && ['experience', 'prices', 'besttime', 'crowds', 'trends'].includes(tab)) {
      setActiveTab(tab as typeof activeTab);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const handlePricePredict = async () => {
    if (!priceOrigin || !priceDest || !priceDate) return;
    setPriceLoading(true);
    try {
      const res = await api.post('/api/agents/predict-prices', {
        origin: priceOrigin,
        destination: priceDest,
        target_date: priceDate,
      });
      setPricePrediction(res.data.prediction);
    } catch {
      setPricePrediction({
        current_estimate: null,
        trend: 'unknown',
        confidence: 0,
        recommendation: 'monitor',
        reasoning: 'Unable to fetch prediction. Try again later.',
      });
    } finally {
      setPriceLoading(false);
    }
  };

  const handleBestTime = async () => {
    if (!btDest) return;
    setBtLoading(true);
    try {
      const res = await api.get(`/api/agents/best-time?destination=${encodeURIComponent(btDest)}`);
      setBestTime(res.data);
    } catch {
      setBestTime({
        destination: btDest,
        overall_recommendation: 'Unable to fetch data. Try again later.',
      });
    } finally {
      setBtLoading(false);
    }
  };

  const handleTrends = async () => {
    setTrendsLoading(true);
    try {
      const res = await api.get('/api/agents/trends?limit=10');
      setTrends(res.data.trending_destinations || []);
    } catch {
      setTrends([]);
    } finally {
      setTrendsLoading(false);
    }
  };

  const handleTripExperience = async () => {
    if (!expDest || !expStart || !expEnd) return;
    setExpLoading(true);
    try {
      const res = await api.post('/api/agents/trip-experience', {
        destination: expDest,
        start_date: expStart,
        end_date: expEnd,
        travelers: expTravelers,
      });
      setTripExperience(res.data);
    } catch {
      setTripExperience(null);
    } finally {
      setExpLoading(false);
    }
  };

  const handleCrowdLevels = async () => {
    if (!crowdDest) return;
    setCrowdLoading(true);
    try {
      const res = await api.get(`/api/agents/crowd-levels?destination=${encodeURIComponent(crowdDest)}`);
      setCrowdData(res.data);
    } catch {
      setCrowdData(null);
    } finally {
      setCrowdLoading(false);
    }
  };

  const trendBadge = (rec: string) => {
    const colors: Record<string, string> = {
      buy_now: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
      wait: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
      monitor: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
    };
    return colors[rec] || colors.monitor;
  };

  const crowdColor = (level: string) => {
    if (level === 'low') return 'text-green-600 dark:text-green-400';
    if (level === 'high') return 'text-red-600 dark:text-red-400';
    return 'text-yellow-600 dark:text-yellow-400';
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <p className="text-gray-600 dark:text-gray-400">Please sign in to access predictions.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Hero */}
      <div className="relative bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 text-white overflow-hidden">
        <div className="absolute inset-0 opacity-20 pointer-events-none">
          <div className="absolute top-10 left-10 text-6xl animate-pulse">✨</div>
          <div className="absolute top-20 right-20 text-5xl animate-pulse delay-150">🌍</div>
          <div className="absolute bottom-10 left-1/3 text-5xl animate-pulse delay-300">🗺️</div>
          <div className="absolute top-1/2 right-10 text-4xl animate-pulse delay-500">🎒</div>
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 text-xs font-medium mb-4">
            <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></span>
            AI-Powered Travel Intelligence
          </div>
          <h1 className="text-xl sm:text-2xl lg:text-3xl font-extrabold mb-3 leading-tight">
            Preview Your Trip <span className="bg-gradient-to-r from-amber-300 to-pink-300 bg-clip-text text-transparent">Before You Go</span>
          </h1>
          <p className="text-sm sm:text-base text-white/90 max-w-2xl">
            Live a preview of your upcoming adventure — weather vibes, local food, hidden gems, cultural moments, and what a day feels like on the ground. All powered by AI.
          </p>
          <div className="mt-6 flex flex-wrap gap-2 text-xs">
            <span className="px-3 py-1.5 rounded-full bg-white/10 backdrop-blur-sm border border-white/20">🌤️ Weather Preview</span>
            <span className="px-3 py-1.5 rounded-full bg-white/10 backdrop-blur-sm border border-white/20">💰 Smart Budget</span>
            <span className="px-3 py-1.5 rounded-full bg-white/10 backdrop-blur-sm border border-white/20">🍜 Food Scene</span>
            <span className="px-3 py-1.5 rounded-full bg-white/10 backdrop-blur-sm border border-white/20">🏛️ Cultural Gems</span>
            <span className="px-3 py-1.5 rounded-full bg-white/10 backdrop-blur-sm border border-white/20">💬 Local Phrases</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 pt-6 sm:pt-8">
        <div className="flex gap-2 sm:gap-3 overflow-x-auto pb-2 scrollbar-hide">
          {([
            { key: 'experience', icon: '✨', label: 'Trip Experience' },
            { key: 'prices', icon: '💰', label: 'Price Forecast' },
            { key: 'besttime', icon: '📅', label: 'Best Time' },
            { key: 'crowds', icon: '👥', label: 'Crowd Levels' },
            { key: 'trends', icon: '🔥', label: 'Trending' },
          ] as const).map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex-shrink-0 px-4 sm:px-5 py-2.5 sm:py-3 rounded-xl font-semibold text-xs sm:text-sm text-center transition-all flex items-center gap-2 border ${
                activeTab === tab.key
                  ? 'bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white shadow-lg border-transparent'
                  : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-700 hover:border-purple-400 dark:hover:border-purple-500 hover:shadow-md'
              }`}
            >
              <span className="text-base">{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4 pb-8">
        {/* Trip Experience Tab */}
        {activeTab === 'experience' && (
          <div className="space-y-6">
            {/* Input form */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
              <div className="flex items-center gap-3 mb-4">
                <span className="text-3xl">✨</span>
                <div>
                  <h2 className="text-xl font-bold text-gray-900 dark:text-white">Preview Your Trip Experience</h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Feel the destination before you even pack.</p>
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                <input
                  type="text"
                  placeholder="Destination (e.g., Kyoto, Japan)"
                  value={expDest}
                  onChange={(e) => setExpDest(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                <input
                  type="date"
                  value={expStart}
                  onChange={(e) => setExpStart(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                <input
                  type="date"
                  value={expEnd}
                  onChange={(e) => setExpEnd(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                <input
                  type="number"
                  min={1}
                  max={20}
                  placeholder="Travelers"
                  value={expTravelers}
                  onChange={(e) => setExpTravelers(parseInt(e.target.value) || 1)}
                  className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              <button
                onClick={handleTripExperience}
                disabled={expLoading || !expDest || !expStart || !expEnd}
                className="mt-4 px-6 py-3 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl hover:from-indigo-700 hover:via-purple-700 hover:to-pink-700 disabled:opacity-50 transition-all flex items-center gap-2"
              >
                {expLoading ? (
                  <>
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                    </svg>
                    Crafting your preview...
                  </>
                ) : (
                  <>
                    <span>✨</span> Generate Experience Preview
                  </>
                )}
              </button>
            </div>

            {/* Skeleton while loading */}
            {expLoading && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 animate-pulse">
                    <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-3"></div>
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full mb-2"></div>
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                  </div>
                ))}
              </div>
            )}

            {/* Results */}
            {tripExperience && !expLoading && (
              <div className="space-y-6">
                {/* Hero card */}
                <div className="relative bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 rounded-3xl shadow-xl p-8 text-white overflow-hidden">
                  <div className="absolute top-4 right-4 text-5xl opacity-80">{tripExperience.vibe_emoji}</div>
                  <p className="text-xs uppercase tracking-widest text-white/70 mb-2">Your Preview</p>
                  <h3 className="text-3xl sm:text-4xl font-extrabold mb-2">{tripExperience.destination}</h3>
                  {tripExperience.tagline && (
                    <p className="text-lg text-white/90 italic">"{tripExperience.tagline}"</p>
                  )}
                  {tripExperience.trip_score && (
                    <div className="mt-6 flex flex-wrap gap-3">
                      <div className="px-4 py-2 bg-white/15 backdrop-blur-sm rounded-xl border border-white/20">
                        <p className="text-xs text-white/70">Overall Score</p>
                        <p className="text-2xl font-bold">{tripExperience.trip_score.overall}/100</p>
                      </div>
                      <div className="flex-1 grid grid-cols-2 sm:grid-cols-5 gap-2 text-center">
                        {[
                          { label: 'Adventure', value: tripExperience.trip_score.adventure, icon: '🧗' },
                          { label: 'Relax', value: tripExperience.trip_score.relaxation, icon: '🧘' },
                          { label: 'Culture', value: tripExperience.trip_score.culture, icon: '🏛️' },
                          { label: 'Food', value: tripExperience.trip_score.food, icon: '🍜' },
                          { label: 'Value', value: tripExperience.trip_score.value, icon: '💎' },
                        ].map((s) => (
                          <div key={s.label} className="px-2 py-2 bg-white/10 rounded-lg">
                            <p className="text-lg">{s.icon}</p>
                            <p className="text-xs text-white/70">{s.label}</p>
                            <p className="text-sm font-bold">{s.value}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Weather + Crowd + Budget */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                  {tripExperience.weather_preview && (
                    <div className="bg-gradient-to-br from-sky-50 to-blue-50 dark:from-sky-900/20 dark:to-blue-900/20 rounded-2xl shadow-md p-6 border border-sky-100 dark:border-sky-800/40">
                      <div className="flex items-center gap-2 mb-3">
                        <span className="text-2xl">🌤️</span>
                        <h4 className="font-bold text-gray-900 dark:text-white">Weather Preview</h4>
                      </div>
                      <div className="flex items-baseline gap-2 mb-2">
                        <span className="text-3xl font-bold text-sky-700 dark:text-sky-300">{tripExperience.weather_preview.avg_temp_high_c}°</span>
                        <span className="text-lg text-gray-500 dark:text-gray-400">/ {tripExperience.weather_preview.avg_temp_low_c}°C</span>
                      </div>
                      <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">{tripExperience.weather_preview.summary}</p>
                      <div className="text-xs text-sky-700 dark:text-sky-400 bg-white/60 dark:bg-sky-900/30 rounded-lg p-2">
                        👕 {tripExperience.weather_preview.what_to_wear}
                      </div>
                    </div>
                  )}
                  {tripExperience.crowd_forecast && (
                    <div className="bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 rounded-2xl shadow-md p-6 border border-amber-100 dark:border-amber-800/40">
                      <div className="flex items-center gap-2 mb-3">
                        <span className="text-2xl">👥</span>
                        <h4 className="font-bold text-gray-900 dark:text-white">Crowd Forecast</h4>
                      </div>
                      <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold uppercase mb-3 ${
                        tripExperience.crowd_forecast.level === 'low' ? 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300' :
                        tripExperience.crowd_forecast.level === 'moderate' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300' :
                        'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300'
                      }`}>{tripExperience.crowd_forecast.level.replace('_', ' ')}</span>
                      <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">{tripExperience.crowd_forecast.description}</p>
                      <div className="text-xs text-amber-700 dark:text-amber-400 bg-white/60 dark:bg-amber-900/30 rounded-lg p-2">
                        💡 {tripExperience.crowd_forecast.tip}
                      </div>
                    </div>
                  )}
                  {tripExperience.daily_budget && (
                    <div className="bg-gradient-to-br from-emerald-50 to-green-50 dark:from-emerald-900/20 dark:to-green-900/20 rounded-2xl shadow-md p-6 border border-emerald-100 dark:border-emerald-800/40">
                      <div className="flex items-center gap-2 mb-3">
                        <span className="text-2xl">💰</span>
                        <h4 className="font-bold text-gray-900 dark:text-white">Daily Budget</h4>
                      </div>
                      <div className="space-y-2 mb-3">
                        <div className="flex justify-between text-sm"><span className="text-gray-600 dark:text-gray-400">Budget</span><span className="font-bold text-emerald-700 dark:text-emerald-400">${tripExperience.daily_budget.budget_usd}/day</span></div>
                        <div className="flex justify-between text-sm"><span className="text-gray-600 dark:text-gray-400">Mid-range</span><span className="font-bold text-emerald-700 dark:text-emerald-400">${tripExperience.daily_budget.mid_range_usd}/day</span></div>
                        <div className="flex justify-between text-sm"><span className="text-gray-600 dark:text-gray-400">Luxury</span><span className="font-bold text-emerald-700 dark:text-emerald-400">${tripExperience.daily_budget.luxury_usd}/day</span></div>
                      </div>
                      <div className="text-xs text-emerald-700 dark:text-emerald-400 bg-white/60 dark:bg-emerald-900/30 rounded-lg p-2">
                        💱 {tripExperience.daily_budget.exchange_note}
                      </div>
                    </div>
                  )}
                </div>

                {/* A Day in Your Trip */}
                {tripExperience.a_day_in_your_trip && (
                  <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                    <div className="flex items-center gap-2 mb-5">
                      <span className="text-2xl">🌅</span>
                      <h4 className="text-lg font-bold text-gray-900 dark:text-white">A Day in Your Trip</h4>
                    </div>
                    <div className="space-y-4">
                      {[
                        { label: 'Morning', icon: '☀️', text: tripExperience.a_day_in_your_trip.morning, color: 'from-amber-100 to-yellow-100 dark:from-amber-900/20 dark:to-yellow-900/20' },
                        { label: 'Afternoon', icon: '🌆', text: tripExperience.a_day_in_your_trip.afternoon, color: 'from-orange-100 to-red-100 dark:from-orange-900/20 dark:to-red-900/20' },
                        { label: 'Evening', icon: '🌙', text: tripExperience.a_day_in_your_trip.evening, color: 'from-indigo-100 to-purple-100 dark:from-indigo-900/20 dark:to-purple-900/20' },
                      ].map((seg) => (
                        <div key={seg.label} className={`bg-gradient-to-r ${seg.color} rounded-xl p-4 flex gap-4`}>
                          <div className="text-3xl">{seg.icon}</div>
                          <div>
                            <p className="text-xs font-bold uppercase tracking-wider text-gray-600 dark:text-gray-400 mb-1">{seg.label}</p>
                            <p className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed">{seg.text}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Cultural Highlights */}
                {tripExperience.cultural_highlights && tripExperience.cultural_highlights.length > 0 && (
                  <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                    <div className="flex items-center gap-2 mb-4">
                      <span className="text-2xl">🏛️</span>
                      <h4 className="text-lg font-bold text-gray-900 dark:text-white">Cultural Highlights</h4>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {tripExperience.cultural_highlights.map((h, i) => (
                        <div key={i} className="flex gap-3 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                          <div className="text-3xl flex-shrink-0">{h.icon}</div>
                          <div>
                            <p className="font-semibold text-gray-900 dark:text-white">{h.title}</p>
                            <p className="text-sm text-gray-600 dark:text-gray-400">{h.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Food Scene */}
                {tripExperience.food_scene && (
                  <div className="bg-gradient-to-br from-rose-50 to-pink-50 dark:from-rose-900/20 dark:to-pink-900/20 rounded-2xl shadow-lg p-6 border border-rose-100 dark:border-rose-800/40">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-2xl">🍜</span>
                      <h4 className="text-lg font-bold text-gray-900 dark:text-white">Food Scene</h4>
                    </div>
                    <p className="text-sm text-gray-700 dark:text-gray-300 mb-4">{tripExperience.food_scene.summary}</p>
                    {tripExperience.food_scene.must_try && tripExperience.food_scene.must_try.length > 0 && (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
                        {tripExperience.food_scene.must_try.map((dish, i) => (
                          <div key={i} className="bg-white/70 dark:bg-gray-800/50 rounded-xl p-3">
                            <div className="flex items-center justify-between mb-1">
                              <p className="font-semibold text-gray-900 dark:text-white">{dish.dish}</p>
                              <span className="text-xs font-bold text-rose-600 dark:text-rose-400">{dish.price_range}</span>
                            </div>
                            <p className="text-xs text-gray-600 dark:text-gray-400">{dish.description}</p>
                          </div>
                        ))}
                      </div>
                    )}
                    <div className="text-xs text-rose-700 dark:text-rose-400 bg-white/60 dark:bg-rose-900/30 rounded-lg p-2">
                      🍽️ {tripExperience.food_scene.dining_tip}
                    </div>
                  </div>
                )}

                {/* Hidden Gems + Local Phrases */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {tripExperience.hidden_gems && tripExperience.hidden_gems.length > 0 && (
                    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                      <div className="flex items-center gap-2 mb-4">
                        <span className="text-2xl">💎</span>
                        <h4 className="text-lg font-bold text-gray-900 dark:text-white">Hidden Gems</h4>
                      </div>
                      <div className="space-y-3">
                        {tripExperience.hidden_gems.map((g, i) => (
                          <div key={i} className="flex gap-3 p-3 bg-gradient-to-r from-violet-50 to-fuchsia-50 dark:from-violet-900/20 dark:to-fuchsia-900/20 rounded-xl">
                            <div className="text-2xl">{g.icon}</div>
                            <div>
                              <p className="font-semibold text-gray-900 dark:text-white text-sm">{g.name}</p>
                              <p className="text-xs text-gray-600 dark:text-gray-400">{g.why}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {tripExperience.local_phrases && tripExperience.local_phrases.length > 0 && (
                    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                      <div className="flex items-center gap-2 mb-4">
                        <span className="text-2xl">💬</span>
                        <h4 className="text-lg font-bold text-gray-900 dark:text-white">Local Phrases</h4>
                      </div>
                      <div className="space-y-2">
                        {tripExperience.local_phrases.map((p, i) => (
                          <div key={i} className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-xl">
                            <div className="flex-1">
                              <p className="font-bold text-gray-900 dark:text-white">{p.phrase}</p>
                              <p className="text-xs text-gray-500 dark:text-gray-400">🗣️ {p.pronunciation}</p>
                            </div>
                            <p className="text-sm text-gray-600 dark:text-gray-400">{p.meaning}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Packing + Safety */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {tripExperience.packing_essentials && tripExperience.packing_essentials.length > 0 && (
                    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                      <div className="flex items-center gap-2 mb-4">
                        <span className="text-2xl">🎒</span>
                        <h4 className="text-lg font-bold text-gray-900 dark:text-white">Packing Essentials</h4>
                      </div>
                      <ul className="space-y-2">
                        {tripExperience.packing_essentials.map((item, i) => (
                          <li key={i} className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                            <span className="w-5 h-5 rounded-full bg-teal-100 dark:bg-teal-900/40 text-teal-600 dark:text-teal-400 flex items-center justify-center text-xs font-bold flex-shrink-0">✓</span>
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {tripExperience.safety_wellness && (
                    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                      <div className="flex items-center gap-2 mb-4">
                        <span className="text-2xl">🛡️</span>
                        <h4 className="text-lg font-bold text-gray-900 dark:text-white">Safety & Wellness</h4>
                      </div>
                      <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold uppercase mb-3 ${
                        tripExperience.safety_wellness.safety_level === 'very_safe' || tripExperience.safety_wellness.safety_level === 'safe' ? 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300' :
                        tripExperience.safety_wellness.safety_level === 'moderate' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300' :
                        'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300'
                      }`}>{tripExperience.safety_wellness.safety_level.replace('_', ' ')}</span>
                      <ul className="space-y-2 mb-3">
                        {tripExperience.safety_wellness.tips?.map((tip, i) => (
                          <li key={i} className="text-sm text-gray-700 dark:text-gray-300 flex gap-2">
                            <span className="text-blue-500">•</span>
                            {tip}
                          </li>
                        ))}
                      </ul>
                      <div className="text-xs text-blue-700 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30 rounded-lg p-2">
                        🏥 {tripExperience.safety_wellness.health_note}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Crowd Levels Tab */}
        {activeTab === 'crowds' && (
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
              <div className="flex items-center gap-3 mb-4">
                <span className="text-3xl">👥</span>
                <div>
                  <h2 className="text-xl font-bold text-gray-900 dark:text-white">Crowd Levels Forecast</h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Know when to go — and when to wait.</p>
                </div>
              </div>
              <div className="flex flex-col sm:flex-row gap-3">
                <input
                  type="text"
                  placeholder="Destination (e.g., Venice, Italy)"
                  value={crowdDest}
                  onChange={(e) => setCrowdDest(e.target.value)}
                  className="flex-1 px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                <button
                  onClick={handleCrowdLevels}
                  disabled={crowdLoading || !crowdDest}
                  className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl font-semibold hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 transition-all"
                >
                  {crowdLoading ? 'Analyzing...' : 'Analyze Crowds'}
                </button>
              </div>
            </div>

            {crowdData && (
              <>
                {/* Summary */}
                <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">{crowdData.destination}</h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {crowdData.best_for_avoiding_crowds && (
                      <div className="bg-gradient-to-br from-emerald-50 to-green-50 dark:from-emerald-900/20 dark:to-green-900/20 rounded-xl p-4 border border-emerald-100 dark:border-emerald-800/40">
                        <p className="text-xs font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400 mb-1">🌿 Best for Avoiding Crowds</p>
                        <p className="text-sm text-gray-800 dark:text-gray-200">{crowdData.best_for_avoiding_crowds}</p>
                      </div>
                    )}
                    {crowdData.peak_periods && crowdData.peak_periods.length > 0 && (
                      <div className="bg-gradient-to-br from-red-50 to-orange-50 dark:from-red-900/20 dark:to-orange-900/20 rounded-xl p-4 border border-red-100 dark:border-red-800/40">
                        <p className="text-xs font-bold uppercase tracking-wider text-red-700 dark:text-red-400 mb-1">🔥 Peak Periods</p>
                        <div className="flex flex-wrap gap-1">
                          {crowdData.peak_periods.map((p, i) => (
                            <span key={i} className="px-2 py-0.5 rounded-full bg-white/70 dark:bg-red-900/40 text-xs text-red-800 dark:text-red-300">{p}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  {crowdData.major_events_driving_crowds && crowdData.major_events_driving_crowds.length > 0 && (
                    <div className="mt-4 bg-amber-50 dark:bg-amber-900/20 rounded-xl p-4 border border-amber-100 dark:border-amber-800/40">
                      <p className="text-xs font-bold uppercase tracking-wider text-amber-700 dark:text-amber-400 mb-2">🎉 Major Events</p>
                      <ul className="text-sm text-gray-800 dark:text-gray-200 space-y-1">
                        {crowdData.major_events_driving_crowds.map((ev, i) => (
                          <li key={i} className="flex gap-2"><span className="text-amber-500">•</span>{ev}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Monthly calendar */}
                {crowdData.months && crowdData.months.length > 0 && (
                  <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                    <h4 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Monthly Crowd Calendar</h4>
                    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                      {crowdData.months.map((m, i) => {
                        const bg = m.crowd_level === 'low' ? 'from-green-400 to-emerald-500' :
                          m.crowd_level === 'moderate' ? 'from-yellow-400 to-amber-500' :
                          m.crowd_level === 'high' ? 'from-orange-400 to-red-500' :
                          'from-red-500 to-rose-600';
                        return (
                          <div key={i} className="rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow">
                            <div className={`bg-gradient-to-br ${bg} p-3 text-white`}>
                              <p className="text-xs uppercase tracking-wider opacity-80">{m.month}</p>
                              <p className="text-lg font-bold capitalize">{m.crowd_level.replace('_', ' ')}</p>
                              <div className="mt-2 flex items-center gap-1">
                                {[...Array(10)].map((_, idx) => (
                                  <div key={idx} className={`h-1 flex-1 rounded-full ${idx < m.score ? 'bg-white' : 'bg-white/30'}`} />
                                ))}
                              </div>
                            </div>
                            <div className="bg-gray-50 dark:bg-gray-700/50 p-3">
                              <p className="text-xs text-gray-700 dark:text-gray-300">{m.notes}</p>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* Price Forecast Tab */}
        {activeTab === 'prices' && (
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Flight Price Prediction</h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
                <input
                  type="text"
                  placeholder="Origin (e.g., NYC)"
                  value={priceOrigin}
                  onChange={(e) => setPriceOrigin(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                <input
                  type="text"
                  placeholder="Destination (e.g., LON)"
                  value={priceDest}
                  onChange={(e) => setPriceDest(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                <input
                  type="date"
                  value={priceDate}
                  onChange={(e) => setPriceDate(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              <button
                onClick={handlePricePredict}
                disabled={priceLoading || !priceOrigin || !priceDest || !priceDate}
                className="px-6 py-3 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl hover:from-indigo-700 hover:via-purple-700 hover:to-pink-700 disabled:opacity-50 transition-all"
              >
                {priceLoading ? 'Analyzing...' : 'Predict Prices'}
              </button>
            </div>

            {pricePrediction && (
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                <div className="flex flex-wrap items-center gap-4 mb-6">
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white">Prediction Results</h3>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${trendBadge(pricePrediction.recommendation)}`}>
                    {pricePrediction.recommendation === 'buy_now' ? 'Buy Now' :
                     pricePrediction.recommendation === 'wait' ? 'Wait' : 'Monitor'}
                  </span>
                  {pricePrediction.trend !== 'unknown' && (
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      Trend: <strong className={pricePrediction.trend === 'falling' ? 'text-green-600' : pricePrediction.trend === 'rising' ? 'text-red-600' : ''}>{pricePrediction.trend}</strong>
                    </span>
                  )}
                </div>

                {pricePrediction.current_estimate && (
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
                    <div className="bg-purple-50 dark:bg-purple-900/20 rounded-xl p-4 text-center">
                      <p className="text-sm text-gray-600 dark:text-gray-400">Current Estimate</p>
                      <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">${pricePrediction.current_estimate}</p>
                    </div>
                    <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4 text-center">
                      <p className="text-sm text-gray-600 dark:text-gray-400">Confidence</p>
                      <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{(pricePrediction.confidence * 100).toFixed(0)}%</p>
                    </div>
                    <div className="bg-purple-50 dark:bg-purple-900/20 rounded-xl p-4 text-center">
                      <p className="text-sm text-gray-600 dark:text-gray-400">Best Window</p>
                      <p className="text-lg font-bold text-purple-600 dark:text-purple-400">{pricePrediction.best_booking_window || 'N/A'}</p>
                    </div>
                  </div>
                )}

                <p className="text-gray-700 dark:text-gray-300 mb-4">{pricePrediction.reasoning}</p>

                {pricePrediction.forecast && pricePrediction.forecast.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-white mb-3">30-Day Forecast</h4>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                      {pricePrediction.forecast.map((f, i) => (
                        <div key={i} className="bg-gray-50 dark:bg-gray-700 rounded-xl p-3 text-center">
                          <p className="text-xs text-gray-500 dark:text-gray-400">Day {f.days_from_now}</p>
                          <p className="text-lg font-bold text-gray-900 dark:text-white">${f.estimated_price}</p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            ${f.range[0]} - ${f.range[1]}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Best Time Tab */}
        {activeTab === 'besttime' && (
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Best Time to Visit</h2>
              <div className="flex gap-4">
                <input
                  type="text"
                  placeholder="Destination (e.g., Paris, France)"
                  value={btDest}
                  onChange={(e) => setBtDest(e.target.value)}
                  className="flex-1 px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                <button
                  onClick={handleBestTime}
                  disabled={btLoading || !btDest}
                  className="px-6 py-3 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl hover:from-indigo-700 hover:via-purple-700 hover:to-pink-700 disabled:opacity-50 transition-all"
                >
                  {btLoading ? 'Analyzing...' : 'Analyze'}
                </button>
              </div>
            </div>

            {bestTime && (
              <div className="space-y-6">
                <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-3">
                    {bestTime.destination}
                  </h3>
                  <p className="text-gray-700 dark:text-gray-300 mb-4">{bestTime.overall_recommendation}</p>

                  {(bestTime.budget_tip || bestTime.weather_tip) && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                      {bestTime.budget_tip && (
                        <div className="bg-green-50 dark:bg-green-900/20 rounded-xl p-4">
                          <p className="text-sm font-semibold text-green-800 dark:text-green-300 mb-1">Budget Tip</p>
                          <p className="text-sm text-green-700 dark:text-green-400">{bestTime.budget_tip}</p>
                        </div>
                      )}
                      {bestTime.weather_tip && (
                        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4">
                          <p className="text-sm font-semibold text-blue-800 dark:text-blue-300 mb-1">Weather Tip</p>
                          <p className="text-sm text-blue-700 dark:text-blue-400">{bestTime.weather_tip}</p>
                        </div>
                      )}
                    </div>
                  )}

                  {bestTime.peak_season && (
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                      <div className="bg-red-50 dark:bg-red-900/20 rounded-xl p-4">
                        <p className="text-sm font-semibold text-red-800 dark:text-red-300 mb-1">Peak Season</p>
                        <p className="text-sm text-red-700 dark:text-red-400">{bestTime.peak_season.months.join(', ')}</p>
                        <p className="text-xs text-red-600 dark:text-red-500 mt-1">{bestTime.peak_season.reason}</p>
                      </div>
                      {bestTime.shoulder_season && (
                        <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-xl p-4">
                          <p className="text-sm font-semibold text-yellow-800 dark:text-yellow-300 mb-1">Shoulder Season</p>
                          <p className="text-sm text-yellow-700 dark:text-yellow-400">{bestTime.shoulder_season.months.join(', ')}</p>
                          <p className="text-xs text-yellow-600 dark:text-yellow-500 mt-1">{bestTime.shoulder_season.reason}</p>
                        </div>
                      )}
                      {bestTime.off_season && (
                        <div className="bg-emerald-50 dark:bg-emerald-900/20 rounded-xl p-4">
                          <p className="text-sm font-semibold text-emerald-800 dark:text-emerald-300 mb-1">Off Season</p>
                          <p className="text-sm text-emerald-700 dark:text-emerald-400">{bestTime.off_season.months.join(', ')}</p>
                          <p className="text-xs text-emerald-600 dark:text-emerald-500 mt-1">{bestTime.off_season.reason}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {bestTime.best_months && bestTime.best_months.length > 0 && (
                  <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                    <h4 className="font-bold text-gray-900 dark:text-white mb-4">Monthly Breakdown</h4>
                    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                      {bestTime.best_months.map((m, i) => (
                        <div key={i} className="bg-gray-50 dark:bg-gray-700 rounded-xl p-3">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-semibold text-gray-900 dark:text-white text-sm">{m.month}</span>
                            <span className="text-xs font-bold text-purple-600 dark:text-purple-400">{m.score}/100</span>
                          </div>
                          <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-1.5 mb-2">
                            <div
                              className="bg-gradient-to-r from-purple-500 to-pink-500 h-1.5 rounded-full"
                              style={{ width: `${m.score}%` }}
                            />
                          </div>
                          <p className="text-xs text-gray-600 dark:text-gray-400">{m.weather}</p>
                          <div className="flex gap-2 mt-1">
                            <span className={`text-xs ${crowdColor(m.crowds)}`}>Crowds: {m.crowds}</span>
                          </div>
                          <span className={`text-xs ${crowdColor(m.prices === 'high' ? 'high' : m.prices === 'low' ? 'low' : 'moderate')}`}>
                            Prices: {m.prices}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Trends Tab */}
        {activeTab === 'trends' && (
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">Trending Destinations</h2>
                <button
                  onClick={handleTrends}
                  disabled={trendsLoading}
                  className="px-5 py-2.5 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl hover:from-indigo-700 hover:via-purple-700 hover:to-pink-700 disabled:opacity-50 transition-all text-sm"
                >
                  {trendsLoading ? 'Loading...' : 'Refresh Trends'}
                </button>
              </div>
              <p className="text-gray-600 dark:text-gray-400 text-sm mb-6">
                Based on search patterns from the last 30 days.
              </p>

              {trends.length > 0 ? (
                <div className="space-y-3">
                  {trends.map((t) => (
                    <div
                      key={t.rank}
                      className="flex items-center gap-4 bg-gray-50 dark:bg-gray-700 rounded-xl p-4 hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
                    >
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-white ${
                        t.rank <= 3 ? 'bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500' : 'bg-gray-400 dark:bg-gray-500'
                      }`}>
                        {t.rank}
                      </div>
                      <div className="flex-1">
                        <p className="font-semibold text-gray-900 dark:text-white">{t.destination}</p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">{t.search_count} searches</p>
                      </div>
                      <div className="w-24 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                        <div
                          className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full"
                          style={{ width: `${Math.min((t.search_count / (trends[0]?.search_count || 1)) * 100, 100)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                  <p className="text-4xl mb-3">📊</p>
                  <p>Click "Refresh Trends" to load trending destinations.</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PredictionsPage;
