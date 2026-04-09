import { useState } from 'react';
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

  const [activeTab, setActiveTab] = useState<'prices' | 'besttime' | 'trends'>('prices');

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
      <div className="bg-gradient-to-br from-amber-600 via-orange-600 to-red-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-20">
          <h1 className="text-lg sm:text-xl lg:text-2xl font-bold mb-4">
            Predictive Travel Intelligence
          </h1>
          <p className="text-lg sm:text-xl text-amber-100 max-w-2xl">
            AI-powered price forecasting, best-time-to-visit analysis, and destination trend insights.
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6">
        <div className="flex gap-2 overflow-x-auto pb-2">
          {(['prices', 'besttime', 'trends'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-5 py-3 rounded-t-xl font-semibold text-sm whitespace-nowrap transition-all ${
                activeTab === tab
                  ? 'bg-white dark:bg-gray-800 text-orange-600 dark:text-orange-400 shadow-lg'
                  : 'bg-white/60 dark:bg-gray-800/60 text-gray-600 dark:text-gray-400 hover:bg-white dark:hover:bg-gray-800'
              }`}
            >
              {tab === 'prices' && 'Price Forecast'}
              {tab === 'besttime' && 'Best Time to Visit'}
              {tab === 'trends' && 'Trending Destinations'}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
                  className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                />
                <input
                  type="text"
                  placeholder="Destination (e.g., LON)"
                  value={priceDest}
                  onChange={(e) => setPriceDest(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                />
                <input
                  type="date"
                  value={priceDate}
                  onChange={(e) => setPriceDate(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                />
              </div>
              <button
                onClick={handlePricePredict}
                disabled={priceLoading || !priceOrigin || !priceDest || !priceDate}
                className="px-6 py-3 bg-gradient-to-r from-amber-500 to-orange-600 text-white rounded-xl font-semibold hover:from-amber-600 hover:to-orange-700 disabled:opacity-50 transition-all"
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
                    <div className="bg-orange-50 dark:bg-orange-900/20 rounded-xl p-4 text-center">
                      <p className="text-sm text-gray-600 dark:text-gray-400">Current Estimate</p>
                      <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">${pricePrediction.current_estimate}</p>
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
                  className="flex-1 px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                />
                <button
                  onClick={handleBestTime}
                  disabled={btLoading || !btDest}
                  className="px-6 py-3 bg-gradient-to-r from-amber-500 to-orange-600 text-white rounded-xl font-semibold hover:from-amber-600 hover:to-orange-700 disabled:opacity-50 transition-all"
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
                            <span className="text-xs font-bold text-orange-600 dark:text-orange-400">{m.score}/100</span>
                          </div>
                          <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-1.5 mb-2">
                            <div
                              className="bg-gradient-to-r from-amber-500 to-orange-500 h-1.5 rounded-full"
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
                  className="px-5 py-2.5 bg-gradient-to-r from-amber-500 to-orange-600 text-white rounded-xl font-semibold hover:from-amber-600 hover:to-orange-700 disabled:opacity-50 transition-all text-sm"
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
                        t.rank <= 3 ? 'bg-gradient-to-br from-amber-500 to-orange-600' : 'bg-gray-400 dark:bg-gray-500'
                      }`}>
                        {t.rank}
                      </div>
                      <div className="flex-1">
                        <p className="font-semibold text-gray-900 dark:text-white">{t.destination}</p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">{t.search_count} searches</p>
                      </div>
                      <div className="w-24 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                        <div
                          className="bg-gradient-to-r from-amber-500 to-orange-500 h-2 rounded-full"
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
