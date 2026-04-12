import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import api from '@/services/api';
import toast from 'react-hot-toast';

interface Coupon {
  id: number;
  code: string;
  title: string;
  description: string;
  discount_type: string;
  discount_value: number;
  min_spend: number;
  partner_name: string;
  partner_category: string;
  partner_destination: string;
  valid_until: string | null;
  qr_data: string;
}

interface ReferralStats {
  code: string;
  total_referrals: number;
  successful_referrals: number;
  total_earnings: number;
  recent_referrals: Array<{
    email: string;
    status: string;
    created_at: string;
  }>;
}

const CATEGORIES = [
  { value: '', label: 'All Categories' },
  { value: 'hotel', label: 'Hotels' },
  { value: 'restaurant', label: 'Restaurants' },
  { value: 'attraction', label: 'Attractions' },
  { value: 'tour', label: 'Tours' },
  { value: 'transport', label: 'Transport' },
  { value: 'shopping', label: 'Shopping' },
  { value: 'spa', label: 'Spa & Wellness' },
];

const DISCOUNT_LABELS: Record<string, string> = {
  percentage: '% OFF',
  fixed: '$ OFF',
  bogo: 'BOGO',
  freebie: 'FREE',
};

type Tab = 'coupons' | 'referrals' | 'partner';

export default function PartnershipsPage() {
  const [searchParams] = useSearchParams();
  const { isAuthenticated } = useAuth();
  const [tab, setTab] = useState<Tab>('coupons');
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [referralStats, setReferralStats] = useState<ReferralStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [destination, setDestination] = useState('');
  const [category, setCategory] = useState('');

  useEffect(() => {
    const dest = searchParams.get('destination');
    if (dest) setDestination(dest);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);
  const [referralEmail, setReferralEmail] = useState('');
  const [copiedCode, setCopiedCode] = useState('');
  // Partner registration
  const [partnerForm, setPartnerForm] = useState({
    name: '', category: 'restaurant', destination: '', description: '',
    contact_email: '', website: '',
  });

  const fetchCoupons = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (destination) params.destination = destination;
      if (category) params.category = category;
      const res = await api.get('/api/agents/coupons', { params });
      // Handle both direct array and nested {coupons: [...]} responses
      const data = res.data;
      const items = Array.isArray(data) ? data
        : Array.isArray(data?.coupons) ? data.coupons
        : Array.isArray(data?.items) ? data.items
        : Array.isArray(data?.results) ? data.results
        : [];
      setCoupons(items);
    } catch {
      setCoupons([]);
    } finally {
      setLoading(false);
    }
  }, [destination, category]);

  const fetchReferral = useCallback(async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    try {
      const res = await api.get('/api/agents/referral');
      const data = res.data;
      if (data?.code || data?.has_referral_code) {
        setReferralStats({
          code: data.code || '',
          total_referrals: data.total_referrals || 0,
          successful_referrals: data.successful_referrals || 0,
          total_earnings: data.total_earnings || 0,
          recent_referrals: data.recent_referrals || [],
        });
      } else {
        setReferralStats(null);
      }
    } catch {
      setReferralStats(null);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (tab === 'coupons') fetchCoupons();
    else if (tab === 'referrals') fetchReferral();
  }, [tab, fetchCoupons, fetchReferral]);

  const copyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    toast.success('Coupon code copied!');
    setTimeout(() => setCopiedCode(''), 2000);
  };

  const sendReferral = async () => {
    if (!referralEmail || !referralStats?.code) return;
    try {
      await api.post('/api/agents/referral/send', {
        referral_code: referralStats.code,
        email: referralEmail,
      });
      toast.success('Referral invitation sent!');
      setReferralEmail('');
      fetchReferral();
    } catch {
      toast.error('Failed to send referral');
    }
  };

  const registerPartner = async () => {
    if (!partnerForm.name || !partnerForm.contact_email || !partnerForm.destination) {
      toast.error('Please fill in all required fields');
      return;
    }
    try {
      await api.post('/api/agents/partners/register', partnerForm);
      toast.success('Partner application submitted! We will review it shortly.');
      setPartnerForm({ name: '', category: 'restaurant', destination: '', description: '', contact_email: '', website: '' });
    } catch {
      toast.error('Failed to submit application');
    }
  };

  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: 'coupons', label: 'Deals & Coupons', icon: '🏷️' },
    { id: 'referrals', label: 'Referral Program', icon: '🎁' },
    { id: 'partner', label: 'Become a Partner', icon: '🤝' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Hero */}
      <div className="bg-gradient-to-br from-emerald-600 via-teal-600 to-cyan-600 dark:from-emerald-800 dark:via-teal-800 dark:to-cyan-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center">
          <h1 className="text-2xl md:text-3xl font-bold text-white mb-2">
            Deals, Coupons & Referrals
          </h1>
          <p className="text-teal-100 text-lg">Save money on every trip with exclusive partner deals</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tabs */}
        <div className="flex gap-2 mb-8 overflow-x-auto pb-2">
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-all ${
                tab === t.id
                  ? 'bg-teal-600 text-white shadow-lg'
                  : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
              }`}
            >
              <span>{t.icon}</span> {t.label}
            </button>
          ))}
        </div>

        {/* Coupons Tab */}
        {tab === 'coupons' && (
          <div>
            {/* Filters */}
            <div className="flex flex-wrap gap-3 mb-6">
              <input
                type="text"
                placeholder="Filter by destination..."
                value={destination}
                onChange={e => setDestination(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && fetchCoupons()}
                className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-teal-500"
              />
              <select
                value={category}
                onChange={e => setCategory(e.target.value)}
                className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-teal-500"
              >
                {CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
              <button onClick={fetchCoupons} className="px-4 py-2 bg-teal-600 text-white rounded-lg text-sm hover:bg-teal-700">
                Search
              </button>
            </div>

            {loading ? (
              <div className="text-center py-12 text-gray-500">Loading deals...</div>
            ) : coupons.length === 0 ? (
              <div className="text-center py-16">
                <div className="text-5xl mb-4">🏷️</div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">No coupons found</h3>
                <p className="text-gray-500">Try adjusting your filters or check back later for new deals</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {coupons.map(coupon => (
                  <div key={coupon.id} className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-xl transition-shadow">
                    <div className="bg-gradient-to-r from-teal-500 to-emerald-500 px-5 py-3 flex items-center justify-between">
                      <span className="text-white font-bold text-lg">
                        {coupon.discount_type === 'percentage' ? `${coupon.discount_value}%` : `$${coupon.discount_value}`}
                        {' '}{DISCOUNT_LABELS[coupon.discount_type] || 'OFF'}
                      </span>
                      <span className="bg-white/20 text-white text-xs px-2 py-1 rounded-full">{coupon.partner_category}</span>
                    </div>
                    <div className="p-5">
                      <h3 className="font-bold text-gray-900 dark:text-white text-lg">{coupon.title}</h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{coupon.partner_name} - {coupon.partner_destination}</p>
                      {coupon.description && (
                        <p className="text-sm text-gray-600 dark:text-gray-300 mt-2">{coupon.description}</p>
                      )}
                      {coupon.min_spend > 0 && (
                        <p className="text-xs text-gray-400 mt-2">Min. spend: ${coupon.min_spend}</p>
                      )}
                      {coupon.valid_until && (
                        <p className="text-xs text-gray-400 mt-1">Expires: {new Date(coupon.valid_until).toLocaleDateString()}</p>
                      )}
                      <div className="mt-4 flex items-center gap-2">
                        <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-lg px-3 py-2 font-mono text-sm text-gray-800 dark:text-gray-200 border-2 border-dashed border-gray-300 dark:border-gray-600 text-center">
                          {coupon.code}
                        </div>
                        <button
                          onClick={() => copyCode(coupon.code)}
                          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                            copiedCode === coupon.code
                              ? 'bg-green-500 text-white'
                              : 'bg-teal-600 text-white hover:bg-teal-700'
                          }`}
                        >
                          {copiedCode === coupon.code ? 'Copied!' : 'Copy'}
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Referrals Tab */}
        {tab === 'referrals' && (
          <div className="max-w-2xl mx-auto">
            {!isAuthenticated ? (
              <div className="text-center py-16">
                <div className="text-5xl mb-4">🔒</div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Sign in to access referrals</h3>
                <p className="text-gray-500">Join our referral program and earn $5 for every friend you refer</p>
              </div>
            ) : loading ? (
              <div className="text-center py-12 text-gray-500">Loading...</div>
            ) : !referralStats ? (
              <div className="text-center py-16">
                <div className="text-5xl mb-4">🎁</div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Setting up your referral code...</h3>
                <p className="text-gray-500 mb-4">Refresh the page to see your referral code and start earning rewards.</p>
                <button
                  onClick={fetchReferral}
                  className="px-6 py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-all"
                >
                  Try Again
                </button>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Referral Code Card */}
                <div className="bg-gradient-to-br from-purple-600 to-indigo-600 rounded-2xl p-8 text-white text-center">
                  <h2 className="text-xl font-bold mb-2">Your Referral Code</h2>
                  <p className="text-purple-200 mb-4">Share this code with friends and earn $5 for each successful referral</p>
                  <div className="bg-white/20 backdrop-blur-sm rounded-xl px-6 py-4 inline-block">
                    <span className="font-mono text-3xl font-bold tracking-wider">{referralStats.code}</span>
                  </div>
                  <button
                    onClick={() => { navigator.clipboard.writeText(referralStats.code); toast.success('Code copied!'); }}
                    className="block mx-auto mt-4 px-6 py-2 bg-white text-purple-700 rounded-lg font-medium text-sm hover:bg-purple-50 transition-all"
                  >
                    Copy Code
                  </button>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-white dark:bg-gray-800 rounded-xl p-5 text-center border border-gray-200 dark:border-gray-700">
                    <div className="text-3xl font-bold text-gray-900 dark:text-white">{referralStats.total_referrals}</div>
                    <div className="text-sm text-gray-500 mt-1">Total Referrals</div>
                  </div>
                  <div className="bg-white dark:bg-gray-800 rounded-xl p-5 text-center border border-gray-200 dark:border-gray-700">
                    <div className="text-3xl font-bold text-green-600">{referralStats.successful_referrals}</div>
                    <div className="text-sm text-gray-500 mt-1">Converted</div>
                  </div>
                  <div className="bg-white dark:bg-gray-800 rounded-xl p-5 text-center border border-gray-200 dark:border-gray-700">
                    <div className="text-3xl font-bold text-purple-600">${referralStats.total_earnings.toFixed(2)}</div>
                    <div className="text-sm text-gray-500 mt-1">Earnings</div>
                  </div>
                </div>

                {/* Send Referral */}
                <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                  <h3 className="font-bold text-gray-900 dark:text-white mb-3">Invite a Friend</h3>
                  <div className="flex gap-3">
                    <input
                      type="email"
                      value={referralEmail}
                      onChange={e => setReferralEmail(e.target.value)}
                      placeholder="friend@email.com"
                      className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                    />
                    <button
                      onClick={sendReferral}
                      disabled={!referralEmail}
                      className="px-5 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 disabled:opacity-50"
                    >
                      Send Invite
                    </button>
                  </div>
                </div>

                {/* Recent Referrals */}
                {referralStats.recent_referrals?.length > 0 && (
                  <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                    <h3 className="font-bold text-gray-900 dark:text-white mb-3">Recent Referrals</h3>
                    <div className="space-y-3">
                      {referralStats.recent_referrals.map((ref, i) => (
                        <div key={i} className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700 last:border-0">
                          <span className="text-sm text-gray-700 dark:text-gray-300">{ref.email}</span>
                          <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                            ref.status === 'rewarded' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                            ref.status === 'converted' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' :
                            'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                          }`}>
                            {ref.status}
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

        {/* Partner Registration Tab */}
        {tab === 'partner' && (
          <div className="max-w-2xl mx-auto">
            {!isAuthenticated ? (
              <div className="text-center py-16">
                <div className="text-5xl mb-4">🔒</div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Sign in to become a partner</h3>
                <p className="text-gray-500">Create an account or sign in to submit your partner application</p>
              </div>
            ) : (
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 p-8">
              <div className="text-center mb-8">
                <div className="text-5xl mb-3">🤝</div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Partner With Us</h2>
                <p className="text-gray-500 dark:text-gray-400 mt-2">
                  List your business, offer exclusive deals to travelers, and earn revenue through our AI-powered platform
                </p>
              </div>

              {/* Benefits */}
              <div className="grid grid-cols-2 gap-4 mb-8">
                {[
                  { icon: '📈', text: 'Reach millions of AI-guided travelers' },
                  { icon: '🎯', text: 'Targeted exposure to your ideal customers' },
                  { icon: '💰', text: 'Revenue share on AI-assisted bookings' },
                  { icon: '📊', text: 'Analytics dashboard for your deals' },
                ].map((b, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                    <span className="text-lg">{b.icon}</span> {b.text}
                  </div>
                ))}
              </div>

              {/* Form */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Business Name *</label>
                  <input
                    type="text"
                    value={partnerForm.name}
                    onChange={e => setPartnerForm(p => ({ ...p, name: e.target.value }))}
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="e.g. Grand Hotel Istanbul"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Category *</label>
                    <select
                      value={partnerForm.category}
                      onChange={e => setPartnerForm(p => ({ ...p, category: e.target.value }))}
                      className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    >
                      {CATEGORIES.filter(c => c.value).map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">City/Destination *</label>
                    <input
                      type="text"
                      value={partnerForm.destination}
                      onChange={e => setPartnerForm(p => ({ ...p, destination: e.target.value }))}
                      className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      placeholder="e.g. Istanbul"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Contact Email *</label>
                  <input
                    type="email"
                    value={partnerForm.contact_email}
                    onChange={e => setPartnerForm(p => ({ ...p, contact_email: e.target.value }))}
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="partner@business.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Website</label>
                  <input
                    type="url"
                    value={partnerForm.website}
                    onChange={e => setPartnerForm(p => ({ ...p, website: e.target.value }))}
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="https://www.yourbusiness.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Description</label>
                  <textarea
                    value={partnerForm.description}
                    onChange={e => setPartnerForm(p => ({ ...p, description: e.target.value }))}
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    rows={3}
                    placeholder="Tell travelers about your business..."
                  />
                </div>
                <button
                  onClick={registerPartner}
                  className="w-full py-3 bg-gradient-to-r from-teal-600 to-emerald-600 text-white rounded-xl font-semibold text-lg hover:from-teal-700 hover:to-emerald-700 shadow-lg transition-all"
                >
                  Submit Application
                </button>
              </div>
            </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
