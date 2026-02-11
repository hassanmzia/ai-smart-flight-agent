import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import CarRentalCard from '../components/car/CarRentalCard';
import carRentalService, { CarRental, CarRentalSearchParams } from '../services/carRentalService';

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
    // Navigate to booking page or show booking modal
    console.log('Selected car:', car);
    // TODO: Implement booking flow
    alert(`Selected: ${car.rental_company} - ${car.vehicle}\nPrice: $${car.total_price} total`);
  };

  // Get min dates for date inputs
  const today = new Date().toISOString().split('T')[0];
  const minDropoffDate = searchParams.pickup_date || today;

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
          🚗 Car Rental Search
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Find the perfect rental car for your trip
        </p>
      </div>

      {/* Search Form */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Search for Car Rentals</CardTitle>
        </CardHeader>
        <CardContent>
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
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:text-white"
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
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:text-white"
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
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:text-white"
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
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:text-white"
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
                className="px-6 py-3 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-400 text-white font-semibold rounded-lg transition-colors flex items-center gap-2"
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
        </CardContent>
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
  );
};

export default CarRentalSearchPage;
