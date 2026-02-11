import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import shoppingService, { ShoppingVenue } from '@/services/shoppingService';
import ShoppingVenueCard from '@/components/shopping/ShoppingVenueCard';
import Button from '@/components/common/Button';

const ShoppingPage = () => {
  const [searchParams] = useSearchParams();
  const [city, setCity] = useState(searchParams.get('city') || '');
  const [category, setCategory] = useState('');
  const [venues, setVenues] = useState<ShoppingVenue[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searched, setSearched] = useState(false);

  const categories = [
    { value: '', label: 'All Categories' },
    { value: 'malls', label: '🏬 Shopping Malls' },
    { value: 'markets', label: '🛒 Markets' },
    { value: 'boutiques', label: '👗 Boutiques' },
    { value: 'outlets', label: '🏷️ Outlets' },
    { value: 'souvenirs', label: '🎁 Souvenirs' },
    { value: 'local_crafts', label: '🎨 Local Crafts' },
  ];

  const handleSearch = async () => {
    if (!city.trim()) {
      setError('Please enter a city name or airport code');
      return;
    }

    setLoading(true);
    setError('');
    setSearched(true);

    try {
      const response = await shoppingService.searchShopping({
        city: city.trim(),
        category: category || undefined,
      });

      if (response.success) {
        setVenues(response.results);
        if (response.results.length === 0) {
          setError('No shopping venues found for this location');
        }
      } else {
        setError(response.error || 'Failed to search shopping venues');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to search shopping venues');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            🛍️ Local Shopping
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Discover the best shopping destinations, malls, markets, and local boutiques
          </p>
        </div>

        {/* Search Section */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* City Input */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                City or Airport Code
              </label>
              <input
                type="text"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="e.g., New York, LAX, London"
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
              />
            </div>

            {/* Category Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
              >
                {categories.map((cat) => (
                  <option key={cat.value} value={cat.value}>
                    {cat.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Search Button */}
            <div className="flex items-end">
              <Button
                onClick={handleSearch}
                disabled={loading}
                className="w-full"
              >
                {loading ? 'Searching...' : 'Search Shopping'}
              </Button>
            </div>
          </div>

          {error && (
            <div className="mt-4 p-4 bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-red-800 dark:text-red-200">{error}</p>
            </div>
          )}
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Finding shopping venues...</p>
          </div>
        )}

        {/* Results */}
        {!loading && searched && venues.length > 0 && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Shopping Venues ({venues.length})
              </h2>
              {category && (
                <button
                  onClick={() => {
                    setCategory('');
                    handleSearch();
                  }}
                  className="text-primary-600 dark:text-primary-400 hover:underline text-sm"
                >
                  Clear filter
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {venues.map((venue, index) => (
                <ShoppingVenueCard key={index} venue={venue} />
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading && !searched && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🛍️</div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              Find Local Shopping
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Enter a city to discover shopping malls, markets, boutiques, and more
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ShoppingPage;
