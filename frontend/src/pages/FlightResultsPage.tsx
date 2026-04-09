import { useQuery } from '@tanstack/react-query';
import { useLocation } from 'react-router-dom';
import { searchFlights } from '@/services/flightService';
import FlightCard from '@/components/flight/FlightCard';
import Loading from '@/components/common/Loading';
import { QUERY_KEYS } from '@/utils/constants';
import type { FlightSearchParams } from '@/types';

const FlightResultsPage = () => {
  const location = useLocation();
  const searchParams = location.state as FlightSearchParams;

  const { data, isLoading, error } = useQuery({
    queryKey: [...QUERY_KEYS.FLIGHTS, searchParams],
    queryFn: () => searchFlights(searchParams),
    enabled: !!searchParams,
  });

  if (!searchParams) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <p className="text-center text-gray-600 dark:text-gray-400">
          No search parameters found. Please start a new search.
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Loading size="lg" text="Searching for flights..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <p className="text-center text-red-600 dark:text-red-400">
          Error loading flights. Please try again.
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <div className="relative overflow-hidden bg-gradient-to-br from-sky-500 via-blue-600 to-indigo-700 dark:from-sky-800 dark:via-blue-800 dark:to-indigo-900">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute -top-10 -right-20 w-64 h-64 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 left-1/4 w-40 h-40 bg-sky-300 rounded-full blur-3xl"></div>
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
          <h1 className="text-3xl md:text-4xl font-extrabold text-white mb-2">
            ✈️ Flight Results
          </h1>
          <p className="text-blue-100 text-lg">
            {searchParams.origin} → {searchParams.destination} • {data?.total || 0} flights found
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6 relative z-10 pb-12">
      <div className="space-y-4">
        {(() => {
          // Handle different response structures
          const flights = data?.items || data?.results || [];
          return flights.length > 0 ? (
            flights.map((flight: any) => <FlightCard key={flight.id} flight={flight} />)
          ) : (
            <p className="text-center text-gray-600 dark:text-gray-400 py-12">
              No flights found for your search criteria.
            </p>
          );
        })()}
      </div>
      </div>
    </div>
  );
};

export default FlightResultsPage;
