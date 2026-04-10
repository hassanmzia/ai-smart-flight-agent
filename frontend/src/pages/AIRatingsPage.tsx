import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '@/services/api';

interface AIRating {
  id: number;
  entity_type: string;
  entity_name: string;
  destination: string;
  overall_score: number;
  safety_score: number | null;
  value_score: number | null;
  food_score: number | null;
  culture_score: number | null;
  accessibility_score: number | null;
  community_rating: number | null;
  review_count: number;
  summary: string;
  pros: string[];
  cons: string[];
  best_for: string[];
  last_updated: string;
}

interface EnjoymentPrediction {
  enjoyment_score: number;
  explanation: string;
  matching_factors: string[];
  concerns: string[];
}

const ENTITY_TYPES = [
  { value: 'destination', label: 'Destination', icon: '\uD83C\uDF0D' },
  { value: 'hotel', label: 'Hotel', icon: '\uD83C\uDFE8' },
  { value: 'restaurant', label: 'Restaurant', icon: '\uD83C\uDF7D\uFE0F' },
  { value: 'attraction', label: 'Attraction', icon: '\uD83C\uDFDB\uFE0F' },
];

function ScoreCircle({ score, label, size = 'md' }: { score: number | null; label: string; size?: 'sm' | 'md' | 'lg' }) {
  if (score === null) return null;
  const s = Number(score);
  const color = s >= 8 ? 'text-green-600' : s >= 6 ? 'text-yellow-600' : s >= 4 ? 'text-orange-600' : 'text-red-600';
  const ring = s >= 8 ? 'ring-green-200' : s >= 6 ? 'ring-yellow-200' : s >= 4 ? 'ring-orange-200' : 'ring-red-200';
  const sz = size === 'lg' ? 'w-20 h-20' : size === 'md' ? 'w-14 h-14' : 'w-11 h-11';
  const textSz = size === 'lg' ? 'text-2xl' : size === 'md' ? 'text-lg' : 'text-sm';

  return (
    <div className="flex flex-col items-center gap-1">
      <div className={`${sz} rounded-full ring-4 ${ring} bg-white dark:bg-gray-800 flex items-center justify-center`}>
        <span className={`${textSz} font-bold ${color}`}>{s.toFixed(1)}</span>
      </div>
      <span className="text-xs text-gray-500 text-center">{label}</span>
    </div>
  );
}

export default function AIRatingsPage() {
  const [entityType, setEntityType] = useState('destination');
  const [entityName, setEntityName] = useState('');
  const [destination, setDestination] = useState('');
  const [rating, setRating] = useState<AIRating | null>(null);
  const [prediction, setPrediction] = useState<EnjoymentPrediction | null>(null);
  const [loading, setLoading] = useState(false);
  const [predicting, setPredicting] = useState(false);

  const getAIRating = async () => {
    if (!entityName.trim() || !destination.trim()) return;
    setLoading(true);
    setRating(null);
    setPrediction(null);
    try {
      const res = await api.post('/api/reviews/ai-ratings/rate/', {
        entity_type: entityType,
        entity_name: entityName,
        destination,
      });
      setRating(res.data);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  const predictEnjoyment = async () => {
    if (!entityName.trim() || !destination.trim()) return;
    setPredicting(true);
    try {
      const res = await api.get('/api/reviews/ai-ratings/predict/', {
        params: { entity_type: entityType, entity_name: entityName, destination },
      });
      setPrediction(res.data);
    } catch {
      // silent
    } finally {
      setPredicting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          AI Quality Ratings
        </h1>
        <p className="text-gray-500 dark:text-gray-400 mb-8">
          Get AI-powered quality scores and personalized enjoyment predictions for any destination, hotel, restaurant, or attraction.
        </p>

        {/* Search */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6 mb-8">
          {/* Entity Type */}
          <div className="flex gap-2 mb-4">
            {ENTITY_TYPES.map((et) => (
              <button
                key={et.value}
                onClick={() => setEntityType(et.value)}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium border-2 transition-all ${
                  entityType === et.value
                    ? 'border-violet-500 bg-violet-50 dark:bg-violet-900/30 text-violet-700'
                    : 'border-gray-200 dark:border-gray-700 text-gray-600'
                }`}
              >
                <span>{et.icon}</span> {et.label}
              </button>
            ))}
          </div>

          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              value={entityName}
              onChange={(e) => setEntityName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && getAIRating()}
              placeholder={entityType === 'destination' ? 'City name (e.g. Tokyo)' : 'Name (e.g. Grand Hyatt)'}
              className="flex-1 px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 dark:bg-gray-700 text-sm"
            />
            <input
              type="text"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && getAIRating()}
              placeholder="Destination (e.g. Tokyo, Japan)"
              className="flex-1 px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 dark:bg-gray-700 text-sm"
            />
            <button
              onClick={getAIRating}
              disabled={loading || !entityName.trim() || !destination.trim()}
              className="px-6 py-3 rounded-xl bg-violet-600 hover:bg-violet-700 text-white font-semibold text-sm transition-colors disabled:opacity-50 flex-shrink-0"
            >
              {loading ? 'Rating...' : 'Get AI Rating'}
            </button>
          </div>
        </div>

        {/* Results */}
        <AnimatePresence>
          {rating && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm overflow-hidden"
            >
              {/* Header */}
              <div className="bg-gradient-to-r from-violet-500 to-purple-600 p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-xl font-bold text-white">{rating.entity_name}</h2>
                    <p className="text-violet-200 text-sm">{rating.destination}</p>
                  </div>
                  <ScoreCircle score={rating.overall_score} label="Overall" size="lg" />
                </div>
              </div>

              <div className="p-6 space-y-6">
                {/* Score Breakdown */}
                <div className="flex flex-wrap justify-center gap-6">
                  <ScoreCircle score={rating.safety_score} label="Safety" />
                  <ScoreCircle score={rating.value_score} label="Value" />
                  <ScoreCircle score={rating.food_score} label="Food" />
                  <ScoreCircle score={rating.culture_score} label="Culture" />
                  <ScoreCircle score={rating.accessibility_score} label="Accessibility" />
                  {rating.community_rating && (
                    <ScoreCircle score={rating.community_rating} label="Community" />
                  )}
                </div>

                {/* Summary */}
                <p className="text-sm text-gray-600 dark:text-gray-400">{rating.summary}</p>

                {/* Pros & Cons */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {rating.pros.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-green-700 dark:text-green-400 mb-2">Pros</h4>
                      <ul className="space-y-1">
                        {rating.pros.map((p, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                            <span className="text-green-500 flex-shrink-0">+</span> {p}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {rating.cons.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-red-700 dark:text-red-400 mb-2">Cons</h4>
                      <ul className="space-y-1">
                        {rating.cons.map((c, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                            <span className="text-red-500 flex-shrink-0">-</span> {c}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Best For */}
                {rating.best_for.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">Best For</h4>
                    <div className="flex flex-wrap gap-2">
                      {rating.best_for.map((b, i) => (
                        <span key={i} className="px-3 py-1 rounded-full bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-300 text-sm font-medium">
                          {b}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Vacation Predictor */}
                <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-semibold text-gray-900 dark:text-white">
                      Vacation Predictor
                    </h4>
                    <button
                      onClick={predictEnjoyment}
                      disabled={predicting}
                      className="px-4 py-1.5 rounded-lg bg-amber-100 text-amber-700 hover:bg-amber-200 text-sm font-medium disabled:opacity-50"
                    >
                      {predicting ? 'Predicting...' : 'How much will I enjoy this?'}
                    </button>
                  </div>

                  {prediction && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      className="bg-amber-50 dark:bg-amber-900/20 rounded-xl p-4"
                    >
                      <div className="flex items-center gap-4 mb-3">
                        <div className="text-center">
                          <div className={`text-3xl font-bold ${
                            prediction.enjoyment_score >= 80 ? 'text-green-600' :
                            prediction.enjoyment_score >= 60 ? 'text-yellow-600' :
                            prediction.enjoyment_score >= 40 ? 'text-orange-600' : 'text-red-600'
                          }`}>
                            {prediction.enjoyment_score}%
                          </div>
                          <p className="text-xs text-gray-500">Enjoyment</p>
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400 flex-1">
                          {prediction.explanation}
                        </p>
                      </div>
                      {prediction.matching_factors.length > 0 && (
                        <div className="flex flex-wrap gap-1.5">
                          {prediction.matching_factors.map((f, i) => (
                            <span key={i} className="px-2 py-0.5 rounded bg-green-100 text-green-700 text-xs">
                              {f}
                            </span>
                          ))}
                        </div>
                      )}
                      {prediction.concerns.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mt-2">
                          {prediction.concerns.map((c, i) => (
                            <span key={i} className="px-2 py-0.5 rounded bg-red-100 text-red-700 text-xs">
                              {c}
                            </span>
                          ))}
                        </div>
                      )}
                    </motion.div>
                  )}
                </div>

                {/* Meta */}
                <p className="text-xs text-gray-400 text-right">
                  Last updated: {new Date(rating.last_updated).toLocaleDateString()} &middot; {rating.review_count} reviews
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
