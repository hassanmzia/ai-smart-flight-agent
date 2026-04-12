import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import api from '@/services/api';
import { API_ENDPOINTS } from '../utils/constants';

interface MedicalFacility {
  id: number;
  name: string;
  facility_type: string;
  address: string;
  phone: string;
  distance_km: number;
  emergency_24h: boolean;
  english_speaking: boolean;
  accepts_travel_insurance: boolean;
  wheelchair_accessible: boolean;
  specialties: string[];
  rating: number;
}

interface AccessibilityInfo {
  venue_name: string;
  venue_type: string;
  mobility_rating: number;
  wheelchair_accessible: boolean;
  elevator_available: boolean;
  accessible_restroom: boolean;
  notes: string;
}

interface MedReminder {
  id: number;
  medication_name: string;
  dosage: string;
  home_time: string;
  home_timezone: string;
  frequency: string;
  notes: string;
  is_active: boolean;
}

interface AdjustedMed {
  medication_name: string;
  original_time: string;
  adjusted_time: string;
  note: string;
}

interface InsuranceInfo {
  country: string;
  risk_level: string;
  recommended_coverage: string[];
  avg_hospital_cost_per_day_usd: number;
  public_healthcare_available: boolean;
  emergency_number: string;
  vaccination_requirements: string[];
  malaria_risk: boolean;
  altitude_risk: boolean;
  notes: string;
}

interface FatigueDay {
  day: number;
  morning: string;
  midday_rest: string;
  afternoon: string;
  evening: string;
  total_walking_km: number;
  rest_periods: number;
  hydration_reminder: string;
}

const FACILITY_TYPES = [
  { value: '', label: 'All Types' },
  { value: 'hospital', label: 'Hospitals' },
  { value: 'clinic', label: 'Clinics' },
  { value: 'pharmacy', label: 'Pharmacies' },
  { value: 'emergency', label: 'Emergency' },
  { value: 'dental', label: 'Dental' },
];

const TIMEZONES = [
  'America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles',
  'Europe/London', 'Europe/Paris', 'Europe/Berlin', 'Europe/Istanbul',
  'Asia/Dubai', 'Asia/Kolkata', 'Asia/Bangkok', 'Asia/Singapore',
  'Asia/Tokyo', 'Asia/Shanghai', 'Australia/Sydney', 'Pacific/Auckland',
];

export default function HealthTravelPage() {
  const [searchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState<'medical' | 'accessibility' | 'medication' | 'insurance' | 'fatigue'>('medical');
  const [destination, setDestination] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const dest = searchParams.get('destination');
    if (dest) setDestination(dest);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  // Medical facilities
  const [facilities, setFacilities] = useState<MedicalFacility[]>([]);
  const [facilityType, setFacilityType] = useState('');
  const [emergencyOnly, setEmergencyOnly] = useState(false);

  // Accessibility
  const [accessibilityData, setAccessibilityData] = useState<AccessibilityInfo[]>([]);
  const [ratingForm, setRatingForm] = useState({
    venue_name: '', venue_type: 'hotel', mobility_rating: 3,
    wheelchair_accessible: false, elevator_available: false,
    accessible_restroom: false, notes: '',
  });

  // Medication
  const [reminders, setReminders] = useState<MedReminder[]>([]);
  const [adjustedMeds, setAdjustedMeds] = useState<AdjustedMed[]>([]);
  const [destTimezone, setDestTimezone] = useState('Europe/London');
  const [newMed, setNewMed] = useState({ medication_name: '', dosage: '', home_time: '08:00', home_timezone: 'America/New_York', frequency: 'daily', notes: '' });

  // Insurance
  const [insurance, setInsurance] = useState<InsuranceInfo | null>(null);
  const [country, setCountry] = useState('');

  // Fatigue itinerary
  const [fatiguePlan, setFatiguePlan] = useState<FatigueDay[]>([]);
  const [fatigueSettings, setFatigueSettings] = useState({ max_walking_km: 10, pace: 'moderate', days: 3 });

  const fetchFacilities = async () => {
    if (!destination) { toast.error('Please enter a destination'); return; }
    setLoading(true);
    try {
      const res = await api.get(API_ENDPOINTS.AGENT.HEALTH_MEDICAL, {
        params: { destination, type: facilityType || undefined, emergency: emergencyOnly || undefined },
      });
      const d = res.data;
      const items = d?.facilities || d?.items || d?.results || (Array.isArray(d) ? d : []);
      setFacilities(Array.isArray(items) ? items : []);
    } catch { toast.error('Failed to load medical facilities'); }
    setLoading(false);
  };

  const fetchAccessibility = async () => {
    if (!destination) { toast.error('Please enter a destination'); return; }
    setLoading(true);
    try {
      const res = await api.get(API_ENDPOINTS.AGENT.HEALTH_ACCESSIBILITY, {
        params: { destination },
      });
      const d = res.data;
      const items = d?.ratings || d?.items || d?.results || (Array.isArray(d) ? d : []);
      setAccessibilityData(Array.isArray(items) ? items : []);
    } catch { toast.error('Failed to load accessibility info'); }
    setLoading(false);
  };

  const submitRating = async () => {
    if (!destination || !ratingForm.venue_name) {
      toast.error('Destination and venue name are required'); return;
    }
    setLoading(true);
    try {
      await api.post(API_ENDPOINTS.AGENT.HEALTH_ACCESSIBILITY_RATE, {
        ...ratingForm, destination,
      });
      toast.success('Accessibility rating submitted!');
      fetchAccessibility();
    } catch { toast.error('Failed to submit rating'); }
    setLoading(false);
  };

  const fetchReminders = async () => {
    setLoading(true);
    try {
      const res = await api.get(API_ENDPOINTS.AGENT.HEALTH_MEDICATION);
      const d = res.data;
      const items = d?.reminders || d?.items || d?.results || (Array.isArray(d) ? d : []);
      setReminders(Array.isArray(items) ? items : []);
    } catch { toast.error('Failed to load medication reminders'); }
    setLoading(false);
  };

  const addReminder = async () => {
    if (!newMed.medication_name) { toast.error('Medication name is required'); return; }
    setLoading(true);
    try {
      await api.post(API_ENDPOINTS.AGENT.HEALTH_MEDICATION, {
        action: 'add', ...newMed,
      });
      toast.success('Medication reminder added!');
      setNewMed({ medication_name: '', dosage: '', home_time: '08:00', home_timezone: 'America/New_York', frequency: 'daily', notes: '' });
      fetchReminders();
    } catch { toast.error('Failed to add reminder'); }
    setLoading(false);
  };

  const adjustMedications = async () => {
    setLoading(true);
    try {
      const res = await api.get(API_ENDPOINTS.AGENT.HEALTH_MED_ADJUST, {
        params: { timezone: destTimezone },
      });
      const d = res.data;
      const items = d?.adjusted_medications || d?.items || (Array.isArray(d) ? d : []);
      setAdjustedMeds(Array.isArray(items) ? items : []);
    } catch { toast.error('Failed to adjust medications'); }
    setLoading(false);
  };

  const fetchInsurance = async () => {
    if (!country) { toast.error('Please enter a country'); return; }
    setLoading(true);
    try {
      const res = await api.get(API_ENDPOINTS.AGENT.HEALTH_INSURANCE, {
        params: { country },
      });
      const d = res.data;
      if (d?.success !== false) {
        setInsurance(d.insurance || d);
      }
    } catch { toast.error('Failed to load insurance info'); }
    setLoading(false);
  };

  const fetchFatiguePlan = async () => {
    if (!destination) { toast.error('Please enter a destination'); return; }
    setLoading(true);
    try {
      const res = await api.get(API_ENDPOINTS.AGENT.HEALTH_FATIGUE, {
        params: {
          destination,
          max_walking_km: fatigueSettings.max_walking_km,
          pace: fatigueSettings.pace,
          days: fatigueSettings.days,
        },
      });
      const d = res.data;
      const items = d?.plan || d?.days || d?.items || (Array.isArray(d) ? d : []);
      setFatiguePlan(Array.isArray(items) ? items : []);
    } catch { toast.error('Failed to generate fatigue plan'); }
    setLoading(false);
  };

  const tabs = [
    { key: 'medical' as const, label: 'Medical Facilities' },
    { key: 'accessibility' as const, label: 'Accessibility' },
    { key: 'medication' as const, label: 'Medications' },
    { key: 'insurance' as const, label: 'Insurance' },
    { key: 'fatigue' as const, label: 'Fatigue Planning' },
  ];

  const riskBadge = (level: string) => {
    const colors: Record<string, string> = {
      low: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
      moderate: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300',
      high: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300',
    };
    return colors[level] || colors.moderate;
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Health-Aware Travel
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Medical facilities, accessibility info, medication management, and fatigue-aware planning
        </p>
      </div>

      {/* Search */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Destination</label>
            <input
              type="text"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              placeholder="Enter city or destination..."
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={() => {
                if (activeTab === 'medical') fetchFacilities();
                else if (activeTab === 'accessibility') fetchAccessibility();
                else if (activeTab === 'medication') fetchReminders();
                else if (activeTab === 'insurance') fetchInsurance();
                else if (activeTab === 'fatigue') fetchFatiguePlan();
              }}
              disabled={loading}
              className="w-full px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium"
            >
              {loading ? 'Loading...' : 'Search'}
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex overflow-x-auto gap-1 mb-6 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            className={`flex-shrink-0 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === t.key
                ? 'bg-white dark:bg-gray-700 text-green-600 dark:text-green-400 shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="space-y-6">
        {/* Medical Facilities */}
        {activeTab === 'medical' && (
          <div>
            <div className="mb-4 flex flex-wrap gap-3 items-center">
              <select
                value={facilityType}
                onChange={(e) => setFacilityType(e.target.value)}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                {FACILITY_TYPES.map((ft) => (
                  <option key={ft.value} value={ft.value}>{ft.label}</option>
                ))}
              </select>
              <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                <input
                  type="checkbox"
                  checked={emergencyOnly}
                  onChange={(e) => setEmergencyOnly(e.target.checked)}
                  className="rounded"
                />
                24h Emergency Only
              </label>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              {facilities.map((f, i) => (
                <div key={f.id || i} className="bg-white dark:bg-gray-800 rounded-xl shadow p-5">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white">{f.name}</h3>
                      <span className="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full">
                        {f.facility_type}
                      </span>
                    </div>
                    {f.distance_km > 0 && (
                      <span className="text-sm text-gray-500 dark:text-gray-400">{f.distance_km} km</span>
                    )}
                  </div>
                  {f.address && <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">{f.address}</p>}
                  {f.phone && <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Tel: {f.phone}</p>}
                  <div className="flex flex-wrap gap-2 mt-2">
                    {f.emergency_24h && (
                      <span className="text-xs px-2 py-0.5 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-full">24h Emergency</span>
                    )}
                    {f.english_speaking && (
                      <span className="text-xs px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full">English Speaking</span>
                    )}
                    {f.accepts_travel_insurance && (
                      <span className="text-xs px-2 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full">Travel Insurance</span>
                    )}
                    {f.wheelchair_accessible && (
                      <span className="text-xs px-2 py-0.5 bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300 rounded-full">Wheelchair OK</span>
                    )}
                    {f.rating > 0 && (
                      <span className="text-xs px-2 py-0.5 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 rounded-full">
                        {f.rating}/5
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {facilities.length === 0 && !loading && (
              <p className="text-center text-gray-500 dark:text-gray-400 py-10">
                {destination ? 'No facilities found. Try searching.' : 'Enter a destination to find medical facilities.'}
              </p>
            )}
          </div>
        )}

        {/* Accessibility */}
        {activeTab === 'accessibility' && (
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Ratings List */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Accessibility Ratings</h3>
              {accessibilityData.length > 0 ? (
                <div className="space-y-3">
                  {accessibilityData.map((a, i) => (
                    <div key={i} className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
                      <div className="flex justify-between items-center mb-2">
                        <h4 className="font-medium text-gray-900 dark:text-white">{a.venue_name}</h4>
                        <span className="text-xs px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded-full text-gray-600 dark:text-gray-400">
                          {a.venue_type}
                        </span>
                      </div>
                      <div className="flex items-center gap-1 mb-2">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <span key={star} className={`text-lg ${star <= a.mobility_rating ? 'text-green-500' : 'text-gray-300 dark:text-gray-600'}`}>
                            *
                          </span>
                        ))}
                        <span className="text-sm text-gray-500 dark:text-gray-400 ml-2">{a.mobility_rating}/5</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {a.wheelchair_accessible && <span className="text-xs px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full">Wheelchair</span>}
                        {a.elevator_available && <span className="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full">Elevator</span>}
                        {a.accessible_restroom && <span className="text-xs px-2 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full">Restroom</span>}
                      </div>
                      {a.notes && <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">{a.notes}</p>}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 dark:text-gray-400 text-center py-8">
                  No accessibility data yet. Be the first to rate!
                </p>
              )}
            </div>

            {/* Submit Rating Form */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-5">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Rate Accessibility</h3>
              <div className="space-y-3">
                <input
                  type="text"
                  value={ratingForm.venue_name}
                  onChange={(e) => setRatingForm({ ...ratingForm, venue_name: e.target.value })}
                  placeholder="Venue name..."
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
                <select
                  value={ratingForm.venue_type}
                  onChange={(e) => setRatingForm({ ...ratingForm, venue_type: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="hotel">Hotel</option>
                  <option value="restaurant">Restaurant</option>
                  <option value="attraction">Attraction</option>
                  <option value="transport">Transport Hub</option>
                  <option value="worship">Place of Worship</option>
                  <option value="medical">Medical Facility</option>
                  <option value="shopping">Shopping</option>
                </select>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Mobility Rating: {ratingForm.mobility_rating}/5
                  </label>
                  <input
                    type="range"
                    min={1}
                    max={5}
                    value={ratingForm.mobility_rating}
                    onChange={(e) => setRatingForm({ ...ratingForm, mobility_rating: parseInt(e.target.value) })}
                    className="w-full"
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { key: 'wheelchair_accessible', label: 'Wheelchair' },
                    { key: 'elevator_available', label: 'Elevator' },
                    { key: 'accessible_restroom', label: 'Restroom' },
                  ].map((item) => (
                    <label key={item.key} className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                      <input
                        type="checkbox"
                        checked={ratingForm[item.key as keyof typeof ratingForm] as boolean}
                        onChange={(e) => setRatingForm({ ...ratingForm, [item.key]: e.target.checked })}
                        className="rounded"
                      />
                      {item.label}
                    </label>
                  ))}
                </div>
                <textarea
                  value={ratingForm.notes}
                  onChange={(e) => setRatingForm({ ...ratingForm, notes: e.target.value })}
                  placeholder="Additional notes..."
                  rows={2}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
                <button
                  onClick={submitRating}
                  disabled={loading || !ratingForm.venue_name}
                  className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  Submit Rating
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Medications */}
        {activeTab === 'medication' && (
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Reminders List + Add Form */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Your Medications</h3>
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-5 mb-4">
                <div className="space-y-3">
                  <input
                    type="text"
                    value={newMed.medication_name}
                    onChange={(e) => setNewMed({ ...newMed, medication_name: e.target.value })}
                    placeholder="Medication name..."
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                  <div className="grid grid-cols-2 gap-3">
                    <input
                      type="text"
                      value={newMed.dosage}
                      onChange={(e) => setNewMed({ ...newMed, dosage: e.target.value })}
                      placeholder="Dosage (e.g. 10mg)"
                      className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                    <input
                      type="time"
                      value={newMed.home_time}
                      onChange={(e) => setNewMed({ ...newMed, home_time: e.target.value })}
                      className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    />
                  </div>
                  <select
                    value={newMed.home_timezone}
                    onChange={(e) => setNewMed({ ...newMed, home_timezone: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  >
                    {TIMEZONES.map((tz) => (
                      <option key={tz} value={tz}>{tz}</option>
                    ))}
                  </select>
                  <button
                    onClick={addReminder}
                    disabled={loading || !newMed.medication_name}
                    className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                  >
                    Add Medication
                  </button>
                </div>
              </div>

              {reminders.length > 0 && (
                <div className="space-y-2">
                  {reminders.map((r) => (
                    <div key={r.id} className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 flex justify-between items-center">
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">{r.medication_name}</p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {r.dosage && `${r.dosage} - `}{r.home_time} ({r.home_timezone})
                        </p>
                      </div>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${r.is_active ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300' : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'}`}>
                        {r.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {reminders.length === 0 && !loading && (
                <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                  No medications added yet. Add your first above.
                </p>
              )}
            </div>

            {/* Timezone Adjustment */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Timezone Adjustment</h3>
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-5 mb-4">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  Adjust your medication schedule for your destination timezone
                </p>
                <select
                  value={destTimezone}
                  onChange={(e) => setDestTimezone(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white mb-3"
                >
                  {TIMEZONES.map((tz) => (
                    <option key={tz} value={tz}>{tz}</option>
                  ))}
                </select>
                <button
                  onClick={adjustMedications}
                  disabled={loading}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  Adjust Schedule
                </button>
              </div>

              {adjustedMeds.length > 0 && (
                <div className="space-y-2">
                  {adjustedMeds.map((m, i) => (
                    <div key={i} className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
                      <p className="font-medium text-gray-900 dark:text-white">{m.medication_name}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-sm text-gray-500 dark:text-gray-400">{m.original_time}</span>
                        <span className="text-gray-400">&rarr;</span>
                        <span className="text-sm font-semibold text-green-600 dark:text-green-400">{m.adjusted_time}</span>
                      </div>
                      {m.note && <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{m.note}</p>}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Insurance */}
        {activeTab === 'insurance' && (
          <div>
            <div className="mb-4 flex gap-3 items-end">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Country</label>
                <input
                  type="text"
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  placeholder="Enter country name..."
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              <button
                onClick={fetchInsurance}
                disabled={loading || !country}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                Check
              </button>
            </div>

            {insurance && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {insurance.country} - Health Insurance Guide
                  </h3>
                  <span className={`text-xs px-3 py-1 rounded-full font-medium ${riskBadge(insurance.risk_level)}`}>
                    {insurance.risk_level?.toUpperCase()} RISK
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <p className="text-sm text-gray-500 dark:text-gray-400">Avg Hospital Cost/Day</p>
                    <p className="text-xl font-bold text-gray-900 dark:text-white">
                      ${insurance.avg_hospital_cost_per_day_usd}
                    </p>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <p className="text-sm text-gray-500 dark:text-gray-400">Emergency Number</p>
                    <p className="text-xl font-bold text-gray-900 dark:text-white">{insurance.emergency_number}</p>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <p className="text-sm text-gray-500 dark:text-gray-400">Public Healthcare</p>
                    <p className="text-xl font-bold text-gray-900 dark:text-white">
                      {insurance.public_healthcare_available ? 'Available' : 'Limited'}
                    </p>
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  {Array.isArray(insurance.recommended_coverage) && insurance.recommended_coverage.length > 0 && (
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white mb-2">Recommended Coverage</h4>
                      <ul className="space-y-1">
                        {insurance.recommended_coverage.map((c, i) => (
                          <li key={i} className="text-sm text-gray-700 dark:text-gray-300 flex items-center gap-2">
                            <span className="text-green-500">*</span> {c}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {Array.isArray(insurance.vaccination_requirements) && insurance.vaccination_requirements.length > 0 && (
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white mb-2">Vaccination Requirements</h4>
                      <ul className="space-y-1">
                        {insurance.vaccination_requirements.map((v, i) => (
                          <li key={i} className="text-sm text-gray-700 dark:text-gray-300 flex items-center gap-2">
                            <span className="text-blue-500">*</span> {v}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                <div className="flex flex-wrap gap-2 mt-4">
                  {insurance.malaria_risk && (
                    <span className="text-xs px-3 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-full">Malaria Risk</span>
                  )}
                  {insurance.altitude_risk && (
                    <span className="text-xs px-3 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 rounded-full">Altitude Risk</span>
                  )}
                </div>

                {insurance.notes && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-4">{insurance.notes}</p>
                )}
              </div>
            )}

            {!insurance && !loading && (
              <p className="text-center text-gray-500 dark:text-gray-400 py-10">
                Enter a country to get health insurance recommendations
              </p>
            )}
          </div>
        )}

        {/* Fatigue Planning */}
        {activeTab === 'fatigue' && (
          <div>
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-5 mb-6">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-3">Fatigue Settings</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Max Walking (km/day): {fatigueSettings.max_walking_km}
                  </label>
                  <input
                    type="range"
                    min={1}
                    max={25}
                    value={fatigueSettings.max_walking_km}
                    onChange={(e) => setFatigueSettings({ ...fatigueSettings, max_walking_km: parseInt(e.target.value) })}
                    className="w-full"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Pace</label>
                  <select
                    value={fatigueSettings.pace}
                    onChange={(e) => setFatigueSettings({ ...fatigueSettings, pace: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  >
                    <option value="slow">Slow / Relaxed</option>
                    <option value="moderate">Moderate</option>
                    <option value="packed">Packed / Active</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Trip Days</label>
                  <input
                    type="number"
                    min={1}
                    max={14}
                    value={fatigueSettings.days}
                    onChange={(e) => setFatigueSettings({ ...fatigueSettings, days: parseInt(e.target.value) || 1 })}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
              </div>
              <button
                onClick={fetchFatiguePlan}
                disabled={loading || !destination}
                className="mt-4 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                Generate Plan
              </button>
            </div>

            {fatiguePlan.length > 0 && (
              <div className="space-y-4">
                {fatiguePlan.map((day, i) => (
                  <div key={i} className="bg-white dark:bg-gray-800 rounded-xl shadow p-5">
                    <div className="flex justify-between items-center mb-3">
                      <h4 className="font-semibold text-gray-900 dark:text-white">Day {day.day || i + 1}</h4>
                      <div className="flex gap-3 text-sm text-gray-500 dark:text-gray-400">
                        <span>Walking: {day.total_walking_km} km</span>
                        <span>Rest: {day.rest_periods}x</span>
                      </div>
                    </div>
                    <div className="space-y-2">
                      {[
                        { label: 'Morning', value: day.morning, color: 'border-l-yellow-400' },
                        { label: 'Midday Rest', value: day.midday_rest, color: 'border-l-green-400' },
                        { label: 'Afternoon', value: day.afternoon, color: 'border-l-orange-400' },
                        { label: 'Evening', value: day.evening, color: 'border-l-purple-400' },
                      ].map((block) => (
                        block.value && (
                          <div key={block.label} className={`border-l-4 ${block.color} pl-3 py-1`}>
                            <p className="text-xs font-medium text-gray-500 dark:text-gray-400">{block.label}</p>
                            <p className="text-sm text-gray-700 dark:text-gray-300">{block.value}</p>
                          </div>
                        )
                      ))}
                    </div>
                    {day.hydration_reminder && (
                      <p className="text-xs text-blue-600 dark:text-blue-400 mt-2">
                        Hydration: {day.hydration_reminder}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}

            {fatiguePlan.length === 0 && !loading && (
              <p className="text-center text-gray-500 dark:text-gray-400 py-10">
                Configure settings and generate a fatigue-aware travel plan
              </p>
            )}
          </div>
        )}
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600" />
        </div>
      )}
    </div>
  );
}
