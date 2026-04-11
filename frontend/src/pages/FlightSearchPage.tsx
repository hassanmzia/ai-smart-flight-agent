import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { CalendarIcon, UserGroupIcon } from '@heroicons/react/24/outline';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import { Card } from '@/components/common';
import AirportAutocomplete from '@/components/common/AirportAutocomplete';
import { ROUTES } from '@/utils/constants';

const FlightSearchPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const initialState = location.state || {};

  const [origin, setOrigin] = useState(initialState.origin || '');
  const [destination, setDestination] = useState(initialState.destination || '');
  const [departureDate, setDepartureDate] = useState(initialState.departureDate || '');
  const [returnDate, setReturnDate] = useState('');
  const [passengers, setPassengers] = useState(initialState.passengers || 1);
  const [selectedClass, setSelectedClass] = useState('economy');

  const handleFlightSearch = (e: React.FormEvent) => {
    e.preventDefault();
    navigate(ROUTES.FLIGHT_RESULTS, {
      state: {
        origin,
        destination,
        departureDate,
        returnDate,
        passengers,
        class: selectedClass,
      },
    });
  };

  return (
    <div className="min-h-screen">
      <div className="relative overflow-hidden bg-gradient-to-br from-sky-500 via-blue-600 to-indigo-700 dark:from-sky-800 dark:via-blue-800 dark:to-indigo-900">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute -top-10 -right-20 w-64 h-64 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 left-1/4 w-40 h-40 bg-sky-300 rounded-full blur-3xl"></div>
        </div>
        <div className="relative max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
          <h1 className="text-2xl md:text-3xl font-bold text-white mb-2">
            ✈️ Search Flights
          </h1>
          <p className="text-blue-100 text-lg">
            Find the best flights for your next trip
          </p>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6 relative z-10 pb-12">
      <Card variant="glass" className="p-6">
        <form onSubmit={handleFlightSearch} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <AirportAutocomplete
              label="From"
              value={origin}
              onChange={(val) => setOrigin(val)}
              placeholder="Search city or airport..."
              required
            />
            <AirportAutocomplete
              label="To"
              value={destination}
              onChange={(val) => setDestination(val)}
              placeholder="Search city or airport..."
              required
            />
            <Input
              label="Departure Date"
              type="date"
              value={departureDate}
              onChange={(e) => setDepartureDate(e.target.value)}
              leftIcon={<CalendarIcon className="h-5 w-5 text-gray-400" />}
              required
            />
            <Input
              label="Return Date (Optional)"
              type="date"
              value={returnDate}
              onChange={(e) => setReturnDate(e.target.value)}
              leftIcon={<CalendarIcon className="h-5 w-5 text-gray-400" />}
            />
            <Input
              label="Passengers"
              type="number"
              value={passengers}
              onChange={(e) => setPassengers(parseInt(e.target.value))}
              min="1"
              leftIcon={<UserGroupIcon className="h-5 w-5 text-gray-400" />}
              required
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Class
              </label>
              <select
                value={selectedClass}
                onChange={(e) => setSelectedClass(e.target.value)}
                className="block w-full rounded-xl border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
              >
                <option value="economy">Economy</option>
                <option value="premium_economy">Premium Economy</option>
                <option value="business">Business</option>
                <option value="first">First Class</option>
              </select>
            </div>
          </div>

          <button type="submit" className="w-full py-3.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold text-base shadow-lg shadow-blue-500/25 hover:shadow-xl hover:shadow-blue-500/30 transition-all duration-200 active:scale-[0.98]">
              Search Flights
            </button>
        </form>
      </Card>
      </div>
    </div>
  );
};

export default FlightSearchPage;
