import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import commuteService, { CommuteData } from '@/services/commuteService';
import Button from '@/components/common/Button';

const CommutePage = () => {
  const [searchParams] = useSearchParams();
  const [city, setCity] = useState(searchParams.get('city') || '');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [commuteData, setCommuteData] = useState<CommuteData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searched, setSearched] = useState(false);

  const handleSearch = async () => {
    if (!city.trim()) {
      setError('Please enter a city name or airport code');
      return;
    }

    if (startDate && endDate && new Date(endDate) < new Date(startDate)) {
      setError('End date must be after start date');
      return;
    }

    setLoading(true);
    setError('');
    setSearched(true);

    try {
      const response = await commuteService.getCommuteInfo({
        city: city.trim(),
        start_date: startDate || undefined,
        end_date: endDate || undefined,
      });

      if (response.success) {
        setCommuteData(response);
      } else {
        setError(response.error || 'Failed to fetch commute information');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch commute information');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const getTrafficLevelColor = (level: number) => {
    if (level >= 70) return 'text-red-600 dark:text-red-400';
    if (level >= 50) return 'text-orange-600 dark:text-orange-400';
    if (level >= 30) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-green-600 dark:text-green-400';
  };

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      high: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      low: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    };
    return colors[severity] || colors.low;
  };

  return (
    <div className="min-h-screen">
      <div className="relative overflow-hidden bg-gradient-to-br from-cyan-500 via-blue-600 to-indigo-600 dark:from-cyan-800 dark:via-blue-800 dark:to-indigo-800">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute -top-10 -right-20 w-64 h-64 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 left-1/4 w-40 h-40 bg-cyan-300 rounded-full blur-3xl"></div>
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
          <h1 className="text-3xl md:text-4xl font-extrabold text-white mb-2">
            🚗 Local Commute & Traffic
          </h1>
          <p className="text-cyan-100 text-lg">
            Get predicted traffic conditions for your travel dates, plus real-time info and commute times
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6 relative z-10 pb-12">

        {/* Search Section */}
        <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl shadow-sm border border-gray-200/60 dark:border-gray-700/50 p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                City or Airport Code
              </label>
              <input
                type="text"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="e.g., New York, LAX, London"
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Travel Start Date
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Travel End Date
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
              />
            </div>
            <div className="flex items-end">
              <Button
                onClick={handleSearch}
                disabled={loading}
                className="w-full"
              >
                {loading ? 'Loading...' : 'Get Traffic Info'}
              </Button>
            </div>
          </div>

          {error && (
            <div className="mt-4 p-4 bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-red-800 dark:text-red-200">{error}</p>
            </div>
          )}
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Fetching traffic information...</p>
          </div>
        )}

        {/* Results */}
        {!loading && searched && commuteData && (
          <div className="space-y-6">
            {/* Daily Traffic Predictions */}
            {commuteData.daily_predictions && commuteData.daily_predictions.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  📅 Traffic Predictions for Your Travel Period
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
                  Plan your trips around predicted traffic conditions
                </p>
                <div className="space-y-4">
                  {commuteData.daily_predictions.map((prediction, index) => (
                    <div
                      key={index}
                      className="border border-gray-200 dark:border-gray-700 rounded-lg p-5"
                    >
                      <div className="flex items-start justify-between mb-4">
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                            {prediction.day_name}, {new Date(prediction.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                          </h3>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                              {prediction.overall_rating}
                            </span>
                            <span className={`text-lg font-bold ${getTrafficLevelColor(prediction.overall_level)}`}>
                              {prediction.overall_level}%
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Traffic Periods */}
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
                        <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                          <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                            {prediction.periods.morning_rush.time}
                          </div>
                          <div className="font-medium text-gray-900 dark:text-white mb-1">
                            Morning Rush
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-gray-700 dark:text-gray-300">
                              {prediction.periods.morning_rush.condition}
                            </span>
                            <span className={`text-sm font-semibold ${getTrafficLevelColor(prediction.periods.morning_rush.traffic_level)}`}>
                              {prediction.periods.morning_rush.traffic_level}%
                            </span>
                          </div>
                        </div>

                        <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                          <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                            {prediction.periods.midday.time}
                          </div>
                          <div className="font-medium text-gray-900 dark:text-white mb-1">
                            Midday
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-gray-700 dark:text-gray-300">
                              {prediction.periods.midday.condition}
                            </span>
                            <span className={`text-sm font-semibold ${getTrafficLevelColor(prediction.periods.midday.traffic_level)}`}>
                              {prediction.periods.midday.traffic_level}%
                            </span>
                          </div>
                        </div>

                        <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                          <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                            {prediction.periods.evening_rush.time}
                          </div>
                          <div className="font-medium text-gray-900 dark:text-white mb-1">
                            Evening Rush
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-gray-700 dark:text-gray-300">
                              {prediction.periods.evening_rush.condition}
                            </span>
                            <span className={`text-sm font-semibold ${getTrafficLevelColor(prediction.periods.evening_rush.traffic_level)}`}>
                              {prediction.periods.evening_rush.traffic_level}%
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Recommendations */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                        <div className="flex items-start gap-2 text-sm">
                          <span className="text-green-600 dark:text-green-400">✓</span>
                          <div>
                            <span className="font-medium text-gray-700 dark:text-gray-300">Best time:</span>{' '}
                            <span className="text-gray-600 dark:text-gray-400">{prediction.best_time_to_travel}</span>
                          </div>
                        </div>
                        <div className="flex items-start gap-2 text-sm">
                          <span className="text-red-600 dark:text-red-400">⚠</span>
                          <div>
                            <span className="font-medium text-gray-700 dark:text-gray-300">Avoid:</span>{' '}
                            <span className="text-gray-600 dark:text-gray-400">{prediction.times_to_avoid.join(', ')}</span>
                          </div>
                        </div>
                      </div>

                      {/* Notes */}
                      {prediction.notes && prediction.notes.length > 0 && (
                        <div className="pt-3 border-t border-gray-200 dark:border-gray-600">
                          <div className="flex flex-wrap gap-2">
                            {prediction.notes.map((note, noteIndex) => (
                              <span
                                key={noteIndex}
                                className="px-2 py-1 bg-blue-50 dark:bg-blue-900 text-blue-700 dark:text-blue-200 text-xs rounded"
                              >
                                {note}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Current Traffic Conditions */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                🚦 Current Traffic - {commuteData.location}
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Condition</div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    {commuteData.traffic_conditions.current_condition}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    {commuteData.traffic_conditions.description}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Traffic Level</div>
                  <div className={`text-2xl font-bold ${getTrafficLevelColor(commuteData.traffic_conditions.traffic_level)}`}>
                    {commuteData.traffic_conditions.traffic_level}%
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Last updated: {commuteData.traffic_conditions.last_updated}
                  </div>
                </div>
              </div>
            </div>

            {/* Peak Hours */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                ⏰ Peak Traffic Hours
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-2xl">🌅</span>
                    <h4 className="font-semibold text-gray-900 dark:text-white">Morning Rush</h4>
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {commuteData.peak_hours.morning.start} - {commuteData.peak_hours.morning.end}
                  </div>
                  <div className="mt-2">
                    <span className="px-3 py-1 bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200 text-xs rounded-full">
                      {commuteData.peak_hours.morning.severity}
                    </span>
                  </div>
                </div>
                <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-2xl">🌆</span>
                    <h4 className="font-semibold text-gray-900 dark:text-white">Evening Rush</h4>
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {commuteData.peak_hours.evening.start} - {commuteData.peak_hours.evening.end}
                  </div>
                  <div className="mt-2">
                    <span className="px-3 py-1 bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200 text-xs rounded-full">
                      {commuteData.peak_hours.evening.severity}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Current Incidents */}
            {commuteData.current_incidents && commuteData.current_incidents.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                  ⚠️ Current Traffic Incidents
                </h3>
                <div className="space-y-3">
                  {commuteData.current_incidents.map((incident, index) => (
                    <div
                      key={index}
                      className="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
                    >
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">{incident.icon}</span>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="font-semibold text-gray-900 dark:text-white">
                              {incident.type}
                            </h4>
                            <span className={`px-2 py-1 text-xs font-medium rounded ${getSeverityColor(incident.severity)}`}>
                              {incident.severity}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                            📍 {incident.location}
                          </p>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                            {incident.description}
                          </p>
                          <div className="flex gap-4 text-xs text-gray-500 dark:text-gray-500">
                            <span>Reported: {incident.reported}</span>
                            <span>Est. clearance: {incident.estimated_clearance}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Public Transportation */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                🚇 Public Transportation
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {commuteData.public_transport.map((transport, index) => (
                  <div key={index} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-2xl">{transport.icon}</span>
                      <h4 className="font-semibold text-gray-900 dark:text-white">{transport.type}</h4>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Frequency:</span>
                        <span className="text-gray-900 dark:text-white">{transport.frequency}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Fare:</span>
                        <span className="text-gray-900 dark:text-white font-semibold">{transport.fare}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Hours:</span>
                        <span className="text-gray-900 dark:text-white text-xs">{transport.operating_hours}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Coverage:</span>
                        <span className="text-gray-900 dark:text-white">{transport.coverage}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Commute Times */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                ⏱️ Average Commute Times
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-xl">✈️</span>
                    <h4 className="font-semibold text-gray-900 dark:text-white">To Airport</h4>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">🚇 Transit:</span>
                      <span className="text-gray-900 dark:text-white">{commuteData.commute_times.airport.public_transport}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">🚗 Driving:</span>
                      <span className="text-gray-900 dark:text-white">{commuteData.commute_times.airport.driving}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">🚕 Taxi:</span>
                      <span className="text-gray-900 dark:text-white">{commuteData.commute_times.airport.taxi}</span>
                    </div>
                  </div>
                </div>
                <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-xl">🏙️</span>
                    <h4 className="font-semibold text-gray-900 dark:text-white">Downtown to Suburbs</h4>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">🚇 Transit:</span>
                      <span className="text-gray-900 dark:text-white">{commuteData.commute_times.downtown_to_suburbs.public_transport}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">🚗 Driving:</span>
                      <span className="text-gray-900 dark:text-white">{commuteData.commute_times.downtown_to_suburbs.driving}</span>
                    </div>
                  </div>
                </div>
                <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-xl">🌆</span>
                    <h4 className="font-semibold text-gray-900 dark:text-white">Cross City</h4>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">🚇 Transit:</span>
                      <span className="text-gray-900 dark:text-white">{commuteData.commute_times.cross_city.public_transport}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">🚗 Driving:</span>
                      <span className="text-gray-900 dark:text-white">{commuteData.commute_times.cross_city.driving}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Major Routes */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                🛣️ Major Routes & Highways
              </h3>
              <div className="space-y-3">
                {commuteData.major_routes.map((route, index) => (
                  <div key={index} className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-700 rounded-lg">
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white">{route.name}</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{route.description}</p>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {route.current_condition}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {route.average_speed}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Parking Information */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                🅿️ Parking Information
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="text-sm text-gray-600 dark:text-gray-400">Availability</div>
                  <div className="text-lg font-semibold text-gray-900 dark:text-white">
                    {commuteData.parking_info.availability}
                  </div>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="text-sm text-gray-600 dark:text-gray-400">Hourly Rate</div>
                  <div className="text-lg font-semibold text-gray-900 dark:text-white">
                    {commuteData.parking_info.average_cost_hourly}
                  </div>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="text-sm text-gray-600 dark:text-gray-400">Daily Rate</div>
                  <div className="text-lg font-semibold text-gray-900 dark:text-white">
                    {commuteData.parking_info.average_cost_daily}
                  </div>
                </div>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium text-gray-900 dark:text-white">Tips:</h4>
                <ul className="space-y-1">
                  {commuteData.parking_info.recommendations.map((tip, index) => (
                    <li key={index} className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-2">
                      <span>•</span>
                      <span>{tip}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Commute Tips */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                💡 Commute Tips
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {commuteData.commute_tips.map((tip, index) => (
                  <div key={index} className="flex items-start gap-3 p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                    <span className="text-2xl">{tip.icon}</span>
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white mb-1">
                        {tip.title}
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {tip.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Road Conditions */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                🚧 Road Conditions
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="text-sm text-gray-600 dark:text-gray-400">Overall</div>
                  <div className="text-lg font-semibold text-gray-900 dark:text-white">
                    {commuteData.road_conditions.overall}
                  </div>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="text-sm text-gray-600 dark:text-gray-400">Construction</div>
                  <div className="text-lg font-semibold text-gray-900 dark:text-white">
                    {commuteData.road_conditions.active_construction}
                  </div>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="text-sm text-gray-600 dark:text-gray-400">Major Closures</div>
                  <div className="text-lg font-semibold text-gray-900 dark:text-white">
                    {commuteData.road_conditions.major_closures}
                  </div>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg col-span-2 md:col-span-1">
                  <div className="text-xs text-gray-600 dark:text-gray-400">
                    {commuteData.road_conditions.detour_info}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading && !searched && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🚗</div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              Get Traffic & Commute Information
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Enter a city to view traffic conditions, public transport options, and commute times
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CommutePage;
