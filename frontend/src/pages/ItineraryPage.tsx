import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useRequireAuth } from '@/hooks/useAuth';
import { Card, Button } from '@/components/common';
import { getItineraries, deleteItinerary } from '@/services/itineraryService';
import { formatDate } from '@/utils/formatters';
import {
  PlusIcon,
  MapPinIcon,
  CalendarIcon,
  UserGroupIcon,
  CurrencyDollarIcon,
  TrashIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import type { Itinerary } from '@/types';
import toast from 'react-hot-toast';

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: string }> = {
  '': { label: 'All', color: 'bg-gray-600 text-white', icon: '' },
  draft: { label: 'Draft', color: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300', icon: '📝' },
  planned: { label: 'Planned', color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200', icon: '📋' },
  approved: { label: 'Approved', color: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200', icon: '✅' },
  booking: { label: 'Booking...', color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200', icon: '⏳' },
  booked: { label: 'Booked', color: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200', icon: '🎫' },
  active: { label: 'Active', color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200', icon: '🚀' },
  completed: { label: 'Completed', color: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200', icon: '🏁' },
  cancelled: { label: 'Cancelled', color: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200', icon: '❌' },
};

const ItineraryPage = () => {
  const { user } = useRequireAuth();
  const navigate = useNavigate();
  const [itineraries, setItineraries] = useState<Itinerary[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

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

  const handleDelete = async (itineraryId: string, e: React.MouseEvent) => {
    e.stopPropagation();

    if (deleteConfirm !== itineraryId) {
      setDeleteConfirm(itineraryId);
      return;
    }

    setDeleting(true);
    try {
      await deleteItinerary(itineraryId);
      setItineraries((prev) => prev.filter((i) => i.id !== itineraryId));
      toast.success('Trip deleted');
      setDeleteConfirm(null);
    } catch (err: any) {
      toast.error(err.message || 'Failed to delete trip');
    } finally {
      setDeleting(false);
    }
  };

  const cancelDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    setDeleteConfirm(null);
  };

  const getStatusColor = (s: string) => STATUS_CONFIG[s]?.color || STATUS_CONFIG.draft.color;

  const calculateDays = (startDate: string, endDate: string) => {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.abs(end.getTime() - start.getTime());
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
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
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            My Trips
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {itineraries.length} trip{itineraries.length !== 1 ? 's' : ''}
          </p>
        </div>
        <div className="flex gap-3">
          <Button
            onClick={() => navigate('/ai-planner')}
            variant="secondary"
            className="inline-flex items-center"
          >
            🤖 AI Planner
          </Button>
          <Button
            onClick={() => navigate('/itineraries/new')}
            className="inline-flex items-center"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            New Trip
          </Button>
        </div>
      </div>

      {/* Status Filter Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-1">
        {Object.entries(STATUS_CONFIG).map(([key, cfg]) => (
          <button
            key={key}
            onClick={() => setStatusFilter(key)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg font-medium text-sm whitespace-nowrap transition-colors ${
              statusFilter === key
                ? 'bg-primary-600 text-white shadow-md'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
            }`}
          >
            {cfg.icon && <span>{cfg.icon}</span>}
            {cfg.label}
          </button>
        ))}
      </div>

      {/* Itineraries List */}
      {itineraries.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <MapPinIcon className="mx-auto h-16 w-16 text-gray-400 dark:text-gray-600 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              {statusFilter ? `No ${statusFilter} trips` : 'No trips yet'}
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              {statusFilter
                ? 'Try selecting a different status filter'
                : 'Start planning your next adventure!'}
            </p>
            <div className="flex gap-3 justify-center">
              <Button onClick={() => navigate('/ai-planner')}>
                🤖 Plan with AI
              </Button>
              <Button variant="secondary" onClick={() => navigate('/itineraries/new')}>
                <PlusIcon className="h-5 w-5 mr-2" />
                Create Manually
              </Button>
            </div>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {itineraries.map((itinerary) => (
            <div
              key={itinerary.id}
              className="relative group"
            >
              <Card
                hover
                onClick={() => navigate(`/itineraries/${itinerary.id}`)}
                className="cursor-pointer overflow-hidden h-full"
              >
                {/* Cover Image */}
                {itinerary.cover_image ? (
                  <img
                    src={itinerary.cover_image}
                    alt={itinerary.title}
                    className="w-full h-44 object-cover"
                  />
                ) : (
                  <div className="w-full h-44 bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center">
                    <MapPinIcon className="h-14 w-14 text-white opacity-50" />
                  </div>
                )}

                {/* Content */}
                <div className="p-5">
                  {/* Status Badge */}
                  <div className="flex items-center justify-between mb-3">
                    <span
                      className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${getStatusColor(
                        itinerary.status
                      )}`}
                    >
                      {STATUS_CONFIG[itinerary.status]?.icon}{' '}
                      {STATUS_CONFIG[itinerary.status]?.label || itinerary.status}
                    </span>
                    {itinerary.status === 'booked' && (
                      <CheckCircleIcon className="h-5 w-5 text-green-500" />
                    )}
                  </div>

                  {/* Title */}
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2 line-clamp-1">
                    {itinerary.title}
                  </h3>

                  {/* Destination */}
                  <div className="flex items-center text-gray-600 dark:text-gray-400 mb-2">
                    <MapPinIcon className="h-4 w-4 mr-1 flex-shrink-0" />
                    <span className="text-sm truncate">{itinerary.destination}</span>
                  </div>

                  {/* Dates */}
                  <div className="flex items-center text-gray-600 dark:text-gray-400 mb-2">
                    <CalendarIcon className="h-4 w-4 mr-1 flex-shrink-0" />
                    <span className="text-sm">
                      {formatDate(itinerary.start_date, 'MMM dd')} -{' '}
                      {formatDate(itinerary.end_date, 'MMM dd, yyyy')}
                    </span>
                    <span className="ml-2 text-xs bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded">
                      {calculateDays(itinerary.start_date, itinerary.end_date)}d
                    </span>
                  </div>

                  {/* Meta row */}
                  <div className="flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400">
                    {itinerary.number_of_travelers > 0 && (
                      <div className="flex items-center">
                        <UserGroupIcon className="h-3.5 w-3.5 mr-1" />
                        {itinerary.number_of_travelers}
                      </div>
                    )}
                    {itinerary.estimated_budget && (
                      <div className="flex items-center">
                        <CurrencyDollarIcon className="h-3.5 w-3.5 mr-0.5" />
                        {Number(itinerary.estimated_budget).toLocaleString()} {itinerary.currency}
                      </div>
                    )}
                    {itinerary.actual_spent && Number(itinerary.actual_spent) > 0 && (
                      <div className="flex items-center text-green-600 dark:text-green-400 font-medium">
                        Spent: ${Number(itinerary.actual_spent).toLocaleString()}
                      </div>
                    )}
                  </div>

                  {/* Description */}
                  {itinerary.description && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 mt-2">
                      {itinerary.description}
                    </p>
                  )}
                </div>

                {/* Delete button overlay */}
                <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                  {deleteConfirm === itinerary.id ? (
                    <div className="flex gap-1 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-1.5" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={(e) => handleDelete(itinerary.id, e)}
                        disabled={deleting}
                        className="px-3 py-1.5 bg-red-600 text-white text-xs font-medium rounded-md hover:bg-red-700 disabled:opacity-50"
                      >
                        {deleting ? '...' : 'Confirm'}
                      </button>
                      <button
                        onClick={cancelDelete}
                        className="px-3 py-1.5 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs rounded-md hover:bg-gray-300"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={(e) => handleDelete(itinerary.id, e)}
                      className="p-2 bg-white/90 dark:bg-gray-800/90 rounded-full shadow-lg hover:bg-red-50 dark:hover:bg-red-900/30 transition-colors"
                      title="Delete trip"
                    >
                      <TrashIcon className="h-4 w-4 text-red-500" />
                    </button>
                  )}
                </div>
              </Card>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ItineraryPage;
