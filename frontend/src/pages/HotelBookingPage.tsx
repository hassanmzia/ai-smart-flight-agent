import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useRequireAuth } from '@/hooks/useAuth';
import { Card, Button } from '@/components/common';
import { formatCurrency, formatDate } from '@/utils/formatters';
import {
  UserIcon,
  CalendarIcon,
  HomeIcon,
  CreditCardIcon,
  CheckCircleIcon,
  StarIcon,
} from '@heroicons/react/24/outline';
import type { Hotel } from '@/types';

interface Guest {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
}

const HotelBookingPage = () => {
  const { hotelId } = useParams<{ hotelId: string }>();
  const { user } = useRequireAuth();
  const navigate = useNavigate();

  const [hotel, setHotel] = useState<Hotel | null>(null);
  const [loading, setLoading] = useState(true);
  const [step, setStep] = useState(1); // 1: Guest Info, 2: Payment, 3: Confirmation

  // Booking details from search/navigation
  const [bookingDetails, setBookingDetails] = useState({
    checkInDate: '',
    checkOutDate: '',
    guests: 1,
    rooms: 1,
  });

  // Form state
  const [primaryGuest, setPrimaryGuest] = useState<Guest>({
    firstName: user?.name?.split(' ')[0] || '',
    lastName: user?.name?.split(' ')[1] || '',
    email: user?.email || '',
    phone: '',
  });

  const [paymentInfo, setPaymentInfo] = useState({
    cardNumber: '',
    cardName: '',
    expiryDate: '',
    cvv: '',
    billingAddress: '',
    city: '',
    zipCode: '',
    country: '',
  });

  const [specialRequests, setSpecialRequests] = useState('');
  const [arrivalTime, setArrivalTime] = useState('');
  const [bookingError, setBookingError] = useState('');
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    // In a real app, fetch hotel details from API
    const savedHotel = sessionStorage.getItem('selectedHotel');
    const savedBookingDetails = sessionStorage.getItem('hotelBookingDetails');

    if (savedHotel) {
      setHotel(JSON.parse(savedHotel));
    }
    if (savedBookingDetails) {
      setBookingDetails(JSON.parse(savedBookingDetails));
    }
    setLoading(false);
  }, [hotelId]);

  const validateGuestInfo = () => {
    if (!primaryGuest.firstName || !primaryGuest.lastName || !primaryGuest.email || !primaryGuest.phone) {
      setBookingError('Please fill in all required guest information');
      return false;
    }
    if (!bookingDetails.checkInDate || !bookingDetails.checkOutDate) {
      setBookingError('Please select check-in and check-out dates');
      return false;
    }
    return true;
  };

  const validatePayment = () => {
    if (!paymentInfo.cardNumber || !paymentInfo.cardName || !paymentInfo.expiryDate || !paymentInfo.cvv) {
      setBookingError('Please fill in all payment information');
      return false;
    }
    return true;
  };

  const handleNextStep = () => {
    setBookingError('');
    if (step === 1 && validateGuestInfo()) {
      setStep(2);
    } else if (step === 2 && validatePayment()) {
      handleBooking();
    }
  };

  const handleBooking = async () => {
    setProcessing(true);
    setBookingError('');

    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 2000));

      // In a real app, call booking API here
      // const response = await createHotelBooking({ hotel, guest, payment, etc });

      setStep(3);
    } catch (error) {
      setBookingError('Booking failed. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

  const calculateNights = () => {
    if (!bookingDetails.checkInDate || !bookingDetails.checkOutDate) return 0;
    const checkIn = new Date(bookingDetails.checkInDate);
    const checkOut = new Date(bookingDetails.checkOutDate);
    const diffTime = Math.abs(checkOut.getTime() - checkIn.getTime());
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </div>
    );
  }

  if (!hotel) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <Card className="p-8 text-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Hotel Not Found
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            The hotel you're trying to book could not be found.
          </p>
          <Button onClick={() => navigate('/hotels')}>Search Hotels</Button>
        </Card>
      </div>
    );
  }

  // Confirmation Step
  if (step === 3) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <Card className="p-8 text-center">
          <CheckCircleIcon className="mx-auto h-16 w-16 text-green-500 mb-4" />
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
            Booking Confirmed!
          </h2>
          <p className="text-lg text-gray-600 dark:text-gray-400 mb-2">
            Your hotel reservation has been successfully booked.
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-500 mb-8">
            Confirmation email sent to {primaryGuest.email}
          </p>

          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 mb-8">
            <div className="grid grid-cols-2 gap-4 text-left">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Booking Reference</p>
                <p className="text-lg font-bold text-gray-900 dark:text-white">
                  {Math.random().toString(36).substring(2, 10).toUpperCase()}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Hotel</p>
                <p className="text-lg font-bold text-gray-900 dark:text-white">{hotel.name}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Check-in</p>
                <p className="text-lg font-bold text-gray-900 dark:text-white">
                  {formatDate(bookingDetails.checkInDate, 'MMM DD, YYYY')}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Check-out</p>
                <p className="text-lg font-bold text-gray-900 dark:text-white">
                  {formatDate(bookingDetails.checkOutDate, 'MMM DD, YYYY')}
                </p>
              </div>
            </div>
          </div>

          <div className="flex gap-4 justify-center">
            <Button onClick={() => navigate('/bookings')}>View My Bookings</Button>
            <Button variant="outline" onClick={() => navigate('/')}>
              Back to Home
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  const nights = calculateNights();
  const subtotal = hotel.pricePerNight * nights * bookingDetails.rooms;
  const taxes = subtotal * 0.12; // 12% tax
  const total = subtotal + taxes;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Progress Steps */}
      <div className="mb-8">
        <div className="flex items-center justify-center">
          {[1, 2].map((stepNum) => (
            <div key={stepNum} className="flex items-center">
              <div
                className={`flex items-center justify-center w-10 h-10 rounded-full ${
                  step >= stepNum
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-500'
                }`}
              >
                {stepNum}
              </div>
              <span
                className={`ml-2 text-sm font-medium ${
                  step >= stepNum
                    ? 'text-gray-900 dark:text-white'
                    : 'text-gray-500 dark:text-gray-400'
                }`}
              >
                {stepNum === 1 ? 'Guest Info' : 'Payment'}
              </span>
              {stepNum < 2 && (
                <div
                  className={`mx-4 h-0.5 w-16 ${
                    step > stepNum ? 'bg-primary-600' : 'bg-gray-200 dark:bg-gray-700'
                  }`}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Form */}
        <div className="lg:col-span-2">
          {/* Step 1: Guest Information */}
          {step === 1 && (
            <div className="space-y-6">
              {/* Booking Dates */}
              <Card>
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                    <CalendarIcon className="h-5 w-5 mr-2" />
                    Booking Dates
                  </h3>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Check-in Date *
                      </label>
                      <input
                        type="date"
                        value={bookingDetails.checkInDate}
                        onChange={(e) =>
                          setBookingDetails({ ...bookingDetails, checkInDate: e.target.value })
                        }
                        min={new Date().toISOString().split('T')[0]}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Check-out Date *
                      </label>
                      <input
                        type="date"
                        value={bookingDetails.checkOutDate}
                        onChange={(e) =>
                          setBookingDetails({ ...bookingDetails, checkOutDate: e.target.value })
                        }
                        min={bookingDetails.checkInDate || new Date().toISOString().split('T')[0]}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Rooms
                      </label>
                      <input
                        type="number"
                        value={bookingDetails.rooms}
                        onChange={(e) =>
                          setBookingDetails({ ...bookingDetails, rooms: parseInt(e.target.value) })
                        }
                        min={1}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Guests
                      </label>
                      <input
                        type="number"
                        value={bookingDetails.guests}
                        onChange={(e) =>
                          setBookingDetails({ ...bookingDetails, guests: parseInt(e.target.value) })
                        }
                        min={1}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                      />
                    </div>
                  </div>

                  {nights > 0 && (
                    <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                      {nights} night{nights > 1 ? 's' : ''}
                    </p>
                  )}
                </div>
              </Card>

              {/* Primary Guest */}
              <Card>
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                    <UserIcon className="h-5 w-5 mr-2" />
                    Primary Guest Information
                  </h3>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        First Name *
                      </label>
                      <input
                        type="text"
                        value={primaryGuest.firstName}
                        onChange={(e) =>
                          setPrimaryGuest({ ...primaryGuest, firstName: e.target.value })
                        }
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Last Name *
                      </label>
                      <input
                        type="text"
                        value={primaryGuest.lastName}
                        onChange={(e) =>
                          setPrimaryGuest({ ...primaryGuest, lastName: e.target.value })
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
                        value={primaryGuest.email}
                        onChange={(e) =>
                          setPrimaryGuest({ ...primaryGuest, email: e.target.value })
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
                        value={primaryGuest.phone}
                        onChange={(e) =>
                          setPrimaryGuest({ ...primaryGuest, phone: e.target.value })
                        }
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                        required
                      />
                    </div>
                  </div>
                </div>
              </Card>

              {/* Arrival Time & Special Requests */}
              <Card>
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Additional Information
                  </h3>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Estimated Arrival Time
                      </label>
                      <input
                        type="time"
                        value={arrivalTime}
                        onChange={(e) => setArrivalTime(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Special Requests (Optional)
                      </label>
                      <textarea
                        value={specialRequests}
                        onChange={(e) => setSpecialRequests(e.target.value)}
                        rows={4}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                        placeholder="Room preferences, accessibility needs, early check-in, etc."
                      />
                    </div>
                  </div>
                </div>
              </Card>
            </div>
          )}

          {/* Step 2: Payment */}
          {step === 2 && (
            <Card>
              <div className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6 flex items-center">
                  <CreditCardIcon className="h-5 w-5 mr-2" />
                  Payment Information
                </h3>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Card Number *
                    </label>
                    <input
                      type="text"
                      value={paymentInfo.cardNumber}
                      onChange={(e) =>
                        setPaymentInfo({ ...paymentInfo, cardNumber: e.target.value })
                      }
                      placeholder="1234 5678 9012 3456"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Cardholder Name *
                    </label>
                    <input
                      type="text"
                      value={paymentInfo.cardName}
                      onChange={(e) =>
                        setPaymentInfo({ ...paymentInfo, cardName: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                      required
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Expiry Date *
                      </label>
                      <input
                        type="text"
                        value={paymentInfo.expiryDate}
                        onChange={(e) =>
                          setPaymentInfo({ ...paymentInfo, expiryDate: e.target.value })
                        }
                        placeholder="MM/YY"
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        CVV *
                      </label>
                      <input
                        type="text"
                        value={paymentInfo.cvv}
                        onChange={(e) => setPaymentInfo({ ...paymentInfo, cvv: e.target.value })}
                        placeholder="123"
                        maxLength={4}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Billing Address
                    </label>
                    <input
                      type="text"
                      value={paymentInfo.billingAddress}
                      onChange={(e) =>
                        setPaymentInfo({ ...paymentInfo, billingAddress: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    />
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        City
                      </label>
                      <input
                        type="text"
                        value={paymentInfo.city}
                        onChange={(e) => setPaymentInfo({ ...paymentInfo, city: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        ZIP Code
                      </label>
                      <input
                        type="text"
                        value={paymentInfo.zipCode}
                        onChange={(e) =>
                          setPaymentInfo({ ...paymentInfo, zipCode: e.target.value })
                        }
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Country
                      </label>
                      <input
                        type="text"
                        value={paymentInfo.country}
                        onChange={(e) =>
                          setPaymentInfo({ ...paymentInfo, country: e.target.value })
                        }
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          )}

          {/* Error Message */}
          {bookingError && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <p className="text-red-800 dark:text-red-200 text-sm">{bookingError}</p>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex gap-4 mt-6">
            {step > 1 && (
              <Button variant="outline" onClick={() => setStep(step - 1)} className="flex-1">
                Back
              </Button>
            )}
            <Button onClick={handleNextStep} className="flex-1" disabled={processing}>
              {processing ? 'Processing...' : step === 2 ? 'Complete Booking' : 'Continue'}
            </Button>
          </div>
        </div>

        {/* Booking Summary Sidebar */}
        <div className="lg:col-span-1">
          <Card className="sticky top-4">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Booking Summary
              </h3>

              {/* Hotel Details */}
              <div className="mb-6">
                {hotel.images && hotel.images[0] && (
                  <img
                    src={hotel.images[0]}
                    alt={hotel.name}
                    className="w-full h-32 object-cover rounded-lg mb-3"
                  />
                )}

                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">{hotel.name}</h4>

                <div className="flex items-center mb-2">
                  {[...Array(hotel.stars || 3)].map((_, i) => (
                    <StarIcon key={i} className="h-4 w-4 text-yellow-400" />
                  ))}
                  {hotel.rating > 0 && (
                    <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">
                      {hotel.rating.toFixed(1)}
                    </span>
                  )}
                </div>

                <p className="text-sm text-gray-600 dark:text-gray-400 flex items-center">
                  <HomeIcon className="h-4 w-4 mr-1" />
                  {hotel.city}, {hotel.country}
                </p>
              </div>

              {/* Stay Details */}
              {bookingDetails.checkInDate && bookingDetails.checkOutDate && (
                <div className="mb-6 text-sm space-y-2">
                  <div className="flex items-center text-gray-600 dark:text-gray-400">
                    <CalendarIcon className="h-4 w-4 mr-2" />
                    <div>
                      <p>{formatDate(bookingDetails.checkInDate, 'MMM DD, YYYY')}</p>
                      <p>{formatDate(bookingDetails.checkOutDate, 'MMM DD, YYYY')}</p>
                    </div>
                  </div>

                  <p className="text-gray-600 dark:text-gray-400">
                    {nights} night{nights > 1 ? 's' : ''} • {bookingDetails.rooms} room
                    {bookingDetails.rooms > 1 ? 's' : ''} • {bookingDetails.guests} guest
                    {bookingDetails.guests > 1 ? 's' : ''}
                  </p>
                </div>
              )}

              {/* Price Breakdown */}
              {nights > 0 && (
                <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between text-gray-600 dark:text-gray-400">
                      <span>
                        {formatCurrency(hotel.pricePerNight, hotel.currency)} x {nights} night
                        {nights > 1 ? 's' : ''}
                      </span>
                      <span>{formatCurrency(hotel.pricePerNight * nights, hotel.currency)}</span>
                    </div>

                    {bookingDetails.rooms > 1 && (
                      <div className="flex justify-between text-gray-600 dark:text-gray-400">
                        <span>x {bookingDetails.rooms} rooms</span>
                        <span>{formatCurrency(subtotal, hotel.currency)}</span>
                      </div>
                    )}

                    <div className="flex justify-between text-gray-600 dark:text-gray-400">
                      <span>Taxes & Fees</span>
                      <span>{formatCurrency(taxes, hotel.currency)}</span>
                    </div>

                    <div className="flex justify-between font-bold text-gray-900 dark:text-white text-lg pt-2 border-t border-gray-200 dark:border-gray-700">
                      <span>Total</span>
                      <span>{formatCurrency(total, hotel.currency)}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default HotelBookingPage;
