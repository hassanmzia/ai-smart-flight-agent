import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useRequireAuth } from '@/hooks/useAuth';
import { Card, Button } from '@/components/common';
import { getItineraries } from '@/services/itineraryService';
import { formatDate } from '@/utils/formatters';
import {
  PlusIcon,
  MapPinIcon,
  CalendarIcon,
  UserGroupIcon,
  CurrencyDollarIcon,
} from '@heroicons/react/24/outline';
import type { Itinerary } from '@/types';

const ItineraryPage = () => {
  const { user } = useRequireAuth();
  const navigate = useNavigate();
  const [itineraries, setItineraries] = useState<Itinerary[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('');

  useEffect(() => {
    fetchItineraries();
  }, [statusFilter]);

  const fetchItineraries = async () => {
    try {
      setLoading(true);
      const data = await getItineraries(statusFilter);
      setItineraries(data);
    } catch (error) {
      console.error('Failed to fetch itineraries:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors = {
      draft: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
      planned: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      active: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      completed: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
      cancelled: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    };
    return colors[status as keyof typeof colors] || colors.draft;
  };

  const calculateDays = (startDate: string, endDate: string) => {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.abs(end.getTime() - start.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays + 1;
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          My Itineraries
        </h1>
        <Button
          onClick={() => navigate('/itineraries/new')}
          className="inline-flex items-center"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          Create Itinerary
        </Button>
      </div>

      {/* Status Filter */}
      <div className="flex gap-2 mb-6 overflow-x-auto">
        {['', 'draft', 'planned', 'active', 'completed', 'cancelled'].map((status) => (
          <button
            key={status}
            onClick={() => setStatusFilter(status)}
            className={`px-4 py-2 rounded-lg font-medium text-sm whitespace-nowrap transition-colors ${
              statusFilter === status
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
            }`}
          >
            {status === '' ? 'All' : status.charAt(0).toUpperCase() + status.slice(1)}
          </button>
        ))}
      </div>

      {/* Itineraries List */}
      {itineraries.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <MapPinIcon className="mx-auto h-16 w-16 text-gray-400 dark:text-gray-600 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No itineraries yet
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Start planning your next trip by creating an itinerary
            </p>
            <Button onClick={() => navigate('/itineraries/new')}>
              <PlusIcon className="h-5 w-5 mr-2" />
              Create Your First Itinerary
            </Button>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {itineraries.map((itinerary) => (
            <Card
              key={itinerary.id}
              hover
              onClick={() => navigate(`/itineraries/${itinerary.id}`)}
              className="cursor-pointer overflow-hidden"
            >
              {/* Cover Image */}
              {itinerary.cover_image ? (
                <img
                  src={itinerary.cover_image}
                  alt={itinerary.title}
                  className="w-full h-48 object-cover"
                />
              ) : (
                <div className="w-full h-48 bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center">
                  <MapPinIcon className="h-16 w-16 text-white opacity-50" />
                </div>
              )}

              {/* Content */}
              <div className="p-6">
                {/* Status Badge */}
                <span
                  className={`inline-block px-2 py-1 rounded-full text-xs font-medium mb-3 ${getStatusColor(
                    itinerary.status
                  )}`}
                >
                  {itinerary.status.charAt(0).toUpperCase() + itinerary.status.slice(1)}
                </span>

                {/* Title */}
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2 line-clamp-1">
                  {itinerary.title}
                </h3>

                {/* Destination */}
                <div className="flex items-center text-gray-600 dark:text-gray-400 mb-3">
                  <MapPinIcon className="h-4 w-4 mr-1" />
                  <span className="text-sm">{itinerary.destination}</span>
                </div>

                {/* Dates */}
                <div className="flex items-center text-gray-600 dark:text-gray-400 mb-3">
                  <CalendarIcon className="h-4 w-4 mr-1" />
                  <span className="text-sm">
                    {formatDate(itinerary.start_date, 'MMM DD')} -{' '}
                    {formatDate(itinerary.end_date, 'MMM DD, YYYY')}
                  </span>
                  <span className="ml-2 text-xs bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded">
                    {calculateDays(itinerary.start_date, itinerary.end_date)} days
                  </span>
                </div>

                {/* Travelers */}
                {itinerary.number_of_travelers > 0 && (
                  <div className="flex items-center text-gray-600 dark:text-gray-400 mb-3">
                    <UserGroupIcon className="h-4 w-4 mr-1" />
                    <span className="text-sm">
                      {itinerary.number_of_travelers}{' '}
                      {itinerary.number_of_travelers === 1 ? 'traveler' : 'travelers'}
                    </span>
                  </div>
                )}

                {/* Budget */}
                {itinerary.estimated_budget && (
                  <div className="flex items-center text-gray-600 dark:text-gray-400 mb-3">
                    <CurrencyDollarIcon className="h-4 w-4 mr-1" />
                    <span className="text-sm">
                      Budget: ${Number(itinerary.estimated_budget).toFixed(0)} {itinerary.currency}
                    </span>
                  </div>
                )}

                {/* Description */}
                {itinerary.description && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mt-3">
                    {itinerary.description}
                  </p>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default ItineraryPage;
