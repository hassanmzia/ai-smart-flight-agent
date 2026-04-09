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
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [category, setCategory] = useState('');
  const [attractions, setAttractions] = useState<TouristAttraction[]>([]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!city.trim()) {
      showError('Please enter a city name');
      return;
    }

    if (startDate && endDate && new Date(endDate) < new Date(startDate)) {
      showError('End date must be after start date');
      return;
    }

    setLoading(true);
    setAttractions([]);

    try {
      const result = await touristAttractionService.searchAttractions({
        city: city.trim(),
        category: category || undefined,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
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
    <div className="min-h-screen">
      <div className="relative overflow-hidden bg-gradient-to-br from-violet-500 via-purple-600 to-indigo-700 dark:from-violet-800 dark:via-purple-800 dark:to-indigo-900">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute -top-10 -right-20 w-64 h-64 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 left-1/4 w-40 h-40 bg-violet-300 rounded-full blur-3xl"></div>
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
          <h1 className="text-3xl md:text-4xl font-extrabold text-white mb-2">
            🗺️ Tourist Attractions
          </h1>
          <p className="text-violet-100 text-lg">
            Discover top-rated attractions and landmarks in your destination
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6 relative z-10 pb-12">
      {/* Search Form */}
      <Card variant="glass" className="mb-8">
        <div className="p-6">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Input
                label="City or Location"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                placeholder="e.g., New York, Paris, Tokyo"
                required
              />

              <Input
                label="Start Date (Optional)"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />

              <Input
                label="End Date (Optional)"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Category (Optional)
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-shadow"
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
        </div>
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
    </div>
  );
};

export default TouristAttractionSearchPage;
