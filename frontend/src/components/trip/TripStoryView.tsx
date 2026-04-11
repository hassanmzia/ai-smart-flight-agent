import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '@/services/api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface StoryDay {
  day_number: number;
  date: string;
  title: string;
  narrative: string;
  highlights: string[];
  mood: string;
}

interface TripStory {
  title: string;
  destination: string;
  summary: string;
  days: StoryDay[];
}

interface TripStoryViewProps {
  itineraryId: string | number;
  itineraryTitle: string;
  destination: string;
}

// ---------------------------------------------------------------------------
// Mood config
// ---------------------------------------------------------------------------

const MOOD_CONFIG: Record<string, { emoji: string; gradient: string; bg: string }> = {
  adventurous: { emoji: '\u26F0\uFE0F', gradient: 'from-orange-500 to-red-500', bg: 'bg-orange-50 dark:bg-orange-900/20' },
  relaxing: { emoji: '\uD83C\uDFD6\uFE0F', gradient: 'from-cyan-500 to-blue-500', bg: 'bg-cyan-50 dark:bg-cyan-900/20' },
  cultural: { emoji: '\uD83C\uDFDB\uFE0F', gradient: 'from-purple-500 to-indigo-500', bg: 'bg-purple-50 dark:bg-purple-900/20' },
  romantic: { emoji: '\uD83C\uDF39', gradient: 'from-pink-500 to-rose-500', bg: 'bg-pink-50 dark:bg-pink-900/20' },
  exciting: { emoji: '\uD83C\uDF89', gradient: 'from-amber-500 to-yellow-500', bg: 'bg-amber-50 dark:bg-amber-900/20' },
  culinary: { emoji: '\uD83C\uDF7D\uFE0F', gradient: 'from-emerald-500 to-teal-500', bg: 'bg-emerald-50 dark:bg-emerald-900/20' },
  serene: { emoji: '\uD83C\uDF3F', gradient: 'from-green-500 to-emerald-500', bg: 'bg-green-50 dark:bg-green-900/20' },
  vibrant: { emoji: '\uD83C\uDF08', gradient: 'from-violet-500 to-fuchsia-500', bg: 'bg-violet-50 dark:bg-violet-900/20' },
};

const DEFAULT_MOOD = { emoji: '\u2728', gradient: 'from-gray-500 to-gray-600', bg: 'bg-gray-50 dark:bg-gray-900/20' };

function getMood(mood: string) {
  return MOOD_CONFIG[mood.toLowerCase()] || DEFAULT_MOOD;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function TripStoryView({ itineraryId, itineraryTitle, destination }: TripStoryViewProps) {
  const [story, setStory] = useState<TripStory | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedDay, setExpandedDay] = useState<number | null>(null);
  const [isAutoPlaying, setIsAutoPlaying] = useState(false);
  const [currentAutoDay, setCurrentAutoDay] = useState(0);

  const generateStory = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.post(
        `/api/itineraries/itineraries/${itineraryId}/generate-story/`,
        {},
        { timeout: 60000 },
      );
      if (res.data?.story) {
        setStory(res.data.story);
        setExpandedDay(0);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to generate story. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, [itineraryId]);

  const startAutoPlay = useCallback(() => {
    if (!story) return;
    setIsAutoPlaying(true);
    setCurrentAutoDay(0);
    setExpandedDay(0);

    let dayIdx = 0;
    const interval = setInterval(() => {
      dayIdx++;
      if (dayIdx >= story.days.length) {
        clearInterval(interval);
        setIsAutoPlaying(false);
        return;
      }
      setCurrentAutoDay(dayIdx);
      setExpandedDay(dayIdx);
    }, 5000);

    return () => clearInterval(interval);
  }, [story]);

  // No story yet — show generation prompt
  if (!story) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg overflow-hidden">
        <div className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 p-8 text-center">
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5, type: 'spring' }}
          >
            <span className="text-5xl block mb-4">{'\uD83D\uDCD6'}</span>
            <h2 className="text-2xl font-bold text-white mb-2">Your Trip Story</h2>
            <p className="text-indigo-100 text-sm max-w-md mx-auto mb-6">
              Let AI craft an immersive, day-by-day narrative of your journey to{' '}
              <span className="font-semibold text-white">{destination}</span>.
              Experience your trip as a story before you even go.
            </p>
            <button
              onClick={generateStory}
              disabled={isLoading}
              className="px-6 py-3 rounded-xl bg-white text-indigo-700 font-bold text-sm hover:bg-indigo-50 transition-all shadow-lg disabled:opacity-50 flex items-center gap-2 mx-auto"
            >
              {isLoading ? (
                <>
                  <span className="animate-spin inline-block w-4 h-4 border-2 border-indigo-600 border-t-transparent rounded-full" />
                  Crafting your story...
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
                  </svg>
                  Generate Trip Story
                </>
              )}
            </button>
            {error && (
              <p className="mt-4 text-red-200 text-sm">{error}</p>
            )}
          </motion.div>
        </div>
      </div>
    );
  }

  // Story generated — show it
  return (
    <div className="space-y-4">
      {/* Story header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 rounded-2xl shadow-lg p-6 text-white"
      >
        <div className="flex items-start justify-between">
          <div>
            <span className="text-3xl mb-2 block">{'\uD83D\uDCD6'}</span>
            <h2 className="text-2xl font-bold mb-1">{story.title}</h2>
            <p className="text-indigo-100 text-sm">{story.destination}</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={startAutoPlay}
              disabled={isAutoPlaying}
              className="px-4 py-2 rounded-lg bg-white/20 hover:bg-white/30 text-white text-sm font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
              </svg>
              {isAutoPlaying ? 'Playing...' : 'Auto-play'}
            </button>
            <button
              onClick={generateStory}
              disabled={isLoading}
              className="px-4 py-2 rounded-lg bg-white/20 hover:bg-white/30 text-white text-sm font-medium transition-colors disabled:opacity-50"
            >
              Regenerate
            </button>
          </div>
        </div>
        <p className="mt-4 text-indigo-50 text-sm leading-relaxed">{story.summary}</p>
      </motion.div>

      {/* Day-by-day story cards */}
      <div className="space-y-3">
        {story.days.map((day, idx) => {
          const mood = getMood(day.mood);
          const isExpanded = expandedDay === idx;

          return (
            <motion.div
              key={day.day_number}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.1 }}
              className={`rounded-2xl shadow-sm overflow-hidden border transition-all ${
                isExpanded
                  ? 'border-indigo-200 dark:border-indigo-700 shadow-md'
                  : 'border-gray-200 dark:border-gray-700'
              }`}
            >
              <button
                onClick={() => setExpandedDay(isExpanded ? null : idx)}
                className={`w-full text-left p-4 ${mood.bg} transition-colors`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{mood.emoji}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full text-white font-bold bg-gradient-to-r ${mood.gradient}`}>
                        Day {day.day_number}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {day.date}
                      </span>
                      <span className="text-xs text-gray-400 dark:text-gray-500 capitalize">
                        {day.mood}
                      </span>
                    </div>
                    <h3 className="font-bold text-gray-900 dark:text-white text-sm mt-1 truncate">
                      {day.title}
                    </h3>
                  </div>
                  <svg
                    className={`w-5 h-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    strokeWidth={2}
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </button>

              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <div className="p-5 bg-white dark:bg-gray-800 space-y-4">
                      {/* Narrative text */}
                      <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">
                        {day.narrative}
                      </p>

                      {/* Highlights */}
                      {day.highlights.length > 0 && (
                        <div>
                          <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
                            Highlights
                          </h4>
                          <div className="flex flex-wrap gap-2">
                            {day.highlights.map((h, hIdx) => (
                              <span
                                key={hIdx}
                                className={`text-xs px-3 py-1.5 rounded-full font-medium ${mood.bg} text-gray-700 dark:text-gray-300`}
                              >
                                {h}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
