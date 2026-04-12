import { ROUTES } from '@/utils/constants';

interface Props {
  destination: string;
  startDate?: string;
  endDate?: string;
  travelers?: number;
  status: string;
}

interface FeatureCard {
  to: string;
  icon: string;
  title: string;
  desc: string;
  gradient: string;
  iconBg: string;
}

/**
 * Trip Intelligence Hub — renders feature-discovery cards on the
 * ItineraryDetailPage, adapted to the current trip status. Every card
 * forwards destination/dates via query params so the target page can
 * auto-fill its forms.
 */
const TripIntelligencePanel = ({ destination, startDate, endDate, travelers, status }: Props) => {
  if (!destination) return null;

  // Build query string for deep links
  const params = new URLSearchParams({ destination });
  if (startDate) params.set('start_date', startDate);
  if (endDate) params.set('end_date', endDate);
  if (travelers) params.set('travelers', String(travelers));
  const q = `?${params.toString()}`;

  // ── BOOKED/ACTIVE: in-trip companions
  const inTripCards: FeatureCard[] = [
    {
      to: `${ROUTES.PARTNERSHIPS}${q}`,
      icon: '🏷️',
      title: 'Local Deals & Coupons',
      desc: 'Discounts at hotels, restaurants, and attractions on your trip.',
      gradient: 'from-rose-500 to-red-500',
      iconBg: 'bg-white/20',
    },
    {
      to: `${ROUTES.HEALTH_TRAVEL}${q}`,
      icon: '🏥',
      title: 'Health & Wellness',
      desc: 'Medical facilities, accessibility, medication timezone adjust.',
      gradient: 'from-sky-500 to-blue-600',
      iconBg: 'bg-white/20',
    },
    {
      to: `${ROUTES.FAITH_TRAVEL}${q}`,
      icon: '🕌',
      title: 'Faith & Cultural',
      desc: 'Prayer times, worship places, dietary-friendly restaurants.',
      gradient: 'from-emerald-500 to-teal-600',
      iconBg: 'bg-white/20',
    },
    {
      to: `${ROUTES.COLLABORATE}${q}`,
      icon: '👥',
      title: 'Invite Travel Buddies',
      desc: 'Collaborate on plans and split costs with your group.',
      gradient: 'from-indigo-500 to-blue-600',
      iconBg: 'bg-white/20',
    },
  ];

  // ── COMPLETED: post-trip memory & sharing
  const postTripCards: FeatureCard[] = [
    {
      to: `${ROUTES.TRIP_MEMORY}${q}`,
      icon: '🧠',
      title: 'Save Trip Memories',
      desc: 'Log highlights, reflections, and photos from your journey.',
      gradient: 'from-purple-500 to-fuchsia-500',
      iconBg: 'bg-white/20',
    },
    {
      to: `${ROUTES.TRAVEL_STORIES}${q}`,
      icon: '📖',
      title: 'Share Your Story',
      desc: 'Turn your trip into a beautiful, shareable travel story.',
      gradient: 'from-pink-500 to-rose-500',
      iconBg: 'bg-white/20',
    },
    {
      to: `${ROUTES.TRIP_GALLERY}${q}`,
      icon: '📸',
      title: 'Upload to Gallery',
      desc: 'Add photos to your personal trip gallery and travel map.',
      gradient: 'from-amber-500 to-orange-500',
      iconBg: 'bg-white/20',
    },
    {
      to: `${ROUTES.CONTENT_HUB}${q}`,
      icon: '💡',
      title: 'Share Tips',
      desc: 'Submit insider tips that help future travelers.',
      gradient: 'from-teal-500 to-cyan-600',
      iconBg: 'bg-white/20',
    },
  ];

  // This panel now shows ONLY stage-specific cards that SmartTripPreview doesn't
  // cover (in-trip and post-trip actions). Pre-trip insights/tools are surfaced
  // inline by SmartTripPreview so this panel stays out of the way until the
  // customer actually needs trip-companion or memory-capture features.
  const showInTrip = ['booked', 'active'].includes(status);
  const showPostTrip = status === 'completed';

  const sections: Array<{ title: string; subtitle: string; icon: string; cards: FeatureCard[] }> = [];
  if (showInTrip) {
    sections.push({
      title: 'Make the Most of Your Trip',
      subtitle: 'Local deals, wellness, and real-time helpers.',
      icon: '🌟',
      cards: inTripCards,
    });
  }
  if (showPostTrip) {
    sections.push({
      title: 'Relive Your Journey',
      subtitle: 'Capture your memories and inspire others.',
      icon: '🏁',
      cards: postTripCards,
    });
  }

  // Pre-trip stages: SmartTripPreview alone covers it, nothing to add here.
  if (sections.length === 0) return null;

  return (
    <div className="mb-8">
      <div className="bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 dark:from-indigo-900/20 dark:via-purple-900/20 dark:to-pink-900/20 rounded-3xl p-6 sm:p-8 border border-purple-100 dark:border-purple-800/30 shadow-sm">
        <div className="flex items-center gap-3 mb-1">
          <span className="text-3xl">🧭</span>
          <h2 className="text-xl sm:text-2xl font-extrabold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 dark:from-indigo-400 dark:via-purple-400 dark:to-pink-400 bg-clip-text text-transparent">
            Trip Intelligence Hub
          </h2>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
          Every tool you need for <span className="font-semibold text-gray-800 dark:text-gray-200">{destination}</span>, pre-configured for your trip.
        </p>
        <div className="mb-6 flex items-start gap-2 text-xs text-gray-600 dark:text-gray-400 bg-white/70 dark:bg-gray-800/50 rounded-xl px-3 py-2 border border-purple-100 dark:border-purple-800/40">
          <span className="mt-0.5">💡</span>
          <span>
            Each card opens in a <span className="font-semibold">new tab</span> so you never lose
            your place here. Close the tab to return — your entries on this page are safe.
          </span>
        </div>

        {sections.map((section, si) => (
          <div key={si} className={si > 0 ? 'mt-8' : ''}>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xl">{section.icon}</span>
              <div>
                <h3 className="font-bold text-gray-900 dark:text-white">{section.title}</h3>
                <p className="text-xs text-gray-500 dark:text-gray-400">{section.subtitle}</p>
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {section.cards.map((card) => (
                <a
                  key={card.to}
                  href={card.to}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`group relative bg-gradient-to-br ${card.gradient} rounded-2xl p-4 text-white overflow-hidden shadow-md hover:shadow-xl hover:scale-[1.02] transition-all duration-200`}
                  title="Opens in a new tab — your planner stays open"
                >
                  <div className={`inline-flex items-center justify-center w-10 h-10 rounded-xl ${card.iconBg} backdrop-blur-sm text-xl mb-2`}>
                    {card.icon}
                  </div>
                  <h4 className="font-bold text-sm mb-1 flex items-center gap-1">
                    {card.title}
                    <span className="opacity-60 text-[10px]" aria-hidden>↗</span>
                  </h4>
                  <p className="text-xs text-white/85 leading-snug">{card.desc}</p>
                </a>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TripIntelligencePanel;
