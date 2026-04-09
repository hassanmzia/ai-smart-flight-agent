import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { MagnifyingGlassIcon, CalendarIcon, UserGroupIcon } from '@heroicons/react/24/outline';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import { Card } from '@/components/common';
import { ROUTES } from '@/utils/constants';

const HotelSearchPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const initialState = location.state || {};

  const [destination, setDestination] = useState(initialState.destination || '');
  const [checkInDate, setCheckInDate] = useState('');
  const [checkOutDate, setCheckOutDate] = useState('');
  const [guests, setGuests] = useState(1);
  const [rooms, setRooms] = useState(1);

  const handleHotelSearch = (e: React.FormEvent) => {
    e.preventDefault();
    navigate(ROUTES.HOTEL_RESULTS, {
      state: {
        destination,
        checkInDate,
        checkOutDate,
        guests,
        rooms,
      },
    });
  };

  return (
    <div className="min-h-screen">
      <div className="relative overflow-hidden bg-gradient-to-br from-emerald-500 via-teal-600 to-cyan-700 dark:from-emerald-800 dark:via-teal-800 dark:to-cyan-900">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute -top-10 -right-20 w-64 h-64 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 left-1/4 w-40 h-40 bg-teal-300 rounded-full blur-3xl"></div>
        </div>
        <div className="relative max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
          <h1 className="text-3xl md:text-4xl font-extrabold text-white mb-2">
            🏨 Search Hotels
          </h1>
          <p className="text-emerald-100 text-lg">
            Find the perfect place to stay for your trip
          </p>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6 relative z-10 pb-12">
      <Card variant="glass" className="p-6">
        <form onSubmit={handleHotelSearch} className="space-y-4">
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

          <button type="submit" className="w-full py-3.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-semibold text-base shadow-lg shadow-emerald-500/25 hover:shadow-xl hover:shadow-emerald-500/30 transition-all duration-200 active:scale-[0.98]">
              Search Hotels
            </button>
        </form>
      </Card>
      </div>
    </div>
  );
};

export default HotelSearchPage;
