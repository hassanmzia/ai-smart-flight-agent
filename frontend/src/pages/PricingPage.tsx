import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import api from '@/services/api';
import toast from 'react-hot-toast';

const PricingPage = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');
  const [currentPlan, setCurrentPlan] = useState<string>('free');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      api.get('/api/agents/subscription').then(res => {
        setCurrentPlan(res.data?.plan || 'free');
      }).catch(() => {});
    }
  }, [isAuthenticated]);

  const handleSubscribe = async (planName: string) => {
    if (!user) {
      navigate('/register');
      return;
    }
    if (planName.toLowerCase() === currentPlan) {
      toast.success('You are already on this plan!');
      return;
    }
    // Free plan — activate directly without payment
    if (planName.toLowerCase() === 'free') {
      setCurrentPlan('free');
      toast.success('You are on the Free plan!');
      return;
    }
    // Paid plans require payment method — Stripe integration not yet configured
    if (planName === 'Business') {
      toast('Business plan requires a custom agreement. Contact us to get started.', { icon: '📧' });
      navigate('/contact');
      return;
    }
    // Pro plan — attempt subscription, show payment required if Stripe is not set up
    setLoading(true);
    try {
      const res = await api.post('/api/agents/subscription/create', {
        plan: planName.toLowerCase(),
        billing_cycle: billingCycle,
      });
      if (res.data?.success || res.data?.plan) {
        setCurrentPlan(planName.toLowerCase());
        toast.success(`Upgraded to ${planName}!`);
      }
    } catch {
      toast.error('Payment method required. Credit/debit card and PayPal support coming soon.');
    } finally {
      setLoading(false);
    }
  };

  const plans = [
    {
      name: 'Free',
      price: { monthly: 0, yearly: 0 },
      description: 'Perfect for occasional travelers',
      features: [
        { text: '3 AI trip plans per month', category: 'ai' },
        { text: '1 active price alert', category: 'alerts' },
        { text: 'Basic flight & hotel search', category: 'search' },
        { text: 'Weather forecasts', category: 'info' },
        { text: 'Destination knowledge base', category: 'kb' },
        { text: 'Coupon & deal access', category: 'deals' },
        { text: 'Referral program', category: 'referral' },
        { text: '5 AI translations/month', category: 'ai' },
        { text: 'Community support', category: 'support' },
      ],
      limitations: [
        'No voice planning',
        'No autonomous agent',
        'No 3D visualization',
        'Ads shown',
      ],
      cta: 'Get Started Free',
      popular: false,
      gradient: 'from-gray-500 to-gray-600',
      icon: '\uD83C\uDF0D',
    },
    {
      name: 'Pro',
      price: { monthly: 9.99, yearly: 99.99 },
      description: 'For frequent travelers who want the best deals',
      features: [
        { text: 'Unlimited AI trip plans', category: 'ai' },
        { text: '10 active price alerts', category: 'alerts' },
        { text: 'Voice-powered planning', category: 'voice' },
        { text: 'Autonomous booking agent', category: 'agent' },
        { text: '3D trip visualization', category: '3d' },
        { text: 'Unlimited AI translations', category: 'ai' },
        { text: 'Smart itinerary auto-builder', category: 'builder' },
        { text: 'Personalized recommendations', category: 'ai' },
        { text: 'Collaborative trips (up to 10)', category: 'collab' },
        { text: 'Real-time price drop alerts', category: 'alerts' },
        { text: 'Ad-free experience', category: 'ads' },
        { text: 'Priority email support', category: 'support' },
      ],
      limitations: [],
      cta: 'Start Pro Trial',
      popular: true,
      gradient: 'from-blue-600 to-indigo-600',
      icon: '\u2708\uFE0F',
    },
    {
      name: 'Business',
      price: { monthly: 29.99, yearly: 299.99 },
      description: 'For teams and travel agencies',
      features: [
        { text: 'Everything in Pro', category: 'all' },
        { text: 'Unlimited price alerts', category: 'alerts' },
        { text: 'Unlimited collaborators', category: 'collab' },
        { text: 'AI Concierge (24/7 agent)', category: 'agent' },
        { text: 'Priority booking assistance', category: 'booking' },
        { text: 'REST API access', category: 'api' },
        { text: 'Custom integrations', category: 'api' },
        { text: 'Dedicated account manager', category: 'support' },
        { text: 'Analytics dashboard', category: 'analytics' },
        { text: 'White-label options', category: 'enterprise' },
        { text: 'SLA guarantee', category: 'enterprise' },
      ],
      limitations: [],
      cta: 'Contact Sales',
      popular: false,
      gradient: 'from-purple-600 to-pink-600',
      icon: '\uD83C\uDFE2',
    },
  ];

  const comparisonFeatures = [
    { name: 'AI Trip Plans', free: '3/month', pro: 'Unlimited', business: 'Unlimited' },
    { name: 'Price Alerts', free: '1', pro: '10', business: 'Unlimited' },
    { name: 'AI Translations', free: '5/month', pro: 'Unlimited', business: 'Unlimited' },
    { name: 'Collaborators', free: '2', pro: '10', business: 'Unlimited' },
    { name: 'Voice Planning', free: false, pro: true, business: true },
    { name: 'Autonomous Agent', free: false, pro: true, business: true },
    { name: '3D Visualization', free: false, pro: true, business: true },
    { name: 'Auto-Builder', free: false, pro: true, business: true },
    { name: 'Ad-Free', free: false, pro: true, business: true },
    { name: 'Destination KB', free: true, pro: true, business: true },
    { name: 'Coupons & Deals', free: true, pro: true, business: true },
    { name: 'Referral Program', free: true, pro: true, business: true },
    { name: 'AI Concierge', free: false, pro: false, business: true },
    { name: 'Priority Booking', free: false, pro: false, business: true },
    { name: 'API Access', free: false, pro: false, business: true },
    { name: 'Analytics Dashboard', free: false, pro: false, business: true },
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Header */}
      <div className="relative overflow-hidden bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 dark:from-indigo-800 dark:via-purple-800 dark:to-pink-800">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute -top-20 -right-20 w-72 h-72 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 left-1/4 w-48 h-48 bg-pink-300 rounded-full blur-3xl"></div>
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 md:py-20 text-center">
          <h1 className="text-xl md:text-2xl font-extrabold text-white mb-4">
            Choose Your Travel Plan
          </h1>
          <p className="text-xl text-purple-100 max-w-2xl mx-auto mb-8">
            Unlock the full power of AI-driven travel planning. Save time, save money, travel smarter.
          </p>

          {/* Billing Toggle */}
          <div className="inline-flex items-center gap-3 bg-white/10 backdrop-blur-sm rounded-full p-1">
            <button
              onClick={() => setBillingCycle('monthly')}
              className={`px-5 py-2 rounded-full text-sm font-medium transition-all ${
                billingCycle === 'monthly'
                  ? 'bg-white text-purple-700 shadow-lg'
                  : 'text-white hover:text-purple-100'
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingCycle('yearly')}
              className={`px-5 py-2 rounded-full text-sm font-medium transition-all ${
                billingCycle === 'yearly'
                  ? 'bg-white text-purple-700 shadow-lg'
                  : 'text-white hover:text-purple-100'
              }`}
            >
              Yearly <span className="text-xs opacity-75">(Save 17%)</span>
            </button>
          </div>
        </div>
      </div>

      {/* Pricing Cards */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-12 relative z-10 pb-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map((plan) => {
            const isCurrent = plan.name.toLowerCase() === currentPlan;
            return (
              <div
                key={plan.name}
                className={`relative bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-2xl shadow-xl border ${
                  plan.popular
                    ? 'border-indigo-300 dark:border-indigo-600 ring-2 ring-indigo-500/20 scale-105'
                    : 'border-gray-200/60 dark:border-gray-700/50'
                } overflow-hidden transition-transform hover:scale-[1.02]`}
              >
                {plan.popular && (
                  <div className="absolute top-0 left-0 right-0 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-center text-sm font-semibold py-1.5">
                    Most Popular
                  </div>
                )}

                <div className={`p-8 ${plan.popular ? 'pt-12' : ''}`}>
                  <div className="text-4xl mb-3">{plan.icon}</div>
                  <h3 className="text-2xl font-bold text-gray-900 dark:text-white">{plan.name}</h3>
                  <p className="text-gray-600 dark:text-gray-400 mt-1 text-sm">{plan.description}</p>

                  <div className="mt-6 mb-8">
                    <span className="text-3xl font-bold text-gray-900 dark:text-white">
                      ${billingCycle === 'monthly' ? plan.price.monthly : plan.price.yearly}
                    </span>
                    {plan.price.monthly > 0 && (
                      <span className="text-gray-500 dark:text-gray-400 ml-1">
                        /{billingCycle === 'monthly' ? 'mo' : 'yr'}
                      </span>
                    )}
                  </div>

                  <button
                    onClick={() => handleSubscribe(plan.name)}
                    disabled={loading || isCurrent}
                    className={`w-full py-3 rounded-xl font-semibold text-white shadow-lg transition-all duration-200 hover:shadow-xl disabled:opacity-60 ${
                      isCurrent
                        ? 'bg-green-500 cursor-default'
                        : plan.popular
                        ? 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 shadow-blue-500/25'
                        : `bg-gradient-to-r ${plan.gradient} hover:opacity-90 shadow-gray-500/10`
                    }`}
                  >
                    {isCurrent ? 'Current Plan' : plan.cta}
                  </button>

                  {/* Features */}
                  <div className="mt-8 space-y-3">
                    {plan.features.map((feature) => (
                      <div key={feature.text} className="flex items-start gap-3">
                        <svg className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span className="text-sm text-gray-700 dark:text-gray-300">{feature.text}</span>
                      </div>
                    ))}
                    {plan.limitations.map((limitation) => (
                      <div key={limitation} className="flex items-start gap-3">
                        <svg className="w-5 h-5 text-gray-300 dark:text-gray-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                        <span className="text-sm text-gray-400 dark:text-gray-500">{limitation}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Feature Comparison Table */}
        <div className="mt-20">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-8 text-center">
            Feature Comparison
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full max-w-4xl mx-auto">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-4 px-4 text-sm font-semibold text-gray-600 dark:text-gray-400">Feature</th>
                  <th className="text-center py-4 px-4 text-sm font-semibold text-gray-600 dark:text-gray-400">Free</th>
                  <th className="text-center py-4 px-4 text-sm font-semibold text-indigo-600 dark:text-indigo-400">Pro</th>
                  <th className="text-center py-4 px-4 text-sm font-semibold text-purple-600 dark:text-purple-400">Business</th>
                </tr>
              </thead>
              <tbody>
                {comparisonFeatures.map((feature, i) => (
                  <tr key={feature.name} className={i % 2 === 0 ? 'bg-gray-50/50 dark:bg-gray-800/50' : ''}>
                    <td className="py-3 px-4 text-sm text-gray-700 dark:text-gray-300">{feature.name}</td>
                    {(['free', 'pro', 'business'] as const).map((plan) => (
                      <td key={plan} className="py-3 px-4 text-center">
                        {typeof feature[plan] === 'boolean' ? (
                          feature[plan] ? (
                            <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-green-100 dark:bg-green-900/30">
                              <svg className="w-4 h-4 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                            </span>
                          ) : (
                            <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-gray-100 dark:bg-gray-700">
                              <svg className="w-4 h-4 text-gray-400 dark:text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                              </svg>
                            </span>
                          )
                        ) : (
                          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{feature[plan]}</span>
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* FAQ Section */}
        <div className="mt-20 text-center">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
            Frequently Asked Questions
          </h2>
          <div className="max-w-3xl mx-auto mt-8 space-y-4">
            {[
              { q: 'Can I cancel anytime?', a: 'Yes! You can cancel your subscription at any time. Your access continues until the end of your billing period.' },
              { q: 'Is there a free trial for Pro?', a: 'Yes, Pro comes with a 14-day free trial. No credit card required to start.' },
              { q: 'What payment methods do you accept?', a: 'We accept all major credit cards, debit cards, and PayPal through our secure Stripe payment system.' },
              { q: 'Can I switch plans?', a: 'Absolutely! You can upgrade or downgrade your plan at any time. Changes take effect on your next billing cycle.' },
              { q: 'Do I get coupons on the Free plan?', a: 'Yes! All users can browse and redeem partner coupons. Pro users get early access to exclusive deals.' },
              { q: 'How does the referral program work?', a: 'Share your referral code with friends. When they sign up and make their first booking, you both earn $5 in travel credits.' },
            ].map((faq, i) => (
              <div key={i} className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 text-left border border-gray-200/60 dark:border-gray-700/50">
                <h4 className="font-semibold text-gray-900 dark:text-white">{faq.q}</h4>
                <p className="text-gray-600 dark:text-gray-400 mt-2 text-sm">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PricingPage;
