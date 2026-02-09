import { useState } from 'use';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Loading from '@/components/common/Loading';
import { useToast } from '@/hooks/useNotifications';
import { API_BASE_URL } from '@/utils/constants';

const AIPlannerPage = () => {
  const { showSuccess, showError } = useToast();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  // Form state
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [departureDate, setDepartureDate] = useState('');
  const [returnDate, setReturnDate] = useState('');
  const [passengers, setPassengers] = useState(1);
  const [budget, setBudget] = useState('');

  const handlePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/agents/plan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: `Plan a trip from ${origin} to ${destination}`,
          origin,
          destination,
          departure_date: departureDate,
          return_date: returnDate || undefined,
          passengers: Number(passengers),
          budget: budget ? Number(budget) : undefined,
        }),
      });

      const data = await response.json();

      if (data.success) {
        setResult(data);
        showSuccess('AI travel planning complete!');
      } else {
        showError(data.error || 'Planning failed');
      }
    } catch (error: any) {
      showError(error.message || 'Failed to connect to AI agent');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
        🤖 AI Travel Planner
      </h1>
      <p className="text-gray-600 dark:text-gray-400 mb-8">
        Let our AI agents find and evaluate the best travel options for you
      </p>

      {/* Planning Form */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Travel Details</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handlePlan} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Origin (Airport Code)"
                value={origin}
                onChange={(e) => setOrigin(e.target.value)}
                placeholder="e.g., JFK, CDG, LHR"
                required
              />
              <Input
                label="Destination (Airport Code)"
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
                placeholder="e.g., LAX, BER, NRT"
                required
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Departure Date"
                type="date"
                value={departureDate}
                onChange={(e) => setDepartureDate(e.target.value)}
                required
              />
              <Input
                label="Return Date (Optional)"
                type="date"
                value={returnDate}
                onChange={(e) => setReturnDate(e.target.value)}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Passengers"
                type="number"
                min="1"
                value={passengers}
                onChange={(e) => setPassengers(Number(e.target.value))}
                required
              />
              <Input
                label="Budget (USD, Optional)"
                type="number"
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
                placeholder="e.g., 500"
              />
            </div>

            <Button
              type="submit"
              className="w-full"
              size="lg"
              isLoading={loading}
              disabled={loading}
            >
              {loading ? 'AI Agents Working...' : '🚀 Plan My Trip with AI'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Loading State */}
      {loading && (
        <Card>
          <CardContent className="py-12">
            <Loading size="lg" text="AI agents are analyzing your request..." />
            <div className="mt-4 text-center text-sm text-gray-600 dark:text-gray-400">
              <p>✈️ Flight Agent searching for best flights...</p>
              <p>🏨 Hotel Agent finding accommodations...</p>
              <p>💰 Budget Agent optimizing costs...</p>
              <p>🎯 Recommendation Agent compiling results...</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {result && result.success && (
        <div className="space-y-6">
          {/* Summary */}
          <Card>
            <CardHeader>
              <CardTitle>✨ AI Recommendation</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Flights Found</p>
                    <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                      {result.recommendation?.summary?.flights_found || 0}
                    </p>
                  </div>
                  <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Hotels Found</p>
                    <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                      {result.recommendation?.summary?.hotels_found || 0}
                    </p>
                  </div>
                  <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Est. Total Cost</p>
                    <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                      ${result.recommendation?.total_estimated_cost || 'N/A'}
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Recommended Flight */}
          {result.recommendation?.recommended_flight && (
            <Card>
              <CardHeader>
                <CardTitle>💎 Best Flight (Within Budget)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <p><strong>Airline:</strong> {result.recommendation.recommended_flight.airline}</p>
                  <p><strong>Price:</strong> ${result.recommendation.recommended_flight.price}</p>
                  <p><strong>Departure:</strong> {result.recommendation.recommended_flight.departure_time}</p>
                  <p><strong>Arrival:</strong> {result.recommendation.recommended_flight.arrival_time}</p>
                  <p><strong>Duration:</strong> {result.recommendation.recommended_flight.total_duration} min</p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Top Hotels */}
          {result.recommendation?.top_5_hotels && result.recommendation.top_5_hotels.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>🏨 Top 5 Hotels (by Utility Score)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {result.recommendation.top_5_hotels.map((hotel: any, idx: number) => (
                    <div key={idx} className="border-l-4 border-blue-500 pl-4 py-2">
                      <h4 className="font-semibold">{hotel.name}</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {'⭐'.repeat(hotel.stars || 3)} | ${hotel.price}/night | 
                        Utility Score: {hotel.utility_score}
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Agent Messages */}
          {result.messages && result.messages.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>🤖 Agent Activity Log</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {result.messages.map((msg: string, idx: number) => (
                    <p key={idx} className="text-sm text-gray-600 dark:text-gray-400">
                      • {msg}
                    </p>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
};

export default AIPlannerPage;
