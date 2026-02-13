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
import TravelChat from '@/components/TravelChat';

type OrderMode = 'form' | 'chat' | 'voice';
type ResultTab = 'itinerary' | 'flights' | 'hotels' | 'cars' | 'dining' | 'intelligence';

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

function parseItineraryNarrative(text: string): ParsedDay[] {
  if (!text) return [];
  const days: ParsedDay[] = [];
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
    const timePattern = /\*{0,2}(\d{1,2}:\d{2}\s*[AaPp][Mm]?)\*{0,2}\s*[-–:]\s*(.+)/g;
    let timeMatch;
    while ((timeMatch = timePattern.exec(section)) !== null) {
      const timeStr = timeMatch[1].trim();
      let activityText = timeMatch[2].trim().replace(/\*\*/g, '').replace(/\*/g, '');
      let cost: number | undefined;
      const costMatch = activityText.match(/[\(~]*\$(\d+(?:\.\d+)?)\)?/);
      if (costMatch) cost = parseFloat(costMatch[1]);
      const itemType = guessItemType(activityText);
      activities.push({ time: timeStr, title: activityText, itemType, estimatedCost: cost });
    }
    const bulletPattern = /^[-*•]\s+(?!\d{1,2}:\d{2})(.+)/gm;
    let bulletMatch;
    while ((bulletMatch = bulletPattern.exec(section)) !== null) {
      const text = bulletMatch[1].trim().replace(/\*\*/g, '').replace(/\*/g, '');
      if (activities.some(a => text.includes(a.title.slice(0, 20)))) continue;
      if (text.startsWith('#') || text.startsWith('---')) continue;
      let cost: number | undefined;
      const costMatch = text.match(/[\(~]*\$(\d+(?:\.\d+)?)\)?/);
      if (costMatch) cost = parseFloat(costMatch[1]);
      const itemType = guessItemType(text);
      activities.push({ time: undefined, title: text, itemType, estimatedCost: cost });
    }
    days.push({ dayNumber: matches[i].dayNum, title: matches[i].title, activities });
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

const ITEM_TYPE_CONFIG: Record<string, { icon: string; color: string; bg: string }> = {
  flight: { icon: '✈️', color: 'text-blue-700 dark:text-blue-300', bg: 'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-800' },
  hotel: { icon: '🏨', color: 'text-purple-700 dark:text-purple-300', bg: 'bg-purple-50 dark:bg-purple-900/30 border-purple-200 dark:border-purple-800' },
  restaurant: { icon: '🍽️', color: 'text-orange-700 dark:text-orange-300', bg: 'bg-orange-50 dark:bg-orange-900/30 border-orange-200 dark:border-orange-800' },
  attraction: { icon: '🏛️', color: 'text-emerald-700 dark:text-emerald-300', bg: 'bg-emerald-50 dark:bg-emerald-900/30 border-emerald-200 dark:border-emerald-800' },
  activity: { icon: '🎯', color: 'text-indigo-700 dark:text-indigo-300', bg: 'bg-indigo-50 dark:bg-indigo-900/30 border-indigo-200 dark:border-indigo-800' },
  transport: { icon: '🚕', color: 'text-cyan-700 dark:text-cyan-300', bg: 'bg-cyan-50 dark:bg-cyan-900/30 border-cyan-200 dark:border-cyan-800' },
  note: { icon: '📝', color: 'text-gray-700 dark:text-gray-300', bg: 'bg-gray-50 dark:bg-gray-900/30 border-gray-200 dark:border-gray-800' },
};

const TAB_CONFIG: { key: ResultTab; label: string; icon: string }[] = [
  { key: 'itinerary', label: 'Itinerary', icon: '📅' },
  { key: 'flights', label: 'Flights', icon: '✈️' },
  { key: 'hotels', label: 'Hotels', icon: '🏨' },
  { key: 'cars', label: 'Cars', icon: '🚗' },
  { key: 'dining', label: 'Dining', icon: '🍽️' },
  { key: 'intelligence', label: 'Intelligence', icon: '🧠' },
];

const AIPlannerPage = () => {
  const navigate = useNavigate();
  const { showSuccess, showError } = useToast();
  const { isAuthenticated, user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [orderMode, setOrderMode] = useState<OrderMode>('form');
  const [activeTab, setActiveTab] = useState<ResultTab>('itinerary');
  const [expandedDay, setExpandedDay] = useState<number | null>(1);

  // Form state
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [departureDate, setDepartureDate] = useState('');
  const [returnDate, setReturnDate] = useState('');
  const [passengers, setPassengers] = useState(1);
  const [budget, setBudget] = useState('');
  const [cuisine, setCuisine] = useState('');
  const [chatParams, setChatParams] = useState<any>({});

  const handlePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/agents/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: `Plan a trip from ${origin} to ${destination}`,
          origin, destination,
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
        setActiveTab('itinerary');
        setExpandedDay(1);
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

  const handleChatPlanReady = (planResult: any) => {
    const merged = { ...planResult, success: planResult.success !== false };
    setResult(merged);
    setActiveTab('itinerary');
    setExpandedDay(1);
    if (chatParams.origin) setOrigin(chatParams.origin);
    if (chatParams.destination) setDestination(chatParams.destination);
    if (chatParams.departure_date) setDepartureDate(chatParams.departure_date);
    if (chatParams.return_date) setReturnDate(chatParams.return_date);
    if (chatParams.passengers) setPassengers(chatParams.passengers);
    if (chatParams.budget) setBudget(String(chatParams.budget));
    if (chatParams.cuisine) setCuisine(chatParams.cuisine);
    showSuccess('AI travel planning complete!');
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
      const parsedDays = parseItineraryNarrative(result.itinerary_text || '');
      const startD = new Date(start);
      const endD = new Date(end);
      const totalDays = Math.max(1, Math.ceil((endD.getTime() - startD.getTime()) / (1000 * 60 * 60 * 24)) + 1);
      const itinerary = await createItinerary({
        title: `AI Trip: ${origin} to ${destination}`,
        destination,
        start_date: start,
        end_date: end,
        status: 'planned',
        number_of_travelers: passengers,
        estimated_budget: totalCost ? String(totalCost) : (budget ? budget : undefined),
        currency: 'USD',
        description: `AI-planned trip from ${origin} to ${destination}. ${passengers} passenger(s).`,
        ai_narrative: result.itinerary_text || '',
      });
      const itineraryId = Number(itinerary.id);
      for (let d = 1; d <= totalDays; d++) {
        const dayDate = new Date(startD);
        dayDate.setDate(dayDate.getDate() + d - 1);
        const dateStr = dayDate.toISOString().split('T')[0];
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
        if (isFirstDay) {
          if (rec?.recommended_flight) {
            const flight = rec.recommended_flight;
            await createItineraryItem({
              day: dayId, item_type: 'flight', order: itemOrder++,
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
              day: dayId, item_type: 'hotel', order: itemOrder++,
              title: `Check in: ${hotel.name || hotel.hotel_name}`,
              description: `${hotel.stars || hotel.star_rating || 0} stars`,
              start_time: '15:00',
              estimated_cost: hotel.price || hotel.price_per_night || undefined,
              location_name: hotel.address || destination,
            });
          }
        }
        if (isLastDay && totalDays > 1) {
          if (rec?.recommended_hotel) {
            const hotel = rec.recommended_hotel;
            await createItineraryItem({
              day: dayId, item_type: 'hotel', order: itemOrder++,
              title: `Check out: ${hotel.name || hotel.hotel_name}`,
              start_time: '10:00',
              location_name: hotel.address || destination,
            });
          }
        }
        if (parsedDay && parsedDay.activities.length > 0) {
          for (const activity of parsedDay.activities) {
            const lowerTitle = activity.title.toLowerCase();
            if (isFirstDay && activity.itemType === 'flight' && itemOrder > 0) continue;
            if (isFirstDay && lowerTitle.includes('check') && lowerTitle.includes('in') && activity.itemType === 'hotel') continue;
            if (isLastDay && lowerTitle.includes('check') && lowerTitle.includes('out') && activity.itemType === 'hotel') continue;
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
              day: dayId, item_type: activity.itemType, order: itemOrder++,
              title: activity.title, start_time: timeHHMM, estimated_cost: activity.estimatedCost,
            });
          }
        } else if (!isFirstDay && !isLastDay) {
          await createItineraryItem({
            day: dayId, item_type: 'activity', order: 0,
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

  // Parse itinerary for structured display
  const parsedDays = result?.itinerary_text ? parseItineraryNarrative(result.itinerary_text) : [];

  // Extract budget table from narrative
  const extractBudgetTable = (text: string) => {
    if (!text) return [];
    const rows: { category: string; cost: string }[] = [];
    const tableMatch = text.match(/\|.*Category.*Cost.*\|[\s\S]*?(?=\n\n|\n#|$)/i);
    if (tableMatch) {
      const lines = tableMatch[0].split('\n').filter(l => l.trim().startsWith('|'));
      for (const line of lines) {
        const cells = line.split('|').map(c => c.trim()).filter(Boolean);
        if (cells.length >= 2 && !/^[-:]+$/.test(cells[0]) && !/Category/i.test(cells[0])) {
          rows.push({ category: cells[0].replace(/\*\*/g, ''), cost: cells[1].replace(/\*\*/g, '') });
        }
      }
    }
    return rows;
  };

  const budgetRows = extractBudgetTable(result?.itinerary_text || '');

  const rec = result?.recommendation;
  const intel = result?.enhanced_data?.destination_intelligence;

  // Compute trip date range string
  const formatDateRange = () => {
    if (!departureDate) return '';
    const opts: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric', year: 'numeric' };
    const d1 = new Date(departureDate + 'T12:00:00');
    const d2 = returnDate ? new Date(returnDate + 'T12:00:00') : d1;
    return `${d1.toLocaleDateString('en-US', opts)} - ${d2.toLocaleDateString('en-US', opts)}`;
  };

  const numNights = (() => {
    if (!departureDate || !returnDate) return 0;
    const d1 = new Date(departureDate);
    const d2 = new Date(returnDate);
    return Math.max(1, Math.ceil((d2.getTime() - d1.getTime()) / (1000 * 60 * 60 * 24)));
  })();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
        AI Travel Planner
      </h1>
      <p className="text-gray-600 dark:text-gray-400 mb-4">
        Let our AI agents find and evaluate the best travel options for you
      </p>

      {/* Order Mode Switcher */}
      <div className="flex gap-2 mb-6">
        {[
          { mode: 'form' as OrderMode, icon: '📝', label: 'Form' },
          { mode: 'chat' as OrderMode, icon: '💬', label: 'Chat' },
          { mode: 'voice' as OrderMode, icon: '🎙️', label: 'Voice' },
        ].map(({ mode, icon, label }) => (
          <button
            key={mode}
            onClick={() => setOrderMode(mode)}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium transition-all ${
              orderMode === mode
                ? 'bg-primary-600 text-white shadow-md'
                : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 hover:border-primary-400'
            }`}
          >
            {icon} {label}
          </button>
        ))}
      </div>

      {/* MODE 1: Form */}
      {orderMode === 'form' && (
        <Card className="mb-8">
          <CardHeader><CardTitle>Travel Details</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={handlePlan} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input label="Origin (Airport Code)" value={origin} onChange={(e) => setOrigin(e.target.value)} placeholder="e.g., JFK, CDG, LHR" required />
                <Input label="Destination (Airport Code)" value={destination} onChange={(e) => setDestination(e.target.value)} placeholder="e.g., LAX, BER, NRT" required />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input label="Departure Date" type="date" value={departureDate} onChange={(e) => setDepartureDate(e.target.value)} required />
                <Input label="Return Date (Optional)" type="date" value={returnDate} onChange={(e) => setReturnDate(e.target.value)} />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input label="Passengers" type="number" min="1" value={passengers} onChange={(e) => setPassengers(Number(e.target.value))} required />
                <Input label="Budget (USD, Optional)" type="number" value={budget} onChange={(e) => setBudget(e.target.value)} placeholder="e.g., 500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Preferred Cuisine (Optional)</label>
                <select value={cuisine} onChange={(e) => setCuisine(e.target.value)} className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500">
                  <option value="">Any Cuisine</option>
                  {['American','Italian','Mexican','Chinese','Japanese','Indian','Thai','French','Mediterranean','Seafood'].map(c => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
              <Button type="submit" className="w-full" size="lg" isLoading={loading} disabled={loading}>
                {loading ? 'AI Agents Working...' : 'Plan My Trip with AI'}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      {/* MODE 2: Chat */}
      {orderMode === 'chat' && (
        <div className="mb-8">
          <TravelChat onPlanReady={handleChatPlanReady} onParamsExtracted={setChatParams} />
        </div>
      )}

      {/* MODE 3: Voice */}
      {orderMode === 'voice' && (
        <div className="mb-8">
          <Card className="border-2 border-dashed border-purple-300 dark:border-purple-700">
            <CardContent className="py-6 text-center">
              <div className="text-5xl mb-4">🎙️</div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Voice-Powered Trip Planning</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 max-w-md mx-auto">
                Speak naturally to plan your trip. The AI will listen, understand your requirements, ask follow-up questions by voice, and create your itinerary.
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500 mb-4">Uses Web Speech API for listening + ElevenLabs for AI voice responses</p>
            </CardContent>
          </Card>
          <div className="mt-4">
            <TravelChat onPlanReady={handleChatPlanReady} onParamsExtracted={setChatParams} initialVoiceEnabled={true} key="voice-chat" />
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <Card>
          <CardContent className="py-12">
            <Loading size="lg" text="AI agents are analyzing your request..." />
            <div className="mt-6 grid grid-cols-2 md:grid-cols-3 gap-3 max-w-lg mx-auto">
              {[
                { icon: '✈️', text: 'Searching flights' },
                { icon: '🏨', text: 'Finding hotels' },
                { icon: '🚗', text: 'Checking rentals' },
                { icon: '🍽️', text: 'Finding restaurants' },
                { icon: '💰', text: 'Optimizing budget' },
                { icon: '🎯', text: 'Compiling results' },
              ].map(({ icon, text }) => (
                <div key={text} className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 rounded-lg px-3 py-2">
                  <span className="animate-pulse">{icon}</span> {text}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* ═══════════════════ RESULTS ═══════════════════ */}
      {result && result.success && (
        <div className="space-y-6">

          {/* ── Trip Overview Banner ── */}
          <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-primary-600 via-primary-700 to-indigo-800 text-white p-6 md:p-8 shadow-xl">
            <div className="absolute inset-0 opacity-10">
              <div className="absolute -right-20 -top-20 w-80 h-80 rounded-full bg-white/20"></div>
              <div className="absolute -left-10 -bottom-10 w-60 h-60 rounded-full bg-white/10"></div>
            </div>
            <div className="relative z-10">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                  <p className="text-primary-200 text-sm font-medium uppercase tracking-wider mb-1">AI-Planned Trip</p>
                  <h2 className="text-2xl md:text-3xl font-bold">
                    {origin || 'Origin'} &rarr; {destination || 'Destination'}
                  </h2>
                  <p className="text-primary-100 mt-1">{formatDateRange()}{passengers > 1 ? ` · ${passengers} travelers` : ''}</p>
                </div>
                <div className="flex gap-4 flex-wrap">
                  {/* Save Button in Banner */}
                  <button
                    onClick={handleSaveAsItinerary}
                    disabled={saving || !isAuthenticated}
                    className="px-5 py-2.5 bg-white/20 hover:bg-white/30 backdrop-blur rounded-xl text-sm font-medium transition-all border border-white/30 disabled:opacity-50"
                  >
                    {saving ? 'Saving...' : 'Save as Itinerary'}
                  </button>
                </div>
              </div>

              {/* Key Stats Row */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mt-6">
                {[
                  { label: 'Est. Total', value: rec?.total_estimated_cost ? `$${rec.total_estimated_cost}` : 'N/A', accent: true },
                  { label: 'Flights', value: rec?.summary?.flights_found || 0 },
                  { label: 'Hotels', value: rec?.summary?.hotels_found || 0 },
                  { label: 'Cars', value: rec?.summary?.cars_found || 0 },
                  { label: 'Restaurants', value: rec?.summary?.restaurants_found || 0 },
                ].map(({ label, value, accent }) => (
                  <div key={label} className={`rounded-xl p-3 ${accent ? 'bg-white/20 backdrop-blur' : 'bg-white/10'}`}>
                    <p className="text-xs text-primary-200">{label}</p>
                    <p className={`text-xl font-bold ${accent ? 'text-white' : 'text-primary-100'}`}>{value}</p>
                  </div>
                ))}
              </div>
              {!isAuthenticated && (
                <p className="text-xs text-primary-200 mt-3">Sign in to save itineraries</p>
              )}
            </div>
          </div>

          {/* ── Tab Navigation ── */}
          <div className="border-b border-gray-200 dark:border-gray-700 overflow-x-auto">
            <nav className="flex gap-0 min-w-max">
              {TAB_CONFIG.map(({ key, label, icon }) => {
                // Show badge count
                let count: number | null = null;
                if (key === 'flights') count = rec?.summary?.flights_found || 0;
                if (key === 'hotels') count = rec?.summary?.hotels_found || 0;
                if (key === 'cars') count = rec?.summary?.cars_found || 0;
                if (key === 'dining') count = rec?.summary?.restaurants_found || 0;
                if (key === 'itinerary') count = parsedDays.length || null;

                return (
                  <button
                    key={key}
                    onClick={() => setActiveTab(key)}
                    className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-all whitespace-nowrap ${
                      activeTab === key
                        ? 'border-primary-600 text-primary-600 dark:text-primary-400 dark:border-primary-400'
                        : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
                    }`}
                  >
                    <span>{icon}</span>
                    {label}
                    {count !== null && count > 0 && (
                      <span className={`ml-1 px-1.5 py-0.5 rounded-full text-xs ${
                        activeTab === key
                          ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
                          : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
                      }`}>
                        {count}
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* ══════ TAB: ITINERARY ══════ */}
          {activeTab === 'itinerary' && (
            <div className="space-y-4">
              {/* Budget Summary Table */}
              {budgetRows.length > 0 && (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                  <div className="px-5 py-3 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                      💰 Budget Summary
                    </h3>
                  </div>
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-100 dark:border-gray-700">
                        <th className="text-left px-5 py-2.5 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Category</th>
                        <th className="text-right px-5 py-2.5 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Cost</th>
                      </tr>
                    </thead>
                    <tbody>
                      {budgetRows.map((row, i) => {
                        const isTotal = /total/i.test(row.category);
                        const isBudget = /budget/i.test(row.category);
                        const isRemaining = /remaining|over/i.test(row.category);
                        return (
                          <tr key={i} className={`border-b border-gray-50 dark:border-gray-800 ${isTotal || isBudget ? 'bg-gray-50 dark:bg-gray-900' : ''}`}>
                            <td className={`px-5 py-2.5 ${isTotal || isBudget ? 'font-semibold text-gray-900 dark:text-white' : 'text-gray-700 dark:text-gray-300'}`}>
                              {row.category}
                            </td>
                            <td className={`px-5 py-2.5 text-right font-medium ${
                              isTotal ? 'text-primary-600 dark:text-primary-400 text-base font-bold' :
                              isRemaining ? (row.cost.includes('-') ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400') :
                              'text-gray-900 dark:text-white'
                            }`}>
                              {row.cost}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Day-by-Day Timeline */}
              {parsedDays.length > 0 ? (
                <div className="space-y-3">
                  {parsedDays.map((day) => {
                    const isExpanded = expandedDay === day.dayNumber;
                    const dayTotal = day.activities.reduce((sum, a) => sum + (a.estimatedCost || 0), 0);
                    return (
                      <div key={day.dayNumber} className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden transition-all">
                        {/* Day Header */}
                        <button
                          onClick={() => setExpandedDay(isExpanded ? null : day.dayNumber)}
                          className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
                        >
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-primary-100 dark:bg-primary-900/50 text-primary-700 dark:text-primary-300 flex items-center justify-center font-bold text-sm">
                              D{day.dayNumber}
                            </div>
                            <div>
                              <h3 className="font-semibold text-gray-900 dark:text-white">Day {day.dayNumber}: {day.title}</h3>
                              <p className="text-xs text-gray-500 dark:text-gray-400">
                                {day.activities.length} activit{day.activities.length === 1 ? 'y' : 'ies'}
                                {dayTotal > 0 && ` · ~$${dayTotal.toFixed(0)}`}
                              </p>
                            </div>
                          </div>
                          <svg className={`w-5 h-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        </button>

                        {/* Day Activities */}
                        {isExpanded && (
                          <div className="border-t border-gray-100 dark:border-gray-700 px-5 py-4">
                            <div className="space-y-2.5">
                              {day.activities.map((activity, idx) => {
                                const config = ITEM_TYPE_CONFIG[activity.itemType] || ITEM_TYPE_CONFIG.activity;
                                return (
                                  <div key={idx} className={`flex items-start gap-3 p-3 rounded-lg border ${config.bg} transition-all`}>
                                    {/* Timeline dot */}
                                    <div className="flex-shrink-0 mt-0.5">
                                      <span className="text-lg">{config.icon}</span>
                                    </div>
                                    {/* Content */}
                                    <div className="flex-1 min-w-0">
                                      <div className="flex items-start justify-between gap-2">
                                        <p className={`text-sm font-medium ${config.color}`}>{activity.title}</p>
                                        {activity.estimatedCost !== undefined && activity.estimatedCost > 0 && (
                                          <span className="flex-shrink-0 text-xs font-semibold text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 px-2 py-0.5 rounded-md shadow-sm">
                                            ${activity.estimatedCost}
                                          </span>
                                        )}
                                      </div>
                                    </div>
                                    {/* Time Badge */}
                                    {activity.time && (
                                      <div className="flex-shrink-0">
                                        <span className="text-xs font-medium text-gray-600 dark:text-gray-400 bg-white dark:bg-gray-700 px-2 py-1 rounded-md shadow-sm">
                                          {activity.time}
                                        </span>
                                      </div>
                                    )}
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : result.itinerary_text ? (
                /* Fallback: raw narrative if parsing didn't extract days */
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm p-6">
                  <div
                    className="prose prose-sm dark:prose-invert max-w-none prose-headings:text-gray-900 dark:prose-headings:text-white prose-h2:text-lg prose-h2:font-bold prose-h2:mt-6 prose-h2:mb-2 prose-h3:text-base prose-h3:font-semibold prose-p:text-gray-700 dark:prose-p:text-gray-300 prose-p:my-1 prose-li:text-gray-700 dark:prose-li:text-gray-300 prose-strong:text-gray-900 dark:prose-strong:text-white prose-ul:my-1 prose-ol:my-1"
                    dangerouslySetInnerHTML={{
                      __html: (() => {
                        let html = result.itinerary_text;
                        html = html.replace(
                          /(?:^\|.+\|$\n?)+/gm,
                          (tableBlock: string) => {
                            const rows = tableBlock.trim().split('\n').filter((r: string) => r.trim());
                            if (rows.length < 2) return tableBlock;
                            let table = '<table class="w-full text-sm border-collapse my-3">';
                            rows.forEach((row: string, i: number) => {
                              if (/^\|[\s\-:|]+\|$/.test(row.trim())) return;
                              const cells = row.split('|').filter((c: string, ci: number, arr: string[]) => ci > 0 && ci < arr.length - 1);
                              const tag = i === 0 ? 'th' : 'td';
                              const cls = i === 0 ? 'bg-gray-100 dark:bg-gray-800 font-semibold' : '';
                              table += `<tr class="${cls}">`;
                              cells.forEach((cell: string) => {
                                table += `<${tag} class="border border-gray-200 dark:border-gray-700 px-3 py-1.5">${cell.trim()}</${tag}>`;
                              });
                              table += '</tr>';
                            });
                            table += '</table>';
                            return table;
                          }
                        );
                        html = html
                          .replace(/^### (.*$)/gm, '<h3>$1</h3>')
                          .replace(/^## (.*$)/gm, '<h2>$1</h2>')
                          .replace(/^# (.*$)/gm, '<h1>$1</h1>')
                          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                          .replace(/\*(.*?)\*/g, '<em>$1</em>')
                          .replace(/^- (.*$)/gm, '<li>$1</li>')
                          .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
                          .replace(/\n\n/g, '</p><p>')
                          .replace(/\n/g, '<br/>');
                        return html;
                      })()
                    }}
                  />
                </div>
              ) : null}
            </div>
          )}

          {/* ══════ TAB: FLIGHTS ══════ */}
          {activeTab === 'flights' && (
            <div className="space-y-6">
              {/* Recommended Flight */}
              {rec?.recommended_flight && (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                  <div className="px-5 py-3 bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/20 border-b border-blue-200 dark:border-blue-800 flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-200 flex items-center gap-2">
                      <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                      Top Pick - Best Value Flight
                    </h3>
                    <span className="text-2xl font-bold text-blue-700 dark:text-blue-300">${rec.recommended_flight.price}</span>
                  </div>
                  <div className="p-5">
                    {/* Airline Header */}
                    <div className="flex items-center gap-3 mb-5">
                      {rec.recommended_flight.airline_logo && (
                        <img src={rec.recommended_flight.airline_logo} alt="" className="h-10 w-10 object-contain rounded" />
                      )}
                      <div>
                        <p className="font-semibold text-gray-900 dark:text-white text-lg">{rec.recommended_flight.airline}</p>
                        {rec.recommended_flight.flight_number && (
                          <p className="text-sm text-gray-500">Flight {rec.recommended_flight.flight_number}</p>
                        )}
                      </div>
                    </div>
                    {/* Route Visual */}
                    <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4 p-4 bg-gray-50 dark:bg-gray-900 rounded-xl mb-5">
                      <div>
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">
                          {rec.recommended_flight.departure_time?.split(' ')[1] || rec.recommended_flight.departure_time}
                        </p>
                        <p className="text-lg font-semibold text-gray-700 dark:text-gray-300">{rec.recommended_flight.departure_airport_code}</p>
                        <p className="text-xs text-gray-500 mt-0.5">{rec.recommended_flight.departure_airport}</p>
                      </div>
                      <div className="text-center px-4">
                        <p className="text-xs text-gray-500 mb-2">
                          {rec.recommended_flight.duration ? `${Math.floor(rec.recommended_flight.duration / 60)}h ${rec.recommended_flight.duration % 60}m` : ''}
                        </p>
                        <div className="flex items-center">
                          <div className="w-2 h-2 rounded-full bg-primary-500"></div>
                          <div className="h-px bg-gray-300 dark:bg-gray-600 flex-1 mx-1"></div>
                          <span className="text-base">✈️</span>
                          <div className="h-px bg-gray-300 dark:bg-gray-600 flex-1 mx-1"></div>
                          <div className="w-2 h-2 rounded-full bg-primary-500"></div>
                        </div>
                        <p className="text-xs text-gray-500 mt-2 font-medium">
                          {rec.recommended_flight.stops === 0 ? 'Nonstop' : `${rec.recommended_flight.stops} stop${rec.recommended_flight.stops > 1 ? 's' : ''}`}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-gray-900 dark:text-white">
                          {rec.recommended_flight.arrival_time?.split(' ')[1] || rec.recommended_flight.arrival_time}
                        </p>
                        <p className="text-lg font-semibold text-gray-700 dark:text-gray-300">{rec.recommended_flight.arrival_airport_code}</p>
                        <p className="text-xs text-gray-500 mt-0.5">{rec.recommended_flight.arrival_airport}</p>
                      </div>
                    </div>
                    {/* Flight Details Grid */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      {[
                        rec.recommended_flight.aircraft && { label: 'Aircraft', value: rec.recommended_flight.aircraft },
                        rec.recommended_flight.travel_class && { label: 'Class', value: rec.recommended_flight.travel_class },
                        rec.recommended_flight.legroom && { label: 'Legroom', value: rec.recommended_flight.legroom },
                        rec.recommended_flight.carbon_emissions?.this_flight && { label: 'CO2', value: `${rec.recommended_flight.carbon_emissions.this_flight} kg` },
                      ].filter(Boolean).map((item: any, idx) => (
                        <div key={idx} className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3">
                          <p className="text-xs text-gray-500 uppercase tracking-wider">{item.label}</p>
                          <p className="text-sm font-semibold text-gray-900 dark:text-white mt-0.5">{item.value}</p>
                        </div>
                      ))}
                    </div>
                    {/* Budget Status */}
                    {rec.recommended_flight.goal_score !== undefined && (
                      <div className={`mt-4 p-3 rounded-lg text-sm ${
                        rec.recommended_flight.budget_status === 'within budget'
                          ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300'
                          : 'bg-orange-50 dark:bg-orange-900/20 text-orange-700 dark:text-orange-300'
                      }`}>
                        {rec.recommended_flight.budget_status === 'within budget'
                          ? `Within budget - saves $${rec.recommended_flight.savings}`
                          : `Over budget by $${rec.recommended_flight.budget_difference}`}
                        <span className="ml-3 text-xs opacity-75">Goal Score: {rec.recommended_flight.goal_score > 0 ? '+' : ''}{rec.recommended_flight.goal_score}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Alternative Flights Table */}
              {result.flights?.flights && result.flights.flights.length > 1 && (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                  <div className="px-5 py-3 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Alternative Flights</h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
                          <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Airline</th>
                          <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Route</th>
                          <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Departure</th>
                          <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Arrival</th>
                          <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Stops</th>
                          <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Duration</th>
                          <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Price</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.flights.flights.slice(1, 8).map((f: any, idx: number) => (
                          <tr key={idx} className="border-b border-gray-50 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors">
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-2">
                                {f.airline_logo && <img src={f.airline_logo} alt="" className="h-5 w-5 object-contain" />}
                                <span className="font-medium text-gray-900 dark:text-white">{f.airline}</span>
                              </div>
                            </td>
                            <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{f.departure_airport_code} → {f.arrival_airport_code}</td>
                            <td className="px-4 py-3 text-center text-gray-900 dark:text-white font-medium">{f.departure_time?.split(' ')[1] || f.departure_time}</td>
                            <td className="px-4 py-3 text-center text-gray-900 dark:text-white font-medium">{f.arrival_time?.split(' ')[1] || f.arrival_time}</td>
                            <td className="px-4 py-3 text-center">
                              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${f.stops === 0 ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300' : 'bg-yellow-100 dark:bg-yellow-900 text-yellow-700 dark:text-yellow-300'}`}>
                                {f.stops === 0 ? 'Nonstop' : `${f.stops} stop${f.stops > 1 ? 's' : ''}`}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-center text-gray-600 dark:text-gray-400">
                              {f.duration ? `${Math.floor(f.duration / 60)}h ${f.duration % 60}m` : '-'}
                            </td>
                            <td className="px-4 py-3 text-right font-bold text-primary-600 dark:text-primary-400">${f.price}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {!rec?.recommended_flight && (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-8 text-center text-gray-500">
                  <p className="text-lg">No flight data available</p>
                  <p className="text-sm mt-1">Try adjusting your search parameters</p>
                </div>
              )}
            </div>
          )}

          {/* ══════ TAB: HOTELS ══════ */}
          {activeTab === 'hotels' && (
            <div className="space-y-6">
              {rec?.recommended_hotel && (() => {
                const h = rec.recommended_hotel;
                return (
                  <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                    <div className="px-5 py-3 bg-gradient-to-r from-green-50 to-emerald-100 dark:from-green-900/30 dark:to-emerald-800/20 border-b border-green-200 dark:border-green-800 flex items-center justify-between">
                      <h3 className="text-sm font-semibold text-green-900 dark:text-green-200 flex items-center gap-2">
                        <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                        Top Pick - Best Value Hotel
                      </h3>
                      <div className="text-right">
                        <span className="text-2xl font-bold text-green-700 dark:text-green-300">${h.price || h.price_per_night}</span>
                        <span className="text-sm text-green-600 dark:text-green-400 ml-1">/night</span>
                      </div>
                    </div>
                    <div className="p-5">
                      <div className="flex flex-col md:flex-row gap-5">
                        {/* Hotel Image */}
                        {h.images?.[0] && (
                          <img src={h.images[0]} alt={h.name || h.hotel_name} className="w-full md:w-72 h-52 object-cover rounded-xl shadow-sm" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                        )}
                        <div className="flex-1 space-y-4">
                          <div>
                            <h3 className="text-xl font-bold text-gray-900 dark:text-white">{h.name || h.hotel_name}</h3>
                            <div className="flex items-center gap-2 mt-1">
                              <span className="text-yellow-500">{'⭐'.repeat(Math.round(h.stars || h.star_rating || 0))}</span>
                              {h.guest_rating > 0 && (
                                <span className="text-sm text-gray-500">({h.guest_rating} guest rating)</span>
                              )}
                            </div>
                          </div>
                          {/* Info Grid */}
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                            {[
                              h.check_in_time && { label: 'Check-in', value: h.check_in_time },
                              h.check_out_time && { label: 'Check-out', value: h.check_out_time },
                              h.distance_from_center && { label: 'Location', value: h.distance_from_center },
                              numNights > 0 && { label: 'Total Stay', value: `$${((h.price || h.price_per_night) * numNights).toFixed(0)} (${numNights} nights)` },
                            ].filter(Boolean).map((item: any, idx) => (
                              <div key={idx} className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3">
                                <p className="text-xs text-gray-500 uppercase tracking-wider">{item.label}</p>
                                <p className="text-sm font-semibold text-gray-900 dark:text-white mt-0.5">{item.value}</p>
                              </div>
                            ))}
                          </div>
                          {h.address && (
                            <p className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-1">
                              <span className="flex-shrink-0">📍</span> {h.address}
                            </p>
                          )}
                          {h.amenities && h.amenities.length > 0 && (
                            <div className="flex flex-wrap gap-1.5">
                              {h.amenities.slice(0, 10).map((a: string, idx: number) => (
                                <span key={idx} className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-2.5 py-1 rounded-full">{a}</span>
                              ))}
                              {h.amenities.length > 10 && <span className="text-xs text-gray-500 px-2 py-1">+{h.amenities.length - 10} more</span>}
                            </div>
                          )}
                          {h.recommendation && (
                            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 text-sm text-blue-700 dark:text-blue-300">
                              {h.recommendation}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* Alternative Hotels Table */}
              {rec?.top_5_hotels && rec.top_5_hotels.length > 1 && (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                  <div className="px-5 py-3 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Alternative Hotels</h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
                          <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Hotel</th>
                          <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Stars</th>
                          <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Rating</th>
                          <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Score</th>
                          <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Price/Night</th>
                          <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rec.top_5_hotels.slice(1, 8).map((h: any, idx: number) => (
                          <tr key={idx} className="border-b border-gray-50 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors">
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-3">
                                {h.images?.[0] ? (
                                  <img src={h.images[0]} alt="" className="w-12 h-12 rounded-lg object-cover flex-shrink-0" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                                ) : (
                                  <div className="w-12 h-12 rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-lg flex-shrink-0">🏨</div>
                                )}
                                <span className="font-medium text-gray-900 dark:text-white">{h.name || h.hotel_name}</span>
                              </div>
                            </td>
                            <td className="px-4 py-3 text-center text-yellow-500">{'⭐'.repeat(Math.round(h.stars || h.star_rating || 0))}</td>
                            <td className="px-4 py-3 text-center text-gray-700 dark:text-gray-300">{h.guest_rating || '-'}</td>
                            <td className="px-4 py-3 text-center">
                              <span className="px-2 py-0.5 bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-full text-xs font-medium">
                                {h.utility_score || h.combined_utility_score || '-'}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-right font-bold text-primary-600 dark:text-primary-400">${h.price || h.price_per_night}</td>
                            <td className="px-4 py-3 text-right text-gray-600 dark:text-gray-400">
                              {numNights > 0 ? `$${((h.price || h.price_per_night) * numNights).toFixed(0)}` : '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {!rec?.recommended_hotel && (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-8 text-center text-gray-500">
                  <p className="text-lg">No hotel data available</p>
                  <p className="text-sm mt-1">Hotels at this location don't have current pricing data</p>
                </div>
              )}
            </div>
          )}

          {/* ══════ TAB: CARS ══════ */}
          {activeTab === 'cars' && (
            <div className="space-y-6">
              {rec?.recommended_car && (() => {
                const c = rec.recommended_car;
                return (
                  <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                    <div className="px-5 py-3 bg-gradient-to-r from-orange-50 to-amber-100 dark:from-orange-900/30 dark:to-amber-800/20 border-b border-orange-200 dark:border-orange-800 flex items-center justify-between">
                      <h3 className="text-sm font-semibold text-orange-900 dark:text-orange-200 flex items-center gap-2">
                        <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                        Top Pick - Best Value Car Rental
                      </h3>
                      <div className="text-right">
                        <span className="text-2xl font-bold text-orange-700 dark:text-orange-300">${c.price_per_day}</span>
                        <span className="text-sm text-orange-600 dark:text-orange-400 ml-1">/day</span>
                      </div>
                    </div>
                    <div className="p-5 space-y-4">
                      <div className="flex items-center gap-4">
                        <div className="w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-xl flex items-center justify-center text-3xl">🚗</div>
                        <div>
                          <h3 className="text-xl font-bold text-gray-900 dark:text-white">{c.rental_company}</h3>
                          <p className="text-gray-500">{c.vehicle || c.car_type}</p>
                        </div>
                        {c.rating > 0 && (
                          <div className="ml-auto text-right">
                            <div className="flex items-center gap-1">
                              <span className="text-yellow-500">⭐</span>
                              <span className="font-semibold">{c.rating.toFixed(1)}</span>
                            </div>
                            {c.reviews > 0 && <p className="text-xs text-gray-500">{c.reviews} reviews</p>}
                          </div>
                        )}
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                        {[
                          { label: 'Type', value: c.car_type },
                          { label: 'Total', value: `$${c.total_price}` },
                          { label: 'Days', value: `${c.rental_days} days` },
                          { label: 'Mileage', value: c.mileage },
                          c.deposit > 0 && { label: 'Deposit', value: `$${c.deposit}` },
                        ].filter(Boolean).map((item: any, idx) => (
                          <div key={idx} className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3">
                            <p className="text-xs text-gray-500 uppercase tracking-wider">{item.label}</p>
                            <p className="text-sm font-semibold text-gray-900 dark:text-white mt-0.5">{item.value}</p>
                          </div>
                        ))}
                      </div>
                      {c.features && c.features.length > 0 && (
                        <div className="flex flex-wrap gap-1.5">
                          {c.features.slice(0, 8).map((f: string, idx: number) => (
                            <span key={idx} className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-2.5 py-1 rounded-full">{f}</span>
                          ))}
                        </div>
                      )}
                      {c.pickup_location && (
                        <p className="text-sm text-gray-600 dark:text-gray-400"><span className="font-medium">Pickup:</span> {c.pickup_location}</p>
                      )}
                      {c.recommendation && (
                        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 text-sm text-blue-700 dark:text-blue-300">{c.recommendation}</div>
                      )}
                    </div>
                  </div>
                );
              })()}

              {/* Alternative Cars Table */}
              {rec?.top_5_cars && rec.top_5_cars.length > 1 && (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                  <div className="px-5 py-3 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Alternative Car Rentals</h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
                          <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Company</th>
                          <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Vehicle</th>
                          <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Type</th>
                          <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Rating</th>
                          <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Score</th>
                          <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Per Day</th>
                          <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rec.top_5_cars.slice(1, 8).map((c: any, idx: number) => (
                          <tr key={idx} className="border-b border-gray-50 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors">
                            <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">{c.rental_company}</td>
                            <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{c.vehicle || c.car_type}</td>
                            <td className="px-4 py-3 text-center">
                              <span className="px-2 py-0.5 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full text-xs font-medium capitalize">{c.car_type}</span>
                            </td>
                            <td className="px-4 py-3 text-center">{c.rating > 0 ? `⭐ ${c.rating.toFixed(1)}` : '-'}</td>
                            <td className="px-4 py-3 text-center">
                              {c.utility_score !== undefined && (
                                <span className="px-2 py-0.5 bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-full text-xs font-medium">{c.utility_score}</span>
                              )}
                            </td>
                            <td className="px-4 py-3 text-right font-bold text-primary-600 dark:text-primary-400">${c.price_per_day}</td>
                            <td className="px-4 py-3 text-right text-gray-600 dark:text-gray-400">${c.total_price}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {!rec?.recommended_car && (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-8 text-center text-gray-500">
                  <p className="text-lg">No car rental data available</p>
                  <p className="text-sm mt-1">Car rentals at this location don't have current pricing data</p>
                </div>
              )}
            </div>
          )}

          {/* ══════ TAB: DINING ══════ */}
          {activeTab === 'dining' && (
            <div className="space-y-6">
              {rec?.recommended_restaurant && (() => {
                const r = rec.recommended_restaurant;
                return (
                  <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                    <div className="px-5 py-3 bg-gradient-to-r from-rose-50 to-pink-100 dark:from-rose-900/30 dark:to-pink-800/20 border-b border-rose-200 dark:border-rose-800 flex items-center justify-between">
                      <h3 className="text-sm font-semibold text-rose-900 dark:text-rose-200 flex items-center gap-2">
                        <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                        Top Pick - Best Restaurant
                      </h3>
                      <span className="text-sm font-bold text-rose-700 dark:text-rose-300">~${r.average_cost_per_person}/person</span>
                    </div>
                    <div className="p-5">
                      <div className="flex flex-col md:flex-row gap-5">
                        {(r.thumbnail || r.primary_image) && (
                          <img src={r.thumbnail || r.primary_image} alt={r.name} className="w-full md:w-72 h-52 object-cover rounded-xl shadow-sm" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                        )}
                        <div className="flex-1 space-y-4">
                          <div>
                            <h3 className="text-xl font-bold text-gray-900 dark:text-white">{r.name}</h3>
                            <p className="text-gray-500">{r.cuisine_type}{r.city ? ` · ${r.city}` : ''}</p>
                          </div>
                          <div className="flex items-center gap-4 flex-wrap">
                            {r.rating > 0 && (
                              <div className="flex items-center gap-1">
                                <span className="text-yellow-500">⭐</span>
                                <span className="font-semibold">{r.rating.toFixed(1)}</span>
                                {r.review_count > 0 && <span className="text-sm text-gray-500">({r.review_count} reviews)</span>}
                              </div>
                            )}
                            <span className="text-lg font-semibold text-green-600 dark:text-green-400">{r.price_range}</span>
                            {r.utility_score !== undefined && (
                              <span className="px-2.5 py-1 bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-full text-xs font-semibold">
                                Score: {r.utility_score}
                              </span>
                            )}
                          </div>
                          <div className="grid grid-cols-2 gap-3">
                            {[
                              r.address && { label: 'Address', value: r.address },
                              r.hours && { label: 'Hours', value: r.hours },
                            ].filter(Boolean).map((item: any, idx) => (
                              <div key={idx} className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3">
                                <p className="text-xs text-gray-500 uppercase tracking-wider">{item.label}</p>
                                <p className="text-sm text-gray-900 dark:text-white mt-0.5">{item.value}</p>
                              </div>
                            ))}
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {r.has_delivery && <span className="text-xs px-3 py-1.5 bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full border border-green-200 dark:border-green-800">Delivery</span>}
                            {r.has_takeout && <span className="text-xs px-3 py-1.5 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full border border-blue-200 dark:border-blue-800">Takeout</span>}
                            {r.has_reservation && <span className="text-xs px-3 py-1.5 bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full border border-purple-200 dark:border-purple-800">Reservations</span>}
                          </div>
                          <div className="flex gap-4 text-sm">
                            {r.phone && <a href={`tel:${r.phone}`} className="text-primary-600 dark:text-primary-400 hover:underline">{r.phone}</a>}
                            {r.website && <a href={r.website} target="_blank" rel="noopener noreferrer" className="text-primary-600 dark:text-primary-400 hover:underline">Website</a>}
                          </div>
                          {r.recommendation && (
                            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 text-sm text-blue-700 dark:text-blue-300">{r.recommendation}</div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* Alternative Restaurants Table */}
              {rec?.top_5_restaurants && rec.top_5_restaurants.length > 1 && (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                  <div className="px-5 py-3 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Alternative Restaurants</h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
                          <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Restaurant</th>
                          <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Cuisine</th>
                          <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Rating</th>
                          <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Price Range</th>
                          <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Score</th>
                          <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Per Person</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rec.top_5_restaurants.slice(1, 8).map((r: any, idx: number) => (
                          <tr key={idx} className="border-b border-gray-50 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors">
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-3">
                                {(r.thumbnail || r.primary_image) ? (
                                  <img src={r.thumbnail || r.primary_image} alt="" className="w-10 h-10 rounded-lg object-cover flex-shrink-0" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                                ) : (
                                  <div className="w-10 h-10 rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center flex-shrink-0">🍽️</div>
                                )}
                                <span className="font-medium text-gray-900 dark:text-white">{r.name}</span>
                              </div>
                            </td>
                            <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{r.cuisine_type}</td>
                            <td className="px-4 py-3 text-center">{r.rating > 0 ? `⭐ ${r.rating.toFixed(1)}` : '-'}</td>
                            <td className="px-4 py-3 text-center font-medium text-green-600 dark:text-green-400">{r.price_range}</td>
                            <td className="px-4 py-3 text-center">
                              {r.utility_score !== undefined && (
                                <span className="px-2 py-0.5 bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-full text-xs font-medium">{r.utility_score}</span>
                              )}
                            </td>
                            <td className="px-4 py-3 text-right font-bold text-primary-600 dark:text-primary-400">${r.average_cost_per_person}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {!rec?.recommended_restaurant && (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-8 text-center text-gray-500">
                  <p className="text-lg">No restaurant data available</p>
                  <p className="text-sm mt-1">Try adjusting your cuisine preferences</p>
                </div>
              )}
            </div>
          )}

          {/* ══════ TAB: INTELLIGENCE ══════ */}
          {activeTab === 'intelligence' && (
            <div className="space-y-4">
              {intel ? (
                <>
                  <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-2">
                    <span className="inline-block w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                    10+ AI agents analyzed {destination} for your travel dates
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Weather */}
                    {intel.weather_by_day && intel.weather_by_day.length > 0 && (
                      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                        <div className="px-5 py-3 bg-amber-50 dark:bg-amber-900/20 border-b border-amber-200 dark:border-amber-800">
                          <h3 className="text-sm font-semibold text-amber-900 dark:text-amber-200">Weather Forecast</h3>
                        </div>
                        <div className="p-4">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="text-xs text-gray-500 uppercase tracking-wider">
                                <th className="text-left pb-2">Date</th>
                                <th className="text-left pb-2">Condition</th>
                                <th className="text-right pb-2">Temp</th>
                                <th className="text-right pb-2">Rain</th>
                              </tr>
                            </thead>
                            <tbody>
                              {intel.weather_by_day.map((day: any, i: number) => (
                                <tr key={i} className="border-t border-gray-50 dark:border-gray-800">
                                  <td className="py-2 text-gray-700 dark:text-gray-300">{day.date}</td>
                                  <td className="py-2 text-gray-600 dark:text-gray-400">{day.condition}</td>
                                  <td className="py-2 text-right font-medium text-gray-900 dark:text-white">{day.high_c}°/{day.low_c}°C</td>
                                  <td className="py-2 text-right">
                                    {day.rain_chance_pct > 30
                                      ? <span className="text-blue-600 dark:text-blue-400 font-medium">{day.rain_chance_pct}%</span>
                                      : <span className="text-gray-400">{day.rain_chance_pct || 0}%</span>}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    {/* Safety */}
                    {intel.safety && (
                      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                        <div className="px-5 py-3 bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800">
                          <h3 className="text-sm font-semibold text-red-900 dark:text-red-200">Safety Intel</h3>
                        </div>
                        <div className="p-4 space-y-3">
                          <div className="flex items-center gap-3">
                            <div className="w-14 h-14 rounded-xl bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                              <span className="text-2xl font-bold text-gray-900 dark:text-white">{intel.safety.overall_score}</span>
                            </div>
                            <div>
                              <p className="text-sm font-medium text-gray-900 dark:text-white">/10 Safety Score</p>
                              <span className={`text-xs px-2 py-0.5 rounded-full ${
                                intel.safety.crime_level === 'low' ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' :
                                intel.safety.crime_level === 'moderate' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300' :
                                'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
                              }`}>{intel.safety.crime_level} crime</span>
                            </div>
                          </div>
                          {intel.safety.areas_to_avoid?.length > 0 && (
                            <div>
                              <p className="text-xs font-semibold text-red-600 dark:text-red-400 uppercase tracking-wider mb-1">Areas to Avoid</p>
                              <p className="text-sm text-gray-600 dark:text-gray-400">{intel.safety.areas_to_avoid.join(', ')}</p>
                            </div>
                          )}
                          {intel.safety.scam_warnings?.length > 0 && (
                            <div>
                              <p className="text-xs font-semibold text-orange-600 dark:text-orange-400 uppercase tracking-wider mb-1">Scam Warnings</p>
                              <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-0.5">
                                {intel.safety.scam_warnings.slice(0, 3).map((s: string, i: number) => <li key={i} className="flex gap-1"><span className="text-orange-400">!</span> {s}</li>)}
                              </ul>
                            </div>
                          )}
                          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-gray-100 dark:border-gray-700 text-xs">
                            <p className="text-gray-500">Emergency: <span className="font-medium text-gray-900 dark:text-white">{intel.safety.emergency_number}</span></p>
                            <p className="text-gray-500">Tap water: <span className="font-medium text-gray-900 dark:text-white">{intel.safety.tap_water_safe ? 'Safe' : 'Not safe'}</span></p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Transport */}
                    {intel.best_transport && (
                      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                        <div className="px-5 py-3 bg-indigo-50 dark:bg-indigo-900/20 border-b border-indigo-200 dark:border-indigo-800">
                          <h3 className="text-sm font-semibold text-indigo-900 dark:text-indigo-200">Transport Decision</h3>
                        </div>
                        <div className="p-4 space-y-3">
                          <div className={`inline-block px-3 py-1 rounded-lg text-sm font-bold ${
                            intel.best_transport.recommendation === 'public_transit'
                              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                              : intel.best_transport.recommendation === 'car_rental'
                                ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                                : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                          }`}>
                            {intel.best_transport.recommendation === 'public_transit' ? 'USE PUBLIC TRANSIT' :
                             intel.best_transport.recommendation === 'car_rental' ? 'RENT A CAR' : 'MIXED TRANSPORT'}
                          </div>
                          <p className="text-sm text-gray-600 dark:text-gray-400">{intel.best_transport.reason}</p>
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            {intel.best_transport.daily_transit_pass_cost && (
                              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-2">
                                <p className="text-xs text-gray-500">Daily Pass</p>
                                <p className="font-medium text-gray-900 dark:text-white">{intel.best_transport.daily_transit_pass_cost}</p>
                              </div>
                            )}
                            {intel.best_transport.airport_to_city && (
                              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-2">
                                <p className="text-xs text-gray-500">Airport to City</p>
                                <p className="font-medium text-gray-900 dark:text-white">{intel.best_transport.airport_to_city}</p>
                              </div>
                            )}
                          </div>
                          <div className="flex flex-wrap gap-1.5 pt-1">
                            {intel.best_transport.metro_available && <span className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded-full">Metro</span>}
                            {intel.best_transport.bus_system && <span className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded-full">Bus</span>}
                            {intel.best_transport.ride_sharing && <span className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded-full">Uber/Lyft</span>}
                            {intel.best_transport.taxi_affordable && <span className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded-full">Taxi</span>}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Local Events */}
                    {intel.local_events && intel.local_events.length > 0 && (
                      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                        <div className="px-5 py-3 bg-purple-50 dark:bg-purple-900/20 border-b border-purple-200 dark:border-purple-800">
                          <h3 className="text-sm font-semibold text-purple-900 dark:text-purple-200">Local Events</h3>
                        </div>
                        <div className="p-4 space-y-3">
                          {intel.local_events.slice(0, 5).map((event: any, i: number) => (
                            <div key={i} className="flex items-start gap-3 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-750">
                              <div className="w-8 h-8 bg-purple-100 dark:bg-purple-900/40 rounded-lg flex items-center justify-center text-sm flex-shrink-0">🎉</div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center justify-between gap-2">
                                  <p className="font-medium text-sm text-gray-900 dark:text-white truncate">{event.name}</p>
                                  <span className="text-xs text-gray-500 flex-shrink-0">{event.date}</span>
                                </div>
                                <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">{event.description}</p>
                                <div className="flex gap-2 mt-1">
                                  <span className="text-xs bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 px-1.5 py-0.5 rounded">{event.type}</span>
                                  <span className="text-xs text-gray-500">{event.cost}</span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Food Scene */}
                    {intel.food_scene && (
                      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                        <div className="px-5 py-3 bg-orange-50 dark:bg-orange-900/20 border-b border-orange-200 dark:border-orange-800">
                          <h3 className="text-sm font-semibold text-orange-900 dark:text-orange-200">Food Scene</h3>
                        </div>
                        <div className="p-4 space-y-3">
                          {intel.food_scene.must_try_dishes?.length > 0 && (
                            <div>
                              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Must Try</p>
                              <div className="flex flex-wrap gap-1.5">
                                {intel.food_scene.must_try_dishes.map((d: string, i: number) => (
                                  <span key={i} className="text-xs bg-orange-50 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 px-2 py-1 rounded-full border border-orange-200 dark:border-orange-800">{d}</span>
                                ))}
                              </div>
                            </div>
                          )}
                          {intel.food_scene.food_markets?.length > 0 && (
                            <div>
                              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Food Markets</p>
                              <p className="text-sm text-gray-600 dark:text-gray-400">{intel.food_scene.food_markets.join(', ')}</p>
                            </div>
                          )}
                          <div className="grid grid-cols-3 gap-2 text-center">
                            {[
                              { label: 'Budget', value: intel.food_scene.budget_meal_cost, color: 'bg-green-50 dark:bg-green-900/20' },
                              { label: 'Mid-Range', value: intel.food_scene.mid_range_meal_cost, color: 'bg-yellow-50 dark:bg-yellow-900/20' },
                              { label: 'Fine Dining', value: intel.food_scene.fine_dining_cost, color: 'bg-red-50 dark:bg-red-900/20' },
                            ].map((tier) => (
                              <div key={tier.label} className={`${tier.color} rounded-lg p-2`}>
                                <p className="text-xs text-gray-500">{tier.label}</p>
                                <p className="text-sm font-semibold text-gray-900 dark:text-white">{tier.value}</p>
                              </div>
                            ))}
                          </div>
                          {intel.food_scene.street_food_safe !== undefined && (
                            <p className="text-xs text-gray-500">Street food: <span className="font-medium">{intel.food_scene.street_food_safe ? 'Safe to eat' : 'Be cautious'}</span></p>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Local Customs */}
                    {intel.local_customs && (
                      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                        <div className="px-5 py-3 bg-teal-50 dark:bg-teal-900/20 border-b border-teal-200 dark:border-teal-800">
                          <h3 className="text-sm font-semibold text-teal-900 dark:text-teal-200">Local Customs</h3>
                        </div>
                        <div className="p-4 space-y-2 text-sm">
                          {[
                            intel.local_customs.tipping && { label: 'Tipping', value: intel.local_customs.tipping },
                            intel.local_customs.language && { label: 'Language', value: intel.local_customs.language },
                            intel.local_customs.dress_code && { label: 'Dress Code', value: intel.local_customs.dress_code },
                            intel.local_customs.dining_etiquette && { label: 'Dining', value: intel.local_customs.dining_etiquette },
                          ].filter(Boolean).map((item: any, idx) => (
                            <div key={idx} className="flex gap-3 py-1.5 border-b border-gray-50 dark:border-gray-800 last:border-0">
                              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider w-20 flex-shrink-0 pt-0.5">{item.label}</span>
                              <span className="text-gray-700 dark:text-gray-300">{item.value}</span>
                            </div>
                          ))}
                          {intel.local_customs.useful_phrases?.length > 0 && (
                            <div className="pt-2 mt-2 border-t border-gray-100 dark:border-gray-700">
                              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Useful Phrases</p>
                              <div className="space-y-1">
                                {intel.local_customs.useful_phrases.slice(0, 4).map((p: string, i: number) => (
                                  <p key={i} className="text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-900 rounded px-3 py-1.5">{p}</p>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-8 text-center text-gray-500">
                  <p className="text-lg">No intelligence data available</p>
                  <p className="text-sm mt-1">Destination intelligence could not be gathered for this location</p>
                </div>
              )}
            </div>
          )}

        </div>
      )}
    </div>
  );
};

export default AIPlannerPage;
