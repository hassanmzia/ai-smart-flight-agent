import { useEffect, useRef, useState } from 'react';
import api from '@/services/api';
import { ROUTES } from '@/utils/constants';

interface Props {
  destination: string;
  startDate?: string;
  endDate?: string;
  travelers?: number;
}

interface Preview {
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
  crowd_forecast?: { level: string; description: string; tip: string };
  daily_budget?: {
    budget_usd: number;
    mid_range_usd: number;
    luxury_usd: number;
    currency: string;
    exchange_note: string;
  };
  safety_wellness?: { safety_level: string; tips: string[]; health_note: string };
  food_scene?: { summary: string; dining_tip: string };
  a_day_in_your_trip?: { morning: string; afternoon: string; evening: string };
  cultural_highlights?: Array<{ title: string; description: string; icon: string }>;
  trip_score?: { overall: number };
}

/**
 * SmartTripPreview — inline, live trip intelligence right on the planning
 * page. Shows weather, safety, budget, crowd, and a "day in your trip"
 * snippet without navigating anywhere. Deep-dive links open in new tabs.
 */
const SmartTripPreview = ({ destination, startDate, endDate, travelers = 2 }: Props) => {
  const [data, setData] = useState<Preview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const cacheRef = useRef<Map<string, Preview>>(new Map());

  // Build query string used by deep-dive chips
  const params = new URLSearchParams({ destination });
  if (startDate) params.set('start_date', startDate);
  if (endDate) params.set('end_date', endDate);
  if (travelers) params.set('travelers', String(travelers));
  const q = `?${params.toString()}`;

  useEffect(() => {
    if (!destination || !startDate || !endDate) {
      setData(null);
      return;
    }
    const key = `${destination}|${startDate}|${endDate}|${travelers}`;
    const cached = cacheRef.current.get(key);
    if (cached) {
      setData(cached);
      return;
    }
    let cancelled = false;
    // Debounce so we don't fire on every keystroke
    const t = setTimeout(() => {
      setLoading(true);
      setError(false);
      api
        .post('/api/agents/trip-experience', {
          destination,
          start_date: startDate,
          end_date: endDate,
          travelers,
        })
        .then((res) => {
          if (cancelled) return;
          cacheRef.current.set(key, res.data);
          setData(res.data);
        })
        .catch(() => {
          if (!cancelled) setError(true);
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    }, 400);
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [destination, startDate, endDate, travelers]);

  if (!destination) return null;

  const cToF = (c: number) => Math.round((c * 9) / 5 + 32);

  const safetyColor = (level?: string) => {
    const l = (level || '').toLowerCase();
    if (l.includes('low') || l.includes('safe')) return 'text-emerald-600 dark:text-emerald-400';
    if (l.includes('moderate') || l.includes('medium')) return 'text-amber-600 dark:text-amber-400';
    if (l.includes('high') || l.includes('caution')) return 'text-orange-600 dark:text-orange-400';
    if (l.includes('extreme') || l.includes('danger')) return 'text-red-600 dark:text-red-400';
    return 'text-gray-600 dark:text-gray-400';
  };

  const crowdColor = (level?: string) => {
    const l = (level || '').toLowerCase();
    if (l.includes('low')) return 'text-emerald-600 dark:text-emerald-400';
    if (l.includes('moderate')) return 'text-amber-600 dark:text-amber-400';
    return 'text-orange-600 dark:text-orange-400';
  };

  // ── Dates missing: compact teaser
  if (!startDate || !endDate) {
    return (
      <div className="mb-6 rounded-2xl border border-purple-200/70 dark:border-purple-800/40 bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 dark:from-indigo-900/20 dark:via-purple-900/20 dark:to-pink-900/20 p-4 sm:p-5">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🧭</span>
          <div className="flex-1 min-w-0">
            <h3 className="font-bold text-gray-900 dark:text-white text-sm sm:text-base">
              Smart Preview for <span className="text-purple-700 dark:text-purple-300">{destination}</span>
            </h3>
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
              Add your travel dates above to see live weather, safety, budget, and crowd insights — all right here, no clicks needed.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // ── Loading: skeleton row
  if (loading && !data) {
    return (
      <div className="mb-6 rounded-2xl border border-purple-200/70 dark:border-purple-800/40 bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 dark:from-indigo-900/20 dark:via-purple-900/20 dark:to-pink-900/20 p-4 sm:p-5">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xl">🧭</span>
          <h3 className="font-bold text-gray-900 dark:text-white text-sm sm:text-base">
            Previewing {destination}…
          </h3>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 sm:gap-3">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="h-20 rounded-xl bg-white/60 dark:bg-gray-800/40 animate-pulse border border-white/60 dark:border-gray-700/40" />
          ))}
        </div>
      </div>
    );
  }

  // ── Error: silent minimal strip (still offers deep-dive chips)
  if (error && !data) {
    return (
      <div className="mb-6 rounded-2xl border border-purple-200/70 dark:border-purple-800/40 bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 dark:from-indigo-900/20 dark:via-purple-900/20 dark:to-pink-900/20 p-4 sm:p-5">
        <div className="flex items-center gap-3 mb-3">
          <span className="text-2xl">🧭</span>
          <div>
            <h3 className="font-bold text-gray-900 dark:text-white text-sm sm:text-base">
              Smart Preview for {destination}
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Live preview unavailable. Explore the deep-dive tools below.</p>
          </div>
        </div>
        <DeepDiveChips q={q} />
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="mb-6 rounded-2xl border border-purple-200/70 dark:border-purple-800/40 bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 dark:from-indigo-900/20 dark:via-purple-900/20 dark:to-pink-900/20 p-4 sm:p-5 shadow-sm">
      {/* Header */}
      <div className="flex items-start gap-3 mb-4">
        <span className="text-3xl sm:text-4xl leading-none">{data.vibe_emoji || '🧭'}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-extrabold text-gray-900 dark:text-white text-base sm:text-lg">
              {destination}
            </h3>
            {data.trip_score?.overall != null && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white text-[11px] font-bold">
                ⭐ {data.trip_score.overall}/10
              </span>
            )}
          </div>
          {data.tagline && (
            <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-300 mt-0.5 italic">
              "{data.tagline}"
            </p>
          )}
        </div>
      </div>

      {/* Stat cards: weather · safety · budget · crowds */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 sm:gap-3 mb-4">
        {/* Weather */}
        {data.weather_preview && (
          <div className="rounded-xl bg-white/80 dark:bg-gray-800/60 border border-white/60 dark:border-gray-700/50 p-3 backdrop-blur-sm">
            <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-sky-700 dark:text-sky-300">
              <span>🌤</span> Weather
            </div>
            <div className="font-bold text-gray-900 dark:text-white text-sm mt-1">
              {data.weather_preview.avg_temp_high_c}°C / {cToF(data.weather_preview.avg_temp_high_c)}°F
            </div>
            <div className="text-[11px] text-gray-600 dark:text-gray-400 leading-snug mt-0.5">
              {data.weather_preview.condition}
            </div>
          </div>
        )}

        {/* Safety */}
        {data.safety_wellness && (
          <div className="rounded-xl bg-white/80 dark:bg-gray-800/60 border border-white/60 dark:border-gray-700/50 p-3 backdrop-blur-sm">
            <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-blue-700 dark:text-blue-300">
              <span>🛡</span> Safety
            </div>
            <div className={`font-bold text-sm mt-1 capitalize ${safetyColor(data.safety_wellness.safety_level)}`}>
              {data.safety_wellness.safety_level || 'Moderate'}
            </div>
            {data.safety_wellness.tips?.[0] && (
              <div className="text-[11px] text-gray-600 dark:text-gray-400 leading-snug mt-0.5 line-clamp-2">
                {data.safety_wellness.tips[0]}
              </div>
            )}
          </div>
        )}

        {/* Budget */}
        {data.daily_budget && (
          <div className="rounded-xl bg-white/80 dark:bg-gray-800/60 border border-white/60 dark:border-gray-700/50 p-3 backdrop-blur-sm">
            <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-emerald-700 dark:text-emerald-300">
              <span>💰</span> Daily Budget
            </div>
            <div className="font-bold text-gray-900 dark:text-white text-sm mt-1">
              ${data.daily_budget.mid_range_usd}/day
            </div>
            <div className="text-[11px] text-gray-600 dark:text-gray-400 leading-snug mt-0.5">
              Budget ${data.daily_budget.budget_usd} · Lux ${data.daily_budget.luxury_usd}
            </div>
          </div>
        )}

        {/* Crowds */}
        {data.crowd_forecast && (
          <div className="rounded-xl bg-white/80 dark:bg-gray-800/60 border border-white/60 dark:border-gray-700/50 p-3 backdrop-blur-sm">
            <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-300">
              <span>👥</span> Crowds
            </div>
            <div className={`font-bold text-sm mt-1 capitalize ${crowdColor(data.crowd_forecast.level)}`}>
              {data.crowd_forecast.level}
            </div>
            <div className="text-[11px] text-gray-600 dark:text-gray-400 leading-snug mt-0.5 line-clamp-2">
              {data.crowd_forecast.description}
            </div>
          </div>
        )}
      </div>

      {/* A day in your trip (compact) */}
      {data.a_day_in_your_trip && (
        <div className="rounded-xl bg-white/80 dark:bg-gray-800/60 border border-white/60 dark:border-gray-700/50 p-3 mb-4 backdrop-blur-sm">
          <div className="text-[11px] font-semibold uppercase tracking-wide text-purple-700 dark:text-purple-300 mb-1.5">
            ✨ A day in your trip
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-xs text-gray-700 dark:text-gray-300">
            {data.a_day_in_your_trip.morning && (
              <div>
                <span className="font-semibold text-gray-900 dark:text-white">🌅 Morning:</span>{' '}
                <span className="text-gray-600 dark:text-gray-400">{data.a_day_in_your_trip.morning}</span>
              </div>
            )}
            {data.a_day_in_your_trip.afternoon && (
              <div>
                <span className="font-semibold text-gray-900 dark:text-white">☀️ Afternoon:</span>{' '}
                <span className="text-gray-600 dark:text-gray-400">{data.a_day_in_your_trip.afternoon}</span>
              </div>
            )}
            {data.a_day_in_your_trip.evening && (
              <div>
                <span className="font-semibold text-gray-900 dark:text-white">🌙 Evening:</span>{' '}
                <span className="text-gray-600 dark:text-gray-400">{data.a_day_in_your_trip.evening}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Deep-dive chips — open in new tab so planner stays put */}
      <DeepDiveChips q={q} />
    </div>
  );
};

const DeepDiveChips = ({ q }: { q: string }) => {
  const chips: Array<{ to: string; icon: string; label: string }> = [
    { to: `${ROUTES.PREDICTIONS}${q}&tab=experience`, icon: '✨', label: 'Full Preview' },
    { to: `${ROUTES.PREDICTIONS}${q}&tab=crowds`, icon: '👥', label: 'Crowd Calendar' },
    { to: `${ROUTES.PREDICTIONS}${q}&tab=prices`, icon: '💰', label: 'Price Forecast' },
    { to: `${ROUTES.SAFETY_DASHBOARD}${q}`, icon: '🛡', label: 'Safety Details' },
    { to: `${ROUTES.LANGUAGE_TOOL}${q}`, icon: '💬', label: 'Local Phrases' },
    { to: `${ROUTES.DESTINATION_GUIDE}${q}`, icon: '📍', label: 'Destination Guide' },
    { to: `${ROUTES.AI_RATINGS}${q}`, icon: '⭐', label: 'AI Ratings' },
    { to: `${ROUTES.PARTNERSHIPS}${q}`, icon: '🏷️', label: 'Deals & Coupons' },
  ];
  return (
    <div>
      <div className="text-[11px] font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
        Go deeper (opens in a new tab)
      </div>
      <div className="flex flex-wrap gap-1.5">
        {chips.map((c) => (
          <a
            key={c.to}
            href={c.to}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-full bg-white/80 dark:bg-gray-800/70 border border-purple-200/70 dark:border-purple-800/50 text-xs font-medium text-gray-700 dark:text-gray-300 hover:bg-white dark:hover:bg-gray-800 hover:border-purple-400 dark:hover:border-purple-600 hover:shadow-sm transition-all"
          >
            <span>{c.icon}</span>
            <span>{c.label}</span>
            <span className="opacity-50 text-[10px]">↗</span>
          </a>
        ))}
      </div>
    </div>
  );
};

export default SmartTripPreview;
