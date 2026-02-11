import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MagnifyingGlassIcon, CalendarIcon, UserGroupIcon } from '@heroicons/react/24/outline';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import { Card } from '@/components/common';
import { ROUTES } from '@/utils/constants';

const HomePage = () => {
  const navigate = useNavigate();
  const [searchType, setSearchType] = useState<'flight' | 'hotel'>('flight');
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [departureDate, setDepartureDate] = useState('');
  const [passengers, setPassengers] = useState(1);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    navigate(ROUTES.SEARCH, {
      state: {
        searchType,
        origin,
        destination,
        departureDate,
        passengers,
      },
    });
  };

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <div className="relative bg-gradient-to-br from-primary-600 via-primary-700 to-primary-900 dark:from-primary-700 dark:via-primary-800 dark:to-primary-950 text-white py-24 overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0" style={{
            backgroundImage: 'radial-gradient(circle at 2px 2px, white 1px, transparent 0)',
            backgroundSize: '40px 40px'
          }}></div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="text-center mb-16">
            <h1 className="text-5xl md:text-6xl font-extrabold mb-6 leading-tight">
              Your AI-Powered Travel Companion
            </h1>
            <p className="text-xl md:text-2xl opacity-95 max-w-3xl mx-auto font-light">
              Smart flight and hotel bookings with goal-based optimization
            </p>
          </div>

          {/* Search Form */}
          <Card className="max-w-4xl mx-auto backdrop-blur-sm">
            <div className="flex space-x-4 mb-8">
              <button
                onClick={() => setSearchType('flight')}
                className={`flex-1 py-3 px-6 rounded-xl font-semibold transition-all duration-200 ${
                  searchType === 'flight'
                    ? 'bg-primary-600 text-white shadow-lg transform scale-105'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                ✈️ Flights
              </button>
              <button
                onClick={() => setSearchType('hotel')}
                className={`flex-1 py-3 px-6 rounded-xl font-semibold transition-all duration-200 ${
                  searchType === 'hotel'
                    ? 'bg-primary-600 text-white shadow-lg transform scale-105'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                🏨 Hotels
              </button>
            </div>

            <form onSubmit={handleSearch} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {searchType === 'flight' && (
                  <Input
                    label="From"
                    value={origin}
                    onChange={(e) => setOrigin(e.target.value)}
                    placeholder="City or airport"
                    leftIcon={<MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />}
                    required
                  />
                )}
                <Input
                  label="To"
                  value={destination}
                  onChange={(e) => setDestination(e.target.value)}
                  placeholder="City or destination"
                  leftIcon={<MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />}
                  required
                />
                <Input
                  label={searchType === 'flight' ? 'Departure Date' : 'Check-in Date'}
                  type="date"
                  value={departureDate}
                  onChange={(e) => setDepartureDate(e.target.value)}
                  leftIcon={<CalendarIcon className="h-5 w-5 text-gray-400" />}
                  required
                />
                <Input
                  label={searchType === 'flight' ? 'Passengers' : 'Guests'}
                  type="number"
                  value={passengers}
                  onChange={(e) => setPassengers(parseInt(e.target.value))}
                  min="1"
                  leftIcon={<UserGroupIcon className="h-5 w-5 text-gray-400" />}
                  required
                />
              </div>

              <Button type="submit" className="w-full shadow-lg hover:shadow-xl" size="lg">
                🔍 Search {searchType === 'flight' ? 'Flights' : 'Hotels'}
              </Button>
            </form>
          </Card>
        </div>
      </div>

      {/* Features Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            Why Choose AI Travel Agent?
          </h2>
          <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            Experience the future of travel planning with our intelligent platform
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <Card hover className="text-center group">
            <div className="w-20 h-20 bg-gradient-to-br from-primary-100 to-primary-200 dark:from-primary-900/30 dark:to-primary-800/20 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform duration-200">
              <MagnifyingGlassIcon className="h-10 w-10 text-primary-600 dark:text-primary-400" />
            </div>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
              Smart Search
            </h3>
            <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
              AI-powered search with goal-based optimization finds the best deals for your needs
            </p>
          </Card>

          <Card hover className="text-center group">
            <div className="w-20 h-20 bg-gradient-to-br from-primary-100 to-primary-200 dark:from-primary-900/30 dark:to-primary-800/20 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform duration-200">
              <CalendarIcon className="h-10 w-10 text-primary-600 dark:text-primary-400" />
            </div>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
              Trip Planning
            </h3>
            <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
              Organize your entire trip with our intuitive itinerary builder
            </p>
          </Card>

          <Card hover className="text-center group">
            <div className="w-20 h-20 bg-gradient-to-br from-primary-100 to-primary-200 dark:from-primary-900/30 dark:to-primary-800/20 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform duration-200">
              <UserGroupIcon className="h-10 w-10 text-primary-600 dark:text-primary-400" />
            </div>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
              24/7 Support
            </h3>
            <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
              AI assistant available anytime to help with your travel needs
            </p>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
