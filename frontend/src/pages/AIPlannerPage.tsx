import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Loading from '@/components/common/Loading';
import { useToast } from '@/hooks/useNotifications';
import { useAuth } from '@/hooks/useAuth';
import { API_BASE_URL } from '@/utils/constants';
import {
  createItinerary,
  createItineraryDay,
  createItineraryItem,
} from '@/services/itineraryService';

interface ParsedActivity {
  time: string | undefined;
  title: string;
  itemType: 'flight' | 'hotel' | 'restaurant' | 'attraction' | 'activity' | 'transport' | 'note';
  estimatedCost: number | undefined;
}

interface ParsedDay {
  dayNumber: number;
  title: string;
  activities: ParsedActivity[];
}

/**
 * Parse the LLM-generated markdown itinerary into structured day/activity data.
 */
function parseItineraryNarrative(text: string): ParsedDay[] {
  if (!text) return [];

  const days: ParsedDay[] = [];
  // Split by day headings: ## Day N: ... or ## Day N - ...
  const dayPattern = /^##\s*Day\s+(\d+)\s*[:\-–]\s*(.*)$/gm;
  const matches: { index: number; dayNum: number; title: string }[] = [];

  let match;
  while ((match = dayPattern.exec(text)) !== null) {
    matches.push({ index: match.index, dayNum: parseInt(match[1]), title: match[2].trim() });
  }

  for (let i = 0; i < matches.length; i++) {
    const start = matches[i].index;
    const end = i + 1 < matches.length ? matches[i + 1].index : text.length;
    const section = text.slice(start, end);

    const activities: ParsedActivity[] = [];

    // Extract time-based lines: "8:00 AM - Activity" or "**8:00 AM** - Activity"
    const timePattern = /\*{0,2}(\d{1,2}:\d{2}\s*[AaPp][Mm]?)\*{0,2}\s*[-–:]\s*(.+)/g;
    let timeMatch;
    while ((timeMatch = timePattern.exec(section)) !== null) {
      const timeStr = timeMatch[1].trim();
      let activityText = timeMatch[2].trim()
        .replace(/\*\*/g, '')
        .replace(/\*/g, '');

      // Extract cost if present: ($XX) or ~$XX or $XX
      let cost: number | undefined;
      const costMatch = activityText.match(/[\(~]*\$(\d+(?:\.\d+)?)\)?/);
      if (costMatch) {
        cost = parseFloat(costMatch[1]);
      }

      const itemType = guessItemType(activityText);
      activities.push({ time: timeStr, title: activityText, itemType, estimatedCost: cost });
    }

    // Also extract bullet points that aren't time-based (- Activity or * Activity)
    const bulletPattern = /^[-*•]\s+(?!\d{1,2}:\d{2})(.+)/gm;
    let bulletMatch;
    while ((bulletMatch = bulletPattern.exec(section)) !== null) {
      const text = bulletMatch[1].trim().replace(/\*\*/g, '').replace(/\*/g, '');
      // Skip if we already captured this as a time line
      if (activities.some(a => text.includes(a.title.slice(0, 20)))) continue;
      // Skip markdown headers and separators
      if (text.startsWith('#') || text.startsWith('---')) continue;

      let cost: number | undefined;
      const costMatch = text.match(/[\(~]*\$(\d+(?:\.\d+)?)\)?/);
      if (costMatch) cost = parseFloat(costMatch[1]);

      const itemType = guessItemType(text);
      activities.push({ time: undefined, title: text, itemType, estimatedCost: cost });
    }

    days.push({
      dayNumber: matches[i].dayNum,
      title: matches[i].title,
      activities,
    });
  }

  return days;
}

function guessItemType(text: string): ParsedActivity['itemType'] {
  const lower = text.toLowerCase();
  if (/\b(flight|fly|airport|depart|land|board)\b/.test(lower)) return 'flight';
  if (/\b(check.?in|check.?out|hotel|hostel|airbnb|accommodation|lodge|resort)\b/.test(lower)) return 'hotel';
  if (/\b(breakfast|lunch|dinner|brunch|restaurant|cafe|eat|dine|dining|food|meal|cuisine)\b/.test(lower)) return 'restaurant';
  if (/\b(museum|monument|palace|cathedral|tower|temple|castle|gallery|park|garden|landmark|visit|tour|sightsee|explore|attraction)\b/.test(lower)) return 'attraction';
  if (/\b(taxi|uber|metro|subway|bus|train|tram|drive|car|transfer|commute|ride|transit)\b/.test(lower)) return 'transport';
  return 'activity';
}

const AIPlannerPage = () => {
  const navigate = useNavigate();
  const { showSuccess, showError } = useToast();
  const { isAuthenticated, user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState<any>(null);

  // Form state
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [departureDate, setDepartureDate] = useState('');
  const [returnDate, setReturnDate] = useState('');
  const [passengers, setPassengers] = useState(1);
  const [budget, setBudget] = useState('');
  const [cuisine, setCuisine] = useState('');

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
          cuisine: cuisine || undefined,
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

  const handleSaveAsItinerary = async () => {
    if (!result || !isAuthenticated || !user) {
      showError('Please log in to save itineraries');
      return;
    }

    setSaving(true);
    try {
      const start = departureDate;
      const end = returnDate || departureDate;
      const totalCost = result.recommendation?.total_estimated_cost;
      const rec = result.recommendation;

      // Parse the LLM narrative into structured days
      const parsedDays = parseItineraryNarrative(result.itinerary_text || '');

      // Calculate trip duration
      const startD = new Date(start);
      const endD = new Date(end);
      const totalDays = Math.max(1, Math.ceil((endD.getTime() - startD.getTime()) / (1000 * 60 * 60 * 24)) + 1);

      // Create itinerary
      const itinerary = await createItinerary({
        title: `AI Trip: ${origin} to ${destination}`,
        destination: destination,
        start_date: start,
        end_date: end,
        user: String(user.id),
        status: 'planned',
        number_of_travelers: passengers,
        estimated_budget: totalCost ? String(totalCost) : (budget ? budget : undefined),
        currency: 'USD',
        description: `AI-planned trip from ${origin} to ${destination}. ${passengers} passenger(s).`,
      });

      const itineraryId = Number(itinerary.id);

      // Create all days and populate with activities from parsed narrative
      for (let d = 1; d <= totalDays; d++) {
        const dayDate = new Date(startD);
        dayDate.setDate(dayDate.getDate() + d - 1);
        const dateStr = dayDate.toISOString().split('T')[0];

        // Find parsed day data from LLM narrative
        const parsedDay = parsedDays.find(p => p.dayNumber === d);
        const isFirstDay = d === 1;
        const isLastDay = d === totalDays;

        let dayTitle = parsedDay?.title
          || (isFirstDay ? `Arrival in ${destination}` : isLastDay ? 'Departure Day' : `Explore ${destination}`);

        const day = await createItineraryDay({
          itinerary: itineraryId,
          day_number: d,
          date: dateStr,
          title: dayTitle,
        });

        const dayId = day.id!;
        let itemOrder = 0;

        // For Day 1, also add structured data from search agents (flight, hotel check-in)
        if (isFirstDay) {
          if (rec?.recommended_flight) {
            const flight = rec.recommended_flight;
            await createItineraryItem({
              day: dayId,
              item_type: 'flight',
              order: itemOrder++,
              title: `${flight.airline} ${flight.flight_number || ''} - ${flight.departure_airport_code || origin} to ${flight.arrival_airport_code || destination}`,
              description: `${flight.stops === 0 ? 'Nonstop' : `${flight.stops} stop(s)`}${flight.duration ? ` · ${Math.floor(flight.duration / 60)}h ${flight.duration % 60}m` : ''}`,
              start_time: flight.departure_time?.split(' ')[1]?.slice(0, 5) || undefined,
              estimated_cost: flight.price || undefined,
              location_name: flight.departure_airport || origin,
            });
          }
          if (rec?.recommended_hotel) {
            const hotel = rec.recommended_hotel;
            await createItineraryItem({
              day: dayId,
              item_type: 'hotel',
              order: itemOrder++,
              title: `Check in: ${hotel.name || hotel.hotel_name}`,
              description: `${hotel.stars || hotel.star_rating || 0} stars`,
              start_time: '15:00',
              estimated_cost: hotel.price || hotel.price_per_night || undefined,
              location_name: hotel.address || destination,
            });
          }
        }

        // For last day, add hotel checkout and return flight
        if (isLastDay && totalDays > 1) {
          if (rec?.recommended_hotel) {
            const hotel = rec.recommended_hotel;
            await createItineraryItem({
              day: dayId,
              item_type: 'hotel',
              order: itemOrder++,
              title: `Check out: ${hotel.name || hotel.hotel_name}`,
              start_time: '10:00',
              location_name: hotel.address || destination,
            });
          }
        }

        // Add activities from parsed LLM narrative
        if (parsedDay && parsedDay.activities.length > 0) {
          for (const activity of parsedDay.activities) {
            // Skip if this is a duplicate of the structured items we already added
            const lowerTitle = activity.title.toLowerCase();
            if (isFirstDay && activity.itemType === 'flight' && itemOrder > 0) continue;
            if (isFirstDay && lowerTitle.includes('check') && lowerTitle.includes('in') && activity.itemType === 'hotel') continue;
            if (isLastDay && lowerTitle.includes('check') && lowerTitle.includes('out') && activity.itemType === 'hotel') continue;

            // Convert time string to HH:MM format
            let timeHHMM: string | undefined;
            if (activity.time) {
              const tMatch = activity.time.match(/(\d{1,2}):(\d{2})\s*([AaPp][Mm]?)/);
              if (tMatch) {
                let hour = parseInt(tMatch[1]);
                const min = tMatch[2];
                const ampm = tMatch[3].toUpperCase();
                if (ampm.startsWith('P') && hour !== 12) hour += 12;
                if (ampm.startsWith('A') && hour === 12) hour = 0;
                timeHHMM = `${hour.toString().padStart(2, '0')}:${min}`;
              }
            }

            await createItineraryItem({
              day: dayId,
              item_type: activity.itemType,
              order: itemOrder++,
              title: activity.title,
              start_time: timeHHMM,
              estimated_cost: activity.estimatedCost,
            });
          }
        } else if (!isFirstDay && !isLastDay) {
          // Fallback: if no parsed activities for middle day, add a placeholder
          await createItineraryItem({
            day: dayId,
            item_type: 'activity',
            order: 0,
            title: `Explore ${destination}`,
            description: 'Add your planned activities for this day',
          });
        }
      }

      showSuccess('Itinerary saved! Redirecting...');
      setTimeout(() => navigate(`/itineraries/${itinerary.id}`), 500);
    } catch (err: any) {
      console.error('Failed to save itinerary:', err);
      showError(err.response?.data?.detail || 'Failed to save itinerary. Make sure you are logged in.');
    } finally {
      setSaving(false);
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

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Preferred Cuisine (Optional)
              </label>
              <select
                value={cuisine}
                onChange={(e) => setCuisine(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">Any Cuisine</option>
                <option value="American">American</option>
                <option value="Italian">Italian</option>
                <option value="Mexican">Mexican</option>
                <option value="Chinese">Chinese</option>
                <option value="Japanese">Japanese</option>
                <option value="Indian">Indian</option>
                <option value="Thai">Thai</option>
                <option value="French">French</option>
                <option value="Mediterranean">Mediterranean</option>
                <option value="Seafood">Seafood</option>
              </select>
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
              <p>🚗 Car Rental Agent searching for vehicles...</p>
              <p>🍽️ Restaurant Agent finding dining options...</p>
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
                <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
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
                  <div className="bg-orange-50 dark:bg-orange-900/20 p-4 rounded-lg">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Cars Found</p>
                    <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                      {result.recommendation?.summary?.cars_found || 0}
                    </p>
                  </div>
                  <div className="bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded-lg">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Restaurants Found</p>
                    <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
                      {result.recommendation?.summary?.restaurants_found || 0}
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

          {/* Enhanced Agent Data: Weather, Safety, Visa, Packing */}
          {result.enhanced_data && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Weather */}
              {result.enhanced_data.weather && (
                <Card>
                  <CardHeader>
                    <CardTitle>🌤️ Weather & Climate</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {result.enhanced_data.weather.source === 'OpenWeatherMap' ? (
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Temperature</span>
                          <span className="font-medium">{result.enhanced_data.weather.temperature}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Feels Like</span>
                          <span className="font-medium">{result.enhanced_data.weather.feels_like}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Condition</span>
                          <span className="font-medium">{result.enhanced_data.weather.description || result.enhanced_data.weather.condition}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Humidity</span>
                          <span className="font-medium">{result.enhanced_data.weather.humidity}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Wind</span>
                          <span className="font-medium">{result.enhanced_data.weather.wind_speed}</span>
                        </div>
                      </div>
                    ) : (
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {result.enhanced_data.weather.note || 'Weather data included in AI itinerary based on general climate knowledge.'}
                      </p>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* Health & Safety */}
              {result.enhanced_data.health_safety && Object.keys(result.enhanced_data.health_safety).length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>🛡️ Health & Safety</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Safety Score</span>
                        <span className="font-medium">{result.enhanced_data.health_safety.safety_score}/10</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Crime Level</span>
                        <span className="font-medium capitalize">{result.enhanced_data.health_safety.crime_level}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Political Stability</span>
                        <span className="font-medium capitalize">{result.enhanced_data.health_safety.political_stability}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Health Infrastructure</span>
                        <span className="font-medium capitalize">{result.enhanced_data.health_safety.health_infrastructure}</span>
                      </div>
                      {result.enhanced_data.health_safety.emergency_numbers && (
                        <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            Emergency: {result.enhanced_data.health_safety.emergency_numbers.police}
                          </p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Visa & Documents */}
              {result.enhanced_data.visa && Object.keys(result.enhanced_data.visa).length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>📋 Visa & Documents</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Visa Required</span>
                        <span className="font-medium">{result.enhanced_data.visa.visa_required}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Max Stay</span>
                        <span className="font-medium">{result.enhanced_data.visa.max_stay} days</span>
                      </div>
                      {result.enhanced_data.visa.required_documents && result.enhanced_data.visa.required_documents.length > 0 && (
                        <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
                          <p className="font-medium mb-1">Required Documents:</p>
                          <ul className="text-xs text-gray-600 dark:text-gray-400 space-y-0.5">
                            {result.enhanced_data.visa.required_documents.slice(0, 4).map((doc: string, i: number) => (
                              <li key={i}>• {doc}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Local Dining Culture */}
              {result.enhanced_data.local_dining && Object.keys(result.enhanced_data.local_dining).length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>🍴 Local Dining Culture</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      {result.enhanced_data.local_dining.must_try_dishes && result.enhanced_data.local_dining.must_try_dishes.length > 0 && (
                        <div>
                          <p className="font-medium mb-1">Must-Try Dishes:</p>
                          <p className="text-gray-600 dark:text-gray-400">
                            {result.enhanced_data.local_dining.must_try_dishes.join(', ')}
                          </p>
                        </div>
                      )}
                      {result.enhanced_data.local_dining.budget_guide && (
                        <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
                          <p className="font-medium mb-1">Meal Prices:</p>
                          <div className="text-xs text-gray-600 dark:text-gray-400 space-y-0.5">
                            <p>Budget: {result.enhanced_data.local_dining.budget_guide.budget_meal}</p>
                            <p>Mid-range: {result.enhanced_data.local_dining.budget_guide.mid_range_meal}</p>
                            <p>Fine dining: {result.enhanced_data.local_dining.budget_guide.fine_dining}</p>
                          </div>
                        </div>
                      )}
                      {result.enhanced_data.local_dining.dining_tips && result.enhanced_data.local_dining.dining_tips.length > 0 && (
                        <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
                          <p className="font-medium mb-1">Tips:</p>
                          <ul className="text-xs text-gray-600 dark:text-gray-400 space-y-0.5">
                            {result.enhanced_data.local_dining.dining_tips.slice(0, 3).map((tip: string, i: number) => (
                              <li key={i}>• {tip}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {/* LLM Day-by-Day Itinerary Narrative */}
          {result.itinerary_text && (
            <Card>
              <CardHeader>
                <CardTitle>📅 AI-Generated Day-by-Day Itinerary</CardTitle>
              </CardHeader>
              <CardContent>
                <div
                  className="prose prose-sm dark:prose-invert max-w-none
                    prose-headings:text-gray-900 dark:prose-headings:text-white
                    prose-h2:text-lg prose-h2:font-bold prose-h2:mt-6 prose-h2:mb-2
                    prose-h3:text-base prose-h3:font-semibold prose-h3:mt-4 prose-h3:mb-1
                    prose-p:text-gray-700 dark:prose-p:text-gray-300 prose-p:my-1
                    prose-li:text-gray-700 dark:prose-li:text-gray-300
                    prose-strong:text-gray-900 dark:prose-strong:text-white
                    prose-ul:my-1 prose-ol:my-1"
                  dangerouslySetInnerHTML={{
                    __html: result.itinerary_text
                      .replace(/^### (.*$)/gm, '<h3>$1</h3>')
                      .replace(/^## (.*$)/gm, '<h2>$1</h2>')
                      .replace(/^# (.*$)/gm, '<h1>$1</h1>')
                      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                      .replace(/\*(.*?)\*/g, '<em>$1</em>')
                      .replace(/^- (.*$)/gm, '<li>$1</li>')
                      .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
                      .replace(/\n\n/g, '</p><p>')
                      .replace(/\n/g, '<br/>')
                  }}
                />
              </CardContent>
            </Card>
          )}

          {/* Save as Itinerary Button */}
          <Card>
            <CardContent>
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-white">Save this plan as an itinerary</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Create a day-by-day trip plan you can edit, export as PDF, and share
                  </p>
                </div>
                <Button
                  onClick={handleSaveAsItinerary}
                  disabled={saving || !isAuthenticated}
                  isLoading={saving}
                  className="whitespace-nowrap"
                >
                  {saving ? 'Saving...' : '📋 Save as Itinerary'}
                </Button>
              </div>
              {!isAuthenticated && (
                <p className="text-xs text-orange-600 dark:text-orange-400 mt-2">
                  Please sign in to save itineraries.
                </p>
              )}
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
                      {result.recommendation.recommended_flight.goal_score !== undefined && (
                        <div className="mt-2 text-xs">
                          <p className={`font-medium ${
                            result.recommendation.recommended_flight.budget_status === 'within budget'
                              ? 'text-green-600 dark:text-green-400'
                              : 'text-orange-600 dark:text-orange-400'
                          }`}>
                            {result.recommendation.recommended_flight.budget_status === 'within budget'
                              ? `✓ Within budget (saves $${result.recommendation.recommended_flight.savings})`
                              : `! Over budget by $${result.recommendation.recommended_flight.budget_difference}`
                            }
                          </p>
                          <p className="text-gray-600 dark:text-gray-400">
                            Goal Score: {result.recommendation.recommended_flight.goal_score > 0 ? '+' : ''}
                            {result.recommendation.recommended_flight.goal_score}
                          </p>
                        </div>
                      )}
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
                        onError={(e) => {
                          // Hide image if it fails to load
                          (e.target as HTMLImageElement).style.display = 'none';
                        }}
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

          {/* No hotels available message */}
          {result.recommendation && !result.recommendation.recommended_hotel && result.recommendation.summary?.hotels_found > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>🏨 Hotel Information</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-6 text-gray-600 dark:text-gray-400">
                  <p className="text-lg">⚠️ No hotels with pricing available</p>
                  <p className="mt-2 text-sm">
                    The hotels in this area don't have current pricing data available.
                    Please try searching for hotels directly or try different dates.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Recommended Car Rental */}
          {result.recommendation?.recommended_car && (
            <Card>
              <CardHeader>
                <CardTitle>🚗 Recommended Car Rental</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Car Header */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-4xl">🚗</span>
                      <div>
                        <h3 className="text-xl font-semibold">
                          {result.recommendation.recommended_car.rental_company}
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {result.recommendation.recommended_car.vehicle || result.recommendation.recommended_car.car_type}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-3xl font-bold text-primary-600 dark:text-primary-400">
                        ${result.recommendation.recommended_car.price_per_day}
                        <span className="text-sm text-gray-600">/day</span>
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Total: ${result.recommendation.recommended_car.total_price}
                      </p>
                      {result.recommendation.recommended_car.utility_score !== undefined && (
                        <p className="text-sm font-semibold mt-1">
                          Utility Score: {result.recommendation.recommended_car.utility_score}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Car Type and Rating */}
                  <div className="flex items-center gap-4">
                    <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full text-sm font-semibold capitalize">
                      {result.recommendation.recommended_car.car_type}
                    </span>
                    {result.recommendation.recommended_car.rating > 0 && (
                      <div className="flex items-center gap-1">
                        <span className="text-yellow-500">⭐</span>
                        <span className="font-semibold">{result.recommendation.recommended_car.rating.toFixed(1)}</span>
                        {result.recommendation.recommended_car.reviews > 0 && (
                          <span className="text-sm text-gray-600 dark:text-gray-400">
                            ({result.recommendation.recommended_car.reviews} reviews)
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Rental Details */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <div>
                      <p className="text-xs text-gray-600 dark:text-gray-400">Rental Days</p>
                      <p className="font-semibold">{result.recommendation.recommended_car.rental_days} days</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600 dark:text-gray-400">Mileage</p>
                      <p className="font-semibold">{result.recommendation.recommended_car.mileage}</p>
                    </div>
                    {result.recommendation.recommended_car.deposit > 0 && (
                      <div>
                        <p className="text-xs text-gray-600 dark:text-gray-400">Deposit</p>
                        <p className="font-semibold">${result.recommendation.recommended_car.deposit}</p>
                      </div>
                    )}
                    <div>
                      <p className="text-xs text-gray-600 dark:text-gray-400">Insurance</p>
                      <p className="font-semibold">
                        {result.recommendation.recommended_car.insurance_available ? 'Available' : 'Not available'}
                      </p>
                    </div>
                  </div>

                  {/* Features */}
                  {result.recommendation.recommended_car.features && result.recommendation.recommended_car.features.length > 0 && (
                    <div>
                      <p className="text-sm font-semibold mb-2">Features:</p>
                      <div className="flex flex-wrap gap-2">
                        {result.recommendation.recommended_car.features.slice(0, 6).map((feature: string, idx: number) => (
                          <span
                            key={idx}
                            className="text-xs bg-gray-100 dark:bg-gray-700 px-3 py-1.5 rounded-full"
                          >
                            {feature}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Pickup Location */}
                  {result.recommendation.recommended_car.pickup_location && (
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      <span className="font-semibold">Pickup Location:</span> {result.recommendation.recommended_car.pickup_location}
                    </div>
                  )}

                  {/* Recommendation */}
                  {result.recommendation.recommended_car.recommendation && (
                    <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                      <p className="text-sm text-blue-700 dark:text-blue-300">
                        💡 {result.recommendation.recommended_car.recommendation}
                      </p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* No car rental message */}
          {result.recommendation && !result.recommendation.recommended_car && result.recommendation.summary?.cars_found > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>🚗 Car Rental Information</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-6 text-gray-600 dark:text-gray-400">
                  <p className="text-lg">⚠️ No car rentals with pricing available</p>
                  <p className="mt-2 text-sm">
                    Car rentals at this location don't have current pricing data available.
                    Please try searching for car rentals directly.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Recommended Restaurant */}
          {result.recommendation?.recommended_restaurant && (
            <Card>
              <CardHeader>
                <CardTitle>🍽️ Recommended Restaurant</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Restaurant Image and Info */}
                  <div className="flex flex-col md:flex-row gap-4">
                    {/* Restaurant Image */}
                    {(result.recommendation.recommended_restaurant.thumbnail || result.recommendation.recommended_restaurant.primary_image) && (
                      <img
                        src={result.recommendation.recommended_restaurant.thumbnail || result.recommendation.recommended_restaurant.primary_image}
                        alt={result.recommendation.recommended_restaurant.name}
                        className="w-full md:w-64 h-48 object-cover rounded-lg"
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = 'none';
                        }}
                      />
                    )}

                    {/* Restaurant Details */}
                    <div className="flex-1 space-y-3">
                      {/* Restaurant Header */}
                      <div>
                        <h3 className="text-xl font-semibold">
                          {result.recommendation.recommended_restaurant.name}
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          {result.recommendation.recommended_restaurant.cuisine_type} • {result.recommendation.recommended_restaurant.city}
                        </p>
                      </div>

                      {/* Rating */}
                      {result.recommendation.recommended_restaurant.rating > 0 && (
                        <div className="flex items-center gap-2">
                          <span className="text-yellow-500">⭐</span>
                          <span className="font-semibold">{result.recommendation.recommended_restaurant.rating.toFixed(1)}</span>
                          {result.recommendation.recommended_restaurant.review_count > 0 && (
                            <span className="text-sm text-gray-600 dark:text-gray-400">
                              ({result.recommendation.recommended_restaurant.review_count} reviews)
                            </span>
                          )}
                        </div>
                      )}

                      {/* Price Info */}
                      <div className="bg-primary-50 dark:bg-primary-900/20 p-3 rounded-lg">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-2xl font-bold text-primary-600 dark:text-primary-400">
                              {result.recommendation.recommended_restaurant.price_range}
                            </p>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              ~${result.recommendation.recommended_restaurant.average_cost_per_person} per person
                            </p>
                          </div>
                          {result.recommendation.recommended_restaurant.utility_score !== undefined && (
                            <div className="text-right">
                              <p className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                                Utility Score
                              </p>
                              <p className="text-xl font-bold text-primary-600 dark:text-primary-400">
                                {result.recommendation.recommended_restaurant.utility_score}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Address */}
                      {result.recommendation.recommended_restaurant.address && (
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          📍 {result.recommendation.recommended_restaurant.address}
                        </div>
                      )}

                      {/* Hours */}
                      {result.recommendation.recommended_restaurant.hours && (
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          🕒 {result.recommendation.recommended_restaurant.hours}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Utility Score Breakdown */}
                  {(result.recommendation.recommended_restaurant.rating_utility_score !== undefined ||
                    result.recommendation.recommended_restaurant.price_utility_score !== undefined) && (
                    <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                        Utility Score Breakdown:
                      </p>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        {result.recommendation.recommended_restaurant.rating_utility_score !== undefined && (
                          <div className="text-gray-600 dark:text-gray-400">
                            • Rating Score: {result.recommendation.recommended_restaurant.rating_utility_score > 0 ? '+' : ''}
                            {result.recommendation.recommended_restaurant.rating_utility_score}
                          </div>
                        )}
                        {result.recommendation.recommended_restaurant.price_utility_score !== undefined && (
                          <div className="text-gray-600 dark:text-gray-400">
                            • Price Score: {result.recommendation.recommended_restaurant.price_utility_score > 0 ? '+' : ''}
                            {result.recommendation.recommended_restaurant.price_utility_score}
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Services */}
                  <div className="flex flex-wrap gap-2">
                    {result.recommendation.recommended_restaurant.has_delivery && (
                      <span className="text-xs px-3 py-1.5 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded-full">
                        🚚 Delivery
                      </span>
                    )}
                    {result.recommendation.recommended_restaurant.has_takeout && (
                      <span className="text-xs px-3 py-1.5 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-full">
                        🥡 Takeout
                      </span>
                    )}
                    {result.recommendation.recommended_restaurant.has_reservation && (
                      <span className="text-xs px-3 py-1.5 bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 rounded-full">
                        📅 Reservations
                      </span>
                    )}
                  </div>

                  {/* Contact */}
                  <div className="flex gap-3 text-sm">
                    {result.recommendation.recommended_restaurant.phone && (
                      <a
                        href={`tel:${result.recommendation.recommended_restaurant.phone}`}
                        className="text-blue-600 dark:text-blue-400 hover:underline"
                      >
                        📞 {result.recommendation.recommended_restaurant.phone}
                      </a>
                    )}
                    {result.recommendation.recommended_restaurant.website && (
                      <a
                        href={result.recommendation.recommended_restaurant.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 dark:text-blue-400 hover:underline"
                      >
                        🌐 Website
                      </a>
                    )}
                  </div>

                  {/* Recommendation */}
                  {result.recommendation.recommended_restaurant.recommendation && (
                    <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                      <p className="text-sm text-blue-700 dark:text-blue-300">
                        💡 {result.recommendation.recommended_restaurant.recommendation}
                      </p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* No restaurant message */}
          {result.recommendation && !result.recommendation.recommended_restaurant && result.recommendation.summary?.restaurants_found > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>🍽️ Restaurant Information</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-6 text-gray-600 dark:text-gray-400">
                  <p className="text-lg">⚠️ No restaurants with ratings available</p>
                  <p className="mt-2 text-sm">
                    Restaurants at this location don't have sufficient rating data.
                    Please try searching for restaurants directly.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Alternative Flights */}
          {result.flights?.flights && result.flights.flights.length > 1 && (
            <Card>
              <CardHeader>
                <CardTitle>✈️ Alternative Flights</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {result.flights.flights.slice(1, 6).map((flight: any, idx: number) => (
                    <div key={idx} className="flex gap-3 p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-primary-500 transition-colors">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          {flight.airline_logo && (
                            <img src={flight.airline_logo} alt={flight.airline} className="h-6 w-6 object-contain" />
                          )}
                          <h4 className="font-semibold">{flight.airline}</h4>
                          {flight.flight_number && <span className="text-sm text-gray-600 dark:text-gray-400">#{flight.flight_number}</span>}
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                          <span>{flight.departure_time?.split(' ')[1] || flight.departure_time}</span>
                          <span className="text-gray-400">→</span>
                          <span>{flight.arrival_time?.split(' ')[1] || flight.arrival_time}</span>
                          <span className="mx-2">•</span>
                          <span>{flight.stops === 0 ? 'Nonstop' : `${flight.stops} stop${flight.stops > 1 ? 's' : ''}`}</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-xl font-bold text-primary-600 dark:text-primary-400">${flight.price}</p>
                      </div>
                    </div>
                  ))}
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
                  {result.recommendation.top_5_hotels.slice(1, 6).map((hotel: any, idx: number) => (
                    <div key={idx} className="flex gap-3 p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-primary-500 transition-colors">
                      {hotel.images?.[0] && (
                        <img
                          src={hotel.images[0]}
                          alt={hotel.name || hotel.hotel_name}
                          className="w-24 h-24 object-cover rounded"
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display = 'none';
                          }}
                        />
                      )}
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

          {/* Alternative Car Rentals */}
          {result.recommendation?.top_5_cars && result.recommendation.top_5_cars.length > 1 && (
            <Card>
              <CardHeader>
                <CardTitle>🚗 Alternative Car Rentals</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {result.recommendation.top_5_cars.slice(1, 6).map((car: any, idx: number) => (
                    <div key={idx} className="flex gap-3 p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-primary-500 transition-colors">
                      <div className="flex-shrink-0">
                        <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center text-2xl">
                          🚗
                        </div>
                      </div>
                      <div className="flex-1">
                        <h4 className="font-semibold">{car.rental_company}</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400">{car.vehicle || car.car_type}</p>
                        <div className="flex items-center gap-3 mt-1">
                          <span className="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded capitalize">
                            {car.car_type}
                          </span>
                          {car.rating > 0 && (
                            <span className="text-xs">⭐ {car.rating.toFixed(1)}</span>
                          )}
                          {car.utility_score !== undefined && (
                            <span className="text-xs text-gray-600 dark:text-gray-400">
                              Score: {car.utility_score}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex-shrink-0 text-right">
                        <p className="text-lg font-bold text-primary-600 dark:text-primary-400">
                          ${car.price_per_day}/day
                        </p>
                        <p className="text-xs text-gray-600 dark:text-gray-400">
                          ${car.total_price} total
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Alternative Restaurants */}
          {result.recommendation?.top_5_restaurants && result.recommendation.top_5_restaurants.length > 1 && (
            <Card>
              <CardHeader>
                <CardTitle>🍽️ Alternative Restaurants</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {result.recommendation.top_5_restaurants.slice(1, 6).map((restaurant: any, idx: number) => (
                    <div key={idx} className="flex gap-3 p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-primary-500 transition-colors">
                      {(restaurant.thumbnail || restaurant.primary_image) ? (
                        <img
                          src={restaurant.thumbnail || restaurant.primary_image}
                          alt={restaurant.name}
                          className="w-24 h-24 object-cover rounded-lg flex-shrink-0"
                          onError={(e) => {
                            const parent = (e.target as HTMLImageElement).parentElement;
                            if (parent) {
                              parent.innerHTML = '<div class="w-24 h-24 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center text-2xl">🍽️</div>';
                            }
                          }}
                        />
                      ) : (
                        <div className="w-24 h-24 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center text-2xl flex-shrink-0">
                          🍽️
                        </div>
                      )}
                      <div className="flex-grow min-w-0">
                        <h4 className="font-semibold truncate">{restaurant.name}</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400">{restaurant.cuisine_type}</p>
                        <div className="flex items-center gap-2 mt-1 flex-wrap">
                          {restaurant.rating > 0 && (
                            <>
                              <span className="text-yellow-500 text-sm">⭐</span>
                              <span className="text-sm font-semibold">{restaurant.rating.toFixed(1)}</span>
                              <span className="text-gray-400">•</span>
                            </>
                          )}
                          <span className="text-sm font-semibold text-green-600 dark:text-green-400">{restaurant.price_range}</span>
                          <span className="text-gray-400">•</span>
                          <span className="text-sm text-gray-600 dark:text-gray-400">Score: {restaurant.utility_score || restaurant.combined_utility_score}</span>
                        </div>
                      </div>
                      <div className="flex-shrink-0 text-right">
                        <p className="text-lg font-bold text-primary-600 dark:text-primary-400">
                          ${restaurant.average_cost_per_person}
                        </p>
                        <p className="text-xs text-gray-600 dark:text-gray-400">
                          per person
                        </p>
                      </div>
                    </div>
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
