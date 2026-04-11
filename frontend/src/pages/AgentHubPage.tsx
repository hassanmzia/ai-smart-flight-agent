import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '@/services/api';

/* ─── Types ─── */
interface FlightStatus {
  flight_number: string;
  status: string;
  delay_minutes: number;
  gate: string;
  terminal: string;
  disruption_type: string;
  recovery_options: Array<{
    action: string;
    description: string;
    cost: number;
    confidence: string;
  }>;
}

interface WeatherAdaptResult {
  adapted_activities: Array<{
    name: string;
    type: string;
    adapted: boolean;
    original_name?: string;
  }>;
  changes_made: string[];
  overall_impact: string;
  tips: string[];
  weather: {
    temperature: number;
    condition: string;
    wind_speed: number;
  };
}

interface BudgetResult {
  total_spent: number;
  remaining: number;
  percentage_used: number;
  status: string;
  breakdown_by_category: Record<string, number>;
  savings_tips: string[];
}

/* ─── Constants ─── */
const IMPACT_COLORS: Record<string, string> = {
  none: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  low: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  moderate: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  high: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  critical: 'bg-red-200 text-red-800 dark:bg-red-900/40 dark:text-red-300',
};

const TABS = [
  { id: 'flight', label: 'Flight Monitor', icon: '&#9992;' },
  { id: 'weather', label: 'Weather Adapt', icon: '&#9925;' },
  { id: 'budget', label: 'Budget Tracker', icon: '&#128176;' },
  { id: 'health', label: 'Health Check', icon: '&#128138;' },
  { id: 'culture', label: 'Culture Guide', icon: '&#127757;' },
] as const;

type TabId = (typeof TABS)[number]['id'];

export default function AgentHubPage() {
  const [activeTab, setActiveTab] = useState<TabId>('flight');

  /* ─── Flight Monitor ─── */
  const [flightNum, setFlightNum] = useState('');
  const [flightDate, setFlightDate] = useState('');
  const [flightStatus, setFlightStatus] = useState<FlightStatus | null>(null);
  const [flightLoading, setFlightLoading] = useState(false);

  const checkFlight = async () => {
    if (!flightNum || !flightDate) return;
    setFlightLoading(true);
    try {
      const res = await api.post('/api/agents/flight-status', {
        flight_number: flightNum,
        date: flightDate,
      });
      setFlightStatus(res.data);
    } catch {
      setFlightStatus(null);
    } finally {
      setFlightLoading(false);
    }
  };

  /* ─── Weather Adapt ─── */
  const [weatherDest, setWeatherDest] = useState('');
  const [weatherResult, setWeatherResult] = useState<WeatherAdaptResult | null>(null);
  const [weatherLoading, setWeatherLoading] = useState(false);

  const adaptWeather = async () => {
    if (!weatherDest) return;
    setWeatherLoading(true);
    try {
      const res = await api.post('/api/agents/weather-adapt', {
        destination: weatherDest,
        activities: [
          { name: 'Walking Tour', type: 'walking_tour', is_outdoor: true },
          { name: 'Museum Visit', type: 'museum', is_outdoor: false },
          { name: 'Beach Day', type: 'beach', is_outdoor: true },
          { name: 'Local Food Tour', type: 'food', is_outdoor: true },
          { name: 'Sunset Cruise', type: 'nature', is_outdoor: true },
        ],
      });
      setWeatherResult(res.data);
    } catch {
      setWeatherResult(null);
    } finally {
      setWeatherLoading(false);
    }
  };

  /* ─── Budget Tracker ─── */
  const [budgetDest, setBudgetDest] = useState('');
  const [budgetTotal, setBudgetTotal] = useState('');
  const [budgetResult, setBudgetResult] = useState<BudgetResult | null>(null);
  const [budgetLoading, setBudgetLoading] = useState(false);

  const trackBudget = async () => {
    if (!budgetDest || !budgetTotal) return;
    setBudgetLoading(true);
    try {
      const res = await api.post('/api/agents/budget/track', {
        destination: budgetDest,
        budget: parseFloat(budgetTotal),
        items: [
          { type: 'flight', name: 'Round-trip flight', cost: parseFloat(budgetTotal) * 0.3 },
          { type: 'hotel', name: 'Hotel (5 nights)', cost: parseFloat(budgetTotal) * 0.35 },
          { type: 'food', name: 'Meals estimate', cost: parseFloat(budgetTotal) * 0.15 },
          { type: 'activity', name: 'Activities', cost: parseFloat(budgetTotal) * 0.1 },
        ],
      });
      setBudgetResult(res.data);
    } catch {
      setBudgetResult(null);
    } finally {
      setBudgetLoading(false);
    }
  };

  /* ─── Health Check ─── */
  const [healthDest, setHealthDest] = useState('');
  const [healthResult, setHealthResult] = useState<Record<string, unknown> | null>(null);
  const [healthLoading, setHealthLoading] = useState(false);

  const runHealthCheck = async () => {
    if (!healthDest) return;
    setHealthLoading(true);
    try {
      const res = await api.post('/api/agents/health-check', {
        destination: healthDest,
        pace: 'moderate',
        max_walking_km: 10,
      });
      setHealthResult(res.data);
    } catch {
      setHealthResult(null);
    } finally {
      setHealthLoading(false);
    }
  };

  /* ─── Culture Guide ─── */
  const [cultureDest, setCultureDest] = useState('');
  const [cultureResult, setCultureResult] = useState<Record<string, unknown> | null>(null);
  const [cultureLoading, setCultureLoading] = useState(false);

  const loadCulture = async () => {
    if (!cultureDest) return;
    setCultureLoading(true);
    try {
      const res = await api.get(
        `/api/agents/etiquette?destination=${encodeURIComponent(cultureDest)}`
      );
      setCultureResult(res.data);
    } catch {
      setCultureResult(null);
    } finally {
      setCultureLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 py-10 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-10"
        >
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-3">
            AI Agent Hub
          </h1>
          <p className="text-gray-600 dark:text-gray-400 text-lg">
            Your autonomous travel agents — monitoring, adapting, and optimizing your trip
          </p>
        </motion.div>

        {/* Tab Bar */}
        <div className="flex overflow-x-auto gap-2 mb-8 pb-2">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-shrink-0 px-5 py-2.5 rounded-full font-medium text-sm transition-all whitespace-nowrap ${
                activeTab === tab.id
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-200 dark:shadow-indigo-900/30'
                  : 'bg-white dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600'
              }`}
            >
              <span dangerouslySetInnerHTML={{ __html: tab.icon }} /> {tab.label}
            </button>
          ))}
        </div>

        <AnimatePresence mode="wait">
          {/* ──── Flight Monitor ──── */}
          {activeTab === 'flight' && (
            <motion.div key="flight" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-6 md:p-8 space-y-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">Flight Monitor</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <input
                    value={flightNum}
                    onChange={(e) => setFlightNum(e.target.value.toUpperCase())}
                    placeholder="Flight number (e.g. AA1234)"
                    className="rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-4 py-3 text-gray-900 dark:text-white"
                  />
                  <input
                    type="date"
                    value={flightDate}
                    onChange={(e) => setFlightDate(e.target.value)}
                    className="rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-4 py-3 text-gray-900 dark:text-white"
                  />
                </div>
                <button
                  onClick={checkFlight}
                  disabled={!flightNum || !flightDate || flightLoading}
                  className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold disabled:opacity-50"
                >
                  {flightLoading ? 'Checking...' : 'Check Status'}
                </button>

                {flightStatus && (
                  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-xl">
                      <div>
                        <p className="text-lg font-bold text-gray-900 dark:text-white">
                          {flightStatus.flight_number}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Gate {flightStatus.gate} &middot; Terminal {flightStatus.terminal}
                        </p>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                        IMPACT_COLORS[flightStatus.disruption_type === 'none' ? 'none' : flightStatus.disruption_type === 'delay_short' ? 'low' : flightStatus.disruption_type === 'delay_long' ? 'moderate' : 'critical']
                      }`}>
                        {flightStatus.status}
                      </span>
                    </div>

                    {flightStatus.recovery_options.length > 0 && (
                      <div>
                        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Recovery Options</h3>
                        <div className="space-y-2">
                          {flightStatus.recovery_options.map((opt, i) => (
                            <div key={i} className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg flex justify-between items-center">
                              <div>
                                <p className="text-sm font-medium text-gray-900 dark:text-white">{opt.description}</p>
                                <p className="text-xs text-gray-500 dark:text-gray-400">
                                  Confidence: {opt.confidence} {opt.cost > 0 ? `· ~$${opt.cost}` : '· Free'}
                                </p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </motion.div>
                )}
              </div>
            </motion.div>
          )}

          {/* ──── Weather Adapt ──── */}
          {activeTab === 'weather' && (
            <motion.div key="weather" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-6 md:p-8 space-y-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">Weather Adaptation</h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Enter a destination to see how weather affects your activities and get smart alternatives
                </p>
                <div className="flex gap-3">
                  <input
                    value={weatherDest}
                    onChange={(e) => setWeatherDest(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && adaptWeather()}
                    placeholder="Destination (e.g. London)"
                    className="flex-1 rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-4 py-3 text-gray-900 dark:text-white"
                  />
                  <button
                    onClick={adaptWeather}
                    disabled={!weatherDest || weatherLoading}
                    className="px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold disabled:opacity-50"
                  >
                    {weatherLoading ? 'Analyzing...' : 'Adapt'}
                  </button>
                </div>

                {weatherResult && (
                  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
                    {/* Weather banner */}
                    <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-xl">
                      <div>
                        <p className="font-bold text-gray-900 dark:text-white">
                          {weatherResult.weather.temperature}&deg;C — {weatherResult.weather.condition}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          Wind: {weatherResult.weather.wind_speed} km/h
                        </p>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${IMPACT_COLORS[weatherResult.overall_impact] || IMPACT_COLORS.none}`}>
                        Impact: {weatherResult.overall_impact}
                      </span>
                    </div>

                    {/* Changes */}
                    {weatherResult.changes_made.length > 0 && (
                      <div>
                        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Changes Made</h3>
                        {weatherResult.changes_made.map((c, i) => (
                          <p key={i} className="text-sm text-gray-600 dark:text-gray-400 py-1">&#8226; {c}</p>
                        ))}
                      </div>
                    )}

                    {/* Adapted activities */}
                    <div>
                      <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Your Adapted Itinerary</h3>
                      <div className="space-y-2">
                        {weatherResult.adapted_activities.map((act, i) => (
                          <div key={i} className={`p-3 rounded-lg ${act.adapted ? 'bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800' : 'bg-gray-50 dark:bg-gray-700'}`}>
                            <p className="text-sm font-medium text-gray-900 dark:text-white">{act.name}</p>
                            {act.adapted && act.original_name && (
                              <p className="text-xs text-yellow-600 dark:text-yellow-400 mt-0.5">
                                Replaces: {act.original_name}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Tips */}
                    <div className="p-4 bg-indigo-50 dark:bg-indigo-900/20 rounded-xl">
                      <h3 className="text-sm font-semibold text-indigo-700 dark:text-indigo-400 mb-2">Tips</h3>
                      {weatherResult.tips.map((tip, i) => (
                        <p key={i} className="text-sm text-gray-700 dark:text-gray-300">&#8226; {tip}</p>
                      ))}
                    </div>
                  </motion.div>
                )}
              </div>
            </motion.div>
          )}

          {/* ──── Budget Tracker ──── */}
          {activeTab === 'budget' && (
            <motion.div key="budget" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-6 md:p-8 space-y-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">Budget Tracker</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <input
                    value={budgetDest}
                    onChange={(e) => setBudgetDest(e.target.value)}
                    placeholder="Destination"
                    className="rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-4 py-3 text-gray-900 dark:text-white"
                  />
                  <input
                    type="number"
                    value={budgetTotal}
                    onChange={(e) => setBudgetTotal(e.target.value)}
                    placeholder="Total budget ($)"
                    className="rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-4 py-3 text-gray-900 dark:text-white"
                  />
                </div>
                <button
                  onClick={trackBudget}
                  disabled={!budgetDest || !budgetTotal || budgetLoading}
                  className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold disabled:opacity-50"
                >
                  {budgetLoading ? 'Analyzing...' : 'Track Budget'}
                </button>

                {budgetResult && (
                  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
                    {/* Budget bar */}
                    <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-xl">
                      <div className="flex justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          ${budgetResult.total_spent.toFixed(0)} spent
                        </span>
                        <span className={`text-sm font-semibold ${
                          budgetResult.status === 'on_track' ? 'text-green-600' :
                          budgetResult.status === 'under_budget' ? 'text-blue-600' : 'text-red-600'
                        }`}>
                          {budgetResult.status.replace('_', ' ')}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                        <div
                          className={`h-3 rounded-full transition-all ${
                            budgetResult.percentage_used > 90 ? 'bg-red-500' :
                            budgetResult.percentage_used > 70 ? 'bg-yellow-500' : 'bg-green-500'
                          }`}
                          style={{ width: `${Math.min(budgetResult.percentage_used, 100)}%` }}
                        />
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        ${budgetResult.remaining.toFixed(0)} remaining ({(100 - budgetResult.percentage_used).toFixed(0)}%)
                      </p>
                    </div>

                    {/* Savings tips */}
                    {budgetResult.savings_tips?.length > 0 && (
                      <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-xl">
                        <h3 className="text-sm font-semibold text-green-700 dark:text-green-400 mb-2">Savings Tips</h3>
                        {budgetResult.savings_tips.map((tip, i) => (
                          <p key={i} className="text-sm text-gray-700 dark:text-gray-300 py-0.5">&#8226; {tip}</p>
                        ))}
                      </div>
                    )}
                  </motion.div>
                )}
              </div>
            </motion.div>
          )}

          {/* ──── Health Check ──── */}
          {activeTab === 'health' && (
            <motion.div key="health" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-6 md:p-8 space-y-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">Trip Health Check</h2>
                <div className="flex gap-3">
                  <input
                    value={healthDest}
                    onChange={(e) => setHealthDest(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && runHealthCheck()}
                    placeholder="Destination (e.g. Bangkok)"
                    className="flex-1 rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-4 py-3 text-gray-900 dark:text-white"
                  />
                  <button
                    onClick={runHealthCheck}
                    disabled={!healthDest || healthLoading}
                    className="px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold disabled:opacity-50"
                  >
                    {healthLoading ? 'Checking...' : 'Check'}
                  </button>
                </div>

                {healthResult && (
                  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
                    {healthResult.risk_level && (
                      <div className={`p-3 rounded-xl text-center ${IMPACT_COLORS[healthResult.risk_level as string] || IMPACT_COLORS.none}`}>
                        <span className="font-semibold capitalize">Health Risk: {healthResult.risk_level as string}</span>
                      </div>
                    )}
                    {Array.isArray(healthResult.health_tips) && (healthResult.health_tips as string[]).length > 0 && (
                      <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl">
                        <h3 className="text-sm font-semibold text-blue-700 dark:text-blue-400 mb-2">Health Tips</h3>
                        {(healthResult.health_tips as string[]).map((tip, i) => (
                          <p key={i} className="text-sm text-gray-700 dark:text-gray-300 py-0.5">&#8226; {tip}</p>
                        ))}
                      </div>
                    )}
                    {healthResult.pacing_suggestions && (
                      <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-xl">
                        <h3 className="text-sm font-semibold text-purple-700 dark:text-purple-400 mb-2">Pacing Advice</h3>
                        <p className="text-sm text-gray-700 dark:text-gray-300">{healthResult.pacing_suggestions as string}</p>
                      </div>
                    )}
                  </motion.div>
                )}
              </div>
            </motion.div>
          )}

          {/* ──── Culture Guide ──── */}
          {activeTab === 'culture' && (
            <motion.div key="culture" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-6 md:p-8 space-y-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">Culture &amp; Etiquette Guide</h2>
                <div className="flex gap-3">
                  <input
                    value={cultureDest}
                    onChange={(e) => setCultureDest(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && loadCulture()}
                    placeholder="Destination (e.g. Tokyo)"
                    className="flex-1 rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-4 py-3 text-gray-900 dark:text-white"
                  />
                  <button
                    onClick={loadCulture}
                    disabled={!cultureDest || cultureLoading}
                    className="px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold disabled:opacity-50"
                  >
                    {cultureLoading ? 'Loading...' : 'Load Guide'}
                  </button>
                </div>

                {cultureResult && (
                  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
                    {cultureResult.greeting && (
                      <div className="p-4 bg-amber-50 dark:bg-amber-900/20 rounded-xl">
                        <h3 className="text-sm font-semibold text-amber-700 dark:text-amber-400 mb-1">Greeting</h3>
                        <p className="text-sm text-gray-700 dark:text-gray-300">{cultureResult.greeting as string}</p>
                      </div>
                    )}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {cultureResult.tipping && (
                        <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-xl">
                          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Tipping</h3>
                          <p className="text-sm text-gray-600 dark:text-gray-400">{cultureResult.tipping as string}</p>
                        </div>
                      )}
                      {cultureResult.dress_code && (
                        <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-xl">
                          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Dress Code</h3>
                          <p className="text-sm text-gray-600 dark:text-gray-400">{cultureResult.dress_code as string}</p>
                        </div>
                      )}
                    </div>
                    {Array.isArray(cultureResult.do_list) && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-xl">
                          <h3 className="text-sm font-semibold text-green-700 dark:text-green-400 mb-2">Do</h3>
                          {(cultureResult.do_list as string[]).map((item, i) => (
                            <p key={i} className="text-sm text-gray-700 dark:text-gray-300 py-0.5">&#10003; {item}</p>
                          ))}
                        </div>
                        {Array.isArray(cultureResult.dont_list) && (
                          <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-xl">
                            <h3 className="text-sm font-semibold text-red-700 dark:text-red-400 mb-2">Don't</h3>
                            {(cultureResult.dont_list as string[]).map((item, i) => (
                              <p key={i} className="text-sm text-gray-700 dark:text-gray-300 py-0.5">&#10007; {item}</p>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                    {cultureResult.dining_etiquette && (
                      <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-xl">
                        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Dining Etiquette</h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">{cultureResult.dining_etiquette as string}</p>
                      </div>
                    )}
                  </motion.div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
