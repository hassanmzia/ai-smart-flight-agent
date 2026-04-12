import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import api from '@/services/api';

interface RiskAssessment {
  destination: string;
  country: string;
  overall_risk_score: number;
  crime_score: number;
  health_score: number;
  natural_disaster_score: number;
  political_stability_score: number;
  terrorism_score: number;
  risk_level: string;
  summary: string;
  recommendations: string[];
}

interface HealthAdvisory {
  destination: string;
  country: string;
  vaccination_requirements: string[];
  health_risks: Array<{ name: string; severity: string; description: string }>;
  water_safety: string;
  altitude_info: string;
  medical_facilities_rating: number;
  health_insurance_required: boolean;
  emergency_numbers: Record<string, string>;
  nearby_hospitals: string[];
}

interface SafetyAlert {
  id: number;
  alert_type: string;
  severity: string;
  title: string;
  description: string;
  source: string;
  issued_at: string;
  is_active: boolean;
}

const RISK_COLORS: Record<string, string> = {
  low: 'text-green-600 bg-green-100',
  moderate: 'text-yellow-600 bg-yellow-100',
  high: 'text-orange-600 bg-orange-100',
  extreme: 'text-red-600 bg-red-100',
};

const SEVERITY_COLORS: Record<string, string> = {
  info: 'border-blue-400 bg-blue-50 dark:bg-blue-900/20',
  warning: 'border-yellow-400 bg-yellow-50 dark:bg-yellow-900/20',
  critical: 'border-orange-400 bg-orange-50 dark:bg-orange-900/20',
  emergency: 'border-red-400 bg-red-50 dark:bg-red-900/20',
};

const WATER_LABELS: Record<string, { text: string; color: string }> = {
  safe: { text: 'Tap water is safe', color: 'text-green-600' },
  boil: { text: 'Boil before drinking', color: 'text-yellow-600' },
  bottled_only: { text: 'Drink bottled water only', color: 'text-orange-600' },
  unsafe: { text: 'Water unsafe - use purification', color: 'text-red-600' },
};

function ScoreBar({ label, score, max = 100 }: { label: string; score: number; max?: number }) {
  const pct = Math.min((score / max) * 100, 100);
  const color = score <= 30 ? 'bg-green-500' : score <= 60 ? 'bg-yellow-500' : score <= 80 ? 'bg-orange-500' : 'bg-red-500';
  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-gray-600 dark:text-gray-400 w-36 flex-shrink-0">{label}</span>
      <div className="flex-1 h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className={`h-full rounded-full ${color}`}
        />
      </div>
      <span className="text-sm font-bold w-8 text-right text-gray-700 dark:text-gray-300">{score}</span>
    </div>
  );
}

export default function SafetyDashboardPage() {
  const [searchParams] = useSearchParams();
  const [destination, setDestination] = useState('');
  const [country, setCountry] = useState('');
  const [risk, setRisk] = useState<RiskAssessment | null>(null);
  const [health, setHealth] = useState<HealthAdvisory | null>(null);
  const [alerts, setAlerts] = useState<SafetyAlert[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'risk' | 'health' | 'alerts'>('risk');

  useEffect(() => {
    const dest = searchParams.get('destination');
    if (dest) setDestination(dest);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const assess = async () => {
    if (!destination.trim()) return;
    setLoading(true);
    setRisk(null);
    setHealth(null);
    setAlerts([]);

    try {
      const [riskRes, healthRes, alertsRes] = await Promise.allSettled([
        api.post('/api/safety/risk-assessments/assess/', { destination, country }),
        api.post('/api/safety/health-advisories/check/', { destination, country }),
        api.get('/api/safety/alerts/', { params: { destination, is_active: true } }),
      ]);

      if (riskRes.status === 'fulfilled') setRisk(riskRes.value.data);
      if (healthRes.status === 'fulfilled') setHealth(healthRes.value.data);
      if (alertsRes.status === 'fulfilled') {
        const d = alertsRes.value.data;
        setAlerts(Array.isArray(d) ? d : d.results || d.items || []);
      }
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Safety Intelligence
        </h1>
        <p className="text-gray-500 dark:text-gray-400 mb-8">
          AI-powered risk assessment, health advisories, and safety alerts for any destination.
        </p>

        {/* Search */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6 mb-8">
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && assess()}
              placeholder="Destination city (e.g. Bangkok)"
              className="flex-1 px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 dark:bg-gray-700 text-sm"
            />
            <input
              type="text"
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && assess()}
              placeholder="Country (e.g. Thailand)"
              className="flex-1 px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 dark:bg-gray-700 text-sm"
            />
            <button
              onClick={assess}
              disabled={loading || !destination.trim()}
              className="px-6 py-3 rounded-xl bg-red-600 hover:bg-red-700 text-white font-semibold text-sm transition-colors disabled:opacity-50 flex-shrink-0"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                  Assessing...
                </span>
              ) : (
                'Assess Safety'
              )}
            </button>
          </div>
        </div>

        {/* Results */}
        {(risk || health || alerts.length > 0) && (
          <>
            {/* Tab bar */}
            <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 rounded-xl p-1 mb-6">
              {(['risk', 'health', 'alerts'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`flex-1 py-2.5 px-4 rounded-lg text-sm font-medium transition-all ${
                    activeTab === tab
                      ? 'bg-white dark:bg-gray-700 shadow text-gray-900 dark:text-white'
                      : 'text-gray-500 dark:text-gray-400 hover:text-gray-700'
                  }`}
                >
                  {tab === 'risk' ? 'Risk Assessment' : tab === 'health' ? 'Health Advisory' : `Alerts (${alerts.length})`}
                </button>
              ))}
            </div>

            <AnimatePresence mode="wait">
              {/* Risk Assessment */}
              {activeTab === 'risk' && risk && (
                <motion.div
                  key="risk"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6"
                >
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                        {risk.destination}, {risk.country}
                      </h2>
                      <span className={`inline-block mt-1 px-3 py-1 rounded-full text-sm font-semibold ${RISK_COLORS[risk.risk_level] || 'text-gray-600 bg-gray-100'}`}>
                        {risk.risk_level.toUpperCase()} RISK
                      </span>
                    </div>
                    <div className="text-center">
                      <div className={`text-4xl font-bold ${
                        risk.overall_risk_score <= 30 ? 'text-green-600' :
                        risk.overall_risk_score <= 60 ? 'text-yellow-600' :
                        risk.overall_risk_score <= 80 ? 'text-orange-600' : 'text-red-600'
                      }`}>
                        {risk.overall_risk_score}
                      </div>
                      <p className="text-xs text-gray-500">Risk Score</p>
                    </div>
                  </div>

                  <div className="space-y-3 mb-6">
                    <ScoreBar label="Crime" score={risk.crime_score} />
                    <ScoreBar label="Health Risks" score={risk.health_score} />
                    <ScoreBar label="Natural Disasters" score={risk.natural_disaster_score} />
                    <ScoreBar label="Political Stability" score={risk.political_stability_score} />
                    <ScoreBar label="Terrorism" score={risk.terrorism_score} />
                  </div>

                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{risk.summary}</p>

                  {risk.recommendations.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">Recommendations</h4>
                      <ul className="space-y-1.5">
                        {risk.recommendations.map((rec, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                            <span className="text-teal-500 mt-0.5 flex-shrink-0">&#x2713;</span>
                            {rec}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </motion.div>
              )}

              {/* Health Advisory */}
              {activeTab === 'health' && health && (
                <motion.div
                  key="health"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6 space-y-6"
                >
                  <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                    Health Advisory: {health.destination}
                  </h2>

                  {/* Water Safety */}
                  <div className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 dark:bg-gray-700/50">
                    <span className="text-xl">&#x1F4A7;</span>
                    <span className={`text-sm font-medium ${WATER_LABELS[health.water_safety]?.color || 'text-gray-600'}`}>
                      {WATER_LABELS[health.water_safety]?.text || health.water_safety}
                    </span>
                  </div>

                  {/* Vaccinations */}
                  {health.vaccination_requirements.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">Vaccination Requirements</h4>
                      <div className="flex flex-wrap gap-2">
                        {health.vaccination_requirements.map((v, i) => (
                          <span key={i} className="px-3 py-1 rounded-full bg-green-100 text-green-700 text-sm font-medium">
                            {v}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Health Risks */}
                  {health.health_risks.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">Health Risks</h4>
                      <div className="space-y-2">
                        {health.health_risks.map((hr, i) => (
                          <div key={i} className={`p-3 rounded-xl border-l-4 ${
                            hr.severity === 'high' ? 'border-red-400 bg-red-50 dark:bg-red-900/10' :
                            hr.severity === 'medium' ? 'border-yellow-400 bg-yellow-50 dark:bg-yellow-900/10' :
                            'border-blue-400 bg-blue-50 dark:bg-blue-900/10'
                          }`}>
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-semibold text-sm">{hr.name}</span>
                              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                                hr.severity === 'high' ? 'bg-red-200 text-red-800' :
                                hr.severity === 'medium' ? 'bg-yellow-200 text-yellow-800' :
                                'bg-blue-200 text-blue-800'
                              }`}>{hr.severity}</span>
                            </div>
                            <p className="text-xs text-gray-600 dark:text-gray-400">{hr.description}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Emergency Numbers */}
                  {Object.keys(health.emergency_numbers).length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">Emergency Numbers</h4>
                      <div className="grid grid-cols-3 gap-2">
                        {Object.entries(health.emergency_numbers).map(([key, val]) => (
                          <div key={key} className="text-center p-3 rounded-xl bg-red-50 dark:bg-red-900/20">
                            <p className="text-xs text-gray-500 capitalize">{key}</p>
                            <p className="text-lg font-bold text-red-600">{val}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Medical Facilities */}
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Medical Facilities:</span>
                    <div className="flex gap-0.5">
                      {[1, 2, 3, 4, 5].map((i) => (
                        <span key={i} className={`text-lg ${i <= health.medical_facilities_rating ? 'text-green-500' : 'text-gray-300'}`}>
                          &#9733;
                        </span>
                      ))}
                    </div>
                    {health.health_insurance_required && (
                      <span className="ml-2 px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-700">
                        Insurance Required
                      </span>
                    )}
                  </div>
                </motion.div>
              )}

              {/* Alerts */}
              {activeTab === 'alerts' && (
                <motion.div
                  key="alerts"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="space-y-3"
                >
                  {alerts.length === 0 ? (
                    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-8 text-center">
                      <span className="text-4xl block mb-2">&#x2705;</span>
                      <p className="text-gray-500 dark:text-gray-400">No active safety alerts for this destination.</p>
                    </div>
                  ) : (
                    alerts.map((alert) => (
                      <div
                        key={alert.id}
                        className={`rounded-xl border-l-4 p-4 ${SEVERITY_COLORS[alert.severity] || 'border-gray-300 bg-gray-50'}`}
                      >
                        <div className="flex items-start justify-between mb-1">
                          <h4 className="font-semibold text-sm text-gray-900 dark:text-white">{alert.title}</h4>
                          <span className="text-xs text-gray-500 flex-shrink-0 ml-2">
                            {new Date(alert.issued_at).toLocaleDateString()}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">{alert.description}</p>
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <span className="px-2 py-0.5 rounded bg-gray-200 dark:bg-gray-700 capitalize">{alert.alert_type.replace('_', ' ')}</span>
                          <span className="capitalize font-medium">{alert.severity}</span>
                          {alert.source && <span>&#x2014; {alert.source}</span>}
                        </div>
                      </div>
                    ))
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </>
        )}
      </motion.div>
    </div>
  );
}
