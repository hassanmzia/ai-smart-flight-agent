import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useRequireAuth } from '@/hooks/useAuth';
import { Card } from '@/components/common';
import Button from '@/components/common/Button';
import { getItineraries, deleteItinerary } from '@/services/itineraryService';
import { formatDate } from '@/utils/formatters';
import {
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
  planned: { label: 'Planned', color: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-200', icon: '📋' },
  approved: { label: 'Approved', color: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-200', icon: '✅' },
  booking: { label: 'Booking...', color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-200', icon: '⏳' },
  booked: { label: 'Booked', color: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-200', icon: '🎫' },
  active: { label: 'Active', color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200', icon: '🚀' },
  completed: { label: 'Completed', color: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-200', icon: '🏁' },
  cancelled: { label: 'Cancelled', color: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200', icon: '❌' },
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
    <div className="min-h-screen">
      {/* Hero Header */}
      <div className="relative overflow-hidden bg-gradient-to-br from-orange-500 via-amber-500 to-yellow-500 dark:from-orange-800 dark:via-amber-800 dark:to-yellow-800">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute -top-10 -right-20 w-64 h-64 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 left-1/4 w-40 h-40 bg-yellow-300 rounded-full blur-3xl"></div>
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-white mb-2">
                My Trips
              </h1>
              <p className="text-orange-100 text-lg">
                {itineraries.length} trip{itineraries.length !== 1 ? 's' : ''} planned
              </p>
            </div>
            <button
              onClick={() => navigate('/ai-planner')}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white/20 backdrop-blur-sm border border-white/30 text-white font-semibold hover:bg-white/30 transition-all"
            >
              🤖 AI Planner
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6 relative z-10 pb-12">
        {/* Status Filter Tabs */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-1 -mx-1 px-1">
          {Object.entries(STATUS_CONFIG).map(([key, cfg]) => (
            <button
              key={key}
              onClick={() => setStatusFilter(key)}
              className={`flex items-center gap-1.5 px-4 py-2.5 rounded-xl font-medium text-sm whitespace-nowrap transition-all duration-200 ${
                statusFilter === key
                  ? 'bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-lg shadow-orange-500/25'
                  : 'bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm text-gray-700 dark:text-gray-300 hover:bg-white dark:hover:bg-gray-700 shadow-sm border border-gray-200/60 dark:border-gray-700/50'
              }`}
            >
              {cfg.icon && <span>{cfg.icon}</span>}
              {cfg.label}
            </button>
          ))}
        </div>

        {/* Itineraries List */}
        {itineraries.length === 0 ? (
          <Card variant="glass">
            <div className="text-center py-16">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-orange-100 to-amber-100 dark:from-orange-900/30 dark:to-amber-900/30 mb-5">
                <span className="text-4xl">🗺️</span>
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                {statusFilter ? `No ${statusFilter} trips` : 'No trips yet'}
              </h3>
              <p className="text-gray-500 dark:text-gray-400 mb-6 max-w-md mx-auto">
                {statusFilter
                  ? 'Try selecting a different status filter'
                  : 'Start planning your next adventure with our AI-powered trip planner!'}
              </p>
              <button
                onClick={() => navigate('/ai-planner')}
                className="px-6 py-3 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white font-semibold shadow-lg shadow-orange-500/25 transition-all"
              >
                🤖 Plan with AI
              </button>
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
                  padding="none"
                >
                  {/* Cover Image */}
                  {itinerary.cover_image ? (
                    <img
                      src={itinerary.cover_image}
                      alt={itinerary.title}
                      className="w-full h-44 object-cover"
                    />
                  ) : (
                    <div className="w-full h-44 bg-gradient-to-br from-orange-400 via-amber-400 to-yellow-400 dark:from-orange-600 dark:via-amber-600 dark:to-yellow-600 flex items-center justify-center">
                      <MapPinIcon className="h-14 w-14 text-white/40" />
                    </div>
                  )}

                  {/* Content */}
                  <div className="p-5">
                    {/* Status Badge */}
                    <div className="flex items-center justify-between mb-3">
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold ${getStatusColor(
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
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2 line-clamp-1 group-hover:text-orange-600 dark:group-hover:text-orange-400 transition-colors">
                      {itinerary.title}
                    </h3>

                    {/* Destination */}
                    <div className="flex items-center text-gray-500 dark:text-gray-400 mb-2">
                      <MapPinIcon className="h-4 w-4 mr-1.5 flex-shrink-0 text-orange-500" />
                      <span className="text-sm truncate">{itinerary.destination}</span>
                    </div>

                    {/* Dates */}
                    <div className="flex items-center text-gray-500 dark:text-gray-400 mb-3">
                      <CalendarIcon className="h-4 w-4 mr-1.5 flex-shrink-0" />
                      <span className="text-sm">
                        {formatDate(itinerary.start_date, 'MMM dd')} -{' '}
                        {formatDate(itinerary.end_date, 'MMM dd, yyyy')}
                      </span>
                      <span className="ml-2 text-xs bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 px-2 py-0.5 rounded-full font-medium">
                        {calculateDays(itinerary.start_date, itinerary.end_date)}d
                      </span>
                    </div>

                    {/* Meta row */}
                    <div className="flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400">
                      {itinerary.number_of_travelers > 0 && (
                        <div className="flex items-center gap-1">
                          <UserGroupIcon className="h-3.5 w-3.5" />
                          {itinerary.number_of_travelers}
                        </div>
                      )}
                      {itinerary.estimated_budget && (
                        <div className="flex items-center gap-0.5">
                          <CurrencyDollarIcon className="h-3.5 w-3.5" />
                          {Number(itinerary.estimated_budget).toLocaleString()} {itinerary.currency}
                        </div>
                      )}
                      {itinerary.actual_spent && Number(itinerary.actual_spent) > 0 && (
                        <div className="flex items-center text-emerald-600 dark:text-emerald-400 font-medium">
                          Spent: ${Number(itinerary.actual_spent).toLocaleString()}
                        </div>
                      )}
                    </div>

                    {/* Description */}
                    {itinerary.description && (
                      <p className="text-xs text-gray-400 dark:text-gray-500 line-clamp-2 mt-3 pt-3 border-t border-gray-100 dark:border-gray-700/50">
                        {itinerary.description}
                      </p>
                    )}
                  </div>

                  {/* Delete button overlay */}
                  <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                    {deleteConfirm === itinerary.id ? (
                      <div className="flex gap-1 bg-white/95 dark:bg-gray-800/95 backdrop-blur-sm rounded-xl shadow-xl p-1.5" onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={(e) => handleDelete(itinerary.id, e)}
                          disabled={deleting}
                          className="px-3 py-1.5 bg-red-600 text-white text-xs font-medium rounded-lg hover:bg-red-700 disabled:opacity-50"
                        >
                          {deleting ? '...' : 'Confirm'}
                        </button>
                        <button
                          onClick={cancelDelete}
                          className="px-3 py-1.5 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs rounded-lg hover:bg-gray-300"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={(e) => handleDelete(itinerary.id, e)}
                        className="p-2 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-xl shadow-lg hover:bg-red-50 dark:hover:bg-red-900/30 transition-colors"
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
    </div>
  );
};

export default ItineraryPage;
