import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/common';
import CarRentalCard from '../components/car/CarRentalCard';
import carRentalService, { CarRental, CarRentalSearchParams } from '../services/carRentalService';

const getCarBookingUrl = (car: CarRental): string => {
  if (car.website && car.website.trim()) return car.website;
  const q = encodeURIComponent(`${car.rental_company} ${car.vehicle || car.car_type} car rental ${car.pickup_location}`);
  return `https://www.google.com/search?q=${q}`;
};

const CarRentalSearchPage: React.FC = () => {
  const [searchParams, setSearchParams] = useState<CarRentalSearchParams>({
    pickup_location: '',
    pickup_date: '',
    dropoff_date: '',
    car_type: '',
  });

  const [cars, setCars] = useState<CarRental[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const carTypes = [
    { value: '', label: 'All Types' },
    { value: 'economy', label: 'Economy' },
    { value: 'compact', label: 'Compact' },
    { value: 'midsize', label: 'Midsize' },
    { value: 'fullsize', label: 'Full-size' },
    { value: 'suv', label: 'SUV' },
    { value: 'luxury', label: 'Luxury' },
    { value: 'van', label: 'Van' },
  ];

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setHasSearched(true);

    try {
      const response = await carRentalService.searchCarRentals(searchParams);

      if (response.success) {
        setCars(response.cars);
        if (response.cars.length === 0) {
          setError('No car rentals found for your search criteria.');
        }
      } else {
        setError(response.error || 'Failed to search car rentals');
        setCars([]);
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred while searching');
      setCars([]);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: keyof CarRentalSearchParams, value: string) => {
    setSearchParams((prev) => ({ ...prev, [field]: value }));
  };

  const handleSelectCar = (car: CarRental) => {
    window.open(getCarBookingUrl(car), '_blank', 'noopener,noreferrer');
  };

  // Get min dates for date inputs
  const today = new Date().toISOString().split('T')[0];
  const minDropoffDate = searchParams.pickup_date || today;

  return (
    <div className="min-h-screen">
      <div className="relative overflow-hidden bg-gradient-to-br from-orange-500 via-amber-600 to-yellow-600 dark:from-orange-800 dark:via-amber-800 dark:to-yellow-800">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute -top-10 -right-20 w-64 h-64 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 left-1/4 w-40 h-40 bg-amber-300 rounded-full blur-3xl"></div>
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
          <h1 className="text-2xl md:text-3xl font-bold text-white mb-2">
            🚗 Car Rental Search
          </h1>
          <p className="text-orange-100 text-lg">
            Find the perfect rental car for your trip
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6 relative z-10 pb-12">
      {/* Search Form */}
      <Card variant="glass" className="mb-8">
        <div className="p-6">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Pickup Location */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Pickup Location *
                </label>
                <input
                  type="text"
                  required
                  placeholder="City or Airport (e.g., Los Angeles, LAX)"
                  value={searchParams.pickup_location}
                  onChange={(e) => handleInputChange('pickup_location', e.target.value)}
                  className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
                />
              </div>

              {/* Pickup Date */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Pickup Date *
                </label>
                <input
                  type="date"
                  required
                  min={today}
                  value={searchParams.pickup_date}
                  onChange={(e) => handleInputChange('pickup_date', e.target.value)}
                  className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
                />
              </div>

              {/* Drop-off Date */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Drop-off Date *
                </label>
                <input
                  type="date"
                  required
                  min={minDropoffDate}
                  value={searchParams.dropoff_date}
                  onChange={(e) => handleInputChange('dropoff_date', e.target.value)}
                  className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
                />
              </div>

              {/* Car Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Car Type
                </label>
                <select
                  value={searchParams.car_type}
                  onChange={(e) => handleInputChange('car_type', e.target.value)}
                  className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
                >
                  {carTypes.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Search Button */}
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-3 rounded-xl bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-700 hover:to-amber-700 text-white font-semibold shadow-lg shadow-orange-500/25 hover:shadow-xl transition-all duration-200 disabled:opacity-50 flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <span className="animate-spin">⏳</span>
                    Searching...
                  </>
                ) : (
                  <>
                    🔍 Search Cars
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </Card>

      {/* Results */}
      {hasSearched && (
        <div>
          {/* Results Header */}
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              {loading ? 'Searching...' : `${cars.length} Cars Found`}
            </h2>
            {cars.length > 0 && (
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Showing results for {searchParams.pickup_location}
              </div>
            )}
          </div>

          {/* Error Message */}
          {error && (
            <Card className="mb-6 border-red-300 bg-red-50 dark:bg-red-900/20">
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 text-red-700 dark:text-red-400">
                  <span className="text-2xl">⚠️</span>
                  <div>
                    <p className="font-semibold">Error</p>
                    <p className="text-sm">{error}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Loading State */}
          {loading && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <Card key={i} className="animate-pulse">
                  <CardContent className="pt-6">
                    <div className="h-40 bg-gray-200 dark:bg-gray-700 rounded"></div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Results Grid */}
          {!loading && cars.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {cars.map((car, index) => (
                <CarRentalCard
                  key={index}
                  car={car}
                  onSelect={handleSelectCar}
                  showUtilityScore={false}
                />
              ))}
            </div>
          )}

          {/* No Results */}
          {!loading && cars.length === 0 && !error && (
            <Card>
              <CardContent className="pt-6 text-center py-12">
                <div className="text-6xl mb-4">🚗</div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                  No Cars Found
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  Try adjusting your search criteria or try a different location.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Initial State */}
      {!hasSearched && (
        <Card>
          <CardContent className="pt-6 text-center py-12">
            <div className="text-6xl mb-4">🚗</div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              Start Your Search
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Enter your pickup location and dates to find available rental cars.
            </p>
          </CardContent>
        </Card>
      )}
      </div>
    </div>
  );
};

export default CarRentalSearchPage;
