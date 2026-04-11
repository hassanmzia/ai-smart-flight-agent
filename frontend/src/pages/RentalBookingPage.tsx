import { useState, useEffect, useMemo } from 'react';
import { useSearchParams, useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useRequireAuth } from '@/hooks/useAuth';
import { Card, Button } from '@/components/common';
import { formatCurrency, formatDate } from '@/utils/formatters';
import api from '@/services/api';
import type { Hotel } from '@/types';

interface GuestDetails {
  name: string;
  email: string;
  phone: string;
}

const RentalBookingPage = () => {
  const { user } = useRequireAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const location = useLocation();

  const rentalId = searchParams.get('rentalId') || (location.state as any)?.rentalId || '';
  const checkIn = searchParams.get('checkIn') || (location.state as any)?.checkIn || '';
  const checkOut = searchParams.get('checkOut') || (location.state as any)?.checkOut || '';
  const guests = parseInt(
    searchParams.get('guests') || (location.state as any)?.guests || '1',
    10
  );

  const [rental, setRental] = useState<Hotel | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const [guestDetails, setGuestDetails] = useState<GuestDetails>({
    name: user?.name || '',
    email: user?.email || '',
    phone: '',
  });

  const [specialRequests, setSpecialRequests] = useState('');
  const [agreeHouseRules, setAgreeHouseRules] = useState(false);

  useEffect(() => {
    const loadRental = async () => {
      setLoading(true);
      try {
        // Try location state first
        const stateRental = (location.state as any)?.rental;
        if (stateRental) {
          setRental(stateRental);
          setLoading(false);
          return;
        }
        // Try sessionStorage
        const saved = sessionStorage.getItem('selectedRental');
        if (saved) {
          setRental(JSON.parse(saved));
          setLoading(false);
          return;
        }
        // Fetch from API
        if (rentalId) {
          const response = await api.get(`/api/hotels/${rentalId}`);
          setRental(response.data?.data || response.data);
        }
      } catch {
        setError('Failed to load rental details.');
      } finally {
        setLoading(false);
      }
    };
    loadRental();
  }, [rentalId, location.state]);

  const nights = useMemo(() => {
    if (!checkIn || !checkOut) return 0;
    const start = new Date(checkIn);
    const end = new Date(checkOut);
    const diff = Math.abs(end.getTime() - start.getTime());
    return Math.ceil(diff / (1000 * 60 * 60 * 24));
  }, [checkIn, checkOut]);

  const pricing = useMemo(() => {
    if (!rental || nights === 0) {
      return { nightlyTotal: 0, cleaningFee: 0, serviceFee: 0, total: 0, perPerson: 0 };
    }
    const nightlyTotal = rental.pricePerNight * nights;
    const cleaningFee = rental.cleaning_fee || 0;
    const serviceFeePercent = rental.service_fee_percent || 0;
    const serviceFee = (nightlyTotal * serviceFeePercent) / 100;
    const total = nightlyTotal + cleaningFee + serviceFee;
    const perPerson = guests > 0 ? total / guests : total;
    return { nightlyTotal, cleaningFee, serviceFee, total, perPerson };
  }, [rental, nights, guests]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!guestDetails.name || !guestDetails.email || !guestDetails.phone) {
      setError('Please fill in all guest details.');
      return;
    }
    if (!agreeHouseRules) {
      setError('You must agree to the house rules before booking.');
      return;
    }

    setSubmitting(true);
    try {
      await api.post('/api/bookings/bookings', {
        item_type: 'rental',
        item_id: rentalId,
        check_in: checkIn,
        check_out: checkOut,
        guests,
        guest_name: guestDetails.name,
        guest_email: guestDetails.email,
        guest_phone: guestDetails.phone,
        special_requests: specialRequests,
        total_amount: pricing.total,
        currency: rental?.currency || 'USD',
      });
      setSuccess(true);
    } catch {
      setError('Booking failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
        </div>
      </div>
    );
  }

  if (!rental) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <Card className="p-8 text-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Rental Not Found
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            The vacation rental you are trying to book could not be found.
          </p>
          <Button onClick={() => navigate('/rentals/search')}>Search Rentals</Button>
        </Card>
      </div>
    );
  }

  if (success) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4 }}
        >
          <Card className="p-8 text-center">
            <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100 dark:bg-green-900/30 mb-4">
              <svg
                className="h-8 w-8 text-green-600 dark:text-green-400"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={2}
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
            </div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
              Booking Confirmed!
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-400 mb-2">
              Your vacation rental has been successfully booked.
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-500 mb-8">
              Confirmation email sent to {guestDetails.email}
            </p>
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 mb-8">
              <div className="grid grid-cols-2 gap-4 text-left">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Property</p>
                  <p className="text-lg font-bold text-gray-900 dark:text-white">{rental.name}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Location</p>
                  <p className="text-lg font-bold text-gray-900 dark:text-white">
                    {rental.city}, {rental.country}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Check-in</p>
                  <p className="text-lg font-bold text-gray-900 dark:text-white">
                    {formatDate(checkIn, 'MMM dd, yyyy')}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Check-out</p>
                  <p className="text-lg font-bold text-gray-900 dark:text-white">
                    {formatDate(checkOut, 'MMM dd, yyyy')}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Total</p>
                  <p className="text-lg font-bold text-gray-900 dark:text-white">
                    {formatCurrency(pricing.total, rental.currency)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Guests</p>
                  <p className="text-lg font-bold text-gray-900 dark:text-white">{guests}</p>
                </div>
              </div>
            </div>
            <div className="flex gap-4 justify-center">
              <Button onClick={() => navigate('/dashboard')}>View My Bookings</Button>
              <Button variant="outline" onClick={() => navigate('/')}>
                Back to Home
              </Button>
            </div>
          </Card>
        </motion.div>
      </div>
    );
  }

  const currency = rental.currency || 'USD';

  return (
    <div className="min-h-screen">
      {/* Header */}
      <div className="relative overflow-hidden bg-gradient-to-br from-purple-500 via-indigo-600 to-purple-700 dark:from-purple-800 dark:via-indigo-800 dark:to-purple-900">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute -top-10 -right-20 w-64 h-64 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 left-1/4 w-40 h-40 bg-indigo-300 rounded-full blur-3xl"></div>
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
          <motion.h1
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="text-2xl md:text-3xl font-bold text-white mb-2"
          >
            Book Your Vacation Rental
          </motion.h1>
          <p className="text-purple-100 text-lg">
            Review property details and confirm your stay
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6 relative z-10 pb-12">
        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Column - Form */}
            <motion.div
              className="lg:col-span-2 space-y-6"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.1 }}
            >
              {/* Property Summary */}
              <Card>
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Property Summary
                  </h3>
                  <div className="flex flex-col sm:flex-row gap-4">
                    {(rental.primary_image || (rental.images && rental.images[0])) && (
                      <img
                        src={rental.primary_image || rental.images[0]}
                        alt={rental.name}
                        className="w-full sm:w-48 h-32 object-cover rounded-lg"
                      />
                    )}
                    <div className="flex-1">
                      <h4 className="text-xl font-bold text-gray-900 dark:text-white mb-1">
                        {rental.name}
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                        {rental.city}, {rental.country}
                      </p>
                      <div className="flex flex-wrap gap-3 text-sm text-gray-600 dark:text-gray-400">
                        {rental.bedrooms !== undefined && (
                          <span>{rental.bedrooms} bedroom{rental.bedrooms !== 1 ? 's' : ''}</span>
                        )}
                        {rental.max_guests !== undefined && (
                          <span>Up to {rental.max_guests} guests</span>
                        )}
                        {rental.bathrooms !== undefined && (
                          <span>{rental.bathrooms} bathroom{rental.bathrooms !== 1 ? 's' : ''}</span>
                        )}
                      </div>
                      {rental.host_name && (
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                          Hosted by {rental.host_name}
                          {rental.is_superhost && (
                            <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300">
                              Superhost
                            </span>
                          )}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </Card>

              {/* Guest Details */}
              <Card>
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Guest Details
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Full Name *
                      </label>
                      <input
                        type="text"
                        value={guestDetails.name}
                        onChange={(e) =>
                          setGuestDetails({ ...guestDetails, name: e.target.value })
                        }
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Email *
                      </label>
                      <input
                        type="email"
                        value={guestDetails.email}
                        onChange={(e) =>
                          setGuestDetails({ ...guestDetails, email: e.target.value })
                        }
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Phone *
                      </label>
                      <input
                        type="tel"
                        value={guestDetails.phone}
                        onChange={(e) =>
                          setGuestDetails({ ...guestDetails, phone: e.target.value })
                        }
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                        required
                      />
                    </div>
                  </div>
                </div>
              </Card>

              {/* Special Requests */}
              <Card>
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Special Requests
                  </h3>
                  <textarea
                    value={specialRequests}
                    onChange={(e) => setSpecialRequests(e.target.value)}
                    rows={4}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    placeholder="Early check-in, extra towels, grocery delivery, etc."
                  />
                </div>
              </Card>

              {/* House Rules & Cancellation */}
              <Card>
                <div className="p-6 space-y-4">
                  {/* Cancellation Policy */}
                  {rental.cancellation_policy && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                        Cancellation Policy
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {rental.cancellation_policy}
                      </p>
                    </div>
                  )}

                  {/* House Rules */}
                  {rental.house_rules && rental.house_rules.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                        House Rules
                      </h3>
                      <ul className="list-disc list-inside text-sm text-gray-600 dark:text-gray-400 space-y-1">
                        {rental.house_rules.map((rule, idx) => (
                          <li key={idx}>{rule}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Agreement Checkbox */}
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={agreeHouseRules}
                      onChange={(e) => setAgreeHouseRules(e.target.checked)}
                      className="mt-1 h-4 w-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      I agree to the house rules and cancellation policy for this property.
                    </span>
                  </label>
                </div>
              </Card>

              {/* Error */}
              {error && (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                  <p className="text-red-800 dark:text-red-200 text-sm">{error}</p>
                </div>
              )}

              {/* Submit Button */}
              <Button
                type="submit"
                disabled={submitting}
                className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white py-3 text-lg font-semibold"
              >
                {submitting ? 'Processing...' : 'Confirm Booking'}
              </Button>
            </motion.div>

            {/* Right Column - Price Breakdown */}
            <motion.div
              className="lg:col-span-1"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.2 }}
            >
              <Card className="lg:sticky lg:top-20">
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Price Breakdown
                  </h3>

                  {/* Stay Dates */}
                  {checkIn && checkOut && (
                    <div className="mb-4 text-sm text-gray-600 dark:text-gray-400 space-y-1">
                      <p>
                        <span className="font-medium">Check-in:</span>{' '}
                        {formatDate(checkIn, 'MMM dd, yyyy')}
                      </p>
                      <p>
                        <span className="font-medium">Check-out:</span>{' '}
                        {formatDate(checkOut, 'MMM dd, yyyy')}
                      </p>
                      <p>
                        <span className="font-medium">Guests:</span> {guests}
                      </p>
                    </div>
                  )}

                  {nights > 0 && (
                    <div className="border-t border-gray-200 dark:border-gray-700 pt-4 space-y-3 text-sm">
                      {/* Nightly rate */}
                      <div className="flex justify-between text-gray-600 dark:text-gray-400">
                        <span>
                          {formatCurrency(rental.pricePerNight, currency)} x {nights} night
                          {nights !== 1 ? 's' : ''}
                        </span>
                        <span>{formatCurrency(pricing.nightlyTotal, currency)}</span>
                      </div>

                      {/* Cleaning fee */}
                      {pricing.cleaningFee > 0 && (
                        <div className="flex justify-between text-gray-600 dark:text-gray-400">
                          <span>Cleaning fee</span>
                          <span>{formatCurrency(pricing.cleaningFee, currency)}</span>
                        </div>
                      )}

                      {/* Service fee */}
                      {pricing.serviceFee > 0 && (
                        <div className="flex justify-between text-gray-600 dark:text-gray-400">
                          <span>Service fee</span>
                          <span>{formatCurrency(pricing.serviceFee, currency)}</span>
                        </div>
                      )}

                      {/* Total */}
                      <div className="flex justify-between font-bold text-gray-900 dark:text-white text-lg pt-3 border-t border-gray-200 dark:border-gray-700">
                        <span>Total</span>
                        <span>{formatCurrency(pricing.total, currency)}</span>
                      </div>

                      {/* Per person */}
                      {guests > 1 && (
                        <div className="flex justify-between text-gray-500 dark:text-gray-400 text-xs">
                          <span>Per person</span>
                          <span>{formatCurrency(pricing.perPerson, currency)}</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Minimum stay notice */}
                  {rental.minimum_stay_nights && nights < rental.minimum_stay_nights && (
                    <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                      <p className="text-yellow-800 dark:text-yellow-200 text-xs">
                        Minimum stay: {rental.minimum_stay_nights} nights
                      </p>
                    </div>
                  )}
                </div>
              </Card>
            </motion.div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RentalBookingPage;
