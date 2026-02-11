import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import safetyService, { SafetyData } from '@/services/safetyService';
import Button from '@/components/common/Button';

const SafetyPage = () => {
  const [searchParams] = useSearchParams();
  const [city, setCity] = useState(searchParams.get('city') || '');
  const [safetyData, setSafetyData] = useState<SafetyData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searched, setSearched] = useState(false);

  const handleSearch = async () => {
    if (!city.trim()) {
      setError('Please enter a city name or airport code');
      return;
    }

    setLoading(true);
    setError('');
    setSearched(true);

    try {
      const response = await safetyService.getSafetyInfo({
        city: city.trim(),
      });

      if (response.success) {
        setSafetyData(response);
      } else {
        setError(response.error || 'Failed to fetch safety information');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch safety information');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const getSafetyScoreColor = (score: number) => {
    if (score >= 85) return 'text-green-600 dark:text-green-400';
    if (score >= 70) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-orange-600 dark:text-orange-400';
  };

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      low: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      high: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    };
    return colors[severity] || colors.low;
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            🛡️ Safety & Travel Alerts
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Get important safety information, local laws, and travel alerts for your destination
          </p>
        </div>

        {/* Search Section */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-8">
          <div className="flex gap-4">
            <div className="flex-1">
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
            <div className="flex items-end">
              <Button
                onClick={handleSearch}
                disabled={loading}
                className="whitespace-nowrap"
              >
                {loading ? 'Loading...' : 'Get Safety Info'}
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
            <p className="mt-4 text-gray-600 dark:text-gray-400">Fetching safety information...</p>
          </div>
        )}

        {/* Results */}
        {!loading && searched && safetyData && (
          <div className="space-y-6">
            {/* Overall Safety Rating */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                Safety Overview - {safetyData.location}
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Overall Rating</div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    {safetyData.overall_rating}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Safety Score</div>
                  <div className={`text-2xl font-bold ${getSafetyScoreColor(safetyData.safety_score)}`}>
                    {safetyData.safety_score}/100
                  </div>
                </div>
              </div>
            </div>

            {/* Active Alerts */}
            {safetyData.active_alerts && safetyData.active_alerts.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                  🚨 Active Alerts
                </h3>
                <div className="space-y-3">
                  {safetyData.active_alerts.map((alert, index) => (
                    <div
                      key={index}
                      className="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
                    >
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">{alert.icon}</span>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="font-semibold text-gray-900 dark:text-white">
                              {alert.title}
                            </h4>
                            <span className={`px-2 py-1 text-xs font-medium rounded ${getSeverityColor(alert.severity)}`}>
                              {alert.severity}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                            {alert.message}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-500">
                            Issued: {alert.issued_at}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Emergency Contacts */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                📞 Emergency Contacts
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <span className="text-2xl">🚓</span>
                  <div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Police</div>
                    <div className="font-semibold text-gray-900 dark:text-white">
                      {safetyData.emergency_contacts.police}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <span className="text-2xl">🚑</span>
                  <div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Ambulance</div>
                    <div className="font-semibold text-gray-900 dark:text-white">
                      {safetyData.emergency_contacts.ambulance}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <span className="text-2xl">🚒</span>
                  <div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Fire</div>
                    <div className="font-semibold text-gray-900 dark:text-white">
                      {safetyData.emergency_contacts.fire}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <span className="text-2xl">👮</span>
                  <div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Tourist Police</div>
                    <div className="font-semibold text-gray-900 dark:text-white">
                      {safetyData.emergency_contacts.tourist_police}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Safety Tips */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                💡 Safety Tips
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {safetyData.safety_tips.map((tip, index) => (
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

            {/* Areas Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Safe Areas */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                  ✅ Safe Areas
                </h3>
                <ul className="space-y-2">
                  {safetyData.safe_areas.map((area, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                      <span className="text-green-500">•</span>
                      <span>{area}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Areas to Avoid */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                  ⚠️ Areas to Avoid
                </h3>
                <ul className="space-y-2">
                  {safetyData.areas_to_avoid.map((area, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                      <span className="text-orange-500">•</span>
                      <span>{area}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Transportation Safety */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                🚗 Transportation Safety
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-xl">🚌</span>
                    <h4 className="font-semibold text-gray-900 dark:text-white">Public Transport</h4>
                    <span className="text-sm text-green-600 dark:text-green-400">
                      ({safetyData.transportation_safety.public_transport.rating})
                    </span>
                  </div>
                  <ul className="space-y-2">
                    {safetyData.transportation_safety.public_transport.tips.map((tip, index) => (
                      <li key={index} className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-2">
                        <span>•</span>
                        <span>{tip}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-xl">🚶</span>
                    <h4 className="font-semibold text-gray-900 dark:text-white">Walking</h4>
                    <span className="text-sm text-green-600 dark:text-green-400">
                      ({safetyData.transportation_safety.walking.rating})
                    </span>
                  </div>
                  <ul className="space-y-2">
                    {safetyData.transportation_safety.walking.tips.map((tip, index) => (
                      <li key={index} className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-2">
                        <span>•</span>
                        <span>{tip}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            {/* Health Information */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                🏥 Health & Medical
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="text-sm text-gray-600 dark:text-gray-400">Tap Water</div>
                  <div className="font-semibold text-gray-900 dark:text-white">
                    {safetyData.health_info.tap_water}
                  </div>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="text-sm text-gray-600 dark:text-gray-400">Air Quality</div>
                  <div className="font-semibold text-gray-900 dark:text-white">
                    {safetyData.health_info.air_quality}
                  </div>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="text-sm text-gray-600 dark:text-gray-400">Hospitals</div>
                  <div className="font-semibold text-gray-900 dark:text-white">
                    {safetyData.health_info.hospitals}
                  </div>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="text-sm text-gray-600 dark:text-gray-400">Pharmacies</div>
                  <div className="font-semibold text-gray-900 dark:text-white">
                    {safetyData.health_info.pharmacies}
                  </div>
                </div>
              </div>
              {safetyData.health_info.vaccinations_required.length > 0 && (
                <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900 border border-blue-200 dark:border-blue-800 rounded-lg">
                  <div className="text-sm font-medium text-blue-900 dark:text-blue-200 mb-1">
                    Recommended Vaccinations
                  </div>
                  <div className="text-sm text-blue-700 dark:text-blue-300">
                    {safetyData.health_info.vaccinations_required.join(', ')}
                  </div>
                </div>
              )}
            </div>

            {/* Local Laws */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                ⚖️ Local Laws & Customs
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {safetyData.local_laws.map((law, index) => (
                  <div key={index} className="flex items-start gap-3 p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                    <span className="text-2xl">{law.icon}</span>
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white mb-1">
                        {law.title}
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {law.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Travel Advisory */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                📋 Travel Advisory
              </h3>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {safetyData.travel_advisory.level}
                  </span>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {safetyData.travel_advisory.summary}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-500">
                  Last updated: {safetyData.travel_advisory.last_updated}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading && !searched && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🛡️</div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              Get Safety Information
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Enter a city to view safety alerts, emergency contacts, and travel advisories
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default SafetyPage;
