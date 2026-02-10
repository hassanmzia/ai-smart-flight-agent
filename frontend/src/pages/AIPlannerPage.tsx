import { useState } from 'react';
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

          {/* Recommended Flight - Enhanced */}
          {result.recommendation?.recommended_flight && (
            <Card>
              <CardHeader>
                <CardTitle>✈️ Recommended Flight</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Airline and Price Header */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {result.recommendation.recommended_flight.airline_logo && (
                        <img
                          src={result.recommendation.recommended_flight.airline_logo}
                          alt={result.recommendation.recommended_flight.airline}
                          className="h-8 w-8 object-contain"
                        />
                      )}
                      <div>
                        <h3 className="font-semibold text-lg">
                          {result.recommendation.recommended_flight.airline}
                        </h3>
                        {result.recommendation.recommended_flight.flight_number && (
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            Flight {result.recommendation.recommended_flight.flight_number}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-primary-600 dark:text-primary-400">
                        ${result.recommendation.recommended_flight.price}
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">per person</p>
                    </div>
                  </div>

                  {/* Flight Route */}
                  <div className="grid grid-cols-3 gap-4 items-center py-4 border-t border-b">
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Departure</p>
                      <p className="text-lg font-semibold">
                        {result.recommendation.recommended_flight.departure_time?.split(' ')[1] || result.recommendation.recommended_flight.departure_time}
                      </p>
                      <p className="text-sm font-medium">
                        {result.recommendation.recommended_flight.departure_airport_code}
                      </p>
                      <p className="text-xs text-gray-600 dark:text-gray-400">
                        {result.recommendation.recommended_flight.departure_airport}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {result.recommendation.recommended_flight.duration
                          ? `${Math.floor(result.recommendation.recommended_flight.duration / 60)}h ${result.recommendation.recommended_flight.duration % 60}m`
                          : 'N/A'}
                      </p>
                      <div className="flex items-center justify-center my-2">
                        <div className="h-px bg-gray-300 dark:bg-gray-600 flex-1"></div>
                        <span className="mx-2 text-gray-400">✈️</span>
                        <div className="h-px bg-gray-300 dark:bg-gray-600 flex-1"></div>
                      </div>
                      <p className="text-xs text-gray-600 dark:text-gray-400">
                        {result.recommendation.recommended_flight.stops === 0
                          ? 'Nonstop'
                          : `${result.recommendation.recommended_flight.stops} stop${result.recommendation.recommended_flight.stops > 1 ? 's' : ''}`
                        }
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-600 dark:text-gray-400">Arrival</p>
                      <p className="text-lg font-semibold">
                        {result.recommendation.recommended_flight.arrival_time?.split(' ')[1] || result.recommendation.recommended_flight.arrival_time}
                      </p>
                      <p className="text-sm font-medium">
                        {result.recommendation.recommended_flight.arrival_airport_code}
                      </p>
                      <p className="text-xs text-gray-600 dark:text-gray-400">
                        {result.recommendation.recommended_flight.arrival_airport}
                      </p>
                    </div>
                  </div>

                  {/* Additional Details */}
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                    {result.recommendation.recommended_flight.aircraft && (
                      <div>
                        <p className="text-gray-600 dark:text-gray-400">Aircraft</p>
                        <p className="font-medium">{result.recommendation.recommended_flight.aircraft}</p>
                      </div>
                    )}
                    {result.recommendation.recommended_flight.travel_class && (
                      <div>
                        <p className="text-gray-600 dark:text-gray-400">Class</p>
                        <p className="font-medium">{result.recommendation.recommended_flight.travel_class}</p>
                      </div>
                    )}
                    {result.recommendation.recommended_flight.legroom && (
                      <div>
                        <p className="text-gray-600 dark:text-gray-400">Legroom</p>
                        <p className="font-medium">{result.recommendation.recommended_flight.legroom}</p>
                      </div>
                    )}
                  </div>

                  {/* Carbon Emissions */}
                  {result.recommendation.recommended_flight.carbon_emissions?.this_flight && (
                    <div className="bg-green-50 dark:bg-green-900/20 p-3 rounded-lg">
                      <p className="text-sm text-green-800 dark:text-green-200">
                        🌱 Carbon emissions: {result.recommendation.recommended_flight.carbon_emissions.this_flight} kg CO₂
                        {result.recommendation.recommended_flight.carbon_emissions.difference_percent && (
                          <span className="ml-2">
                            ({result.recommendation.recommended_flight.carbon_emissions.difference_percent > 0 ? '+' : ''}
                            {result.recommendation.recommended_flight.carbon_emissions.difference_percent}% vs typical)
                          </span>
                        )}
                      </p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Recommended Hotel - Enhanced */}
          {result.recommendation?.recommended_hotel && (
            <Card>
              <CardHeader>
                <CardTitle>🏨 Recommended Hotel</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Hotel Image and Info */}
                  <div className="flex flex-col md:flex-row gap-4">
                    {/* Hotel Image */}
                    {result.recommendation.recommended_hotel.images?.[0] && (
                      <img
                        src={result.recommendation.recommended_hotel.images[0]}
                        alt={result.recommendation.recommended_hotel.name || result.recommendation.recommended_hotel.hotel_name}
                        className="w-full md:w-64 h-48 object-cover rounded-lg"
                      />
                    )}

                    {/* Hotel Details */}
                    <div className="flex-1 space-y-2">
                      <div>
                        <h3 className="text-xl font-semibold">
                          {result.recommendation.recommended_hotel.name || result.recommendation.recommended_hotel.hotel_name}
                        </h3>
                        <div className="flex items-center gap-2 mt-1">
                          <div className="text-yellow-500">
                            {'⭐'.repeat(Math.round(result.recommendation.recommended_hotel.stars || result.recommendation.recommended_hotel.star_rating || 0))}
                          </div>
                          {result.recommendation.recommended_hotel.guest_rating > 0 && (
                            <span className="text-sm text-gray-600 dark:text-gray-400">
                              ({result.recommendation.recommended_hotel.guest_rating} reviews)
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Price and Rates */}
                      <div className="bg-primary-50 dark:bg-primary-900/20 p-4 rounded-lg space-y-2">
                        <div className="flex items-baseline gap-2">
                          <p className="text-3xl font-bold text-primary-600 dark:text-primary-400">
                            ${result.recommendation.recommended_hotel.price || result.recommendation.recommended_hotel.price_per_night}
                          </p>
                          <span className="text-sm text-gray-600 dark:text-gray-400">/night</span>
                        </div>
                        {result.recommendation.recommended_hotel.total_rate && result.recommendation.recommended_hotel.total_rate > 0 && (
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            Total stay: <span className="font-medium">${result.recommendation.recommended_hotel.total_rate}</span>
                          </p>
                        )}
                        <div className="pt-2 border-t border-primary-200 dark:border-primary-800">
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            Utility Score: <span className="font-medium">{result.recommendation.recommended_hotel.utility_score || result.recommendation.recommended_hotel.combined_utility_score}</span>
                          </p>
                          {result.recommendation.recommended_hotel.recommendation && (
                            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                              {result.recommendation.recommended_hotel.recommendation}
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Hotel Details Grid */}
                      <div className="grid grid-cols-2 gap-3 text-sm border-t border-gray-200 dark:border-gray-700 pt-3">
                        {result.recommendation.recommended_hotel.check_in_time && (
                          <div>
                            <p className="text-gray-600 dark:text-gray-400">Check-in</p>
                            <p className="font-medium">{result.recommendation.recommended_hotel.check_in_time}</p>
                          </div>
                        )}
                        {result.recommendation.recommended_hotel.check_out_time && (
                          <div>
                            <p className="text-gray-600 dark:text-gray-400">Check-out</p>
                            <p className="font-medium">{result.recommendation.recommended_hotel.check_out_time}</p>
                          </div>
                        )}
                        {result.recommendation.recommended_hotel.distance_from_center && (
                          <div>
                            <p className="text-gray-600 dark:text-gray-400">Location</p>
                            <p className="font-medium">{result.recommendation.recommended_hotel.distance_from_center}</p>
                          </div>
                        )}
                        {result.recommendation.recommended_hotel.guest_rating > 0 && (
                          <div>
                            <p className="text-gray-600 dark:text-gray-400">Guest Rating</p>
                            <p className="font-medium">{result.recommendation.recommended_hotel.guest_rating} reviews</p>
                          </div>
                        )}
                      </div>

                      {/* Address */}
                      {result.recommendation.recommended_hotel.address && (
                        <div className="border-t border-gray-200 dark:border-gray-700 pt-3">
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            📍 {result.recommendation.recommended_hotel.address}
                          </p>
                        </div>
                      )}

                      {/* Amenities */}
                      {result.recommendation.recommended_hotel.amenities && result.recommendation.recommended_hotel.amenities.length > 0 && (
                        <div className="border-t border-gray-200 dark:border-gray-700 pt-3">
                          <p className="text-sm font-medium mb-2">Amenities & Features:</p>
                          <div className="flex flex-wrap gap-2">
                            {result.recommendation.recommended_hotel.amenities.slice(0, 12).map((amenity: string, idx: number) => (
                              <span
                                key={idx}
                                className="text-xs bg-gray-100 dark:bg-gray-800 px-3 py-1.5 rounded-full"
                              >
                                {amenity}
                              </span>
                            ))}
                            {result.recommendation.recommended_hotel.amenities.length > 12 && (
                              <span className="text-xs text-gray-600 dark:text-gray-400 px-3 py-1.5">
                                +{result.recommendation.recommended_hotel.amenities.length - 12} more
                              </span>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Booking Link */}
                      {result.recommendation.recommended_hotel.link && (
                        <a
                          href={result.recommendation.recommended_hotel.link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-block text-sm text-primary-600 dark:text-primary-400 hover:underline"
                        >
                          View on booking site →
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Alternative Hotels */}
          {result.recommendation?.top_5_hotels && result.recommendation.top_5_hotels.length > 1 && (
            <Card>
              <CardHeader>
                <CardTitle>🏨 Alternative Hotels</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {result.recommendation.top_5_hotels.slice(1, 5).map((hotel: any, idx: number) => (
                    <div key={idx} className="flex gap-3 p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-primary-500 transition-colors">
                      {/* Hotel Thumbnail */}
                      {hotel.images?.[0] && (
                        <img
                          src={hotel.images[0]}
                          alt={hotel.name || hotel.hotel_name}
                          className="w-24 h-24 object-cover rounded"
                        />
                      )}

                      {/* Hotel Info */}
                      <div className="flex-1">
                        <h4 className="font-semibold">{hotel.name || hotel.hotel_name}</h4>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          <span className="text-yellow-500">
                            {'⭐'.repeat(Math.round(hotel.stars || hotel.star_rating || 0))}
                          </span>
                          <span className="mx-2">•</span>
                          <span className="font-medium">${hotel.price || hotel.price_per_night}/night</span>
                          <span className="mx-2">•</span>
                          <span>Score: {hotel.utility_score || hotel.combined_utility_score}</span>
                        </div>
                      </div>
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
