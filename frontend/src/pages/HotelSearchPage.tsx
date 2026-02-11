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
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          🏨 Search Hotels
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Find the perfect place to stay for your trip
        </p>
      </div>

      <Card className="p-6">
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

          <Button type="submit" className="w-full" size="lg">
            Search Hotels
          </Button>
        </form>
      </Card>
    </div>
  );
};

export default HotelSearchPage;
