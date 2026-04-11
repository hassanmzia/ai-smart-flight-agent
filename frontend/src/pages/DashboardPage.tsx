import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useRequireAuth } from '@/hooks/useAuth';
import { useAuth } from '@/hooks/useAuth';
import { getBookings } from '@/services/bookingService';
import { getItineraries } from '@/services/itineraryService';
import { Card, CardContent } from '@/components/common';
import Loading from '@/components/common/Loading';
import Button from '@/components/common/Button';
import { QUERY_KEYS, ROUTES } from '@/utils/constants';
import { formatCurrency, formatDate } from '@/utils/formatters';

const DashboardPage = () => {
  const { isLoading: isAuthLoading } = useRequireAuth();
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const { data: bookingsData, isLoading: isLoadingBookings } = useQuery({
    queryKey: QUERY_KEYS.BOOKINGS,
    queryFn: () => getBookings(),
    enabled: isAuthenticated,
  });

  const { data: itinerariesData, isLoading: isLoadingItineraries } = useQuery({
    queryKey: QUERY_KEYS.ITINERARIES,
    queryFn: () => getItineraries(),
    enabled: isAuthenticated,
  });

  const isLoading = isAuthLoading || isLoadingBookings || isLoadingItineraries;

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Loading size="lg" text="Loading your dashboard..." />
      </div>
    );
  }

  // Handle different response structures for bookings
  let bookings: any[] = [];
  if (bookingsData) {
    if (Array.isArray(bookingsData.items)) {
      bookings = bookingsData.items;
    } else if (Array.isArray(bookingsData)) {
      bookings = bookingsData;
    } else if (Array.isArray(bookingsData.results)) {
      bookings = bookingsData.results;
    }
  }

  // Handle different response structures for itineraries
  let itineraries: any[] = [];
  if (itinerariesData) {
    if (Array.isArray(itinerariesData)) {
      itineraries = itinerariesData;
    } else if (Array.isArray((itinerariesData as any).results)) {
      itineraries = (itinerariesData as any).results;
    }
  }

  // Filter upcoming itineraries (planned or active status, start date in future or ongoing)
  const upcomingItineraries = itineraries.filter((itinerary) => {
    const endDate = new Date(itinerary.end_date);
    const now = new Date();
    return (
      (itinerary.status === 'planned' || itinerary.status === 'active') &&
      endDate >= now
    );
  });

  const totalSpent = bookings.reduce((sum: number, b: any) => sum + parseFloat(b.total_amount || 0), 0);
  const firstName = user?.first_name || 'Traveler';

  const stats = [
    {
      label: 'Total Bookings',
      value: bookings.length,
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 6v.75m0 3v.75m0 3v.75m0 3V18m-9-5.25h5.25M7.5 15h3M3.375 5.25c-.621 0-1.125.504-1.125 1.125v3.026a2.999 2.999 0 010 5.198v3.026c0 .621.504 1.125 1.125 1.125h17.25c.621 0 1.125-.504 1.125-1.125v-3.026a2.999 2.999 0 010-5.198V6.375c0-.621-.504-1.125-1.125-1.125H3.375z" />
        </svg>
      ),
      gradient: 'from-blue-500 to-cyan-500',
      bgLight: 'from-blue-50 to-cyan-50 dark:from-blue-950/30 dark:to-cyan-950/30',
    },
    {
      label: 'Upcoming Trips',
      value: upcomingItineraries.length,
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M6.115 5.19l.319 1.913A6 6 0 008.11 10.36L9.75 12l-.387.775c-.217.433-.132.956.21 1.298l1.348 1.348c.21.21.329.497.329.795v1.089c0 .426.24.815.622 1.006l.153.076c.433.217.956.132 1.298-.21l.723-.723a8.7 8.7 0 002.288-4.042 1.087 1.087 0 00-.358-1.099l-1.33-1.108c-.251-.21-.582-.299-.905-.245l-1.17.195a1.125 1.125 0 01-.98-.314l-.295-.295a1.125 1.125 0 010-1.591l.13-.132a1.125 1.125 0 011.3-.21l.603.302a.809.809 0 001.086-1.086L14.25 7.5l1.256-.837a4.5 4.5 0 001.528-1.732l.146-.292M6.115 5.19A9 9 0 1017.18 4.64M6.115 5.19A8.965 8.965 0 0112 3c1.929 0 3.716.607 5.18 1.64" />
        </svg>
      ),
      gradient: 'from-emerald-500 to-teal-500',
      bgLight: 'from-emerald-50 to-teal-50 dark:from-emerald-950/30 dark:to-teal-950/30',
    },
    {
      label: 'Total Spent',
      value: formatCurrency(totalSpent),
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" />
        </svg>
      ),
      gradient: 'from-violet-500 to-purple-500',
      bgLight: 'from-violet-50 to-purple-50 dark:from-violet-950/30 dark:to-purple-950/30',
    },
  ];

  const quickActions = [
    { label: 'Plan a Trip', route: ROUTES.AI_PLANNER, icon: '✈️', gradient: 'from-blue-600 to-indigo-600' },
    { label: 'Search Flights', route: ROUTES.SEARCH, icon: '🔍', gradient: 'from-emerald-600 to-teal-600' },
    { label: 'My Trips', route: ROUTES.ITINERARY, icon: '🗺️', gradient: 'from-orange-600 to-amber-600' },
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Header */}
      <div className="relative overflow-hidden bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-700 dark:from-blue-800 dark:via-indigo-800 dark:to-purple-900">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 -right-40 w-80 h-80 bg-white rounded-full blur-3xl"></div>
          <div className="absolute -bottom-20 -left-20 w-60 h-60 bg-purple-300 rounded-full blur-3xl"></div>
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
          <h1 className="text-2xl md:text-3xl font-bold text-white mb-2">
            Welcome back, {firstName}
          </h1>
          <p className="text-blue-100 text-lg">
            Your travel command center. Plan, book, and explore.
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8 relative z-10 pb-12">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
          {stats.map((stat) => (
            <Card key={stat.label} variant="glass" padding="none" className="overflow-hidden">
              <div className={`bg-gradient-to-br ${stat.bgLight} p-6`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                      {stat.label}
                    </p>
                    <p className="text-3xl font-extrabold text-gray-900 dark:text-white">
                      {stat.value}
                    </p>
                  </div>
                  <div className={`p-3 rounded-xl bg-gradient-to-br ${stat.gradient} text-white shadow-lg`}>
                    {stat.icon}
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          {quickActions.map((action) => (
            <button
              key={action.label}
              onClick={() => navigate(action.route)}
              className={`group relative overflow-hidden rounded-2xl bg-gradient-to-br ${action.gradient} p-5 text-white shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-0.5`}
            >
              <div className="absolute top-0 right-0 w-20 h-20 bg-white/10 rounded-full -translate-y-6 translate-x-6 group-hover:scale-150 transition-transform duration-500"></div>
              <div className="relative flex items-center gap-3">
                <span className="text-2xl">{action.icon}</span>
                <span className="text-lg font-semibold">{action.label}</span>
                <svg className="w-5 h-5 ml-auto opacity-70 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                </svg>
              </div>
            </button>
          ))}
        </div>

        {/* Upcoming Itineraries */}
        {upcomingItineraries.length > 0 && (
          <Card className="mb-8" variant="glass">
            <div className="flex items-center gap-3 mb-5 px-6 pt-6">
              <div className="p-2 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-500 text-white">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">Upcoming Trips</h2>
            </div>
            <CardContent className="px-6 pb-6">
              <div className="space-y-3">
                {upcomingItineraries.map((itinerary) => (
                  <div
                    key={itinerary.id}
                    onClick={() => navigate(`/itineraries/${itinerary.id}`)}
                    className="group flex justify-between items-center p-4 rounded-xl bg-gray-50/80 dark:bg-gray-700/30 hover:bg-gradient-to-r hover:from-emerald-50 hover:to-teal-50 dark:hover:from-emerald-900/10 dark:hover:to-teal-900/10 border border-transparent hover:border-emerald-200/60 dark:hover:border-emerald-800/40 transition-all duration-200 cursor-pointer"
                  >
                    <div className="flex items-center gap-4">
                      <div className="hidden sm:flex w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-100 to-teal-100 dark:from-emerald-900/30 dark:to-teal-900/30 items-center justify-center text-xl">
                        🌍
                      </div>
                      <div>
                        <p className="font-semibold text-gray-900 dark:text-white group-hover:text-emerald-700 dark:group-hover:text-emerald-300 transition-colors">
                          {itinerary.title}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {itinerary.destination} &middot; {formatDate(itinerary.start_date, 'MMM dd')} - {formatDate(itinerary.end_date, 'MMM dd, yyyy')}
                        </p>
                      </div>
                    </div>
                    <div className="text-right flex items-center gap-3">
                      <div>
                        {itinerary.estimated_budget && (
                          <p className="font-semibold text-gray-900 dark:text-white">
                            {formatCurrency(itinerary.estimated_budget, itinerary.currency)}
                          </p>
                        )}
                        <span
                          className={`inline-block text-xs px-2.5 py-1 rounded-full font-medium ${
                            itinerary.status === 'active'
                              ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
                              : itinerary.status === 'planned'
                              ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                              : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'
                          }`}
                        >
                          {itinerary.status}
                        </span>
                      </div>
                      <svg className="w-5 h-5 text-gray-300 group-hover:text-emerald-500 group-hover:translate-x-0.5 transition-all" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                      </svg>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Recent Bookings */}
        <Card variant="glass">
          <div className="flex items-center justify-between px-6 pt-6 mb-5">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-gradient-to-br from-violet-500 to-purple-500 text-white">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">Recent Bookings</h2>
            </div>
            {bookings.length > 0 && (
              <Button variant="ghost" size="sm" onClick={() => navigate(ROUTES.BOOKING)}>
                View all
              </Button>
            )}
          </div>
          <CardContent className="px-6 pb-6">
            {bookings.length > 0 ? (
              <div className="space-y-3">
                {bookings.slice(0, 5).map((booking: any) => (
                  <div
                    key={booking.id}
                    className="group flex justify-between items-center p-4 rounded-xl bg-gray-50/80 dark:bg-gray-700/30 hover:bg-gradient-to-r hover:from-violet-50 hover:to-purple-50 dark:hover:from-violet-900/10 dark:hover:to-purple-900/10 border border-transparent hover:border-violet-200/60 dark:hover:border-violet-800/40 transition-all duration-200"
                  >
                    <div className="flex items-center gap-4">
                      <div className="hidden sm:flex w-12 h-12 rounded-xl bg-gradient-to-br from-violet-100 to-purple-100 dark:from-violet-900/30 dark:to-purple-900/30 items-center justify-center text-xl">
                        {booking.booking_type === 'flight' ? '✈️' : booking.booking_type === 'hotel' ? '🏨' : '📋'}
                      </div>
                      <div>
                        <p className="font-semibold text-gray-900 dark:text-white">
                          {booking.notes || `Booking #${booking.booking_number}`}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {formatDate(booking.booking_date)} &middot; {booking.booking_number}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-gray-900 dark:text-white">
                        {formatCurrency(parseFloat(booking.total_amount || 0), booking.currency)}
                      </p>
                      <span
                        className={`inline-block text-xs px-2.5 py-1 rounded-full font-medium ${
                          booking.status === 'confirmed'
                            ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
                            : booking.status === 'pending'
                            ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                            : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'
                        }`}
                      >
                        {booking.status_display || booking.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-100 to-indigo-100 dark:from-blue-900/30 dark:to-indigo-900/30 mb-4">
                  <span className="text-3xl">✈️</span>
                </div>
                <p className="text-gray-500 dark:text-gray-400 mb-4">
                  No bookings yet. Start planning your next adventure!
                </p>
                <Button onClick={() => navigate(ROUTES.AI_PLANNER)}>
                  Plan a Trip
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default DashboardPage;
