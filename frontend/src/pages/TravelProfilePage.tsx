import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import api from '@/services/api';

interface TravelDNA {
  destinations: { favorite_destinations: string[]; total_destinations: number };
  budget: { range: string; average_spend: number; total_spend: number };
  style: { style: string; avg_trip_duration: number; top_interests: string[] };
  timing: { preferred_booking_months: string[]; avg_advance_days: number };
  dietary: { preference: string; allergies: string[]; preferred_cuisines: string[] };
  faith: { faith: string; prayer_reminders: boolean; faith_site_interest: boolean };
  health: { mobility: string; max_walking_km: number; health_conditions: string[]; medications: string[] };
  pace: { pace: string; max_activities_per_day: number };
  languages: { spoken: string[] };
}

interface UserPrefs {
  dietary_preference: string;
  dietary_allergies: string[];
  faith: string;
  prayer_reminders: boolean;
  faith_site_interest: boolean;
  mobility: string;
  max_walking_km_per_day: number;
  health_conditions: string[];
  medications: string[];
  pace: string;
  max_activities_per_day: number;
  languages_spoken: string[];
  budget_range: string;
  trip_style: string;
  preferred_cuisines: string[];
}

const DIETARY_OPTIONS = [
  { value: 'none', label: 'No Restrictions' },
  { value: 'vegetarian', label: 'Vegetarian' },
  { value: 'vegan', label: 'Vegan' },
  { value: 'halal', label: 'Halal' },
  { value: 'kosher', label: 'Kosher' },
  { value: 'gluten_free', label: 'Gluten Free' },
  { value: 'other', label: 'Other' },
];

const FAITH_OPTIONS = [
  { value: 'none', label: 'Not Specified' },
  { value: 'islam', label: 'Islam' },
  { value: 'christianity', label: 'Christianity' },
  { value: 'judaism', label: 'Judaism' },
  { value: 'hinduism', label: 'Hinduism' },
  { value: 'buddhism', label: 'Buddhism' },
  { value: 'sikhism', label: 'Sikhism' },
  { value: 'other', label: 'Other' },
];

const MOBILITY_OPTIONS = [
  { value: 'full', label: 'Full Mobility' },
  { value: 'limited', label: 'Limited Mobility' },
  { value: 'wheelchair', label: 'Wheelchair' },
  { value: 'elderly', label: 'Elderly-Friendly' },
];

const PACE_OPTIONS = [
  { value: 'slow', label: 'Slow & Relaxed', desc: '2-3 activities/day' },
  { value: 'moderate', label: 'Balanced', desc: '4-5 activities/day' },
  { value: 'packed', label: 'Packed Schedule', desc: '6+ activities/day' },
];

const STYLE_OPTIONS = [
  { value: 'adventure', label: 'Adventure', icon: '\u26F0\uFE0F' },
  { value: 'relaxation', label: 'Relaxation', icon: '\uD83C\uDFD6\uFE0F' },
  { value: 'cultural', label: 'Cultural', icon: '\uD83C\uDFDB\uFE0F' },
  { value: 'business', label: 'Business', icon: '\uD83D\uDCBC' },
  { value: 'family', label: 'Family', icon: '\uD83D\uDC68\u200D\uD83D\uDC69\u200D\uD83D\uDC67\u200D\uD83D\uDC66' },
];

const LANGUAGE_OPTIONS = [
  'en', 'es', 'fr', 'de', 'it', 'pt', 'ar', 'zh', 'ja', 'ko',
  'hi', 'bn', 'ru', 'tr', 'nl', 'sv', 'pl', 'th', 'vi', 'id',
];

const LANGUAGE_LABELS: Record<string, string> = {
  en: 'English', es: 'Spanish', fr: 'French', de: 'German', it: 'Italian',
  pt: 'Portuguese', ar: 'Arabic', zh: 'Chinese', ja: 'Japanese', ko: 'Korean',
  hi: 'Hindi', bn: 'Bengali', ru: 'Russian', tr: 'Turkish', nl: 'Dutch',
  sv: 'Swedish', pl: 'Polish', th: 'Thai', vi: 'Vietnamese', id: 'Indonesian',
};

export default function TravelProfilePage() {
  const [dna, setDna] = useState<TravelDNA | null>(null);
  const [prefs, setPrefs] = useState<UserPrefs>({
    dietary_preference: 'none', dietary_allergies: [],
    faith: 'none', prayer_reminders: false, faith_site_interest: false,
    mobility: 'full', max_walking_km_per_day: 10, health_conditions: [], medications: [],
    pace: 'moderate', max_activities_per_day: 5,
    languages_spoken: ['en'], budget_range: 'any', trip_style: 'cultural',
    preferred_cuisines: [],
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [rebuilding, setRebuilding] = useState(false);
  const [saved, setSaved] = useState(false);
  const [allergyInput, setAllergyInput] = useState('');
  const [conditionInput, setConditionInput] = useState('');

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    setLoading(true);
    try {
      const [dnaRes, prefsRes] = await Promise.allSettled([
        api.get('/api/agents/travel-dna'),
        api.get('/api/agents/preferences/me/'),
      ]);
      if (dnaRes.status === 'fulfilled' && dnaRes.value.data?.travel_dna) {
        setDna(dnaRes.value.data.travel_dna);
      }
      if (prefsRes.status === 'fulfilled' && prefsRes.value.data) {
        const p = prefsRes.value.data;
        setPrefs({
          dietary_preference: p.dietary_preference || 'none',
          dietary_allergies: p.dietary_allergies || [],
          faith: p.faith || 'none',
          prayer_reminders: p.prayer_reminders || false,
          faith_site_interest: p.faith_site_interest || false,
          mobility: p.mobility || 'full',
          max_walking_km_per_day: p.max_walking_km_per_day || 10,
          health_conditions: p.health_conditions || [],
          medications: p.medications || [],
          pace: p.pace || 'moderate',
          max_activities_per_day: p.max_activities_per_day || 5,
          languages_spoken: p.languages_spoken || ['en'],
          budget_range: p.budget_range || 'any',
          trip_style: p.trip_style || 'cultural',
          preferred_cuisines: p.preferred_cuisines || [],
        });
      }
    } catch {
      // Use defaults
    } finally {
      setLoading(false);
    }
  };

  const savePreferences = async () => {
    setSaving(true);
    setSaved(false);
    try {
      await api.patch('/api/agents/preferences/me/', prefs);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch {
      // silent
    } finally {
      setSaving(false);
    }
  };

  const rebuildDna = async () => {
    setRebuilding(true);
    try {
      const res = await api.post('/api/agents/travel-dna');
      if (res.data?.travel_dna) setDna(res.data.travel_dna);
    } catch {
      // silent
    } finally {
      setRebuilding(false);
    }
  };

  const addAllergy = () => {
    const val = allergyInput.trim();
    if (val && !prefs.dietary_allergies.includes(val)) {
      setPrefs({ ...prefs, dietary_allergies: [...prefs.dietary_allergies, val] });
      setAllergyInput('');
    }
  };

  const addCondition = () => {
    const val = conditionInput.trim();
    if (val && !prefs.health_conditions.includes(val)) {
      setPrefs({ ...prefs, health_conditions: [...prefs.health_conditions, val] });
      setConditionInput('');
    }
  };

  const toggleLanguage = (lang: string) => {
    const langs = prefs.languages_spoken.includes(lang)
      ? prefs.languages_spoken.filter((l) => l !== lang)
      : [...prefs.languages_spoken, lang];
    setPrefs({ ...prefs, languages_spoken: langs });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60dvh]">
        <div className="animate-spin w-8 h-8 border-4 border-teal-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Travel DNA Profile
        </h1>
        <p className="text-gray-500 dark:text-gray-400 mb-8">
          Tell us about yourself so our AI can personalize every trip to match your needs.
        </p>

        {/* Travel DNA Summary */}
        {dna && (
          <div className="bg-gradient-to-br from-teal-50 to-cyan-50 dark:from-teal-900/20 dark:to-cyan-900/20 rounded-2xl p-6 mb-8 border border-teal-200 dark:border-teal-800">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-teal-900 dark:text-teal-200">
                Your Travel DNA
              </h2>
              <button
                onClick={rebuildDna}
                disabled={rebuilding}
                className="text-sm px-3 py-1.5 rounded-lg bg-teal-600 text-white hover:bg-teal-700 disabled:opacity-50"
              >
                {rebuilding ? 'Rebuilding...' : 'Rebuild DNA'}
              </button>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="bg-white/70 dark:bg-gray-800/50 rounded-xl p-3 text-center">
                <p className="text-2xl font-bold text-teal-700 dark:text-teal-300">
                  {dna.destinations?.total_destinations || 0}
                </p>
                <p className="text-xs text-gray-500">Destinations</p>
              </div>
              <div className="bg-white/70 dark:bg-gray-800/50 rounded-xl p-3 text-center">
                <p className="text-2xl font-bold text-teal-700 dark:text-teal-300">
                  {dna.budget?.range || 'N/A'}
                </p>
                <p className="text-xs text-gray-500">Budget Range</p>
              </div>
              <div className="bg-white/70 dark:bg-gray-800/50 rounded-xl p-3 text-center">
                <p className="text-2xl font-bold text-teal-700 dark:text-teal-300">
                  {dna.style?.avg_trip_duration || 0}d
                </p>
                <p className="text-xs text-gray-500">Avg Trip</p>
              </div>
              <div className="bg-white/70 dark:bg-gray-800/50 rounded-xl p-3 text-center">
                <p className="text-2xl font-bold text-teal-700 dark:text-teal-300">
                  {dna.style?.style || 'balanced'}
                </p>
                <p className="text-xs text-gray-500">Style</p>
              </div>
            </div>
          </div>
        )}

        {/* Preferences Form */}
        <div className="space-y-8">
          {/* Travel Style */}
          <section className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Travel Style
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              {STYLE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setPrefs({ ...prefs, trip_style: opt.value })}
                  className={`p-3 rounded-xl border-2 text-center transition-all ${
                    prefs.trip_style === opt.value
                      ? 'border-teal-500 bg-teal-50 dark:bg-teal-900/30'
                      : 'border-gray-200 dark:border-gray-700 hover:border-teal-300'
                  }`}
                >
                  <span className="text-2xl block mb-1">{opt.icon}</span>
                  <span className="text-sm font-medium">{opt.label}</span>
                </button>
              ))}
            </div>
          </section>

          {/* Pace */}
          <section className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Trip Pace
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {PACE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setPrefs({ ...prefs, pace: opt.value })}
                  className={`p-4 rounded-xl border-2 text-left transition-all ${
                    prefs.pace === opt.value
                      ? 'border-teal-500 bg-teal-50 dark:bg-teal-900/30'
                      : 'border-gray-200 dark:border-gray-700 hover:border-teal-300'
                  }`}
                >
                  <span className="font-semibold text-sm block">{opt.label}</span>
                  <span className="text-xs text-gray-500">{opt.desc}</span>
                </button>
              ))}
            </div>
            <div className="mt-4">
              <label className="text-sm text-gray-600 dark:text-gray-400 block mb-1">
                Max activities per day: {prefs.max_activities_per_day}
              </label>
              <input
                type="range"
                min={1} max={10}
                value={prefs.max_activities_per_day}
                onChange={(e) => setPrefs({ ...prefs, max_activities_per_day: Number(e.target.value) })}
                className="w-full accent-teal-600"
              />
            </div>
          </section>

          {/* Dietary */}
          <section className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Dietary Preferences
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4">
              {DIETARY_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setPrefs({ ...prefs, dietary_preference: opt.value })}
                  className={`px-3 py-2 rounded-lg text-sm font-medium border-2 transition-all ${
                    prefs.dietary_preference === opt.value
                      ? 'border-orange-500 bg-orange-50 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300'
                      : 'border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
            <div>
              <label className="text-sm text-gray-600 dark:text-gray-400 block mb-2">
                Food Allergies
              </label>
              <div className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={allergyInput}
                  onChange={(e) => setAllergyInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addAllergy()}
                  placeholder="e.g. peanuts, shellfish"
                  className="flex-1 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-700 text-sm"
                />
                <button onClick={addAllergy} className="px-3 py-2 rounded-lg bg-orange-100 text-orange-700 text-sm font-medium hover:bg-orange-200">
                  Add
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {prefs.dietary_allergies.map((a, i) => (
                  <span key={i} className="px-2 py-1 rounded-full bg-red-100 text-red-700 text-xs font-medium flex items-center gap-1">
                    {a}
                    <button onClick={() => setPrefs({ ...prefs, dietary_allergies: prefs.dietary_allergies.filter((_, j) => j !== i) })} className="hover:text-red-900">&times;</button>
                  </span>
                ))}
              </div>
            </div>
          </section>

          {/* Faith */}
          <section className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Faith & Spiritual Preferences
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4">
              {FAITH_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setPrefs({ ...prefs, faith: opt.value })}
                  className={`px-3 py-2 rounded-lg text-sm font-medium border-2 transition-all ${
                    prefs.faith === opt.value
                      ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
                      : 'border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
            {prefs.faith !== 'none' && (
              <div className="space-y-3 mt-3">
                <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={prefs.prayer_reminders}
                    onChange={(e) => setPrefs({ ...prefs, prayer_reminders: e.target.checked })}
                    className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                  />
                  Enable prayer time reminders during trips
                </label>
                <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={prefs.faith_site_interest}
                    onChange={(e) => setPrefs({ ...prefs, faith_site_interest: e.target.checked })}
                    className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                  />
                  Show nearby places of worship in itineraries
                </label>
              </div>
            )}
          </section>

          {/* Health & Mobility */}
          <section className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Health & Mobility
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4">
              {MOBILITY_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setPrefs({ ...prefs, mobility: opt.value })}
                  className={`px-3 py-2 rounded-lg text-sm font-medium border-2 transition-all ${
                    prefs.mobility === opt.value
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                      : 'border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
            <div className="mb-4">
              <label className="text-sm text-gray-600 dark:text-gray-400 block mb-1">
                Max walking distance per day: {prefs.max_walking_km_per_day} km
              </label>
              <input
                type="range"
                min={1} max={30} step={0.5}
                value={prefs.max_walking_km_per_day}
                onChange={(e) => setPrefs({ ...prefs, max_walking_km_per_day: Number(e.target.value) })}
                className="w-full accent-blue-600"
              />
            </div>
            <div>
              <label className="text-sm text-gray-600 dark:text-gray-400 block mb-2">
                Health Conditions
              </label>
              <div className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={conditionInput}
                  onChange={(e) => setConditionInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addCondition()}
                  placeholder="e.g. asthma, diabetes"
                  className="flex-1 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-700 text-sm"
                />
                <button onClick={addCondition} className="px-3 py-2 rounded-lg bg-blue-100 text-blue-700 text-sm font-medium hover:bg-blue-200">
                  Add
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {prefs.health_conditions.map((c, i) => (
                  <span key={i} className="px-2 py-1 rounded-full bg-blue-100 text-blue-700 text-xs font-medium flex items-center gap-1">
                    {c}
                    <button onClick={() => setPrefs({ ...prefs, health_conditions: prefs.health_conditions.filter((_, j) => j !== i) })} className="hover:text-blue-900">&times;</button>
                  </span>
                ))}
              </div>
            </div>
          </section>

          {/* Languages */}
          <section className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Languages You Speak
            </h3>
            <div className="flex flex-wrap gap-2">
              {LANGUAGE_OPTIONS.map((lang) => (
                <button
                  key={lang}
                  onClick={() => toggleLanguage(lang)}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium border-2 transition-all ${
                    prefs.languages_spoken.includes(lang)
                      ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300'
                      : 'border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400'
                  }`}
                >
                  {LANGUAGE_LABELS[lang] || lang}
                </button>
              ))}
            </div>
          </section>

          {/* Save Button */}
          <div className="flex items-center gap-4">
            <button
              onClick={savePreferences}
              disabled={saving}
              className="px-6 py-3 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-semibold text-sm transition-colors disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Preferences'}
            </button>
            {saved && (
              <motion.span
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="text-green-600 text-sm font-medium"
              >
                Preferences saved!
              </motion.span>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  );
}
