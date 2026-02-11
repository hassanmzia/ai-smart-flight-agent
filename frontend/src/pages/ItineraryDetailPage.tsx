import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useRequireAuth } from '@/hooks/useAuth';
import { Card, Button } from '@/components/common';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';
import { createItinerary, getItinerary, updateItinerary } from '@/services/itineraryService';
import toast from 'react-hot-toast';

const ItineraryDetailPage = () => {
  const { user } = useRequireAuth();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isNewItinerary = id === 'new';

  const [formData, setFormData] = useState({
    title: '',
    destination: '',
    start_date: '',
    end_date: '',
    description: '',
    number_of_travelers: 1,
    estimated_budget: '',
    currency: 'USD',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isNewItinerary && id) {
      // Load existing itinerary for editing
      loadItinerary(id);
    }
  }, [id, isNewItinerary]);

  const loadItinerary = async (itineraryId: string) => {
    try {
      setLoading(true);
      const data = await getItinerary(itineraryId);
      setFormData({
        title: data.title,
        destination: data.destination,
        start_date: data.start_date,
        end_date: data.end_date,
        description: data.description || '',
        number_of_travelers: data.number_of_travelers,
        estimated_budget: data.estimated_budget || '',
        currency: data.currency || 'USD',
      });
    } catch (err) {
      console.error('Failed to load itinerary:', err);
      toast.error('Failed to load itinerary');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Form submitted with data:', formData);
    console.log('id:', id);
    console.log('isNewItinerary:', isNewItinerary);

    setLoading(true);
    setError(null);

    try {
      if (isNewItinerary) {
        // Create new itinerary
        console.log('Creating new itinerary...');
        const dataWithUser = {
          ...formData,
          user: String(user.id), // Add the authenticated user's ID as string
          status: 'planned', // Set default status to 'planned'
        };
        const result = await createItinerary(dataWithUser);
        console.log('Itinerary created:', result);
        toast.success('Itinerary created successfully!');
      } else if (id) {
        // Update existing itinerary
        console.log('Updating itinerary...', id);
        const result = await updateItinerary(id, formData);
        console.log('Itinerary updated:', result);
        toast.success('Itinerary updated successfully!');
      }
      console.log('Navigating to /itinerary');
      navigate('/itinerary');
    } catch (err: any) {
      console.error('Failed to save itinerary - Full error:', err);
      console.error('Error message:', err.message);
      console.error('Error response:', err.response);
      console.error('Error data:', err.response?.data);

      // The axios interceptor transforms errors, so check both formats
      let errorMessage = 'Failed to save itinerary';

      if (err.response?.data?.message) {
        errorMessage = err.response.data.message;
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err.response?.data) {
        // If data is an object with field errors, format them
        if (typeof err.response.data === 'object') {
          const errors = Object.entries(err.response.data)
            .map(([field, msgs]) => `${field}: ${Array.isArray(msgs) ? msgs.join(', ') : msgs}`)
            .join('; ');
          errorMessage = errors || errorMessage;
        }
      } else if (err.message) {
        errorMessage = err.message;
      }

      console.error('Parsed error message:', errorMessage);
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <Button
          variant="ghost"
          onClick={() => navigate('/itinerary')}
          className="mb-4"
        >
          <ArrowLeftIcon className="h-5 w-5 mr-2" />
          Back to Itineraries
        </Button>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          {isNewItinerary ? 'Create New Itinerary' : 'Edit Itinerary'}
        </h1>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}

      {/* Form */}
      <Card>
        {loading && !formData.title ? (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
          {/* Title */}
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Trip Title *
            </label>
            <input
              type="text"
              id="title"
              name="title"
              required
              value={formData.title}
              onChange={handleChange}
              placeholder="e.g., Summer Vacation to Paris"
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:text-white"
            />
          </div>

          {/* Destination */}
          <div>
            <label htmlFor="destination" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Destination *
            </label>
            <input
              type="text"
              id="destination"
              name="destination"
              required
              value={formData.destination}
              onChange={handleChange}
              placeholder="e.g., Paris, France"
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:text-white"
            />
          </div>

          {/* Dates */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="start_date" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Start Date *
              </label>
              <input
                type="date"
                id="start_date"
                name="start_date"
                required
                value={formData.start_date}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:text-white"
              />
            </div>
            <div>
              <label htmlFor="end_date" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                End Date *
              </label>
              <input
                type="date"
                id="end_date"
                name="end_date"
                required
                value={formData.end_date}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:text-white"
              />
            </div>
          </div>

          {/* Travelers and Budget */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="number_of_travelers" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Number of Travelers
              </label>
              <input
                type="number"
                id="number_of_travelers"
                name="number_of_travelers"
                min="1"
                value={formData.number_of_travelers}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:text-white"
              />
            </div>
            <div>
              <label htmlFor="estimated_budget" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Estimated Budget
              </label>
              <div className="flex gap-2">
                <input
                  type="number"
                  id="estimated_budget"
                  name="estimated_budget"
                  min="0"
                  step="0.01"
                  value={formData.estimated_budget}
                  onChange={handleChange}
                  placeholder="1000"
                  className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:text-white"
                />
                <select
                  name="currency"
                  value={formData.currency}
                  onChange={handleChange}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:text-white"
                >
                  <option value="USD">USD</option>
                  <option value="EUR">EUR</option>
                  <option value="GBP">GBP</option>
                  <option value="JPY">JPY</option>
                  <option value="CAD">CAD</option>
                  <option value="AUD">AUD</option>
                </select>
              </div>
            </div>
          </div>

          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Description
            </label>
            <textarea
              id="description"
              name="description"
              rows={4}
              value={formData.description}
              onChange={handleChange}
              placeholder="Describe your trip plans..."
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:text-white"
            />
          </div>

          {/* Buttons */}
          <div className="flex gap-4 justify-end">
            <Button
              type="button"
              variant="secondary"
              onClick={() => navigate('/itinerary')}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Saving...' : (isNewItinerary ? 'Create Itinerary' : 'Save Changes')}
            </Button>
          </div>
        </form>
        )}
      </Card>
    </div>
  );
};

export default ItineraryDetailPage;
