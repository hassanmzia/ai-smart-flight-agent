import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  MagnifyingGlassIcon,
  CalendarIcon,
  UserGroupIcon,
  SparklesIcon,
  MapPinIcon,
  ClockIcon,
  ShieldCheckIcon,
  CurrencyDollarIcon,
  StarIcon,
  UserPlusIcon,
  ArrowRightIcon,
} from '@heroicons/react/24/outline';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import { Card } from '@/components/common';
import { ROUTES } from '@/utils/constants';
import useAuthStore from '@/store/authStore';

const HomePage = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
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
      <div className="relative bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 dark:from-blue-800 dark:via-purple-800 dark:to-pink-800 text-white py-32 overflow-hidden">
        {/* Animated Background Pattern */}
        <div className="absolute inset-0 opacity-20">
          <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0zNiAxOGMzLjMxNCAwIDYgMi42ODYgNiA2cy0yLjY4NiA2LTYgNi02LTIuNjg2LTYtNiAyLjY4Ni02IDYtNnptMCAzNmMzLjMxNCAwIDYgMi42ODYgNiA2cy0yLjY4NiA2LTYgNi02LTIuNjg2LTYtNiAyLjY4Ni02IDYtNnpNMTIgNmMzLjMxNCAwIDYgMi42ODYgNiA2cy0yLjY4NiA2LTYgNi02LTIuNjg2LTYtNiAyLjY4Ni02IDYtNnoiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIyIi8+PC9nPjwvc3ZnPg==')] animate-pulse"></div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm px-4 py-2 rounded-full mb-6">
              <SparklesIcon className="h-5 w-5" />
              <span className="text-sm font-medium">Powered by Advanced AI</span>
            </div>
            <h1 className="text-6xl md:text-7xl font-extrabold mb-6 leading-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-blue-100 to-purple-100">
              Plan Your Dream Trip
            </h1>
            <p className="text-xl md:text-2xl opacity-95 max-w-3xl mx-auto font-light mb-4">
              Complete travel planning powered by AI - flights, hotels, restaurants, attractions & more
            </p>
            <div className="flex flex-wrap justify-center gap-4 mt-8">
              <div className="flex items-center gap-2 text-sm">
                <ShieldCheckIcon className="h-5 w-5" />
                <span>Secure Booking</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <CurrencyDollarIcon className="h-5 w-5" />
                <span>Best Prices</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <ClockIcon className="h-5 w-5" />
                <span>24/7 Support</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <StarIcon className="h-5 w-5" />
                <span>5-Star Rated</span>
              </div>
            </div>
          </div>

          {/* Quick Actions & Search — Only for authenticated users */}
          <div className="max-w-5xl mx-auto">
            {isAuthenticated ? (
              <>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                  <button
                    onClick={() => navigate(ROUTES.AI_PLANNER)}
                    className="bg-white/10 backdrop-blur-md hover:bg-white/20 border border-white/20 rounded-2xl p-6 text-left transition-all hover:scale-105 transform"
                  >
                    <div className="text-4xl mb-3">🤖</div>
                    <h3 className="text-lg font-bold mb-1">AI Trip Planner</h3>
                    <p className="text-sm opacity-90">Let AI create your perfect itinerary</p>
                  </button>

                  <button
                    onClick={() => navigate(ROUTES.FLIGHT_SEARCH)}
                    className="bg-white/10 backdrop-blur-md hover:bg-white/20 border border-white/20 rounded-2xl p-6 text-left transition-all hover:scale-105 transform"
                  >
                    <div className="text-4xl mb-3">✈️</div>
                    <h3 className="text-lg font-bold mb-1">Search Flights</h3>
                    <p className="text-sm opacity-90">Find the best flight deals</p>
                  </button>

                  <button
                    onClick={() => navigate(ROUTES.HOTEL_SEARCH)}
                    className="bg-white/10 backdrop-blur-md hover:bg-white/20 border border-white/20 rounded-2xl p-6 text-left transition-all hover:scale-105 transform"
                  >
                    <div className="text-4xl mb-3">🏨</div>
                    <h3 className="text-lg font-bold mb-1">Book Hotels</h3>
                    <p className="text-sm opacity-90">Discover amazing accommodations</p>
                  </button>
                </div>

                {/* Search Form */}
                <Card className="backdrop-blur-md bg-white/95 dark:bg-gray-900/95 shadow-2xl">
                  <div className="flex flex-wrap gap-2 mb-6">
                    <button
                      onClick={() => setSearchType('flight')}
                      className={`px-6 py-2.5 rounded-lg font-semibold transition-all duration-200 ${
                        searchType === 'flight'
                          ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg'
                          : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                      }`}
                    >
                      ✈️ Flights
                    </button>
                    <button
                      onClick={() => setSearchType('hotel')}
                      className={`px-6 py-2.5 rounded-lg font-semibold transition-all duration-200 ${
                        searchType === 'hotel'
                          ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg'
                          : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
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
                          leftIcon={<MapPinIcon className="h-5 w-5 text-gray-400" />}
                          required
                        />
                      )}
                      <Input
                        label="To"
                        value={destination}
                        onChange={(e) => setDestination(e.target.value)}
                        placeholder="City or destination"
                        leftIcon={<MapPinIcon className="h-5 w-5 text-gray-400" />}
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

                    <Button type="submit" className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-lg hover:shadow-xl" size="lg">
                      <MagnifyingGlassIcon className="h-5 w-5 mr-2 inline" />
                      Search {searchType === 'flight' ? 'Flights' : 'Hotels'}
                    </Button>
                  </form>
                </Card>
              </>
            ) : (
              /* Auth Gate — shown to anonymous visitors */
              <Card className="backdrop-blur-md bg-white/95 dark:bg-gray-900/95 shadow-2xl max-w-2xl mx-auto text-center">
                <div className="py-6 px-4">
                  <div className="mx-auto w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mb-6 shadow-lg">
                    <UserPlusIcon className="h-10 w-10 text-white" />
                  </div>
                  <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-3">
                    Create an Account to Get Started
                  </h2>
                  <p className="text-gray-600 dark:text-gray-400 text-lg mb-8 max-w-md mx-auto">
                    Sign up for free to search flights, book hotels, and plan your trips with our AI-powered travel assistant.
                  </p>

                  <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
                    <Button
                      onClick={() => navigate(ROUTES.REGISTER)}
                      size="lg"
                      className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-lg hover:shadow-xl px-8 text-lg font-bold"
                    >
                      <UserPlusIcon className="h-5 w-5 mr-2 inline" />
                      Create Free Account
                    </Button>
                    <Button
                      onClick={() => navigate(ROUTES.LOGIN)}
                      size="lg"
                      variant="outline"
                      className="border-2 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 px-8 text-lg font-bold"
                    >
                      Sign In
                      <ArrowRightIcon className="h-5 w-5 ml-2 inline" />
                    </Button>
                  </div>

                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <div className="text-2xl mb-1">✈️</div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">Search Flights</p>
                    </div>
                    <div>
                      <div className="text-2xl mb-1">🏨</div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">Book Hotels</p>
                    </div>
                    <div>
                      <div className="text-2xl mb-1">🤖</div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">AI Trip Planner</p>
                    </div>
                  </div>
                </div>
              </Card>
            )}
          </div>
        </div>
      </div>

      {/* Travel Services - Professional Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
        <div className="text-center mb-20">
          <div className="inline-block mb-4">
            <span className="text-sm font-semibold text-blue-600 dark:text-blue-400 uppercase tracking-wider">
              Complete Travel Suite
            </span>
          </div>
          <h2 className="text-5xl font-bold text-gray-900 dark:text-white mb-6 tracking-tight">
            Everything You Need for the
            <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent"> Perfect Trip</span>
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto leading-relaxed">
            From intelligent planning to seamless booking - all powered by advanced AI technology
          </p>
        </div>

        {/* Premium Service Categories */}
        <div className="space-y-16">
          {/* Core Services */}
          <div>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-8 flex items-center gap-3">
              <div className="w-1 h-8 bg-gradient-to-b from-blue-600 to-purple-600 rounded-full"></div>
              Core Services
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div
                onClick={() => navigate(ROUTES.AI_PLANNER)}
                className="group relative bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-950/20 dark:to-purple-950/20 rounded-2xl p-8 cursor-pointer border border-blue-100 dark:border-blue-900/30 hover:shadow-2xl hover:scale-105 transition-all duration-300 overflow-hidden"
              >
                <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-blue-200/20 to-purple-200/20 rounded-full blur-3xl group-hover:scale-150 transition-transform duration-500"></div>
                <div className="relative">
                  <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl flex items-center justify-center mb-6 text-3xl shadow-lg group-hover:rotate-6 transition-transform">
                    🤖
                  </div>
                  <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">AI Trip Planner</h3>
                  <p className="text-gray-600 dark:text-gray-400 leading-relaxed mb-4">
                    Let our intelligent AI create personalized itineraries tailored to your preferences and budget
                  </p>
                  <div className="flex items-center text-blue-600 dark:text-blue-400 font-semibold group-hover:gap-3 gap-2 transition-all">
                    <span>Start Planning</span>
                    <span className="group-hover:translate-x-1 transition-transform">→</span>
                  </div>
                </div>
              </div>

              <div
                onClick={() => navigate(ROUTES.FLIGHT_SEARCH)}
                className="group relative bg-gradient-to-br from-sky-50 to-blue-50 dark:from-sky-950/20 dark:to-blue-950/20 rounded-2xl p-8 cursor-pointer border border-sky-100 dark:border-sky-900/30 hover:shadow-2xl hover:scale-105 transition-all duration-300 overflow-hidden"
              >
                <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-sky-200/20 to-blue-200/20 rounded-full blur-3xl group-hover:scale-150 transition-transform duration-500"></div>
                <div className="relative">
                  <div className="w-16 h-16 bg-gradient-to-br from-sky-600 to-blue-600 rounded-2xl flex items-center justify-center mb-6 text-3xl shadow-lg group-hover:rotate-6 transition-transform">
                    ✈️
                  </div>
                  <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">Flight Search</h3>
                  <p className="text-gray-600 dark:text-gray-400 leading-relaxed mb-4">
                    Compare thousands of flights to find the best deals with real-time pricing and availability
                  </p>
                  <div className="flex items-center text-sky-600 dark:text-sky-400 font-semibold group-hover:gap-3 gap-2 transition-all">
                    <span>Search Flights</span>
                    <span className="group-hover:translate-x-1 transition-transform">→</span>
                  </div>
                </div>
              </div>

              <div
                onClick={() => navigate(ROUTES.HOTEL_SEARCH)}
                className="group relative bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-indigo-950/20 dark:to-purple-950/20 rounded-2xl p-8 cursor-pointer border border-indigo-100 dark:border-indigo-900/30 hover:shadow-2xl hover:scale-105 transition-all duration-300 overflow-hidden"
              >
                <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-indigo-200/20 to-purple-200/20 rounded-full blur-3xl group-hover:scale-150 transition-transform duration-500"></div>
                <div className="relative">
                  <div className="w-16 h-16 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-2xl flex items-center justify-center mb-6 text-3xl shadow-lg group-hover:rotate-6 transition-transform">
                    🏨
                  </div>
                  <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">Hotels & Stays</h3>
                  <p className="text-gray-600 dark:text-gray-400 leading-relaxed mb-4">
                    Discover and book from luxury resorts to budget-friendly accommodations worldwide
                  </p>
                  <div className="flex items-center text-indigo-600 dark:text-indigo-400 font-semibold group-hover:gap-3 gap-2 transition-all">
                    <span>Find Hotels</span>
                    <span className="group-hover:translate-x-1 transition-transform">→</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Explore & Experience */}
          <div>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-8 flex items-center gap-3">
              <div className="w-1 h-8 bg-gradient-to-b from-purple-600 to-pink-600 rounded-full"></div>
              Explore & Experience
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
              {[
                { icon: '🍽️', title: 'Restaurants', desc: 'Fine dining & local cuisine', path: '/restaurants', color: 'rose' },
                { icon: '🗽', title: 'Attractions', desc: 'Must-see destinations', path: '/attractions', color: 'orange' },
                { icon: '🎭', title: 'Events', desc: 'Shows & entertainment', path: '/events', color: 'purple' },
                { icon: '🚗', title: 'Car Rentals', desc: 'Vehicles for every need', path: '/cars', color: 'blue' },
                { icon: '🛍️', title: 'Shopping', desc: 'Best shopping spots', path: '/shopping', color: 'pink' },
              ].map((service, idx) => (
                <div
                  key={idx}
                  onClick={() => navigate(service.path)}
                  className={`group bg-white dark:bg-gray-800 rounded-xl p-6 cursor-pointer border-2 border-gray-100 dark:border-gray-700 hover:border-${service.color}-300 dark:hover:border-${service.color}-600 hover:shadow-xl hover:-translate-y-1 transition-all duration-300`}
                >
                  <div className="text-4xl mb-3 group-hover:scale-110 transition-transform">{service.icon}</div>
                  <h4 className="font-bold text-gray-900 dark:text-white mb-1">{service.title}</h4>
                  <p className="text-xs text-gray-600 dark:text-gray-400">{service.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Travel Essentials */}
          <div>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-8 flex items-center gap-3">
              <div className="w-1 h-8 bg-gradient-to-b from-green-600 to-teal-600 rounded-full"></div>
              Travel Essentials
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {[
                { icon: '🌤️', title: 'Weather', desc: 'Real-time forecasts', path: '/weather', gradient: 'from-cyan-500 to-blue-500' },
                { icon: '🛡️', title: 'Safety', desc: 'Travel advisories', path: '/safety', gradient: 'from-green-500 to-emerald-500' },
                { icon: '🚇', title: 'Commute', desc: 'Local transit info', path: '/commute', gradient: 'from-violet-500 to-purple-500' },
                { icon: '📋', title: 'Itineraries', desc: 'Manage your trips', path: ROUTES.ITINERARY, gradient: 'from-orange-500 to-red-500' },
              ].map((service, idx) => (
                <div
                  key={idx}
                  onClick={() => navigate(service.path)}
                  className="group bg-white dark:bg-gray-800 rounded-xl p-6 cursor-pointer border border-gray-200 dark:border-gray-700 hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
                >
                  <div className={`w-12 h-12 bg-gradient-to-br ${service.gradient} rounded-xl flex items-center justify-center mb-4 text-2xl shadow-md group-hover:scale-110 transition-transform`}>
                    {service.icon}
                  </div>
                  <h4 className="font-bold text-gray-900 dark:text-white mb-1">{service.title}</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{service.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Why Choose Us - Professional Features */}
      <div className="relative bg-gradient-to-br from-gray-50 to-blue-50/30 dark:from-gray-900 dark:to-blue-950/20 py-24 overflow-hidden">
        <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="text-center mb-20">
            <div className="inline-block mb-4">
              <span className="text-sm font-semibold text-blue-600 dark:text-blue-400 uppercase tracking-wider">
                Why Choose Us
              </span>
            </div>
            <h2 className="text-5xl font-bold text-gray-900 dark:text-white mb-6 tracking-tight">
              The Future of Travel Planning
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto leading-relaxed">
              Experience unparalleled service with cutting-edge AI technology designed for the modern traveler
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">
            <div className="group bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-lg hover:shadow-2xl transition-all duration-300 border border-gray-100 dark:border-gray-700">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 group-hover:rotate-3 transition-all duration-300 shadow-lg">
                <SparklesIcon className="h-8 w-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3">
                AI-Powered Intelligence
              </h3>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                Advanced algorithms analyze millions of options to find your perfect match in seconds
              </p>
            </div>

            <div className="group bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-lg hover:shadow-2xl transition-all duration-300 border border-gray-100 dark:border-gray-700">
              <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 group-hover:rotate-3 transition-all duration-300 shadow-lg">
                <ShieldCheckIcon className="h-8 w-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3">
                Secure & Trusted
              </h3>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                Bank-level encryption and verified partners ensure your data and payments are always safe
              </p>
            </div>

            <div className="group bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-lg hover:shadow-2xl transition-all duration-300 border border-gray-100 dark:border-gray-700">
              <div className="w-16 h-16 bg-gradient-to-br from-orange-500 to-red-600 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 group-hover:rotate-3 transition-all duration-300 shadow-lg">
                <CurrencyDollarIcon className="h-8 w-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3">
                Best Price Guarantee
              </h3>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                We compare prices across thousands of providers to ensure you always get the best deal
              </p>
            </div>

            <div className="group bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-lg hover:shadow-2xl transition-all duration-300 border border-gray-100 dark:border-gray-700">
              <div className="w-16 h-16 bg-gradient-to-br from-violet-500 to-purple-600 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 group-hover:rotate-3 transition-all duration-300 shadow-lg">
                <ClockIcon className="h-8 w-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3">
                24/7 Expert Support
              </h3>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                Our AI assistant and human experts are always available to help with any questions
              </p>
            </div>
          </div>

          {/* Stats Section */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-5xl mx-auto">
            <div className="text-center">
              <div className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-2">
                2M+
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400 font-medium">Happy Travelers</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent mb-2">
                150+
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400 font-medium">Countries Covered</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold bg-gradient-to-r from-orange-600 to-red-600 bg-clip-text text-transparent mb-2">
                $2B+
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400 font-medium">Saved for Customers</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent mb-2">
                4.9
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400 font-medium">Average Rating</div>
            </div>
          </div>
        </div>
      </div>

      {/* Testimonials Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
        <div className="text-center mb-16">
          <div className="inline-block mb-4">
            <span className="text-sm font-semibold text-blue-600 dark:text-blue-400 uppercase tracking-wider">
              Testimonials
            </span>
          </div>
          <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            Loved by Travelers Worldwide
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {[
            {
              name: 'Sarah Johnson',
              role: 'Business Traveler',
              image: '👩‍💼',
              rating: 5,
              text: 'The AI planner saved me hours of research. It found the perfect flights and hotels for my business trips every time!'
            },
            {
              name: 'Michael Chen',
              role: 'Adventure Seeker',
              image: '🧑‍🦱',
              rating: 5,
              text: 'From booking to planning activities, everything was seamless. The local recommendations were spot-on!'
            },
            {
              name: 'Emma Williams',
              role: 'Family Vacationer',
              image: '👩‍👧‍👦',
              rating: 5,
              text: 'Planning our family vacation has never been easier. The interface is intuitive and the AI suggestions were perfect for kids!'
            }
          ].map((testimonial, idx) => (
            <div key={idx} className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-lg border border-gray-100 dark:border-gray-700">
              <div className="flex items-center gap-1 mb-4">
                {[...Array(testimonial.rating)].map((_, i) => (
                  <StarIcon key={i} className="h-5 w-5 fill-yellow-400 text-yellow-400" />
                ))}
              </div>
              <p className="text-gray-700 dark:text-gray-300 mb-6 leading-relaxed italic">
                "{testimonial.text}"
              </p>
              <div className="flex items-center gap-4">
                <div className="text-4xl">{testimonial.image}</div>
                <div>
                  <div className="font-bold text-gray-900 dark:text-white">{testimonial.name}</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">{testimonial.role}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* CTA Section */}
      <div className="relative bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 py-20 overflow-hidden">
        <div className="absolute inset-0 bg-black/10"></div>
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Ready to Start Your Journey?
          </h2>
          <p className="text-xl text-white/90 mb-8 max-w-2xl mx-auto">
            Join millions of travelers who trust AI Travel Agent for their perfect trip
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              onClick={() => navigate(ROUTES.AI_PLANNER)}
              size="lg"
              className="bg-white text-blue-600 hover:bg-gray-100 shadow-xl hover:shadow-2xl px-8 py-4 text-lg font-bold"
            >
              <SparklesIcon className="h-6 w-6 mr-2 inline" />
              Plan with AI
            </Button>
            <Button
              onClick={() => navigate(ROUTES.REGISTER)}
              size="lg"
              variant="outline"
              className="border-2 border-white text-white hover:bg-white/10 px-8 py-4 text-lg font-bold"
            >
              Create Free Account
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
