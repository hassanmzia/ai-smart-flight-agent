import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { MagnifyingGlassIcon, CalendarIcon, UserGroupIcon } from '@heroicons/react/24/outline';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import { Card } from '@/components/common';
import { ROUTES } from '@/utils/constants';

type AccommodationType = 'all' | 'hotel' | 'rental';

const HotelSearchPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const initialState = location.state || {};

  const [destination, setDestination] = useState(initialState.destination || '');
  const [checkInDate, setCheckInDate] = useState('');
  const [checkOutDate, setCheckOutDate] = useState('');
  const [guests, setGuests] = useState(1);
  const [rooms, setRooms] = useState(1);
  const [accommodationType, setAccommodationType] = useState<AccommodationType>('all');

  // Rental-specific filters
  const [minBedrooms, setMinBedrooms] = useState(1);
  const [entirePropertyOnly, setEntirePropertyOnly] = useState(false);
  const [petFriendly, setPetFriendly] = useState(false);

  const pageTitle =
    accommodationType === 'hotel'
      ? 'Search Hotels'
      : accommodationType === 'rental'
        ? 'Search Vacation Rentals'
        : 'Search Accommodation';

  const handleHotelSearch = (e: React.FormEvent) => {
    e.preventDefault();
    navigate(ROUTES.HOTEL_RESULTS, {
      state: {
        destination,
        checkInDate,
        checkOutDate,
        guests,
        rooms,
        type: accommodationType,
        ...(accommodationType === 'rental' && {
          minBedrooms,
          entirePropertyOnly,
          petFriendly,
        }),
      },
    });
  };

  const toggleOptions: { value: AccommodationType; label: string }[] = [
    { value: 'all', label: 'All' },
    { value: 'hotel', label: 'Hotels' },
    { value: 'rental', label: 'Vacation Rentals' },
  ];

  return (
    <div className="min-h-screen">
      <div className="relative overflow-hidden bg-gradient-to-br from-emerald-500 via-teal-600 to-cyan-700 dark:from-emerald-800 dark:via-teal-800 dark:to-cyan-900">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute -top-10 -right-20 w-64 h-64 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 left-1/4 w-40 h-40 bg-teal-300 rounded-full blur-3xl"></div>
        </div>
        <div className="relative max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
          <h1 className="text-3xl md:text-4xl font-extrabold text-white mb-2">
            {pageTitle}
          </h1>
          <p className="text-emerald-100 text-lg">
            Find the perfect place to stay for your trip
          </p>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6 relative z-10 pb-12">
      <Card variant="glass" className="p-6">
        <form onSubmit={handleHotelSearch} className="space-y-4">
          {/* Accommodation type toggle */}
          <div className="flex rounded-xl overflow-hidden border border-gray-200 dark:border-gray-700 w-fit">
            {toggleOptions.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setAccommodationType(option.value)}
                className={`px-4 py-2 text-sm font-medium transition-colors duration-200 ${
                  accommodationType === option.value
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Destination"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              placeholder="City or destination"
              leftIcon={<MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />}
              required
            />
            <Input
              label="Check-in Date"
              type="date"
              value={checkInDate}
              onChange={(e) => setCheckInDate(e.target.value)}
              leftIcon={<CalendarIcon className="h-5 w-5 text-gray-400" />}
              required
            />
            <Input
              label="Check-out Date"
              type="date"
              value={checkOutDate}
              onChange={(e) => setCheckOutDate(e.target.value)}
              leftIcon={<CalendarIcon className="h-5 w-5 text-gray-400" />}
              required
            />
            <Input
              label="Guests"
              type="number"
              value={guests}
              onChange={(e) => setGuests(parseInt(e.target.value))}
              min="1"
              leftIcon={<UserGroupIcon className="h-5 w-5 text-gray-400" />}
              required
            />
            <Input
              label="Rooms"
              type="number"
              value={rooms}
              onChange={(e) => setRooms(parseInt(e.target.value))}
              min="1"
              required
            />
          </div>

          {/* Rental-specific filters */}
          {accommodationType === 'rental' && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 border-t border-gray-200 dark:border-gray-700">
              <Input
                label="Min Bedrooms"
                type="number"
                value={minBedrooms}
                onChange={(e) => setMinBedrooms(Math.min(10, Math.max(1, parseInt(e.target.value) || 1)))}
                min="1"
                max="10"
              />
              <div className="flex items-center gap-3 pt-6">
                <input
                  id="entirePropertyOnly"
                  type="checkbox"
                  checked={entirePropertyOnly}
                  onChange={(e) => setEntirePropertyOnly(e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                />
                <label htmlFor="entirePropertyOnly" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Entire Property Only
                </label>
              </div>
              <div className="flex items-center gap-3 pt-6">
                <input
                  id="petFriendly"
                  type="checkbox"
                  checked={petFriendly}
                  onChange={(e) => setPetFriendly(e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                />
                <label htmlFor="petFriendly" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Pet Friendly
                </label>
              </div>
            </div>
          )}

          <button type="submit" className="w-full py-3.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-semibold text-base shadow-lg shadow-emerald-500/25 hover:shadow-xl hover:shadow-emerald-500/30 transition-all duration-200 active:scale-[0.98]">
              {pageTitle}
            </button>
        </form>
      </Card>
      </div>
    </div>
  );
};

export default HotelSearchPage;
