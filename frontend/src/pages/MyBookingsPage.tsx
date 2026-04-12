import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useRequireAuth } from '@/hooks/useAuth';
import { getBookings } from '@/services/bookingService';
import { Card, CardContent } from '@/components/common';
import Button from '@/components/common/Button';
import Loading from '@/components/common/Loading';
import { QUERY_KEYS, ROUTES } from '@/utils/constants';
import { formatCurrency, formatDate } from '@/utils/formatters';

type StatusFilter = 'all' | 'pending' | 'confirmed' | 'completed' | 'cancelled';

const STATUS_TABS: { id: StatusFilter; label: string; icon: string }[] = [
  { id: 'all', label: 'All', icon: '🧾' },
  { id: 'pending', label: 'Pending', icon: '⏳' },
  { id: 'confirmed', label: 'Confirmed', icon: '✅' },
  { id: 'completed', label: 'Completed', icon: '🏁' },
  { id: 'cancelled', label: 'Cancelled', icon: '🚫' },
];

const PAGE_SIZE = 10;

const statusPillCls = (status: string) => {
  switch (status) {
    case 'confirmed':
      return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300';
    case 'pending':
      return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300';
    case 'completed':
      return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300';
    case 'cancelled':
      return 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400';
    case 'refunded':
      return 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300';
    default:
      return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400';
  }
};

const MyBookingsPage = () => {
  useRequireAuth();
  const navigate = useNavigate();

  const [filter, setFilter] = useState<StatusFilter>('all');
  const [page, setPage] = useState(1);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: [...QUERY_KEYS.BOOKINGS, filter, page],
    queryFn: () => getBookings(page, PAGE_SIZE, filter === 'all' ? undefined : filter),
  });

  // Accept any of the list-endpoint shapes the backend may return.
  const bookings: any[] = (() => {
    const d: any = data;
    if (!d) return [];
    if (Array.isArray(d)) return d;
    if (Array.isArray(d.items)) return d.items;
    if (Array.isArray(d.results)) return d.results;
    return [];
  })();

  const total: number =
    (data as any)?.total ??
    (data as any)?.count ??
    bookings.length;
  const totalPages: number =
    (data as any)?.totalPages ??
    Math.max(1, Math.ceil(total / PAGE_SIZE));

  const onFilterChange = (next: StatusFilter) => {
    setFilter(next);
    setPage(1);
  };

  return (
    <div className="min-h-screen">
      {/* Hero header */}
      <div className="relative overflow-hidden bg-gradient-to-br from-violet-600 via-purple-600 to-indigo-600 dark:from-violet-800 dark:via-purple-800 dark:to-indigo-800">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute -top-20 -right-20 w-72 h-72 bg-white rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-1/3 w-48 h-48 bg-pink-300 rounded-full blur-3xl" />
        </div>
        <div className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h1 className="text-2xl md:text-3xl font-extrabold text-white mb-1">
                My Bookings
              </h1>
              <p className="text-purple-100">
                Every flight, hotel, rental, and tour you have reserved through us.
              </p>
            </div>
            <Button
              variant="secondary"
              onClick={() => navigate(ROUTES.AI_PLANNER)}
              className="!bg-white/90 !text-purple-700 hover:!bg-white"
            >
              + New Trip
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6 relative z-10 pb-12">
        {/* Status tabs */}
        <div className="flex gap-1.5 sm:gap-2 mb-6 overflow-x-auto pb-1 -mx-1 px-1 scrollbar-hide">
          {STATUS_TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => onFilterChange(t.id)}
              className={`flex items-center gap-1 sm:gap-2 px-3 sm:px-5 py-2.5 rounded-xl font-medium text-xs sm:text-sm transition-all duration-200 whitespace-nowrap flex-shrink-0 ${
                filter === t.id
                  ? 'bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-lg shadow-violet-500/25'
                  : 'bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm text-gray-700 dark:text-gray-300 hover:bg-white dark:hover:bg-gray-700 shadow-sm border border-gray-200/60 dark:border-gray-700/50'
              }`}
            >
              <span>{t.icon}</span>
              {t.label}
            </button>
          ))}
        </div>

        <Card>
          <CardContent className="p-0">
            {isLoading ? (
              <div className="py-16 flex justify-center">
                <Loading />
              </div>
            ) : isError ? (
              <div className="text-center py-16 px-6">
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  We couldn’t load your bookings. Please try again.
                </p>
                <Button onClick={() => refetch()}>Retry</Button>
              </div>
            ) : bookings.length === 0 ? (
              <div className="text-center py-16 px-6">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-100 to-indigo-100 dark:from-violet-900/30 dark:to-indigo-900/30 mb-4">
                  <span className="text-3xl">✈️</span>
                </div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
                  {filter === 'all'
                    ? 'No bookings yet'
                    : `No ${filter} bookings`}
                </h3>
                <p className="text-gray-500 dark:text-gray-400 mb-6">
                  {filter === 'all'
                    ? 'Start planning your next adventure and your bookings will show up here.'
                    : 'Try a different filter or plan your next trip.'}
                </p>
                <Button onClick={() => navigate(ROUTES.AI_PLANNER)}>
                  Plan a Trip
                </Button>
              </div>
            ) : (
              <ul className="divide-y divide-gray-100 dark:divide-gray-700/60">
                {bookings.map((b: any) => {
                  const amount = parseFloat(b.total_amount || b.totalAmount || 0);
                  const currency = b.currency || 'USD';
                  const date = b.booking_date || b.bookingDate || b.created_at;
                  const title =
                    b.notes ||
                    b.primary_traveler_name ||
                    `Booking #${b.booking_number}`;
                  const itemCount = b.item_count ?? b.itemCount;
                  return (
                    <li
                      key={b.id || b.booking_number}
                      className="flex items-center justify-between gap-4 px-5 sm:px-6 py-4 hover:bg-gray-50/80 dark:hover:bg-gray-700/30 transition-colors"
                    >
                      <div className="flex items-center gap-4 min-w-0">
                        <div className="hidden sm:flex w-12 h-12 rounded-xl bg-gradient-to-br from-violet-100 to-purple-100 dark:from-violet-900/30 dark:to-purple-900/30 items-center justify-center text-xl">
                          🧾
                        </div>
                        <div className="min-w-0">
                          <p className="font-semibold text-gray-900 dark:text-white truncate">
                            {title}
                          </p>
                          <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
                            {date ? formatDate(date) : '—'}
                            {b.booking_number && (
                              <>
                                {' '}·{' '}
                                <span className="font-mono text-xs">
                                  {b.booking_number}
                                </span>
                              </>
                            )}
                            {typeof itemCount === 'number' && itemCount > 0 && (
                              <> · {itemCount} item{itemCount === 1 ? '' : 's'}</>
                            )}
                          </p>
                        </div>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <p className="font-semibold text-gray-900 dark:text-white">
                          {formatCurrency(amount, currency)}
                        </p>
                        <span
                          className={`inline-block mt-1 text-xs px-2.5 py-1 rounded-full font-medium ${statusPillCls(
                            b.status,
                          )}`}
                        >
                          {b.status_display || b.status}
                        </span>
                        {b.id && (
                          <div className="mt-2">
                            <Link
                              to={`/booking/${b.id}`}
                              className="text-xs font-medium text-violet-600 dark:text-violet-300 hover:underline"
                            >
                              View details →
                            </Link>
                          </div>
                        )}
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </CardContent>
        </Card>

        {/* Pagination */}
        {!isLoading && !isError && bookings.length > 0 && totalPages > 1 && (
          <div className="flex items-center justify-between mt-6">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Page {page} of {totalPages} · {total} booking{total === 1 ? '' : 's'}
            </p>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
              >
                Previous
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MyBookingsPage;
