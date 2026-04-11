import { useQuery } from '@tanstack/react-query';
import { useLocation } from 'react-router-dom';
import { searchHotels } from '@/services/hotelService';
import HotelCard from '@/components/hotel/HotelCard';
import RentalCard from '@/components/rental/RentalCard';
import Loading from '@/components/common/Loading';
import { QUERY_KEYS } from '@/utils/constants';
import type { HotelSearchParams } from '@/types';

const RENTAL_PROPERTY_TYPES = [
  'vacation rental',
  'apartment',
  'house',
  'villa',
  'cabin',
  'cottage',
  'condo',
  'townhouse',
  'bungalow',
  'chalet',
];

const isRentalItem = (item: any): boolean => {
  if (item.is_rental) return true;
  if (item.property_type && RENTAL_PROPERTY_TYPES.includes(item.property_type.toLowerCase())) {
    return true;
  }
  return false;
};

const HotelResultsPage = () => {
  const location = useLocation();
  const searchParams = location.state as HotelSearchParams & { type?: string };

  const { data, isLoading, error } = useQuery({
    queryKey: [...QUERY_KEYS.HOTELS, searchParams],
    queryFn: () => searchHotels(searchParams),
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
        <Loading size="lg" text="Searching for accommodations..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <p className="text-center text-red-600 dark:text-red-400">
          Error loading results. Please try again.
        </p>
      </div>
    );
  }

  const resultLabel =
    searchParams.type === 'rental'
      ? 'vacation rentals'
      : searchParams.type === 'hotel'
        ? 'hotels'
        : 'accommodations';

  return (
    <div className="min-h-screen">
      <div className="relative overflow-hidden bg-gradient-to-br from-emerald-500 via-teal-600 to-cyan-700 dark:from-emerald-800 dark:via-teal-800 dark:to-cyan-900">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute -top-10 -right-20 w-64 h-64 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 left-1/4 w-40 h-40 bg-emerald-300 rounded-full blur-3xl"></div>
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
          <h1 className="text-2xl md:text-3xl font-bold text-white mb-2">
            Results
          </h1>
          <p className="text-emerald-100 text-lg">
            {searchParams.destination} {data?.total != null ? `\u2022 ${data.total} ${resultLabel} found` : ''}
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6 relative z-10 pb-12">
      <div className="space-y-4">
        {data?.items && data.items.length > 0 ? (
          data.items.map((item: any) =>
            isRentalItem(item) ? (
              <RentalCard key={item.id} rental={item} />
            ) : (
              <HotelCard key={item.id} hotel={item} />
            )
          )
        ) : (
          <p className="text-center text-gray-600 dark:text-gray-400 py-12">
            No {resultLabel} found for your search criteria.
          </p>
        )}
      </div>
      </div>
    </div>
  );
};

export default HotelResultsPage;
