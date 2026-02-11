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
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">🍽️ Restaurant Search</h1>

      {/* Search Form */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Find Restaurants</CardTitle>
        </CardHeader>
        <CardContent>
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
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
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
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
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
                  className="w-full px-4 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
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
              className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors disabled:bg-gray-400"
            >
              {loading ? 'Searching...' : 'Search Restaurants'}
            </button>
          </form>
        </CardContent>
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
                className="bg-primary-600 hover:bg-primary-700 text-white font-semibold py-3 px-8 rounded-lg transition-colors shadow-md hover:shadow-lg"
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
  );
};

export default RestaurantSearchPage;
