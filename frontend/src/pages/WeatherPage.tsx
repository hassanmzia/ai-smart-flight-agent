import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Loading from '@/components/common/Loading';
import { useToast } from '@/hooks/useNotifications';
import weatherService, { type WeatherData, type WeatherForecast } from '@/services/weatherService';

const WeatherPage = () => {
  const { showSuccess, showError } = useToast();
  const [loading, setLoading] = useState(false);
  const [city, setCity] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [weatherData, setWeatherData] = useState<WeatherData | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!city.trim()) {
      showError('Please enter a city name');
      return;
    }

    setLoading(true);
    setWeatherData(null);

    try {
      const result = await weatherService.getWeatherForecast({
        city: city.trim(),
        start_date: startDate || undefined,
        end_date: endDate || undefined,
      });

      setWeatherData(result);
      showSuccess(`Weather forecast loaded for ${result.location.city}`);
    } catch (error: any) {
      showError(error.message || 'Failed to fetch weather forecast');
    } finally {
      setLoading(false);
    }
  };

  const getTempColor = (temp: number) => {
    if (temp >= 30) return 'text-red-600 dark:text-red-400';
    if (temp >= 25) return 'text-orange-600 dark:text-orange-400';
    if (temp >= 20) return 'text-yellow-600 dark:text-yellow-400';
    if (temp >= 15) return 'text-blue-600 dark:text-blue-400';
    return 'text-cyan-600 dark:text-cyan-400';
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
        🌤️ Weather Forecast
      </h1>
      <p className="text-gray-600 dark:text-gray-400 mb-8">
        Check local weather conditions for your travel dates
      </p>

      {/* Search Form */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Search Weather Forecast</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Input
                label="City or Location"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                placeholder="e.g., New York, Paris, Tokyo"
                required
              />

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
            </div>

            <Button type="submit" className="w-full" isLoading={loading} disabled={loading}>
              {loading ? 'Loading Forecast...' : '🔍 Get Weather Forecast'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Loading State */}
      {loading && (
        <Card>
          <CardContent className="py-12">
            <Loading size="lg" text="Fetching weather forecast..." />
          </CardContent>
        </Card>
      )}

      {/* Weather Results */}
      {!loading && weatherData && (
        <div className="space-y-6">
          {/* Location Header */}
          <Card>
            <CardContent className="py-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                    {weatherData.location.city}
                    {weatherData.location.country && `, ${weatherData.location.country}`}
                  </h2>
                  <p className="text-gray-600 dark:text-gray-400 mt-1">
                    {weatherData.start_date} to {weatherData.end_date} ({weatherData.total_days} days)
                  </p>
                </div>
                {weatherData.note && (
                  <div className="text-sm text-gray-500 dark:text-gray-400 bg-yellow-50 dark:bg-yellow-900/20 px-3 py-2 rounded">
                    ℹ️ {weatherData.note}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Daily Forecasts */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {weatherData.forecasts.map((forecast: WeatherForecast, index: number) => (
              <Card key={index} className="hover:shadow-lg transition-shadow">
                <CardContent className="p-4">
                  {/* Date Header */}
                  <div className="text-center mb-4">
                    <h3 className="font-semibold text-lg text-gray-900 dark:text-white">
                      {forecast.day_of_week}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {forecast.date}
                    </p>
                  </div>

                  {/* Weather Icon & Condition */}
                  <div className="text-center mb-4">
                    <div className="text-6xl mb-2">{forecast.icon}</div>
                    <p className="font-medium text-gray-900 dark:text-white capitalize">
                      {forecast.description}
                    </p>
                  </div>

                  {/* Temperature */}
                  <div className="text-center mb-4 pb-4 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-center gap-3">
                      <span className={`text-3xl font-bold ${getTempColor(forecast.temp_max)}`}>
                        {forecast.temp_max}°
                      </span>
                      <span className="text-gray-400">/</span>
                      <span className="text-2xl text-gray-600 dark:text-gray-400">
                        {forecast.temp_min}°
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                      Avg: {forecast.temp_avg}°C
                    </p>
                  </div>

                  {/* Weather Details */}
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600 dark:text-gray-400">💧 Humidity</span>
                      <span className="font-medium text-gray-900 dark:text-white">{forecast.humidity}%</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-gray-600 dark:text-gray-400">💨 Wind</span>
                      <span className="font-medium text-gray-900 dark:text-white">{forecast.wind_speed} m/s</span>
                    </div>

                    {forecast.precipitation_mm > 0 && (
                      <div className="flex items-center justify-between">
                        <span className="text-gray-600 dark:text-gray-400">🌧️ Rain</span>
                        <span className="font-medium text-gray-900 dark:text-white">{forecast.precipitation_mm} mm</span>
                      </div>
                    )}

                    <div className="flex items-center justify-between">
                      <span className="text-gray-600 dark:text-gray-400">☔ Rain Chance</span>
                      <span className="font-medium text-gray-900 dark:text-white">{forecast.precipitation_chance}%</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-gray-600 dark:text-gray-400">☀️ UV Index</span>
                      <span className={`font-medium ${forecast.uv_index >= 6 ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'}`}>
                        {forecast.uv_index}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* No Results */}
      {!loading && !weatherData && city && (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-gray-600 dark:text-gray-400 text-lg">
              Enter a city and click "Get Weather Forecast" to see the weather
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default WeatherPage;
