import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useRequireAuth } from '@/hooks/useAuth';
import { Card, Button } from '@/components/common';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // TODO: Implement API call to create/update itinerary
    console.log('Creating itinerary:', formData);

    // For now, just navigate back to the list
    alert('Itinerary creation is coming soon! This feature is under development.');
    navigate('/itinerary');
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

      {/* Form */}
      <Card>
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
            >
              Cancel
            </Button>
            <Button type="submit">
              {isNewItinerary ? 'Create Itinerary' : 'Save Changes'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};

export default ItineraryDetailPage;
