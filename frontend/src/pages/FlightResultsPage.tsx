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
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Flight Results
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          {searchParams.origin} → {searchParams.destination} • {data?.total || 0} flights found
        </p>
      </div>

      {/* Flights List */}
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
  );
};

export default FlightResultsPage;
