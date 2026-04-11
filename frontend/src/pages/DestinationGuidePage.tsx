import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '@/services/api';

interface GuideItem {
  name: string;
  description: string;
  rating: number;
  price_range: string;
  best_time: string;
  address: string;
  tags: string[];
}

interface Guide {
  id: number;
  destination: string;
  guide_type: string;
  title: string;
  description: string;
  items: GuideItem[];
}

const GUIDE_TYPES = [
  { value: 'must_visit', label: 'Must Visit', icon: '&#128205;' },
  { value: 'must_eat', label: 'Must Eat', icon: '&#127860;' },
  { value: 'must_see', label: 'Must See', icon: '&#128247;' },
  { value: 'must_do', label: 'Must Do', icon: '&#127947;' },
  { value: 'hidden_gem', label: 'Hidden Gems', icon: '&#128142;' },
];

const PRICE_COLORS: Record<string, string> = {
  $: 'text-green-600 bg-green-100 dark:bg-green-900/30 dark:text-green-400',
  $$: 'text-blue-600 bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400',
  $$$: 'text-purple-600 bg-purple-100 dark:bg-purple-900/30 dark:text-purple-400',
  $$$$: 'text-amber-600 bg-amber-100 dark:bg-amber-900/30 dark:text-amber-400',
};

function ScoreCircle({ score }: { score: number }) {
  const pct = (score / 10) * 100;
  const color =
    score >= 8.5
      ? 'text-green-500'
      : score >= 7
        ? 'text-blue-500'
        : score >= 5
          ? 'text-yellow-500'
          : 'text-red-500';
  const stroke =
    score >= 8.5
      ? 'stroke-green-500'
      : score >= 7
        ? 'stroke-blue-500'
        : score >= 5
          ? 'stroke-yellow-500'
          : 'stroke-red-500';

  return (
    <div className="relative w-12 h-12">
      <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
        <circle
          cx="18"
          cy="18"
          r="15"
          fill="none"
          stroke="currentColor"
          strokeWidth="3"
          className="text-gray-200 dark:text-gray-700"
        />
        <circle
          cx="18"
          cy="18"
          r="15"
          fill="none"
          strokeWidth="3"
          strokeDasharray={`${pct} 100`}
          strokeLinecap="round"
          className={stroke}
        />
      </svg>
      <span
        className={`absolute inset-0 flex items-center justify-center text-xs font-bold ${color}`}
      >
        {score}
      </span>
    </div>
  );
}

export default function DestinationGuidePage() {
  const [destination, setDestination] = useState('');
  const [selectedType, setSelectedType] = useState('must_visit');
  const [guide, setGuide] = useState<Guide | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Live context state
  const [liveCtx, setLiveCtx] = useState<Record<string, unknown> | null>(null);
  const [loadingCtx, setLoadingCtx] = useState(false);

  const fetchGuide = async (type?: string) => {
    const guideType = type || selectedType;
    if (!destination.trim()) return;
    setLoading(true);
    setError('');
    try {
      const res = await api.post('/api/community/curated-guides/generate/', {
        destination: destination.trim(),
        guide_type: guideType,
      });
      setGuide(res.data);
    } catch {
      setError('Could not load guide. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchLiveContext = async () => {
    if (!destination.trim()) return;
    setLoadingCtx(true);
    try {
      const res = await api.get(
        `/api/agents/live-context?destination=${encodeURIComponent(destination.trim())}`
      );
      setLiveCtx(res.data);
    } catch {
      setLiveCtx(null);
    } finally {
      setLoadingCtx(false);
    }
  };

  const handleSearch = () => {
    fetchGuide();
    fetchLiveContext();
  };

  const weather = liveCtx?.weather as
    | { temperature: number; condition: string; impact_level: string; suggestion: string; icon: string }
    | undefined;
  const crowd = liveCtx?.crowd_summary as
    | { current_level: number; current_label: string; best_time_to_visit: string[] }
    | undefined;

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 py-10 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-10"
        >
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-3">
            Destination Guide
          </h1>
          <p className="text-gray-600 dark:text-gray-400 text-lg">
            AI-curated must-visit, must-eat, and must-see lists for any destination
          </p>
        </motion.div>

        {/* Search */}
        <div className="flex gap-3 mb-8 max-w-2xl mx-auto">
          <input
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Enter a destination (e.g. Paris, Tokyo, Barcelona...)"
            className="flex-1 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-5 py-3 text-gray-900 dark:text-white focus:ring-2 focus:ring-teal-500 focus:border-transparent"
          />
          <button
            onClick={handleSearch}
            disabled={!destination.trim() || loading}
            className="px-6 py-3 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-semibold disabled:opacity-50 transition-colors"
          >
            {loading ? 'Loading...' : 'Explore'}
          </button>
        </div>

        {/* Live Context Banner */}
        {liveCtx && weather && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-5 mb-8 grid grid-cols-1 md:grid-cols-3 gap-4"
          >
            {/* Weather */}
            <div className="flex items-center gap-3">
              <img
                src={`https://openweathermap.org/img/wn/${weather.icon}@2x.png`}
                alt={weather.condition}
                className="w-14 h-14"
              />
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {weather.temperature}&deg;C
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400 capitalize">
                  {weather.condition}
                </p>
              </div>
            </div>

            {/* Crowd */}
            {crowd && (
              <div className="flex items-center gap-3">
                <div
                  className={`w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold ${
                    crowd.current_level <= 4
                      ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                      : crowd.current_level <= 7
                        ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                        : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                  }`}
                >
                  {crowd.current_level}
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-900 dark:text-white">
                    {crowd.current_label}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Best: {crowd.best_time_to_visit?.slice(0, 2).join(', ')}
                  </p>
                </div>
              </div>
            )}

            {/* Impact */}
            <div className="flex items-center">
              <p className="text-sm text-gray-600 dark:text-gray-400 leading-snug">
                {weather.suggestion}
              </p>
            </div>
          </motion.div>
        )}

        {loadingCtx && !liveCtx && (
          <div className="text-center mb-6 text-sm text-gray-500 dark:text-gray-400">
            Loading live conditions...
          </div>
        )}

        {/* Guide Type Tabs */}
        {(guide || loading) && (
          <div className="flex flex-wrap justify-center gap-2 mb-8">
            {GUIDE_TYPES.map((t) => (
              <button
                key={t.value}
                onClick={() => {
                  setSelectedType(t.value);
                  fetchGuide(t.value);
                }}
                className={`px-4 py-2 rounded-full font-medium text-sm transition-all ${
                  selectedType === t.value
                    ? 'bg-teal-600 text-white shadow-lg'
                    : 'bg-white dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600'
                }`}
              >
                <span dangerouslySetInnerHTML={{ __html: t.icon }} /> {t.label}
              </button>
            ))}
          </div>
        )}

        {error && (
          <div className="text-center text-red-500 mb-6">{error}</div>
        )}

        {/* Loading */}
        {loading && (
          <div className="text-center py-16">
            <div className="animate-spin h-10 w-10 border-4 border-teal-400 border-t-transparent rounded-full mx-auto mb-4" />
            <p className="text-gray-500 dark:text-gray-400">Generating curated guide...</p>
          </div>
        )}

        {/* Guide Results */}
        <AnimatePresence mode="wait">
          {!loading && guide && (
            <motion.div
              key={guide.guide_type}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <div className="mb-6">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                  {guide.title}
                </h2>
                <p className="text-gray-600 dark:text-gray-400 mt-1">
                  {guide.description}
                </p>
              </div>

              <div className="space-y-4">
                {guide.items.map((item, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-5 flex gap-5"
                  >
                    {/* Rank number */}
                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-400 flex items-center justify-center font-bold text-lg">
                      {idx + 1}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-3">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                          {item.name}
                        </h3>
                        <ScoreCircle score={item.rating} />
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        {item.description}
                      </p>

                      <div className="flex flex-wrap items-center gap-3 mt-3">
                        {item.price_range && (
                          <span
                            className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                              PRICE_COLORS[item.price_range] ||
                              'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                            }`}
                          >
                            {item.price_range}
                          </span>
                        )}
                        {item.best_time && (
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            Best: {item.best_time}
                          </span>
                        )}
                        {item.address && (
                          <span className="text-xs text-gray-500 dark:text-gray-400 truncate max-w-[200px]">
                            {item.address}
                          </span>
                        )}
                      </div>

                      {item.tags?.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mt-2">
                          {item.tags.map((tag) => (
                            <span
                              key={tag}
                              className="px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-xs text-gray-600 dark:text-gray-400"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Empty state */}
        {!loading && !guide && !error && (
          <div className="text-center py-20 text-gray-400 dark:text-gray-500">
            <p className="text-5xl mb-4">&#127758;</p>
            <p className="text-lg">Enter a destination to discover curated guides</p>
          </div>
        )}
      </div>
    </div>
  );
}
