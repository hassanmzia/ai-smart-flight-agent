import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Tab } from '@headlessui/react';
import { MagnifyingGlassIcon, CalendarIcon, UserGroupIcon } from '@heroicons/react/24/outline';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import { Card } from '@/components/common';
import { ROUTES } from '@/utils/constants';
import { cn } from '@/utils/helpers';

const SearchPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const initialState = location.state || {};

  const [origin, setOrigin] = useState(initialState.origin || '');
  const [destination, setDestination] = useState(initialState.destination || '');
  const [departureDate, setDepartureDate] = useState(initialState.departureDate || '');
  const [returnDate, setReturnDate] = useState('');
  const [checkInDate, setCheckInDate] = useState('');
  const [checkOutDate, setCheckOutDate] = useState('');
  const [passengers, setPassengers] = useState(initialState.passengers || 1);
  const [guests, setGuests] = useState(1);
  const [rooms, setRooms] = useState(1);
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
      {/* Hero Header */}
      <div className="relative overflow-hidden bg-gradient-to-br from-indigo-600 via-blue-600 to-cyan-600 dark:from-indigo-800 dark:via-blue-800 dark:to-cyan-800">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute -top-20 -right-20 w-72 h-72 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 left-1/3 w-48 h-48 bg-cyan-300 rounded-full blur-3xl"></div>
        </div>
        <div className="relative max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
          <h1 className="text-3xl md:text-4xl font-extrabold text-white mb-2">
            Search Flights & Hotels
          </h1>
          <p className="text-blue-100 text-lg">
            Find the best deals for your next journey
          </p>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8 relative z-10 pb-12">
        <Card variant="glass" padding="none">
          <Tab.Group>
            <Tab.List className="flex p-2 m-4 mb-0 rounded-xl bg-gray-100/80 dark:bg-gray-700/50">
              <Tab
                className={({ selected }) =>
                  cn(
                    'flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-lg font-semibold text-sm transition-all duration-200',
                    selected
                      ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/25'
                      : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-white/60 dark:hover:bg-gray-600/40'
                  )
                }
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
                </svg>
                Flights
              </Tab>
              <Tab
                className={({ selected }) =>
                  cn(
                    'flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-lg font-semibold text-sm transition-all duration-200',
                    selected
                      ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/25'
                      : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-white/60 dark:hover:bg-gray-600/40'
                  )
                }
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 0h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008z" />
                </svg>
                Hotels
              </Tab>
            </Tab.List>

            <Tab.Panels className="p-6">
              {/* Flight Search */}
              <Tab.Panel>
                <form onSubmit={handleFlightSearch} className="space-y-5">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                    <Input
                      label="From"
                      value={origin}
                      onChange={(e) => setOrigin(e.target.value)}
                      placeholder="City or airport"
                      leftIcon={<MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />}
                      required
                    />
                    <Input
                      label="To"
                      value={destination}
                      onChange={(e) => setDestination(e.target.value)}
                      placeholder="City or airport"
                      leftIcon={<MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />}
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
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
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

                  <button
                    type="submit"
                    className="w-full py-3.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold text-base shadow-lg shadow-blue-500/25 hover:shadow-xl hover:shadow-blue-500/30 transition-all duration-200 active:scale-[0.98]"
                  >
                    Search Flights
                  </button>
                </form>
              </Tab.Panel>

              {/* Hotel Search */}
              <Tab.Panel>
                <form onSubmit={handleHotelSearch} className="space-y-5">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
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

                  <button
                    type="submit"
                    className="w-full py-3.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold text-base shadow-lg shadow-blue-500/25 hover:shadow-xl hover:shadow-blue-500/30 transition-all duration-200 active:scale-[0.98]"
                  >
                    Search Hotels
                  </button>
                </form>
              </Tab.Panel>
            </Tab.Panels>
          </Tab.Group>
        </Card>
      </div>
    </div>
  );
};

export default SearchPage;
