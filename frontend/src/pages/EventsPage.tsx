import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Loading from '@/components/common/Loading';
import EventCard from '@/components/event/EventCard';
import { useToast } from '@/hooks/useNotifications';
import eventService, { type Event } from '@/services/eventService';

const EventsPage = () => {
  const { showSuccess, showError } = useToast();
  const [loading, setLoading] = useState(false);
  const [city, setCity] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [category, setCategory] = useState('');
  const [events, setEvents] = useState<Event[]>([]);
  const [searchInfo, setSearchInfo] = useState<{ location: string; start_date: string; end_date: string } | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!city.trim()) {
      showError('Please enter a city name');
      return;
    }

    setLoading(true);
    setEvents([]);
    setSearchInfo(null);

    try {
      const result = await eventService.searchEvents({
        city: city.trim(),
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        category: category || undefined,
      });

      setEvents(result.results);
      setSearchInfo({
        location: result.location,
        start_date: result.start_date,
        end_date: result.end_date
      });
      showSuccess(`Found ${result.total} events in ${result.location}`);
    } catch (error: any) {
      showError(error.message || 'Failed to search events');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
        🎉 Events & Festivals
      </h1>
      <p className="text-gray-600 dark:text-gray-400 mb-8">
        Discover exciting local events, festivals, and happenings during your travel dates
      </p>

      {/* Search Form */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Search Events</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <Input
                  label="City or Location"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  placeholder="e.g., New York, Paris, Tokyo"
                  required
                />
              </div>

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

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Category (Optional)
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="">All Categories</option>
                  <option value="music">🎵 Music Concerts & Shows</option>
                  <option value="arts">🎨 Arts & Culture</option>
                  <option value="food">🍔 Food & Drink</option>
                  <option value="sports">⚽ Sports Events</option>
                  <option value="cultural">🎊 Cultural Celebrations</option>
                  <option value="festivals">🎉 Festivals & Fairs</option>
                </select>
              </div>
            </div>

            <Button type="submit" className="w-full" isLoading={loading} disabled={loading}>
              {loading ? 'Searching...' : '🔍 Search Events'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Loading State */}
      {loading && (
        <Card>
          <CardContent className="py-12">
            <Loading size="lg" text="Searching for events..." />
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {!loading && events.length > 0 && searchInfo && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Events in {searchInfo.location}
            </h2>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              {searchInfo.start_date} to {searchInfo.end_date}
              {category && (
                <>
                  {' '}• <span className="font-semibold capitalize">{category}</span>
                </>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6">
            {events.map((event, index) => (
              <EventCard key={index} event={event} />
            ))}
          </div>
        </div>
      )}

      {/* No Results */}
      {!loading && events.length === 0 && city && (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-gray-600 dark:text-gray-400 text-lg mb-2">
              No events found for "{city}"
              {category && ` in category "${category}"`}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-500">
              Try searching with different dates or category
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default EventsPage;
