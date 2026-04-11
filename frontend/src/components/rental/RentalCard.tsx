import { motion } from 'framer-motion';
import { MapPinIcon, StarIcon } from '@heroicons/react/24/solid';
import { Card } from '@/components/common';
import Button from '@/components/common/Button';
import { formatCurrency } from '@/utils/formatters';

interface RentalCardProps {
  rental: {
    id: string;
    name: string;
    city: string;
    country: string;
    description?: string;
    guest_rating: number;
    review_count: number;
    property_type: string;
    primary_image: string;
    images: string[];
    pricePerNight: number;
    price_range_min: number;
    currency: string;
    amenities: string[];
    is_rental: boolean;
    is_entire_property: boolean;
    bedrooms?: number;
    bathrooms?: number;
    beds?: number;
    max_guests?: number;
    has_kitchen: boolean;
    has_pool: boolean;
    has_parking: boolean;
    pet_friendly: boolean;
    pricing_model: string;
    cleaning_fee?: number;
    is_superhost: boolean;
    host_name?: string;
    cancellation_policy?: string;
  };
  nights?: number;
  guests?: number;
  onBook?: (id: string) => void;
}

const RentalCard = ({ rental, nights, guests, onBook }: RentalCardProps) => {
  const imageSrc = rental.primary_image || (rental.images && rental.images.length > 0 ? rental.images[0] : '');

  const keyAmenities: { label: string; show: boolean }[] = [
    { label: 'Kitchen', show: rental.has_kitchen },
    { label: 'Pool', show: rental.has_pool },
    { label: 'Parking', show: rental.has_parking },
    { label: 'Pet-friendly', show: rental.pet_friendly },
  ];

  const visibleAmenities = keyAmenities.filter((a) => a.show);

  const totalPrice = nights ? rental.pricePerNight * nights + (rental.cleaning_fee || 0) : null;
  const perPerson = totalPrice && guests && guests > 0 ? totalPrice / guests : null;

  return (
    <motion.div
      whileHover={{ y: -4 }}
      transition={{ duration: 0.2 }}
    >
      <Card hover className="p-0 overflow-hidden">
        <div className="flex flex-col md:flex-row">
          {/* Image with badge overlays */}
          <div className="relative w-full md:w-72 h-56 flex-shrink-0">
            {imageSrc ? (
              <img
                src={imageSrc}
                alt={rental.name}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
                <span className="text-gray-400">No image</span>
              </div>
            )}

            {/* Entire home badge - top left */}
            {rental.is_entire_property && (
              <span className="absolute top-3 left-3 px-2.5 py-1 rounded-lg text-xs font-semibold bg-indigo-600 text-white shadow-md">
                Entire home
              </span>
            )}

            {/* Superhost badge - top right */}
            {rental.is_superhost && (
              <span className="absolute top-3 right-3 px-2.5 py-1 rounded-lg text-xs font-semibold bg-purple-600 text-white shadow-md">
                Superhost
              </span>
            )}
          </div>

          {/* Content */}
          <div className="flex-1 p-4 md:p-6">
            <div className="flex flex-col sm:flex-row justify-between items-start gap-4">
              <div className="flex-1 min-w-0">
                {/* Name and property type */}
                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <h3 className="font-semibold text-lg md:text-xl text-gray-900 dark:text-white">
                    {rental.name}
                  </h3>
                  {rental.property_type && (
                    <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-indigo-100 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-200">
                      {rental.property_type}
                    </span>
                  )}
                </div>

                {/* Location */}
                <div className="flex items-center space-x-1 text-gray-600 dark:text-gray-400 mb-2">
                  <MapPinIcon className="h-4 w-4" />
                  <span className="text-sm">{rental.city}, {rental.country}</span>
                </div>

                {/* Bedrooms / Bathrooms / Beds / Max guests icons row */}
                <div className="flex flex-wrap items-center gap-3 mb-3 text-sm text-gray-700 dark:text-gray-300">
                  {rental.bedrooms != null && (
                    <span className="inline-flex items-center gap-1">
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0h4" />
                      </svg>
                      {rental.bedrooms} {rental.bedrooms === 1 ? 'bedroom' : 'bedrooms'}
                    </span>
                  )}
                  {rental.bathrooms != null && (
                    <span className="inline-flex items-center gap-1">
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4 16V8a4 4 0 014-4h1M4 16h16M4 16l1 4h14l1-4M20 16V12a2 2 0 00-2-2H6" />
                      </svg>
                      {rental.bathrooms} {rental.bathrooms === 1 ? 'bath' : 'baths'}
                    </span>
                  )}
                  {rental.beds != null && (
                    <span className="inline-flex items-center gap-1">
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3 7v4a1 1 0 001 1h16a1 1 0 001-1V7M3 12v5a1 1 0 001 1h1m16-6v5a1 1 0 01-1 1h-1M5 18v2m14-2v2M3 7h18" />
                      </svg>
                      {rental.beds} {rental.beds === 1 ? 'bed' : 'beds'}
                    </span>
                  )}
                  {rental.max_guests != null && (
                    <span className="inline-flex items-center gap-1">
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      {rental.max_guests} {rental.max_guests === 1 ? 'guest' : 'guests'}
                    </span>
                  )}
                </div>

                {/* Guest rating and review count */}
                <div className="flex items-center space-x-2 mb-3">
                  <span className="inline-flex items-center px-2 py-1 bg-indigo-600 text-white text-xs font-bold rounded">
                    <StarIcon className="h-3 w-3 mr-1" />
                    {rental.guest_rating.toFixed(1)}
                  </span>
                  {rental.review_count > 0 && (
                    <span className="text-xs text-gray-600 dark:text-gray-400">
                      ({rental.review_count} {rental.review_count === 1 ? 'review' : 'reviews'})
                    </span>
                  )}
                </div>

                {/* Description */}
                {rental.description && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                    {rental.description}
                  </p>
                )}

                {/* Key amenities pills */}
                {visibleAmenities.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-3">
                    {visibleAmenities.map((amenity) => (
                      <span
                        key={amenity.label}
                        className="px-2.5 py-1 text-xs font-medium bg-purple-100 dark:bg-purple-900/40 text-purple-800 dark:text-purple-200 rounded-full"
                      >
                        {amenity.label}
                      </span>
                    ))}
                  </div>
                )}

                {/* Host and cancellation info */}
                <div className="flex flex-wrap gap-3 text-xs text-gray-500 dark:text-gray-400">
                  {rental.host_name && (
                    <span>Hosted by {rental.host_name}</span>
                  )}
                  {rental.cancellation_policy && (
                    <span>Cancellation: {rental.cancellation_policy}</span>
                  )}
                </div>
              </div>

              {/* Price and Book */}
              <div className="sm:ml-6 text-left sm:text-right flex sm:flex-col items-center sm:items-end gap-3 sm:gap-0">
                <div>
                  <p className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-0 sm:mb-1">
                    {formatCurrency(rental.pricePerNight, rental.currency)}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
                    per night, {rental.is_entire_property ? 'entire property' : rental.pricing_model}
                  </p>
                </div>

                {rental.cleaning_fee != null && rental.cleaning_fee > 0 && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                    + {formatCurrency(rental.cleaning_fee, rental.currency)} cleaning fee
                  </p>
                )}

                {totalPrice != null && nights != null && (
                  <div className="mb-3 text-right">
                    <p className="text-sm font-semibold text-indigo-700 dark:text-indigo-300">
                      Total: {formatCurrency(totalPrice, rental.currency)} for {nights} {nights === 1 ? 'night' : 'nights'}
                    </p>
                    {perPerson != null && guests != null && guests > 1 && (
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        ~{formatCurrency(perPerson, rental.currency)} per person
                      </p>
                    )}
                  </div>
                )}

                <Button
                  onClick={() => onBook?.(rental.id)}
                  className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white shadow-lg shadow-indigo-500/25 hover:shadow-xl hover:shadow-indigo-500/30"
                >
                  Book Rental
                </Button>
              </div>
            </div>
          </div>
        </div>
      </Card>
    </motion.div>
  );
};

export default RentalCard;
