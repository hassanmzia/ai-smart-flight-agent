import { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { API_BASE_URL, API_ENDPOINTS } from '../utils/constants';

interface PrayerTimes {
  fajr: string;
  sunrise: string;
  dhuhr: string;
  asr: string;
  maghrib: string;
  isha: string;
  destination: string;
  date: string;
}

interface WorshipPlace {
  id: number;
  name: string;
  worship_type: string;
  faith: string;
  address: string;
  distance_km: number;
  description: string;
  rating: number;
  halal_food_nearby: boolean;
  kosher_food_nearby: boolean;
  services: string[];
  amenities: string[];
}

interface SpiritualSite {
  id: number;
  name: string;
  category: string;
  faiths: string[];
  description: string;
  significance: string;
  visitor_tips: string;
  dress_code: string;
  best_time_to_visit: string;
}

interface Restaurant {
  name: string;
  cuisine: string;
  distance: string;
  rating: number;
  dietary_certifications: string[];
  description: string;
}

interface RamadanSchedule {
  suhoor_time: string;
  iftar_time: string;
  fasting_hours: string;
  activity_windows: { period: string; activities: string }[];
  tips: string[];
}

const FAITH_OPTIONS = [
  { value: 'islam', label: 'Islam', icon: '🕌' },
  { value: 'christianity', label: 'Christianity', icon: '⛪' },
  { value: 'judaism', label: 'Judaism', icon: '🕍' },
  { value: 'hinduism', label: 'Hinduism', icon: '🛕' },
  { value: 'buddhism', label: 'Buddhism', icon: '☸️' },
  { value: 'sikhism', label: 'Sikhism', icon: '🙏' },
];

const DIETARY_OPTIONS = [
  { value: 'halal', label: 'Halal' },
  { value: 'kosher', label: 'Kosher' },
  { value: 'vegetarian', label: 'Vegetarian' },
  { value: 'vegan', label: 'Vegan' },
];

const QUICK_DESTINATIONS = [
  'Mecca', 'Jerusalem', 'Vatican City', 'Varanasi', 'Bodh Gaya',
  'Amritsar', 'Istanbul', 'Cairo', 'Lourdes', 'Haridwar',
];

export default function FaithTravelPage() {
  const [activeTab, setActiveTab] = useState<'prayer' | 'worship' | 'dietary' | 'spiritual' | 'ramadan'>('prayer');
  const [destination, setDestination] = useState('');
  const [selectedFaith, setSelectedFaith] = useState('islam');
  const [loading, setLoading] = useState(false);

  // Prayer times state
  const [prayerTimes, setPrayerTimes] = useState<PrayerTimes | null>(null);
  const [prayerDate, setPrayerDate] = useState(new Date().toISOString().split('T')[0]);

  // Worship places state
  const [worshipPlaces, setWorshipPlaces] = useState<WorshipPlace[]>([]);
  const [worshipFilter, setWorshipFilter] = useState('');

  // Spiritual sites state
  const [spiritualSites, setSpiritualSites] = useState<SpiritualSite[]>([]);
  const [siteCategory, setSiteCategory] = useState('');

  // Dietary restaurants state
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [dietaryType, setDietaryType] = useState('halal');

  // Ramadan state
  const [ramadanSchedule, setRamadanSchedule] = useState<RamadanSchedule | null>(null);

  const token = localStorage.getItem('auth_token');
  const headers = { Authorization: `Bearer ${token}` };

  const fetchPrayerTimes = async () => {
    if (!destination) { toast.error('Please enter a destination'); return; }
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE_URL}${API_ENDPOINTS.AGENT.FAITH_PRAYER_TIMES}`, {
        params: { destination, date: prayerDate }, headers,
      });
      const d = res.data;
      if (d?.success !== false) {
        setPrayerTimes(d.prayer_times || d);
      }
    } catch { toast.error('Failed to load prayer times'); }
    setLoading(false);
  };

  const fetchWorshipPlaces = async () => {
    if (!destination) { toast.error('Please enter a destination'); return; }
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE_URL}${API_ENDPOINTS.AGENT.FAITH_WORSHIP_PLACES}`, {
        params: { destination, faith: selectedFaith, type: worshipFilter || undefined }, headers,
      });
      const d = res.data;
      const items = d?.places || d?.items || d?.results || (Array.isArray(d) ? d : []);
      setWorshipPlaces(Array.isArray(items) ? items : []);
    } catch { toast.error('Failed to load worship places'); }
    setLoading(false);
  };

  const fetchSpiritualSites = async () => {
    if (!destination) { toast.error('Please enter a destination'); return; }
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE_URL}${API_ENDPOINTS.AGENT.FAITH_SPIRITUAL_SITES}`, {
        params: { destination, faith: selectedFaith, category: siteCategory || undefined }, headers,
      });
      const d = res.data;
      const items = d?.sites || d?.items || d?.results || (Array.isArray(d) ? d : []);
      setSpiritualSites(Array.isArray(items) ? items : []);
    } catch { toast.error('Failed to load spiritual sites'); }
    setLoading(false);
  };

  const fetchDietaryRestaurants = async () => {
    if (!destination) { toast.error('Please enter a destination'); return; }
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE_URL}${API_ENDPOINTS.AGENT.FAITH_DIETARY}`, {
        params: { destination, type: dietaryType }, headers,
      });
      const d = res.data;
      const items = d?.restaurants || d?.items || d?.results || (Array.isArray(d) ? d : []);
      setRestaurants(Array.isArray(items) ? items : []);
    } catch { toast.error('Failed to load restaurants'); }
    setLoading(false);
  };

  const fetchRamadanSchedule = async () => {
    if (!destination) { toast.error('Please enter a destination'); return; }
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE_URL}${API_ENDPOINTS.AGENT.FAITH_RAMADAN}`, {
        params: { destination, date: prayerDate }, headers,
      });
      const d = res.data;
      if (d?.success !== false) {
        setRamadanSchedule(d.schedule || d);
      }
    } catch { toast.error('Failed to load Ramadan schedule'); }
    setLoading(false);
  };

  useEffect(() => {
    if (!destination) return;
    if (activeTab === 'prayer') fetchPrayerTimes();
    else if (activeTab === 'worship') fetchWorshipPlaces();
    else if (activeTab === 'spiritual') fetchSpiritualSites();
    else if (activeTab === 'dietary') fetchDietaryRestaurants();
    else if (activeTab === 'ramadan') fetchRamadanSchedule();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  const tabs = [
    { key: 'prayer' as const, label: 'Prayer Times' },
    { key: 'worship' as const, label: 'Worship Places' },
    { key: 'dietary' as const, label: 'Dietary Options' },
    { key: 'spiritual' as const, label: 'Spiritual Sites' },
    { key: 'ramadan' as const, label: 'Ramadan Mode' },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Faith-Aware Travel
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Prayer times, worship places, dietary options, and spiritual sites for faith-conscious travelers
        </p>
      </div>

      {/* Search Bar */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Destination
            </label>
            <input
              type="text"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              placeholder="Enter city or destination..."
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Faith
            </label>
            <select
              value={selectedFaith}
              onChange={(e) => setSelectedFaith(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              {FAITH_OPTIONS.map((f) => (
                <option key={f.value} value={f.value}>{f.icon} {f.label}</option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={() => {
                if (activeTab === 'prayer') fetchPrayerTimes();
                else if (activeTab === 'worship') fetchWorshipPlaces();
                else if (activeTab === 'spiritual') fetchSpiritualSites();
                else if (activeTab === 'dietary') fetchDietaryRestaurants();
                else if (activeTab === 'ramadan') fetchRamadanSchedule();
              }}
              disabled={loading || !destination}
              className="w-full px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>
        </div>

        {/* Quick picks */}
        <div className="mt-3 flex flex-wrap gap-2">
          <span className="text-sm text-gray-500 dark:text-gray-400">Quick picks:</span>
          {QUICK_DESTINATIONS.map((d) => (
            <button
              key={d}
              onClick={() => setDestination(d)}
              className="text-sm px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full hover:bg-blue-100 dark:hover:bg-blue-900/30"
            >
              {d}
            </button>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex overflow-x-auto gap-1 mb-6 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            className={`flex-shrink-0 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === t.key
                ? 'bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="space-y-6">
        {/* Prayer Times */}
        {activeTab === 'prayer' && (
          <div>
            <div className="mb-4 flex gap-3 items-end">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Date</label>
                <input
                  type="date"
                  value={prayerDate}
                  onChange={(e) => setPrayerDate(e.target.value)}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
            </div>

            {prayerTimes && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                  Prayer Times for {prayerTimes.destination}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">{prayerTimes.date}</p>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                  {[
                    { name: 'Fajr', time: prayerTimes.fajr, color: 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-800 dark:text-indigo-300' },
                    { name: 'Sunrise', time: prayerTimes.sunrise, color: 'bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-300' },
                    { name: 'Dhuhr', time: prayerTimes.dhuhr, color: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300' },
                    { name: 'Asr', time: prayerTimes.asr, color: 'bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-300' },
                    { name: 'Maghrib', time: prayerTimes.maghrib, color: 'bg-rose-100 dark:bg-rose-900/30 text-rose-800 dark:text-rose-300' },
                    { name: 'Isha', time: prayerTimes.isha, color: 'bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300' },
                  ].map((p) => (
                    <div key={p.name} className={`${p.color} rounded-lg p-4 text-center`}>
                      <p className="text-sm font-medium">{p.name}</p>
                      <p className="text-2xl font-bold mt-1">{p.time}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {!prayerTimes && !loading && destination && (
              <p className="text-center text-gray-500 dark:text-gray-400 py-10">
                Click Search to load prayer times
              </p>
            )}
          </div>
        )}

        {/* Worship Places */}
        {activeTab === 'worship' && (
          <div>
            <div className="mb-4">
              <select
                value={worshipFilter}
                onChange={(e) => setWorshipFilter(e.target.value)}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">All Types</option>
                <option value="mosque">Mosques</option>
                <option value="church">Churches</option>
                <option value="synagogue">Synagogues</option>
                <option value="temple">Temples</option>
                <option value="gurdwara">Gurdwaras</option>
                <option value="monastery">Monasteries</option>
              </select>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              {worshipPlaces.map((place, i) => (
                <div key={place.id || i} className="bg-white dark:bg-gray-800 rounded-xl shadow p-5">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white">{place.name}</h3>
                      <span className="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full">
                        {place.worship_type}
                      </span>
                    </div>
                    {place.distance_km && (
                      <span className="text-sm text-gray-500 dark:text-gray-400">
                        {place.distance_km} km
                      </span>
                    )}
                  </div>
                  {place.address && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">{place.address}</p>
                  )}
                  {place.description && (
                    <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">{place.description}</p>
                  )}
                  <div className="flex flex-wrap gap-2 mt-2">
                    {place.rating > 0 && (
                      <span className="text-xs px-2 py-0.5 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 rounded-full">
                        Rating: {place.rating}/5
                      </span>
                    )}
                    {place.halal_food_nearby && (
                      <span className="text-xs px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full">
                        Halal nearby
                      </span>
                    )}
                    {place.kosher_food_nearby && (
                      <span className="text-xs px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full">
                        Kosher nearby
                      </span>
                    )}
                    {Array.isArray(place.amenities) && place.amenities.map((a, j) => (
                      <span key={j} className="text-xs px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded-full">
                        {a}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {worshipPlaces.length === 0 && !loading && (
              <p className="text-center text-gray-500 dark:text-gray-400 py-10">
                {destination ? 'No worship places found. Try searching.' : 'Enter a destination to find worship places.'}
              </p>
            )}
          </div>
        )}

        {/* Dietary Restaurants */}
        {activeTab === 'dietary' && (
          <div>
            <div className="mb-4 flex gap-2">
              {DIETARY_OPTIONS.map((d) => (
                <button
                  key={d.value}
                  onClick={() => setDietaryType(d.value)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    dietaryType === d.value
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                >
                  {d.label}
                </button>
              ))}
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {restaurants.map((r, i) => (
                <div key={i} className="bg-white dark:bg-gray-800 rounded-xl shadow p-5">
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-1">{r.name}</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">{r.cuisine}</p>
                  {r.description && (
                    <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">{r.description}</p>
                  )}
                  <div className="flex flex-wrap gap-2 mt-2">
                    {r.distance && (
                      <span className="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full">
                        {r.distance}
                      </span>
                    )}
                    {r.rating > 0 && (
                      <span className="text-xs px-2 py-0.5 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 rounded-full">
                        {r.rating}/5
                      </span>
                    )}
                    {Array.isArray(r.dietary_certifications) && r.dietary_certifications.map((c, j) => (
                      <span key={j} className="text-xs px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full">
                        {c}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {restaurants.length === 0 && !loading && (
              <p className="text-center text-gray-500 dark:text-gray-400 py-10">
                {destination ? 'No restaurants found. Try searching.' : 'Enter a destination to find restaurants.'}
              </p>
            )}
          </div>
        )}

        {/* Spiritual Sites */}
        {activeTab === 'spiritual' && (
          <div>
            <div className="mb-4">
              <select
                value={siteCategory}
                onChange={(e) => setSiteCategory(e.target.value)}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">All Categories</option>
                <option value="pilgrimage">Pilgrimage Sites</option>
                <option value="heritage">Religious Heritage</option>
                <option value="meditation">Meditation / Retreat</option>
                <option value="festival_venue">Festival Venues</option>
                <option value="sacred_natural">Sacred Natural Sites</option>
              </select>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              {spiritualSites.map((site, i) => (
                <div key={site.id || i} className="bg-white dark:bg-gray-800 rounded-xl shadow p-5">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-semibold text-gray-900 dark:text-white">{site.name}</h3>
                    <span className="text-xs px-2 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full">
                      {site.category}
                    </span>
                  </div>
                  <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">{site.description}</p>
                  {site.significance && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                      <span className="font-medium">Significance:</span> {site.significance}
                    </p>
                  )}
                  {site.visitor_tips && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                      <span className="font-medium">Tips:</span> {site.visitor_tips}
                    </p>
                  )}
                  <div className="flex flex-wrap gap-2 mt-2">
                    {site.dress_code && (
                      <span className="text-xs px-2 py-0.5 bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-300 rounded-full">
                        Dress: {site.dress_code}
                      </span>
                    )}
                    {site.best_time_to_visit && (
                      <span className="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full">
                        Best: {site.best_time_to_visit}
                      </span>
                    )}
                    {Array.isArray(site.faiths) && site.faiths.map((f, j) => (
                      <span key={j} className="text-xs px-2 py-0.5 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded-full">
                        {f}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {spiritualSites.length === 0 && !loading && (
              <p className="text-center text-gray-500 dark:text-gray-400 py-10">
                {destination ? 'No spiritual sites found. Try searching.' : 'Enter a destination to discover spiritual sites.'}
              </p>
            )}
          </div>
        )}

        {/* Ramadan Mode */}
        {activeTab === 'ramadan' && (
          <div>
            {ramadanSchedule && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Ramadan Schedule - {destination}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div className="bg-indigo-50 dark:bg-indigo-900/20 rounded-lg p-4 text-center">
                    <p className="text-sm text-indigo-600 dark:text-indigo-400 font-medium">Suhoor (Pre-Dawn)</p>
                    <p className="text-2xl font-bold text-indigo-800 dark:text-indigo-300 mt-1">
                      {ramadanSchedule.suhoor_time}
                    </p>
                  </div>
                  <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-4 text-center">
                    <p className="text-sm text-orange-600 dark:text-orange-400 font-medium">Iftar (Breaking Fast)</p>
                    <p className="text-2xl font-bold text-orange-800 dark:text-orange-300 mt-1">
                      {ramadanSchedule.iftar_time}
                    </p>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 text-center">
                    <p className="text-sm text-gray-600 dark:text-gray-400 font-medium">Fasting Duration</p>
                    <p className="text-2xl font-bold text-gray-800 dark:text-gray-200 mt-1">
                      {ramadanSchedule.fasting_hours}
                    </p>
                  </div>
                </div>

                {Array.isArray(ramadanSchedule.activity_windows) && ramadanSchedule.activity_windows.length > 0 && (
                  <div className="mb-6">
                    <h4 className="font-medium text-gray-900 dark:text-white mb-3">Recommended Activity Windows</h4>
                    <div className="space-y-2">
                      {ramadanSchedule.activity_windows.map((w, i) => (
                        <div key={i} className="flex items-center gap-3 bg-gray-50 dark:bg-gray-700 p-3 rounded-lg">
                          <span className="font-medium text-sm text-gray-700 dark:text-gray-300 w-32">{w.period}</span>
                          <span className="text-sm text-gray-600 dark:text-gray-400">{w.activities}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {Array.isArray(ramadanSchedule.tips) && ramadanSchedule.tips.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-white mb-3">Ramadan Travel Tips</h4>
                    <ul className="space-y-2">
                      {ramadanSchedule.tips.map((tip, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                          <span className="text-green-500 mt-0.5">*</span>
                          {tip}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {!ramadanSchedule && !loading && (
              <div className="text-center py-10">
                <p className="text-gray-500 dark:text-gray-400 mb-4">
                  {destination ? 'Click Search to load Ramadan schedule' : 'Enter a destination for Ramadan-aware scheduling'}
                </p>
                <p className="text-sm text-gray-400 dark:text-gray-500">
                  Get optimized daily schedules that respect fasting hours, with suhoor and iftar times
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Loading overlay */}
      {loading && (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      )}
    </div>
  );
}
