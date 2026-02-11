import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Loading from '@/components/common/Loading';
import TouristAttractionCard from '@/components/attraction/TouristAttractionCard';
import { useToast } from '@/hooks/useNotifications';
import touristAttractionService, { type TouristAttraction } from '@/services/touristAttractionService';

const TouristAttractionSearchPage = () => {
  const { showSuccess, showError } = useToast();
  const [loading, setLoading] = useState(false);
  const [city, setCity] = useState('');
  const [category, setCategory] = useState('');
  const [attractions, setAttractions] = useState<TouristAttraction[]>([]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!city.trim()) {
      showError('Please enter a city name');
      return;
    }

    setLoading(true);
    setAttractions([]);

    try {
      const result = await touristAttractionService.searchAttractions({
        city: city.trim(),
        category: category || undefined,
      });

      if (result.success) {
        setAttractions(result.results);
        showSuccess(`Found ${result.total} tourist attractions`);
      } else {
        showError(result.error || 'Failed to search attractions');
      }
    } catch (error: any) {
      showError(error.message || 'An error occurred while searching');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
        🗺️ Tourist Attractions
      </h1>
      <p className="text-gray-600 dark:text-gray-400 mb-8">
        Discover top-rated tourist attractions and landmarks in your destination
      </p>

      {/* Search Form */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Search Tourist Attractions</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="City or Location"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                placeholder="e.g., New York, Paris, Tokyo"
                required
              />

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Category (Optional)
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="">All Categories</option>
                  <option value="museums">🏛️ Museums & Galleries</option>
                  <option value="parks">🌳 Parks & Gardens</option>
                  <option value="landmarks">🗽 Landmarks & Monuments</option>
                  <option value="entertainment">🎢 Entertainment & Theme Parks</option>
                  <option value="religious">⛪ Religious Sites</option>
                  <option value="shopping">🛍️ Shopping Districts</option>
                  <option value="beaches">🏖️ Beaches & Waterfronts</option>
                </select>
              </div>
            </div>

            <Button type="submit" className="w-full" isLoading={loading} disabled={loading}>
              {loading ? 'Searching...' : '🔍 Search Attractions'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Loading State */}
      {loading && (
        <Card>
          <CardContent className="py-12">
            <Loading size="lg" text="Searching for tourist attractions..." />
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {!loading && attractions.length > 0 && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Found {attractions.length} Attractions
            </h2>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Showing results for <span className="font-semibold">{city}</span>
              {category && (
                <>
                  {' '}in <span className="font-semibold capitalize">{category}</span>
                </>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6">
            {attractions.map((attraction, index) => (
              <TouristAttractionCard key={attraction.place_id || index} attraction={attraction} />
            ))}
          </div>
        </div>
      )}

      {/* No Results */}
      {!loading && attractions.length === 0 && city && (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-gray-600 dark:text-gray-400 text-lg mb-2">
              No attractions found for "{city}"
              {category && ` in category "${category}"`}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-500">
              Try searching with a different city or category
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default TouristAttractionSearchPage;
