import { useState, useCallback } from 'react';
import { useAuth } from '@/hooks/useAuth';
import api from '@/services/api';
import toast from 'react-hot-toast';

interface CulturalEntry {
  category: string;
  title: string;
  content: string;
  severity: string;
}

interface UserTip {
  id: number;
  user_name: string;
  title: string;
  content: string;
  category: string;
  upvotes: number;
  downvotes: number;
  created_at: string;
}

interface DestinationData {
  id: number;
  destination: string;
  country: string;
  continent: string;
  summary: string;
  history: string;
  culture: string;
  heritage_sites: Array<string | { name: string; description?: string; type?: string }>;
  festivals: Array<{ name: string; month: string; description: string }>;
  customs: string[];
  best_months: string[];
  languages_spoken: string[];
  currency: string;
  timezone_info: string;
  official_tourism_url: string;
  emergency_numbers: Record<string, string>;
  visa_info: string;
  cultural_info: CulturalEntry[];
  user_tips: UserTip[];
  views_count: number;
}

interface SearchResult {
  id: number;
  destination: string;
  country: string;
  continent: string;
  views_count: number;
}

const SEVERITY_COLORS: Record<string, string> = {
  info: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  advisory: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  important: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  critical: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
};

const CATEGORY_ICONS: Record<string, string> = {
  dress_code: '👔', tipping: '💵', greetings: '🤝', dining: '🍽️',
  religious: '🕌', business: '💼', photography: '📸', laws: '⚖️', taboos: '🚫',
};

type Tab = 'overview' | 'culture' | 'festivals' | 'tips';

export default function DestinationKBPage() {
  const { isAuthenticated } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [data, setData] = useState<DestinationData | null>(null);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState<Tab>('overview');
  const [tipForm, setTipForm] = useState({ title: '', content: '', category: 'food' });
  const [submittingTip, setSubmittingTip] = useState(false);

  const searchDestinations = useCallback(async () => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    try {
      const res = await api.get('/api/agents/destinations/search', { params: { q: searchQuery, limit: 8 } });
      setSearchResults(res.data?.destinations || []);
    } catch {
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  }, [searchQuery]);

  const loadDestination = async (name: string, country: string = '') => {
    setLoading(true);
    setData(null);
    try {
      const res = await api.get('/api/agents/destinations/knowledge', { params: { destination: name, country } });
      setData(res.data || null);
      setSearchResults([]);
      setTab('overview');
    } catch {
      toast.error('Failed to load destination');
    } finally {
      setLoading(false);
    }
  };

  const submitTip = async () => {
    if (!data?.id || !tipForm.title || !tipForm.content) {
      toast.error('Please fill in title and content');
      return;
    }
    setSubmittingTip(true);
    try {
      const res = await api.post('/api/agents/destinations/tips/submit', {
        destination_id: data.id,
        ...tipForm,
      });
      if (res.data?.success) {
        toast.success(res.data.status === 'approved' ? 'Tip published!' : 'Tip submitted for review');
        setTipForm({ title: '', content: '', category: 'food' });
        loadDestination(data.destination, data.country);
      }
    } catch {
      toast.error('Failed to submit tip');
    } finally {
      setSubmittingTip(false);
    }
  };

  const voteTip = async (tipId: number, vote: 'up' | 'down') => {
    try {
      await api.post('/api/agents/destinations/tips/vote', { tip_id: tipId, vote });
      if (data) loadDestination(data.destination, data.country);
    } catch {
      toast.error('Please sign in to vote');
    }
  };

  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: 'overview', label: 'Overview', icon: '📖' },
    { id: 'culture', label: 'Culture & Etiquette', icon: '🎭' },
    { id: 'festivals', label: 'Festivals', icon: '🎉' },
    { id: 'tips', label: 'Traveler Tips', icon: '💡' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Hero */}
      <div className="bg-gradient-to-br from-amber-600 via-orange-600 to-red-600 dark:from-amber-800 dark:via-orange-800 dark:to-red-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center">
          <h1 className="text-2xl md:text-3xl font-extrabold text-white mb-2">
            Destination Knowledge Base
          </h1>
          <p className="text-orange-100 text-lg mb-6">History, culture, festivals, etiquette & local insights</p>

          {/* Search */}
          <div className="max-w-xl mx-auto flex gap-3">
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') { searchQuery.trim() && loadDestination(searchQuery.trim()); } }}
              placeholder="Search any destination..."
              className="flex-1 px-5 py-3 rounded-xl text-gray-900 bg-white shadow-lg text-sm focus:ring-2 focus:ring-orange-300"
            />
            <button
              onClick={() => searchQuery.trim() && loadDestination(searchQuery.trim())}
              className="px-6 py-3 bg-white text-orange-700 rounded-xl font-semibold text-sm shadow-lg hover:bg-orange-50 transition-all"
            >
              Explore
            </button>
          </div>

          {/* Quick Search Results */}
          {searchResults.length > 0 && (
            <div className="max-w-xl mx-auto mt-3 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 divide-y divide-gray-100 dark:divide-gray-700 text-left">
              {searchResults.map(r => (
                <button
                  key={r.id}
                  onClick={() => loadDestination(r.destination, r.country)}
                  className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  <div>
                    <span className="font-medium text-gray-900 dark:text-white">{r.destination}</span>
                    <span className="text-sm text-gray-500 ml-2">{r.country}</span>
                  </div>
                  <span className="text-xs text-gray-400">{r.views_count} views</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="max-w-7xl mx-auto px-4 py-16 text-center">
          <div className="animate-pulse text-gray-500 dark:text-gray-400">
            <div className="text-4xl mb-4">🌍</div>
            <p>Generating destination knowledge...</p>
          </div>
        </div>
      )}

      {/* Destination Content */}
      {data && !loading && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <div className="mb-8">
            <h2 className="text-3xl font-extrabold text-gray-900 dark:text-white">
              {data.destination}
              {data.country && <span className="text-gray-400 font-normal">, {data.country}</span>}
            </h2>
            <div className="flex flex-wrap gap-3 mt-3">
              {data.continent && (
                <span className="px-3 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 rounded-full text-xs font-medium">{data.continent}</span>
              )}
              {data.currency && (
                <span className="px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full text-xs font-medium">Currency: {data.currency}</span>
              )}
              {data.timezone_info && (
                <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded-full text-xs font-medium">{data.timezone_info}</span>
              )}
              {data.languages_spoken?.length > 0 && (
                <span className="px-3 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 rounded-full text-xs font-medium">
                  {data.languages_spoken.slice(0, 3).join(', ')}
                </span>
              )}
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
            {tabs.map(t => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-all ${
                  tab === t.id
                    ? 'bg-orange-600 text-white shadow-lg'
                    : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-700'
                }`}
              >
                <span>{t.icon}</span> {t.label}
              </button>
            ))}
          </div>

          {/* Overview Tab */}
          {tab === 'overview' && (
            <div className="space-y-6">
              {data.summary && (
                <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-200 dark:border-gray-700">
                  <h3 className="font-bold text-lg text-gray-900 dark:text-white mb-3">Overview</h3>
                  <p className="text-gray-700 dark:text-gray-300 leading-relaxed">{data.summary}</p>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {data.history && (
                  <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-200 dark:border-gray-700">
                    <h3 className="font-bold text-lg text-gray-900 dark:text-white mb-3">History</h3>
                    <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed">{data.history}</p>
                  </div>
                )}
                {data.culture && (
                  <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-200 dark:border-gray-700">
                    <h3 className="font-bold text-lg text-gray-900 dark:text-white mb-3">Culture</h3>
                    <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed">{data.culture}</p>
                  </div>
                )}
              </div>

              {data.heritage_sites?.length > 0 && (
                <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-200 dark:border-gray-700">
                  <h3 className="font-bold text-lg text-gray-900 dark:text-white mb-3">Heritage Sites</h3>
                  <div className="flex flex-wrap gap-2">
                    {data.heritage_sites.map((site, i) => (
                      <span key={i} className="px-3 py-1.5 bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-300 rounded-lg text-sm">
                        {typeof site === 'string' ? site : site.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {data.best_months?.length > 0 && (
                <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-200 dark:border-gray-700">
                  <h3 className="font-bold text-lg text-gray-900 dark:text-white mb-3">Best Time to Visit</h3>
                  <div className="flex flex-wrap gap-2">
                    {data.best_months.map((month, i) => (
                      <span key={i} className="px-3 py-1.5 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 rounded-lg text-sm font-medium">{month}</span>
                    ))}
                  </div>
                </div>
              )}

              {data.visa_info && (
                <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-200 dark:border-gray-700">
                  <h3 className="font-bold text-lg text-gray-900 dark:text-white mb-3">Visa Information</h3>
                  <p className="text-gray-700 dark:text-gray-300 text-sm">{data.visa_info}</p>
                </div>
              )}

              {data.emergency_numbers && Object.keys(data.emergency_numbers).length > 0 && (
                <div className="bg-red-50 dark:bg-red-900/10 rounded-2xl p-6 border border-red-200 dark:border-red-800">
                  <h3 className="font-bold text-lg text-red-800 dark:text-red-300 mb-3">Emergency Numbers</h3>
                  <div className="flex flex-wrap gap-4">
                    {Object.entries(data.emergency_numbers).map(([key, val]) => (
                      <div key={key} className="text-sm">
                        <span className="font-medium text-red-700 dark:text-red-400 capitalize">{key.replace(/_/g, ' ')}:</span>{' '}
                        <span className="text-red-900 dark:text-red-200 font-mono">{val}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {data.official_tourism_url && (
                <a
                  href={data.official_tourism_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg text-sm font-medium hover:bg-orange-700 transition-all"
                >
                  Official Tourism Site &rarr;
                </a>
              )}
            </div>
          )}

          {/* Culture & Etiquette Tab */}
          {tab === 'culture' && (
            <div className="space-y-4">
              {data.cultural_info?.length > 0 ? (
                data.cultural_info.map((info, i) => (
                  <div key={i} className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-3 mb-3">
                      <span className="text-2xl">{CATEGORY_ICONS[info.category] || '📋'}</span>
                      <div className="flex-1">
                        <h3 className="font-bold text-gray-900 dark:text-white">{info.title}</h3>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${SEVERITY_COLORS[info.severity] || SEVERITY_COLORS.info}`}>
                          {info.severity}
                        </span>
                      </div>
                    </div>
                    <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed">{info.content}</p>
                  </div>
                ))
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <div className="text-4xl mb-3">🎭</div>
                  <p>No cultural info available yet. It will be generated when you explore this destination.</p>
                </div>
              )}

              {data.customs?.length > 0 && (
                <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-200 dark:border-gray-700">
                  <h3 className="font-bold text-lg text-gray-900 dark:text-white mb-3">Local Customs</h3>
                  <ul className="space-y-2">
                    {data.customs.map((custom, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                        <span className="text-orange-500 mt-0.5">&#9679;</span> {custom}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Festivals Tab */}
          {tab === 'festivals' && (
            <div>
              {data.festivals?.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {data.festivals.map((festival, i) => (
                    <div key={i} className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-200 dark:border-gray-700">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-3xl">🎉</span>
                        <div>
                          <h3 className="font-bold text-gray-900 dark:text-white">{festival.name}</h3>
                          <span className="text-xs text-orange-600 dark:text-orange-400 font-medium">{festival.month}</span>
                        </div>
                      </div>
                      <p className="text-sm text-gray-700 dark:text-gray-300">{festival.description}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <div className="text-4xl mb-3">🎉</div>
                  <p>No festivals data available yet.</p>
                </div>
              )}
            </div>
          )}

          {/* Tips Tab */}
          {tab === 'tips' && (
            <div className="space-y-6">
              {/* Submit Tip Form */}
              {isAuthenticated && (
                <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-200 dark:border-gray-700">
                  <h3 className="font-bold text-gray-900 dark:text-white mb-4">Share a Tip</h3>
                  <div className="space-y-3">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <input
                        type="text"
                        value={tipForm.title}
                        onChange={e => setTipForm(f => ({ ...f, title: e.target.value }))}
                        placeholder="Tip title..."
                        className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                      />
                      <select
                        value={tipForm.category}
                        onChange={e => setTipForm(f => ({ ...f, category: e.target.value }))}
                        className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                      >
                        {['food', 'transport', 'safety', 'money', 'culture', 'accommodation', 'general'].map(c => (
                          <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
                        ))}
                      </select>
                    </div>
                    <textarea
                      value={tipForm.content}
                      onChange={e => setTipForm(f => ({ ...f, content: e.target.value }))}
                      placeholder="Share your experience and advice..."
                      className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                      rows={3}
                    />
                    <button
                      onClick={submitTip}
                      disabled={submittingTip}
                      className="px-5 py-2 bg-orange-600 text-white rounded-lg text-sm font-medium hover:bg-orange-700 disabled:opacity-50"
                    >
                      {submittingTip ? 'Submitting...' : 'Submit Tip'}
                    </button>
                  </div>
                </div>
              )}

              {/* Tips List */}
              {data.user_tips?.length > 0 ? (
                data.user_tips.map(tip => (
                  <div key={tip.id} className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-200 dark:border-gray-700">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h4 className="font-bold text-gray-900 dark:text-white">{tip.title}</h4>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs text-gray-500">{tip.user_name}</span>
                          <span className="text-xs text-gray-400">&#9679;</span>
                          <span className="text-xs px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded-full">{tip.category}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button onClick={() => voteTip(tip.id, 'up')} className="text-green-500 hover:text-green-700 text-sm">
                          &#9650; {tip.upvotes}
                        </button>
                        <button onClick={() => voteTip(tip.id, 'down')} className="text-red-500 hover:text-red-700 text-sm">
                          &#9660; {tip.downvotes}
                        </button>
                      </div>
                    </div>
                    <p className="text-sm text-gray-700 dark:text-gray-300">{tip.content}</p>
                  </div>
                ))
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <div className="text-4xl mb-3">💡</div>
                  <p>No tips yet. Be the first to share your experience!</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!data && !loading && (
        <div className="max-w-7xl mx-auto px-4 py-16 text-center">
          <div className="text-6xl mb-4">🌍</div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Explore Any Destination</h2>
          <p className="text-gray-500 max-w-lg mx-auto mb-8">
            Search for a city or country to discover its history, culture, festivals, etiquette guides, and tips from fellow travelers
          </p>
          <div className="flex flex-wrap justify-center gap-2">
            {['Paris', 'Tokyo', 'Istanbul', 'Dubai', 'New York', 'Bangkok', 'Rome', 'Cape Town'].map(city => (
              <button
                key={city}
                onClick={() => { setSearchQuery(city); loadDestination(city); }}
                className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-orange-50 dark:hover:bg-gray-700 hover:border-orange-300 dark:hover:border-orange-600 transition-all"
              >
                {city}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
