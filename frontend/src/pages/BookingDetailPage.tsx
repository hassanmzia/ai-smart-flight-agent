import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { useRequireAuth } from '@/hooks/useAuth';
import {
  getBookingDetails,
  cancelBooking,
} from '@/services/bookingService';
import { Card, CardContent } from '@/components/common';
import Button from '@/components/common/Button';
import Loading from '@/components/common/Loading';
import Modal from '@/components/common/Modal';
import { QUERY_KEYS, ROUTES } from '@/utils/constants';
import { formatCurrency, formatDate } from '@/utils/formatters';

const ITEM_ICON: Record<string, string> = {
  flight: '✈️',
  hotel: '🏨',
  car: '🚗',
  rental: '🚗',
  tour: '🗺️',
  attraction: '🎟️',
  restaurant: '🍽️',
  activity: '🎯',
  package: '📦',
};

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

const BookingDetailPage = () => {
  useRequireAuth();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [showCancelModal, setShowCancelModal] = useState(false);
  const [cancelReason, setCancelReason] = useState('');

  const {
    data: booking,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: id ? QUERY_KEYS.BOOKING(id) : ['booking', 'unknown'],
    queryFn: () => getBookingDetails(id!),
    enabled: !!id,
  });

  const cancelMutation = useMutation({
    mutationFn: () => cancelBooking(id!, cancelReason || undefined),
    onSuccess: () => {
      toast.success('Booking cancelled');
      setShowCancelModal(false);
      setCancelReason('');
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.BOOKINGS });
      refetch();
    },
    onError: (err: any) => {
      toast.error(err?.message || 'Could not cancel booking');
    },
  });

  if (!id) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 text-center">
        <p className="text-gray-600 dark:text-gray-400">Missing booking ID.</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12">
        <Loading size="lg" text="Loading booking details..." />
      </div>
    );
  }

  if (isError || !booking) {
    const status = (error as any)?.status;
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-rose-100 dark:bg-rose-900/30 mb-4 text-3xl">
          🔍
        </div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          {status === 404 ? 'Booking not found' : 'Could not load this booking'}
        </h1>
        <p className="text-gray-500 dark:text-gray-400 mb-6">
          {status === 404
            ? "We couldn't find a booking with that ID under your account."
            : (error as any)?.message || 'Please try again in a moment.'}
        </p>
        <div className="flex justify-center gap-3">
          <Button variant="secondary" onClick={() => navigate(ROUTES.MY_BOOKINGS)}>
            Back to My Bookings
          </Button>
          <Button onClick={() => refetch()}>Retry</Button>
        </div>
      </div>
    );
  }

  const b: any = booking;
  const items: any[] = Array.isArray(b.items) ? b.items : [];
  const history: any[] = Array.isArray(b.status_history) ? b.status_history : [];
  const currency = b.currency || 'USD';
  const subtotal = parseFloat(b.total_amount || 0);
  const tax = parseFloat(b.tax_amount || 0);
  const discount = parseFloat(b.discount_amount || 0);
  const finalAmount =
    b.final_amount != null ? parseFloat(b.final_amount) : subtotal + tax - discount;

  const canCancel = !['cancelled', 'completed', 'refunded'].includes(b.status);

  return (
    <div className="min-h-screen">
      {/* Hero */}
      <div className="relative overflow-hidden bg-gradient-to-br from-violet-600 via-purple-600 to-indigo-600 dark:from-violet-800 dark:via-purple-800 dark:to-indigo-800">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute -top-20 -right-20 w-72 h-72 bg-white rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-1/3 w-48 h-48 bg-pink-300 rounded-full blur-3xl" />
        </div>
        <div className="relative max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
          <Link
            to={ROUTES.MY_BOOKINGS}
            className="inline-flex items-center gap-1 text-purple-100 hover:text-white text-sm mb-3"
          >
            <span>←</span> Back to My Bookings
          </Link>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl md:text-3xl font-extrabold text-white mb-1">
                {b.notes || b.primary_traveler_name || 'Booking details'}
              </h1>
              <p className="text-purple-100 font-mono text-sm">
                #{b.booking_number}
              </p>
            </div>
            <span
              className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold ${statusPillCls(
                b.status,
              )}`}
            >
              {b.status_display || b.status}
            </span>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6 relative z-10 pb-12 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column — items + history */}
        <div className="lg:col-span-2 space-y-6">
          {/* Items */}
          <Card variant="glass">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-gradient-to-br from-violet-500 to-purple-500 text-white">
                📋
              </div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                What's included
              </h2>
            </div>
            {items.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                No items recorded for this booking.
              </p>
            ) : (
              <ul className="space-y-3">
                {items.map((it) => {
                  const icon = ITEM_ICON[it.item_type] || '🧳';
                  return (
                    <li
                      key={it.id}
                      className="p-4 rounded-xl bg-gray-50/80 dark:bg-gray-700/30 border border-gray-100 dark:border-gray-700/40"
                    >
                      <div className="flex items-start gap-3">
                        <div className="w-11 h-11 rounded-lg bg-white dark:bg-gray-800 flex items-center justify-center text-xl shadow-sm shrink-0">
                          {icon}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <p className="font-semibold text-gray-900 dark:text-white truncate">
                                {it.item_name}
                              </p>
                              <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                                {it.item_type_display || it.item_type}
                              </p>
                            </div>
                            <p className="font-semibold text-gray-900 dark:text-white whitespace-nowrap">
                              {formatCurrency(parseFloat(it.total_price || 0), currency)}
                            </p>
                          </div>
                          {it.item_description && (
                            <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                              {it.item_description}
                            </p>
                          )}
                          <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500 dark:text-gray-400">
                            {it.start_date && (
                              <span>
                                <strong>From:</strong>{' '}
                                {formatDate(it.start_date)}
                              </span>
                            )}
                            {it.end_date && (
                              <span>
                                <strong>To:</strong> {formatDate(it.end_date)}
                              </span>
                            )}
                            {it.quantity != null && (
                              <span>
                                <strong>Qty:</strong> {it.quantity}
                              </span>
                            )}
                            {it.unit_price != null && (
                              <span>
                                <strong>Unit:</strong>{' '}
                                {formatCurrency(parseFloat(it.unit_price), currency)}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </Card>

          {/* Status history */}
          {history.length > 0 && (
            <Card variant="glass">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-500 text-white">
                  🕒
                </div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                  Status history
                </h2>
              </div>
              <ol className="relative border-l border-gray-200 dark:border-gray-700 pl-5 space-y-4">
                {history.map((h) => (
                  <li key={h.id} className="relative">
                    <span className="absolute -left-[27px] top-1.5 w-3 h-3 rounded-full bg-indigo-500 ring-4 ring-white dark:ring-gray-800" />
                    <p className="text-sm font-semibold text-gray-900 dark:text-white">
                      {h.old_status ? `${h.old_status} → ${h.new_status}` : h.new_status}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {h.timestamp && formatDate(h.timestamp, 'MMM dd, yyyy HH:mm')}
                      {h.changed_by_email && ` · by ${h.changed_by_email}`}
                    </p>
                    {(h.reason || h.notes) && (
                      <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                        {h.reason || h.notes}
                      </p>
                    )}
                  </li>
                ))}
              </ol>
            </Card>
          )}

          {/* Special requests / notes */}
          {(b.special_requests || b.notes) && (
            <Card variant="glass">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 rounded-lg bg-gradient-to-br from-amber-500 to-orange-500 text-white">
                  📝
                </div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">Notes</h2>
              </div>
              {b.special_requests && (
                <CardContent className="p-0">
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
                    Special requests
                  </p>
                  <p className="text-gray-900 dark:text-white whitespace-pre-line mb-3">
                    {b.special_requests}
                  </p>
                </CardContent>
              )}
              {b.notes && (
                <CardContent className="p-0">
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Notes</p>
                  <p className="text-gray-900 dark:text-white whitespace-pre-line">
                    {b.notes}
                  </p>
                </CardContent>
              )}
            </Card>
          )}
        </div>

        {/* Right column — totals + traveler */}
        <div className="space-y-6">
          {/* Summary */}
          <Card variant="glass">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-500 text-white">
                💳
              </div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">Summary</h2>
            </div>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500 dark:text-gray-400">Subtotal</dt>
                <dd className="text-gray-900 dark:text-white">
                  {formatCurrency(subtotal, currency)}
                </dd>
              </div>
              {tax > 0 && (
                <div className="flex justify-between">
                  <dt className="text-gray-500 dark:text-gray-400">Tax</dt>
                  <dd className="text-gray-900 dark:text-white">
                    {formatCurrency(tax, currency)}
                  </dd>
                </div>
              )}
              {discount > 0 && (
                <div className="flex justify-between">
                  <dt className="text-gray-500 dark:text-gray-400">Discount</dt>
                  <dd className="text-emerald-600 dark:text-emerald-400">
                    -{formatCurrency(discount, currency)}
                  </dd>
                </div>
              )}
              <div className="border-t border-gray-200 dark:border-gray-700 my-2" />
              <div className="flex justify-between text-base font-semibold">
                <dt className="text-gray-900 dark:text-white">Total</dt>
                <dd className="text-gray-900 dark:text-white">
                  {formatCurrency(finalAmount, currency)}
                </dd>
              </div>
            </dl>
            {canCancel && (
              <Button
                variant="danger"
                className="w-full mt-5"
                onClick={() => setShowCancelModal(true)}
              >
                Cancel booking
              </Button>
            )}
          </Card>

          {/* Traveler */}
          <Card variant="glass">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-gradient-to-br from-sky-500 to-blue-500 text-white">
                👤
              </div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                Primary traveler
              </h2>
            </div>
            <dl className="space-y-2 text-sm">
              <div>
                <dt className="text-gray-500 dark:text-gray-400">Name</dt>
                <dd className="text-gray-900 dark:text-white">
                  {b.primary_traveler_name || '—'}
                </dd>
              </div>
              {b.primary_traveler_email && (
                <div>
                  <dt className="text-gray-500 dark:text-gray-400">Email</dt>
                  <dd className="text-gray-900 dark:text-white break-all">
                    {b.primary_traveler_email}
                  </dd>
                </div>
              )}
              {b.primary_traveler_phone && (
                <div>
                  <dt className="text-gray-500 dark:text-gray-400">Phone</dt>
                  <dd className="text-gray-900 dark:text-white">
                    {b.primary_traveler_phone}
                  </dd>
                </div>
              )}
            </dl>
          </Card>

          {/* Dates */}
          <Card variant="glass">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-gradient-to-br from-fuchsia-500 to-pink-500 text-white">
                📅
              </div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">Timeline</h2>
            </div>
            <dl className="space-y-2 text-sm">
              {b.booking_date && (
                <div className="flex justify-between">
                  <dt className="text-gray-500 dark:text-gray-400">Booked on</dt>
                  <dd className="text-gray-900 dark:text-white">
                    {formatDate(b.booking_date)}
                  </dd>
                </div>
              )}
              {b.confirmation_date && (
                <div className="flex justify-between">
                  <dt className="text-gray-500 dark:text-gray-400">Confirmed</dt>
                  <dd className="text-gray-900 dark:text-white">
                    {formatDate(b.confirmation_date)}
                  </dd>
                </div>
              )}
              {b.cancellation_date && (
                <div className="flex justify-between">
                  <dt className="text-gray-500 dark:text-gray-400">Cancelled</dt>
                  <dd className="text-gray-900 dark:text-white">
                    {formatDate(b.cancellation_date)}
                  </dd>
                </div>
              )}
            </dl>
          </Card>
        </div>
      </div>

      {/* Cancel modal */}
      <Modal
        isOpen={showCancelModal}
        onClose={() => setShowCancelModal(false)}
        title="Cancel this booking?"
      >
        <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">
          This will mark the booking as cancelled. Refund eligibility depends on the
          provider's policy.
        </p>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Reason (optional)
        </label>
        <textarea
          value={cancelReason}
          onChange={(e) => setCancelReason(e.target.value)}
          rows={3}
          className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-2 text-sm"
          placeholder="Plans changed, found a better deal, etc."
        />
        <div className="flex justify-end gap-2 mt-4">
          <Button variant="ghost" onClick={() => setShowCancelModal(false)}>
            Keep booking
          </Button>
          <Button
            variant="danger"
            isLoading={cancelMutation.isPending}
            onClick={() => cancelMutation.mutate()}
          >
            Yes, cancel
          </Button>
        </div>
      </Modal>
    </div>
  );
};

export default BookingDetailPage;
