import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/common';
import RestaurantCard from '@/components/restaurant/RestaurantCard';
import restaurantService, { Restaurant, RestaurantSearchParams } from '@/services/restaurantService';

const RestaurantSearchPage: React.FC = () => {
  const [searchParams, setSearchParams] = useState<RestaurantSearchParams>({
    city: '',
    cuisine: '',
    price_level: undefined,
  });
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);
  const [displayCount, setDisplayCount] = useState(9); // Show 9 initially

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchParams.city) {
      setError('Please enter a city');
      return;
    }

    setLoading(true);
    setError(null);
    setSearched(true);
    setDisplayCount(9); // Reset display count on new search

    try {
      const result = await restaurantService.searchRestaurants(searchParams);
      if (result.success) {
        setRestaurants(result.restaurants);
        if (result.restaurants.length === 0) {
          setError('No restaurants found for your search criteria.');
        }
      } else {
        setError(result.error || 'Failed to search restaurants');
      }
    } catch (err) {
      setError('An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleShowMore = () => {
    setDisplayCount(prev => prev + 9);
  };

  const cuisineOptions = [
    'American',
    'Italian',
    'Mexican',
    'Chinese',
    'Japanese',
    'Indian',
    'Thai',
    'French',
    'Mediterranean',
    'Seafood',
  ];

  return (
    <div className="min-h-screen">
      <div className="relative overflow-hidden bg-gradient-to-br from-rose-500 via-pink-600 to-fuchsia-700 dark:from-rose-800 dark:via-pink-800 dark:to-fuchsia-900">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute -top-10 -right-20 w-64 h-64 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 left-1/4 w-40 h-40 bg-rose-300 rounded-full blur-3xl"></div>
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
          <h1 className="text-2xl md:text-3xl font-bold text-white mb-2">
            🍽️ Restaurant Search
          </h1>
          <p className="text-rose-100 text-lg">
            Discover amazing restaurants at your destination
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6 relative z-10 pb-12">
      {/* Search Form */}
      <Card variant="glass" className="mb-8">
        <div className="p-6">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* City */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  City *
                </label>
                <input
                  type="text"
                  value={searchParams.city}
                  onChange={(e) => setSearchParams({ ...searchParams, city: e.target.value })}
                  placeholder="e.g., Los Angeles, LAX, New York"
                  className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-rose-500 focus:border-transparent transition-shadow"
                  required
                />
              </div>

              {/* Cuisine */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Cuisine (Optional)
                </label>
                <select
                  value={searchParams.cuisine}
                  onChange={(e) => setSearchParams({ ...searchParams, cuisine: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-rose-500 focus:border-transparent transition-shadow"
                >
                  <option value="">Any Cuisine</option>
                  {cuisineOptions.map((cuisine) => (
                    <option key={cuisine} value={cuisine}>
                      {cuisine}
                    </option>
                  ))}
                </select>
              </div>

              {/* Price Level */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Price Range (Optional)
                </label>
                <select
                  value={searchParams.price_level || ''}
                  onChange={(e) =>
                    setSearchParams({
                      ...searchParams,
                      price_level: e.target.value ? parseInt(e.target.value) : undefined,
                    })
                  }
                  className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-rose-500 focus:border-transparent transition-shadow"
                >
                  <option value="">Any Price</option>
                  <option value="1">$ (Budget)</option>
                  <option value="2">$$ (Moderate)</option>
                  <option value="3">$$$ (Upscale)</option>
                  <option value="4">$$$$ (Fine Dining)</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 rounded-xl bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-700 hover:to-pink-700 text-white font-semibold shadow-lg shadow-rose-500/25 hover:shadow-xl transition-all duration-200 disabled:opacity-50"
            >
              {loading ? 'Searching...' : 'Search Restaurants'}
            </button>
          </form>
        </div>
      </Card>

      {/* Error Message */}
      {error && (
        <Card className="mb-8 border-red-200 dark:border-red-800">
          <CardContent className="text-center py-6">
            <p className="text-red-600 dark:text-red-400">⚠️ {error}</p>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {searched && !loading && restaurants.length > 0 && (
        <>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold">
              Found {restaurants.length} Restaurant{restaurants.length !== 1 ? 's' : ''}
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Showing {Math.min(displayCount, restaurants.length)} of {restaurants.length}
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {restaurants.slice(0, displayCount).map((restaurant) => (
              <RestaurantCard key={restaurant.id} restaurant={restaurant} />
            ))}
          </div>

          {/* Show More Button */}
          {displayCount < restaurants.length && (
            <div className="mt-8 text-center">
              <button
                onClick={handleShowMore}
                className="py-3 px-8 rounded-xl bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-700 hover:to-pink-700 text-white font-semibold shadow-lg shadow-rose-500/25 hover:shadow-xl transition-all duration-200"
              >
                Show More ({restaurants.length - displayCount} remaining)
              </button>
            </div>
          )}
        </>
      )}

      {/* No Results but searched */}
      {searched && !loading && restaurants.length === 0 && !error && (
        <Card>
          <CardContent className="text-center py-12">
            <p className="text-xl text-gray-600 dark:text-gray-400">
              No restaurants found. Try a different search.
            </p>
          </CardContent>
        </Card>
      )}
      </div>
    </div>
  );
};

export default RestaurantSearchPage;
