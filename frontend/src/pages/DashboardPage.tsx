import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { differenceInCalendarDays, differenceInDays, parseISO } from 'date-fns';
import { useAuth, useRequireAuth } from '@/hooks/useAuth';
import { getBookings } from '@/services/bookingService';
import { getItineraries } from '@/services/itineraryService';
import { getNotifications } from '@/services/notificationService';
import { getPriceAlerts } from '@/services/priceAlertService';
import weatherService from '@/services/weatherService';
import safetyService from '@/services/safetyService';
import api from '@/services/api';
import { Card, CardContent } from '@/components/common';
import Loading from '@/components/common/Loading';
import Button from '@/components/common/Button';
import { QUERY_KEYS, ROUTES, API_ENDPOINTS } from '@/utils/constants';
import { formatCurrency, formatDate } from '@/utils/formatters';

/* -------------------------------------------------------------------------- */
/* Helpers                                                                     */
/* -------------------------------------------------------------------------- */

const safeParse = (d?: string | null): Date | null => {
  if (!d) return null;
  try {
    return parseISO(d);
  } catch {
    return null;
  }
};

const firstCity = (destination?: string): string => {
  if (!destination) return '';
  return destination.split(',')[0].trim();
};

const asArray = <T,>(data: any): T[] => {
  if (!data) return [];
  if (Array.isArray(data)) return data as T[];
  if (Array.isArray(data.items)) return data.items as T[];
  if (Array.isArray(data.results)) return data.results as T[];
  return [];
};

/* -------------------------------------------------------------------------- */
/* DashboardPage                                                               */
/* -------------------------------------------------------------------------- */

const DashboardPage = () => {
  const { isLoading: isAuthLoading } = useRequireAuth();
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  // ── Core queries (must resolve before we can render)
  const { data: bookingsData, isLoading: isLoadingBookings } = useQuery({
    queryKey: QUERY_KEYS.BOOKINGS,
    queryFn: () => getBookings(1, 50),
    enabled: isAuthenticated,
  });

  const { data: itinerariesData, isLoading: isLoadingItineraries } = useQuery({
    queryKey: QUERY_KEYS.ITINERARIES,
    queryFn: () => getItineraries(),
    enabled: isAuthenticated,
  });

  // ── Supplemental queries (render gracefully if they fail)
  const { data: notificationsData } = useQuery({
    queryKey: [...QUERY_KEYS.NOTIFICATIONS, 'dashboard'],
    queryFn: () => getNotifications(1, 5, true),
    enabled: isAuthenticated,
    retry: false,
  });

  const { data: priceAlertsData } = useQuery({
    queryKey: [...QUERY_KEYS.PRICE_ALERTS, 'dashboard'],
    queryFn: () => getPriceAlerts('active'),
    enabled: isAuthenticated,
    retry: false,
  });

  const { data: travelDna } = useQuery({
    queryKey: ['travel-dna', 'dashboard'],
    queryFn: async () => {
      const res = await api.get(API_ENDPOINTS.AGENT.TRAVEL_DNA);
      return res.data;
    },
    enabled: isAuthenticated,
    retry: false,
  });

  const { data: recommendations } = useQuery({
    queryKey: ['recommendations', 'dashboard'],
    queryFn: async () => {
      const res = await api.get(API_ENDPOINTS.AGENT.RECOMMENDATIONS);
      return res.data;
    },
    enabled: isAuthenticated,
    retry: false,
  });

  // Normalize core data
  const bookings = asArray<any>(bookingsData);
  const itineraries = asArray<any>(itinerariesData);
  const notifications = asArray<any>(notificationsData);
  const priceAlerts = asArray<any>(priceAlertsData);
  const recoList = asArray<any>(recommendations).slice(0, 4);

  /* ---------------------------- Derived insights --------------------------- */

  // Next upcoming trip (for outlook card)
  const nextTrip = useMemo(() => {
    const now = new Date();
    const upcoming = itineraries
      .filter((t: any) => {
        const end = safeParse(t.end_date);
        return end && end >= now && ['planned', 'approved', 'booked', 'active'].includes(t.status);
      })
      .sort((a: any, b: any) => {
        const da = safeParse(a.start_date)?.getTime() || 0;
        const db = safeParse(b.start_date)?.getTime() || 0;
        return da - db;
      });
    return upcoming[0] || null;
  }, [itineraries]);

  const nextTripCountdown = useMemo(() => {
    if (!nextTrip) return null;
    const start = safeParse(nextTrip.start_date);
    if (!start) return null;
    const days = differenceInCalendarDays(start, new Date());
    return { days, start, trip: nextTrip };
  }, [nextTrip]);

  // Action items — trips/bookings that need the user's attention
  const actionItems = useMemo(() => {
    const items: Array<{
      id: string;
      icon: string;
      title: string;
      subtitle: string;
      cta: string;
      to: string;
      accent: string;
    }> = [];

    itineraries.forEach((t: any) => {
      if (t.status === 'draft') {
        items.push({
          id: `draft-${t.id}`,
          icon: '📝',
          title: `Finish planning "${t.title}"`,
          subtitle: `${t.destination} · Awaiting your review`,
          cta: 'Review plan',
          to: `/itineraries/${t.id}`,
          accent: 'from-amber-500 to-orange-500',
        });
      } else if (t.status === 'planned') {
        items.push({
          id: `planned-${t.id}`,
          icon: '✅',
          title: `Approve "${t.title}"`,
          subtitle: `${t.destination} · Ready for your sign-off`,
          cta: 'Approve',
          to: `/itineraries/${t.id}`,
          accent: 'from-blue-500 to-indigo-500',
        });
      } else if (t.status === 'approved') {
        items.push({
          id: `approved-${t.id}`,
          icon: '💳',
          title: `Book "${t.title}"`,
          subtitle: `${t.destination} · Lock in flights & stays`,
          cta: 'Book now',
          to: `/itineraries/${t.id}`,
          accent: 'from-emerald-500 to-teal-500',
        });
      }
    });

    bookings.forEach((b: any) => {
      if (b.status === 'pending') {
        items.push({
          id: `booking-${b.id}`,
          icon: '⏳',
          title: b.notes || `Complete booking #${b.booking_number}`,
          subtitle: `Payment pending · ${formatCurrency(parseFloat(b.total_amount || 0), b.currency)}`,
          cta: 'Complete',
          to: `/booking/${b.id}`,
          accent: 'from-rose-500 to-pink-500',
        });
      }
    });

    return items.slice(0, 4);
  }, [itineraries, bookings]);

  // Travel stats (derived — no duplication of Trips/Bookings lists)
  const stats = useMemo(() => {
    const completed = itineraries.filter((t: any) => t.status === 'completed');
    const countries = new Set<string>();
    completed.forEach((t: any) => {
      const country = (t.destination_country || '').trim();
      if (country) countries.add(country.toLowerCase());
      else if (t.destination) {
        const parts = t.destination.split(',').map((s: string) => s.trim());
        if (parts.length > 1) countries.add(parts[parts.length - 1].toLowerCase());
      }
    });
    const nights = completed.reduce((sum: number, t: any) => {
      const start = safeParse(t.start_date);
      const end = safeParse(t.end_date);
      if (start && end) return sum + Math.max(0, differenceInDays(end, start));
      return sum;
    }, 0);
    const activeWatches = priceAlerts.filter((a: any) => a.status !== 'paused' && a.status !== 'expired').length;

    return {
      countries: countries.size,
      completedTrips: completed.length,
      nightsAway: nights,
      priceWatches: activeWatches,
    };
  }, [itineraries, priceAlerts]);

  // Weather + safety for next trip (only fires when destination known)
  const nextTripCity = firstCity(nextTrip?.destination);
  const { data: nextTripWeather } = useQuery({
    queryKey: ['dashboard-next-weather', nextTripCity, nextTrip?.start_date, nextTrip?.end_date],
    queryFn: () =>
      weatherService.getWeatherForecast({
        city: nextTripCity,
        start_date: nextTrip?.start_date,
        end_date: nextTrip?.end_date,
      }),
    enabled: isAuthenticated && !!nextTripCity,
    retry: false,
    staleTime: 1000 * 60 * 30,
  });

  const { data: nextTripSafety } = useQuery({
    queryKey: ['dashboard-next-safety', nextTripCity, nextTrip?.start_date, nextTrip?.end_date],
    queryFn: () =>
      safetyService.getSafetyInfo({
        city: nextTripCity,
        start_date: nextTrip?.start_date,
        end_date: nextTrip?.end_date,
      }),
    enabled: isAuthenticated && !!nextTripCity,
    retry: false,
    staleTime: 1000 * 60 * 30,
  });

  /* --------------------------------- Render -------------------------------- */

  const isLoading = isAuthLoading || isLoadingBookings || isLoadingItineraries;

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Loading size="lg" text="Loading your dashboard..." />
      </div>
    );
  }

  const firstName = user?.first_name || 'Traveler';
  const dnaPrimary =
    travelDna?.primary_personality ||
    travelDna?.personality ||
    travelDna?.archetype ||
    travelDna?.top_type;
  const dnaIcon = travelDna?.icon || '🧬';

  const statCards = [
    {
      label: 'Countries Visited',
      value: stats.countries,
      icon: '🌍',
      gradient: 'from-blue-500 to-cyan-500',
      tone: 'from-blue-50 to-cyan-50 dark:from-blue-950/30 dark:to-cyan-950/30',
    },
    {
      label: 'Completed Trips',
      value: stats.completedTrips,
      icon: '🎒',
      gradient: 'from-emerald-500 to-teal-500',
      tone: 'from-emerald-50 to-teal-50 dark:from-emerald-950/30 dark:to-teal-950/30',
    },
    {
      label: 'Nights Away',
      value: stats.nightsAway,
      icon: '🌙',
      gradient: 'from-violet-500 to-purple-500',
      tone: 'from-violet-50 to-purple-50 dark:from-violet-950/30 dark:to-purple-950/30',
    },
    {
      label: 'Price Watches',
      value: stats.priceWatches,
      icon: '📉',
      gradient: 'from-amber-500 to-orange-500',
      tone: 'from-amber-50 to-orange-50 dark:from-amber-950/30 dark:to-orange-950/30',
    },
  ];

  return (
    <div className="min-h-screen">
      {/* ─────────────────── Hero ─────────────────── */}
      <div className="relative overflow-hidden bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-700 dark:from-blue-800 dark:via-indigo-800 dark:to-purple-900">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 -right-40 w-80 h-80 bg-white rounded-full blur-3xl" />
          <div className="absolute -bottom-20 -left-20 w-60 h-60 bg-purple-300 rounded-full blur-3xl" />
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-white mb-2">
                Welcome back, {firstName}
              </h1>
              <p className="text-blue-100 text-lg">
                Your intelligent travel command center — insights, alerts, and next steps.
              </p>
              {dnaPrimary && (
                <button
                  onClick={() => navigate(ROUTES.TRAVEL_PROFILE)}
                  className="mt-4 inline-flex items-center gap-2 rounded-full bg-white/15 hover:bg-white/25 backdrop-blur px-4 py-2 text-sm font-medium text-white transition"
                >
                  <span>{dnaIcon}</span>
                  <span>Your Travel DNA:</span>
                  <span className="font-semibold">{dnaPrimary}</span>
                  <span className="opacity-70">→</span>
                </button>
              )}
            </div>

            {nextTripCountdown && (
              <div className="rounded-2xl bg-white/10 backdrop-blur border border-white/20 p-5 text-white min-w-[220px]">
                <p className="text-xs uppercase tracking-wider text-blue-100 mb-1">Next Trip</p>
                <p className="text-xl font-semibold truncate">{nextTripCountdown.trip.title}</p>
                <p className="text-sm text-blue-100 truncate">{nextTripCountdown.trip.destination}</p>
                <div className="mt-3 flex items-baseline gap-2">
                  <span className="text-4xl font-bold">
                    {nextTripCountdown.days > 0
                      ? nextTripCountdown.days
                      : nextTripCountdown.days === 0
                      ? 'Today'
                      : 'Live'}
                  </span>
                  {nextTripCountdown.days > 0 && (
                    <span className="text-sm text-blue-100">
                      {nextTripCountdown.days === 1 ? 'day to go' : 'days to go'}
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8 relative z-10 pb-12 space-y-6">
        {/* ─────────────────── Stats ─────────────────── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {statCards.map((s) => (
            <Card key={s.label} variant="glass" padding="none" className="overflow-hidden">
              <div className={`bg-gradient-to-br ${s.tone} p-5`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1 uppercase tracking-wide">
                      {s.label}
                    </p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">{s.value}</p>
                  </div>
                  <div
                    className={`w-11 h-11 rounded-xl bg-gradient-to-br ${s.gradient} text-white shadow-lg flex items-center justify-center text-xl`}
                  >
                    {s.icon}
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>

        {/* ─────────────────── Action Items + Alerts row ─────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* Action Items */}
          <Card variant="glass" className="lg:col-span-2">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-gradient-to-br from-amber-500 to-orange-500 text-white">
                  ⚡
                </div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">Action Items</h2>
              </div>
              <span className="text-xs px-2.5 py-1 rounded-full bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400 font-medium">
                {actionItems.length} pending
              </span>
            </div>
            {actionItems.length === 0 ? (
              <div className="text-center py-8">
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald-100 to-teal-100 dark:from-emerald-900/30 dark:to-teal-900/30 mb-3 text-3xl">
                  🎉
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  You're all caught up. No pending trips or bookings need attention.
                </p>
              </div>
            ) : (
              <div className="space-y-2.5">
                {actionItems.map((a) => (
                  <button
                    key={a.id}
                    onClick={() => navigate(a.to)}
                    className="w-full flex items-center gap-3 p-3.5 rounded-xl bg-gray-50/80 dark:bg-gray-700/30 hover:bg-white dark:hover:bg-gray-700/60 border border-transparent hover:border-gray-200/80 dark:hover:border-gray-600 transition-all text-left group"
                  >
                    <div
                      className={`w-10 h-10 rounded-lg bg-gradient-to-br ${a.accent} text-white flex items-center justify-center text-lg shadow-md shrink-0`}
                    >
                      {a.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-gray-900 dark:text-white truncate">{a.title}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{a.subtitle}</p>
                    </div>
                    <span className="text-sm font-medium text-indigo-600 dark:text-indigo-400 group-hover:translate-x-0.5 transition-transform shrink-0">
                      {a.cta} →
                    </span>
                  </button>
                ))}
              </div>
            )}
          </Card>

          {/* Alerts / Notifications */}
          <Card variant="glass">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-gradient-to-br from-rose-500 to-pink-500 text-white">
                  🔔
                </div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">Alerts</h2>
              </div>
              {notifications.length > 0 && (
                <span className="text-xs px-2.5 py-1 rounded-full bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400 font-medium">
                  {notifications.length} new
                </span>
              )}
            </div>
            {notifications.length === 0 ? (
              <div className="text-center py-8">
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-700 mb-3 text-3xl">
                  ✨
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">No new alerts.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {notifications.slice(0, 4).map((n: any) => (
                  <div
                    key={n.id}
                    className="p-3 rounded-lg bg-gray-50/80 dark:bg-gray-700/30 border-l-2 border-rose-400 dark:border-rose-500"
                  >
                    <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                      {n.title || n.message_title || 'Notification'}
                    </p>
                    {n.message && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2">
                        {n.message}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* ─────────────────── Next Trip Outlook ─────────────────── */}
        {nextTrip && (
          <Card variant="glass">
            <div className="flex items-center justify-between mb-5">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-gradient-to-br from-sky-500 to-indigo-500 text-white">
                  🧭
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900 dark:text-white">Next Trip Outlook</h2>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {nextTrip.destination} ·{' '}
                    {nextTrip.start_date && formatDate(nextTrip.start_date, 'MMM dd')} -{' '}
                    {nextTrip.end_date && formatDate(nextTrip.end_date, 'MMM dd, yyyy')}
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate(`/itineraries/${nextTrip.id}`)}
              >
                Open trip
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Weather */}
              <div className="rounded-xl bg-gradient-to-br from-sky-50 to-blue-50 dark:from-sky-950/30 dark:to-blue-950/30 p-4 border border-sky-100 dark:border-sky-900/40">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-2xl">🌤️</span>
                  <p className="font-semibold text-gray-900 dark:text-white">Weather</p>
                </div>
                {nextTripWeather?.forecasts?.length ? (
                  <>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {Math.round(nextTripWeather.forecasts[0].temp_avg)}°
                      <span className="text-base font-normal text-gray-500 dark:text-gray-400 ml-1">
                        avg
                      </span>
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-300 capitalize">
                      {nextTripWeather.forecasts[0].description}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {nextTripWeather.forecasts.length}-day forecast available
                    </p>
                  </>
                ) : (
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Forecast loading — check closer to your dates.
                  </p>
                )}
              </div>

              {/* Safety */}
              <div className="rounded-xl bg-gradient-to-br from-emerald-50 to-green-50 dark:from-emerald-950/30 dark:to-green-950/30 p-4 border border-emerald-100 dark:border-emerald-900/40">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-2xl">🛡️</span>
                  <p className="font-semibold text-gray-900 dark:text-white">Safety Score</p>
                </div>
                {nextTripSafety?.safety_score != null ? (
                  <>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {nextTripSafety.safety_score}
                      <span className="text-base font-normal text-gray-500 dark:text-gray-400 ml-1">
                        /100
                      </span>
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-300 capitalize">
                      {nextTripSafety.overall_rating || 'Assessment ready'}
                    </p>
                    {nextTripSafety.active_alerts?.length ? (
                      <p className="text-xs text-rose-600 dark:text-rose-400 mt-1">
                        {nextTripSafety.active_alerts.length} active alert(s)
                      </p>
                    ) : (
                      <p className="text-xs text-emerald-600 dark:text-emerald-400 mt-1">
                        No active alerts
                      </p>
                    )}
                  </>
                ) : (
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Assessing destination safety…
                  </p>
                )}
              </div>

              {/* Budget / Readiness */}
              <div className="rounded-xl bg-gradient-to-br from-violet-50 to-purple-50 dark:from-violet-950/30 dark:to-purple-950/30 p-4 border border-violet-100 dark:border-violet-900/40">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-2xl">💼</span>
                  <p className="font-semibold text-gray-900 dark:text-white">Trip Readiness</p>
                </div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white capitalize">
                  {nextTrip.status}
                </p>
                {nextTrip.estimated_budget && (
                  <p className="text-sm text-gray-600 dark:text-gray-300">
                    Budget:{' '}
                    {formatCurrency(
                      parseFloat(nextTrip.estimated_budget),
                      nextTrip.currency || 'USD'
                    )}
                  </p>
                )}
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {nextTrip.number_of_travelers || 1} traveler
                  {(nextTrip.number_of_travelers || 1) !== 1 ? 's' : ''}
                </p>
              </div>
            </div>
          </Card>
        )}

        {/* ─────────────────── AI Recommendations ─────────────────── */}
        {recoList.length > 0 && (
          <Card variant="glass">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-gradient-to-br from-fuchsia-500 to-pink-500 text-white">
                  ✨
                </div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                  Picked for You
                </h2>
              </div>
              <span className="text-xs text-gray-500 dark:text-gray-400">AI-powered</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {recoList.map((r: any, idx: number) => {
                const title = r.destination || r.title || r.name || `Idea ${idx + 1}`;
                const reason = r.reason || r.description || r.summary || '';
                return (
                  <button
                    key={r.id || idx}
                    onClick={() =>
                      navigate(
                        `${ROUTES.AI_PLANNER}?destination=${encodeURIComponent(title)}`
                      )
                    }
                    className="text-left p-4 rounded-xl bg-gradient-to-br from-fuchsia-50 to-pink-50 dark:from-fuchsia-950/20 dark:to-pink-950/20 border border-fuchsia-100 dark:border-fuchsia-900/30 hover:shadow-md hover:-translate-y-0.5 transition-all"
                  >
                    <p className="font-semibold text-gray-900 dark:text-white mb-1 truncate">
                      {title}
                    </p>
                    {reason && (
                      <p className="text-xs text-gray-600 dark:text-gray-300 line-clamp-3">
                        {reason}
                      </p>
                    )}
                    <p className="text-xs text-fuchsia-600 dark:text-fuchsia-400 mt-2 font-medium">
                      Plan a trip →
                    </p>
                  </button>
                );
              })}
            </div>
          </Card>
        )}

        {/* ─────────────────── Explore Intelligence Tools ─────────────────── */}
        <Card variant="glass">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-gradient-to-br from-indigo-500 to-blue-500 text-white">
              🧠
            </div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              Intelligence Tools
            </h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {[
              { icon: '🌍', label: 'My Travel Map', to: ROUTES.TRIP_MAP },
              { icon: '🔮', label: 'Predictions', to: ROUTES.PREDICTIONS },
              { icon: '🛡️', label: 'Safety', to: ROUTES.SAFETY_DASHBOARD },
              { icon: '🧬', label: 'Travel DNA', to: ROUTES.TRAVEL_PROFILE },
              { icon: '🏷️', label: 'Deals', to: ROUTES.DEALS },
              { icon: '👥', label: 'Community', to: ROUTES.COMMUNITY },
            ].map((t) => (
              <button
                key={t.label}
                onClick={() => navigate(t.to)}
                className="flex flex-col items-center justify-center p-3 rounded-xl bg-gray-50/80 dark:bg-gray-700/30 hover:bg-gradient-to-br hover:from-indigo-50 hover:to-blue-50 dark:hover:from-indigo-950/30 dark:hover:to-blue-950/30 border border-transparent hover:border-indigo-200/60 dark:hover:border-indigo-800/40 transition-all group"
              >
                <span className="text-2xl mb-1 group-hover:scale-110 transition-transform">
                  {t.icon}
                </span>
                <span className="text-xs font-medium text-gray-700 dark:text-gray-300 text-center">
                  {t.label}
                </span>
              </button>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default DashboardPage;
