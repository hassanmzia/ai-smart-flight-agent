import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useRequireAuth } from '@/hooks/useAuth';
import { Card, Button } from '@/components/common';
import { formatCurrency, formatDate, formatDuration } from '@/utils/formatters';
import {
  UserIcon,
  CalendarIcon,
  ClockIcon,
  CreditCardIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import type { Flight, Passenger } from '@/types';

const FlightBookingPage = () => {
  const { flightId } = useParams<{ flightId: string }>();
  const { user } = useRequireAuth();
  const navigate = useNavigate();

  const [flight, setFlight] = useState<Flight | null>(null);
  const [loading, setLoading] = useState(true);
  const [step, setStep] = useState(1); // 1: Passengers, 2: Payment, 3: Confirmation

  // Form state
  const [passengers, setPassengers] = useState<Passenger[]>([
    {
      firstName: user?.name?.split(' ')[0] || '',
      lastName: user?.name?.split(' ')[1] || '',
      dateOfBirth: '',
      passportNumber: '',
      nationality: '',
      email: user?.email || '',
      phone: '',
    },
  ]);

  const [contactInfo, setContactInfo] = useState({
    email: user?.email || '',
    phone: '',
    emergencyContact: '',
    emergencyPhone: '',
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
  const [bookingError, setBookingError] = useState('');
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    // In a real app, fetch flight details from API
    // For now, we'll get it from navigation state or localStorage
    const savedFlight = sessionStorage.getItem('selectedFlight');
    if (savedFlight) {
      setFlight(JSON.parse(savedFlight));
    }
    setLoading(false);
  }, [flightId]);

  const addPassenger = () => {
    setPassengers([
      ...passengers,
      {
        firstName: '',
        lastName: '',
        dateOfBirth: '',
        passportNumber: '',
        nationality: '',
        email: '',
        phone: '',
      },
    ]);
  };

  const updatePassenger = (index: number, field: keyof Passenger, value: string) => {
    const updated = [...passengers];
    updated[index] = { ...updated[index], [field]: value };
    setPassengers(updated);
  };

  const removePassenger = (index: number) => {
    if (passengers.length > 1) {
      setPassengers(passengers.filter((_, i) => i !== index));
    }
  };

  const validatePassengers = () => {
    for (const passenger of passengers) {
      if (!passenger.firstName || !passenger.lastName || !passenger.dateOfBirth) {
        setBookingError('Please fill in all required passenger information');
        return false;
      }
    }
    if (!contactInfo.email || !contactInfo.phone) {
      setBookingError('Please provide contact information');
      return false;
    }
    return true;
  };

  const validatePayment = () => {
    if (
      !paymentInfo.cardNumber ||
      !paymentInfo.cardName ||
      !paymentInfo.expiryDate ||
      !paymentInfo.cvv
    ) {
      setBookingError('Please fill in all payment information');
      return false;
    }
    return true;
  };

  const handleNextStep = () => {
    setBookingError('');
    if (step === 1 && validatePassengers()) {
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
      // const response = await createBooking({ flight, passengers, payment, etc });

      setStep(3);
    } catch (error) {
      setBookingError('Booking failed. Please try again.');
    } finally {
      setProcessing(false);
    }
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

  if (!flight) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <Card className="p-8 text-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Flight Not Found
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            The flight you're trying to book could not be found.
          </p>
          <Button onClick={() => navigate('/flights')}>Search Flights</Button>
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
            Your flight has been successfully booked.
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-500 mb-8">
            Confirmation email sent to {contactInfo.email}
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
                <p className="text-sm text-gray-500 dark:text-gray-400">Flight</p>
                <p className="text-lg font-bold text-gray-900 dark:text-white">
                  {flight.airline} {flight.flightNumber}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Route</p>
                <p className="text-lg font-bold text-gray-900 dark:text-white">
                  {flight.origin.code} → {flight.destination.code}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Date</p>
                <p className="text-lg font-bold text-gray-900 dark:text-white">
                  {formatDate(flight.departureTime, 'MMM DD, YYYY')}
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

  const totalPrice = flight.price * passengers.length;

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
                {stepNum === 1 ? 'Passengers' : 'Payment'}
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
          {/* Step 1: Passenger Information */}
          {step === 1 && (
            <div className="space-y-6">
              {/* Passengers */}
              {passengers.map((passenger, index) => (
                <Card key={index}>
                  <div className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
                        <UserIcon className="h-5 w-5 mr-2" />
                        Passenger {index + 1}
                      </h3>
                      {passengers.length > 1 && (
                        <button
                          onClick={() => removePassenger(index)}
                          className="text-red-600 hover:text-red-700 text-sm"
                        >
                          Remove
                        </button>
                      )}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          First Name *
                        </label>
                        <input
                          type="text"
                          value={passenger.firstName}
                          onChange={(e) => updatePassenger(index, 'firstName', e.target.value)}
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
                          value={passenger.lastName}
                          onChange={(e) => updatePassenger(index, 'lastName', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                          required
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Date of Birth *
                        </label>
                        <input
                          type="date"
                          value={passenger.dateOfBirth}
                          onChange={(e) => updatePassenger(index, 'dateOfBirth', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                          required
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Nationality
                        </label>
                        <input
                          type="text"
                          value={passenger.nationality || ''}
                          onChange={(e) => updatePassenger(index, 'nationality', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Passport Number
                        </label>
                        <input
                          type="text"
                          value={passenger.passportNumber || ''}
                          onChange={(e) =>
                            updatePassenger(index, 'passportNumber', e.target.value)
                          }
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                        />
                      </div>
                    </div>
                  </div>
                </Card>
              ))}

              <Button variant="outline" onClick={addPassenger} className="w-full">
                + Add Another Passenger
              </Button>

              {/* Contact Information */}
              <Card>
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Contact Information
                  </h3>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Email *
                      </label>
                      <input
                        type="email"
                        value={contactInfo.email}
                        onChange={(e) =>
                          setContactInfo({ ...contactInfo, email: e.target.value })
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
                        value={contactInfo.phone}
                        onChange={(e) =>
                          setContactInfo({ ...contactInfo, phone: e.target.value })
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
                    Special Requests (Optional)
                  </h3>
                  <textarea
                    value={specialRequests}
                    onChange={(e) => setSpecialRequests(e.target.value)}
                    rows={4}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    placeholder="Meal preferences, seat requests, accessibility needs, etc."
                  />
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

              {/* Flight Details */}
              <div className="mb-6">
                <div className="flex items-center gap-3 mb-3">
                  {flight.airlineLogo && (
                    <img src={flight.airlineLogo} alt={flight.airline} className="h-8 w-8" />
                  )}
                  <div>
                    <p className="font-semibold text-gray-900 dark:text-white">
                      {flight.airline}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {flight.flightNumber}
                    </p>
                  </div>
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex items-center text-gray-600 dark:text-gray-400">
                    <CalendarIcon className="h-4 w-4 mr-2" />
                    {formatDate(flight.departureTime, 'MMM DD, YYYY')}
                  </div>

                  <div className="flex items-center text-gray-600 dark:text-gray-400">
                    <ClockIcon className="h-4 w-4 mr-2" />
                    {formatDate(flight.departureTime, 'HH:mm')} -{' '}
                    {formatDate(flight.arrivalTime, 'HH:mm')}
                  </div>

                  <div className="text-gray-600 dark:text-gray-400">
                    {flight.origin.code} → {flight.destination.code}
                  </div>

                  <div className="text-gray-600 dark:text-gray-400">
                    Duration: {formatDuration(flight.duration)}
                  </div>

                  {flight.stops > 0 && (
                    <div className="text-gray-600 dark:text-gray-400">
                      {flight.stops} stop{flight.stops > 1 ? 's' : ''}
                    </div>
                  )}
                </div>
              </div>

              {/* Price Breakdown */}
              <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between text-gray-600 dark:text-gray-400">
                    <span>Base Fare ({passengers.length}x)</span>
                    <span>{formatCurrency(flight.price * passengers.length, flight.currency)}</span>
                  </div>

                  <div className="flex justify-between text-gray-600 dark:text-gray-400">
                    <span>Taxes & Fees</span>
                    <span>{formatCurrency(totalPrice * 0.15, flight.currency)}</span>
                  </div>

                  <div className="flex justify-between font-bold text-gray-900 dark:text-white text-lg pt-2 border-t border-gray-200 dark:border-gray-700">
                    <span>Total</span>
                    <span>{formatCurrency(totalPrice * 1.15, flight.currency)}</span>
                  </div>
                </div>
              </div>

              {/* Passengers List */}
              <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Passengers ({passengers.length})
                </p>
                <ul className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
                  {passengers.map((p, i) => (
                    <li key={i}>
                      {p.firstName} {p.lastName || '(Not filled)'}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default FlightBookingPage;
