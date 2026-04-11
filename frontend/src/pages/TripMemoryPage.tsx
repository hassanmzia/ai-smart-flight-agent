import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '@/services/api';

/* ─── Types ─── */
interface TripMemory {
  id: number;
  destination: string;
  trip_date: string;
  sentiment: string;
  highlights: string[];
  lowlights: string[];
  tags: string[];
  budget_spent: number | null;
  rating: number;
  notes: string;
}

interface Suggestion {
  destination: string;
  reason: string;
  match_score: number;
  based_on: string;
}

interface FeedbackSummary {
  total_trips: number;
  avg_rating: number;
  top_sentiments: Record<string, number>;
  most_visited: Array<{ destination: string; count: number }>;
  favorite_tags: Array<{ tag: string; count: number }>;
  spending_trend: string;
}

const SENTIMENT_CONFIG: Record<string, { emoji: string; color: string; label: string }> = {
  loved: { emoji: '&#10084;&#65039;', color: 'text-red-500', label: 'Loved' },
  liked: { emoji: '&#128077;', color: 'text-blue-500', label: 'Liked' },
  neutral: { emoji: '&#128528;', color: 'text-gray-500', label: 'Neutral' },
  disliked: { emoji: '&#128078;', color: 'text-orange-500', label: 'Disliked' },
};

function StarRating({
  value,
  onChange,
}: {
  value: number;
  onChange?: (v: number) => void;
}) {
  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          onClick={() => onChange?.(star)}
          className={`text-xl transition-colors ${
            star <= value ? 'text-yellow-400' : 'text-gray-300 dark:text-gray-600'
          } ${onChange ? 'cursor-pointer hover:text-yellow-300' : 'cursor-default'}`}
        >
          &#9733;
        </button>
      ))}
    </div>
  );
}

export default function TripMemoryPage() {
  const [activeTab, setActiveTab] = useState<'memories' | 'add' | 'insights' | 'suggestions'>(
    'memories'
  );

  /* ─── Memories List ─── */
  const [memories, setMemories] = useState<TripMemory[]>([]);
  const [loadingMemories, setLoadingMemories] = useState(false);

  /* ─── Add Memory Form ─── */
  const [formDest, setFormDest] = useState('');
  const [formDate, setFormDate] = useState('');
  const [formSentiment, setFormSentiment] = useState('liked');
  const [formRating, setFormRating] = useState(4);
  const [formHighlights, setFormHighlights] = useState('');
  const [formLowlights, setFormLowlights] = useState('');
  const [formTags, setFormTags] = useState('');
  const [formBudget, setFormBudget] = useState('');
  const [formNotes, setFormNotes] = useState('');
  const [saving, setSaving] = useState(false);

  /* ─── Insights ─── */
  const [insights, setInsights] = useState<Record<string, unknown> | null>(null);
  const [loadingInsights, setLoadingInsights] = useState(false);
  const [summary, setSummary] = useState<FeedbackSummary | null>(null);

  /* ─── Suggestions ─── */
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);

  const fetchMemories = async () => {
    setLoadingMemories(true);
    try {
      const res = await api.get('/api/agents/memories');
      setMemories(res.data.memories || res.data.items || res.data || []);
    } catch {
      setMemories([]);
    } finally {
      setLoadingMemories(false);
    }
  };

  const saveMemory = async () => {
    if (!formDest) return;
    setSaving(true);
    try {
      await api.post('/api/agents/memories/record', {
        destination: formDest,
        trip_date: formDate || null,
        sentiment: formSentiment,
        rating: formRating,
        highlights: formHighlights
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
        lowlights: formLowlights
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
        tags: formTags
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
        budget_spent: formBudget ? parseFloat(formBudget) : null,
        notes: formNotes,
      });
      // Reset form
      setFormDest('');
      setFormDate('');
      setFormSentiment('liked');
      setFormRating(4);
      setFormHighlights('');
      setFormLowlights('');
      setFormTags('');
      setFormBudget('');
      setFormNotes('');
      setActiveTab('memories');
      fetchMemories();
    } catch {
      /* ignore */
    } finally {
      setSaving(false);
    }
  };

  const fetchInsights = async () => {
    setLoadingInsights(true);
    try {
      const [insRes, sumRes] = await Promise.all([
        api.get('/api/agents/memories/insights'),
        api.get('/api/agents/memories/summary'),
      ]);
      setInsights(insRes.data.insights || insRes.data);
      setSummary(sumRes.data.summary || sumRes.data);
    } catch {
      setInsights(null);
      setSummary(null);
    } finally {
      setLoadingInsights(false);
    }
  };

  const fetchSuggestions = async () => {
    setLoadingSuggestions(true);
    try {
      const res = await api.get('/api/agents/memories/suggestions');
      setSuggestions(res.data.suggestions || []);
    } catch {
      setSuggestions([]);
    } finally {
      setLoadingSuggestions(false);
    }
  };

  useEffect(() => {
    fetchMemories();
  }, []);

  useEffect(() => {
    if (activeTab === 'insights') fetchInsights();
    if (activeTab === 'suggestions') fetchSuggestions();
  }, [activeTab]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-rose-50 via-white to-orange-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 py-10 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-10"
        >
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-3">
            Trip Memory
          </h1>
          <p className="text-gray-600 dark:text-gray-400 text-lg">
            Record your travels and let AI learn your preferences for smarter recommendations
          </p>
        </motion.div>

        {/* Tabs */}
        <div className="flex justify-center gap-2 mb-8 flex-wrap">
          {(
            [
              { id: 'memories', label: 'My Trips' },
              { id: 'add', label: 'Add Trip' },
              { id: 'insights', label: 'Insights' },
              { id: 'suggestions', label: 'Suggestions' },
            ] as const
          ).map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-5 py-2.5 rounded-full font-medium text-sm transition-all ${
                activeTab === tab.id
                  ? 'bg-rose-600 text-white shadow-lg'
                  : 'bg-white dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <AnimatePresence mode="wait">
          {/* ──── Memories List ──── */}
          {activeTab === 'memories' && (
            <motion.div key="memories" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              {loadingMemories ? (
                <div className="text-center py-12">
                  <div className="animate-spin h-8 w-8 border-4 border-rose-400 border-t-transparent rounded-full mx-auto mb-3" />
                </div>
              ) : memories.length === 0 ? (
                <div className="text-center py-16 text-gray-400">
                  <p className="text-5xl mb-4">&#128747;</p>
                  <p className="text-lg">No trip memories yet. Add your first trip!</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {memories.map((m) => {
                    const sc = SENTIMENT_CONFIG[m.sentiment] || SENTIMENT_CONFIG.neutral;
                    return (
                      <motion.div
                        key={m.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-5"
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                              {m.destination}
                            </h3>
                            <p className="text-sm text-gray-500 dark:text-gray-400">
                              {m.trip_date || 'Date not recorded'}
                            </p>
                          </div>
                          <div className="flex items-center gap-2">
                            <span
                              className={`text-lg ${sc.color}`}
                              dangerouslySetInnerHTML={{ __html: sc.emoji }}
                            />
                            <StarRating value={m.rating} />
                          </div>
                        </div>

                        {m.highlights.length > 0 && (
                          <div className="mt-3">
                            <span className="text-xs font-semibold text-green-600 dark:text-green-400">Highlights: </span>
                            <span className="text-sm text-gray-600 dark:text-gray-400">
                              {m.highlights.join(', ')}
                            </span>
                          </div>
                        )}

                        {m.tags.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 mt-2">
                            {m.tags.map((tag) => (
                              <span
                                key={tag}
                                className="px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-xs text-gray-600 dark:text-gray-400"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}

                        {m.budget_spent != null && (
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                            Budget spent: ${m.budget_spent.toFixed(0)}
                          </p>
                        )}
                      </motion.div>
                    );
                  })}
                </div>
              )}
            </motion.div>
          )}

          {/* ──── Add Trip ──── */}
          {activeTab === 'add' && (
            <motion.div key="add" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-6 md:p-8 space-y-5">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">Record a Trip</h2>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Destination *
                    </label>
                    <input
                      value={formDest}
                      onChange={(e) => setFormDest(e.target.value)}
                      placeholder="e.g. Tokyo"
                      className="w-full rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-4 py-3 text-gray-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Trip Date
                    </label>
                    <input
                      type="date"
                      value={formDate}
                      onChange={(e) => setFormDate(e.target.value)}
                      className="w-full rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-4 py-3 text-gray-900 dark:text-white"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    How was it?
                  </label>
                  <div className="flex gap-3 flex-wrap">
                    {Object.entries(SENTIMENT_CONFIG).map(([key, cfg]) => (
                      <button
                        key={key}
                        onClick={() => setFormSentiment(key)}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                          formSentiment === key
                            ? 'bg-rose-600 text-white'
                            : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                        }`}
                      >
                        <span dangerouslySetInnerHTML={{ __html: cfg.emoji }} /> {cfg.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Rating
                  </label>
                  <StarRating value={formRating} onChange={setFormRating} />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Highlights (comma-separated)
                  </label>
                  <input
                    value={formHighlights}
                    onChange={(e) => setFormHighlights(e.target.value)}
                    placeholder="e.g. Amazing food, Beautiful temples, Friendly locals"
                    className="w-full rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-4 py-3 text-gray-900 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Lowlights (comma-separated)
                  </label>
                  <input
                    value={formLowlights}
                    onChange={(e) => setFormLowlights(e.target.value)}
                    placeholder="e.g. Crowded trains, Expensive meals"
                    className="w-full rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-4 py-3 text-gray-900 dark:text-white"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Tags (comma-separated)
                    </label>
                    <input
                      value={formTags}
                      onChange={(e) => setFormTags(e.target.value)}
                      placeholder="e.g. beach, food, history"
                      className="w-full rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-4 py-3 text-gray-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Budget Spent ($)
                    </label>
                    <input
                      type="number"
                      value={formBudget}
                      onChange={(e) => setFormBudget(e.target.value)}
                      placeholder="e.g. 2500"
                      className="w-full rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-4 py-3 text-gray-900 dark:text-white"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Notes</label>
                  <textarea
                    value={formNotes}
                    onChange={(e) => setFormNotes(e.target.value)}
                    rows={3}
                    placeholder="Any additional notes about the trip..."
                    className="w-full rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-4 py-3 text-gray-900 dark:text-white"
                  />
                </div>

                <button
                  onClick={saveMemory}
                  disabled={!formDest || saving}
                  className="w-full py-3 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-semibold disabled:opacity-50"
                >
                  {saving ? 'Saving...' : 'Save Memory'}
                </button>
              </div>
            </motion.div>
          )}

          {/* ──── Insights ──── */}
          {activeTab === 'insights' && (
            <motion.div key="insights" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              {loadingInsights ? (
                <div className="text-center py-12">
                  <div className="animate-spin h-8 w-8 border-4 border-rose-400 border-t-transparent rounded-full mx-auto mb-3" />
                  <p className="text-gray-500 dark:text-gray-400">Analyzing your travel history...</p>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Summary stats */}
                  {summary && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-4 text-center">
                        <p className="text-3xl font-bold text-rose-600">{summary.total_trips}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Trips Recorded</p>
                      </div>
                      <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-4 text-center">
                        <p className="text-3xl font-bold text-yellow-500">{summary.avg_rating?.toFixed(1) || '—'}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Avg Rating</p>
                      </div>
                      <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-4 text-center">
                        <p className="text-3xl font-bold text-blue-600">
                          {summary.most_visited?.[0]?.destination || '—'}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Most Visited</p>
                      </div>
                      <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-4 text-center">
                        <p className="text-3xl font-bold text-green-600 capitalize">{summary.spending_trend || '—'}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Spending Trend</p>
                      </div>
                    </div>
                  )}

                  {/* AI insights */}
                  {insights && (
                    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-6 space-y-4">
                      <h2 className="text-xl font-bold text-gray-900 dark:text-white">AI Travel Insights</h2>
                      {insights.travel_personality && (
                        <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-xl">
                          <h3 className="text-sm font-semibold text-purple-700 dark:text-purple-400 mb-1">Your Travel Personality</h3>
                          <p className="text-sm text-gray-700 dark:text-gray-300">{insights.travel_personality as string}</p>
                        </div>
                      )}
                      {Array.isArray(insights.preferred_styles) && (
                        <div>
                          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Preferred Styles</h3>
                          <div className="flex flex-wrap gap-2">
                            {(insights.preferred_styles as string[]).map((s) => (
                              <span key={s} className="px-3 py-1 rounded-full bg-rose-100 dark:bg-rose-900/30 text-rose-700 dark:text-rose-400 text-sm font-medium">
                                {s}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      {insights.budget_pattern && (
                        <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-xl">
                          <h3 className="text-sm font-semibold text-green-700 dark:text-green-400 mb-1">Budget Pattern</h3>
                          <p className="text-sm text-gray-700 dark:text-gray-300">{insights.budget_pattern as string}</p>
                        </div>
                      )}
                      {Array.isArray(insights.growth_areas) && (
                        <div>
                          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Growth Areas</h3>
                          {(insights.growth_areas as string[]).map((a, i) => (
                            <p key={i} className="text-sm text-gray-600 dark:text-gray-400 py-0.5">&#8226; {a}</p>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {!insights && !summary && (
                    <div className="text-center py-12 text-gray-400">
                      <p className="text-lg">Record more trips to unlock AI insights!</p>
                    </div>
                  )}
                </div>
              )}
            </motion.div>
          )}

          {/* ──── Suggestions ──── */}
          {activeTab === 'suggestions' && (
            <motion.div key="suggestions" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              {loadingSuggestions ? (
                <div className="text-center py-12">
                  <div className="animate-spin h-8 w-8 border-4 border-rose-400 border-t-transparent rounded-full mx-auto mb-3" />
                  <p className="text-gray-500 dark:text-gray-400">Finding your next adventure...</p>
                </div>
              ) : suggestions.length === 0 ? (
                <div className="text-center py-16 text-gray-400">
                  <p className="text-5xl mb-4">&#127760;</p>
                  <p className="text-lg">Record some trips first so we can suggest destinations for you!</p>
                </div>
              ) : (
                <div className="space-y-4">
                  <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                    Recommended for You
                  </h2>
                  {suggestions.map((s, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-5 flex items-center gap-4"
                    >
                      <div
                        className="w-14 h-14 rounded-full bg-rose-100 dark:bg-rose-900/30 flex items-center justify-center text-lg font-bold text-rose-600 dark:text-rose-400 flex-shrink-0"
                      >
                        {Math.round(s.match_score * 100)}%
                      </div>
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                          {s.destination}
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">{s.reason}</p>
                        <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                          Based on: {s.based_on}
                        </p>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
