import { useNavigate } from 'react-router-dom';
import {
  StarIcon,
  MapPinIcon,
  ClockIcon,
  BuildingOfficeIcon,
  InformationCircleIcon
} from '@heroicons/react/24/solid';
import { Card } from '@/components/common';
import Button from '@/components/common/Button';
import { formatCurrency, formatDistance } from '@/utils/formatters';
import { RECOMMENDATION_COLORS } from '@/utils/constants';
import { cn } from '@/utils/helpers';
import type { Hotel } from '@/types';

interface HotelCardProps {
  hotel: Hotel;
  onSelect?: (hotel: Hotel) => void;
}

const HotelCard = ({ hotel, onSelect }: HotelCardProps) => {
  const navigate = useNavigate();

  const handleBookClick = () => {
    if (onSelect) {
      onSelect(hotel);
    } else {
      navigate(`/booking/hotel/${hotel.id}`);
    }
  };

  const recommendationColor = hotel.utilityScore
    ? RECOMMENDATION_COLORS[hotel.utilityScore.recommendation]
    : null;

  return (
    <Card hover className="p-0 overflow-hidden">
      <div className="flex">
        {/* Image */}
        <div className="w-64 h-48 flex-shrink-0">
          {hotel.images && hotel.images.length > 0 ? (
            <img
              src={hotel.images[0]}
              alt={hotel.name}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
              <span className="text-gray-400">No image</span>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 p-6">
          <div className="flex justify-between items-start">
            <div className="flex-1">
              {/* Name, Property Type, and Stars */}
              <div className="flex items-center gap-2 mb-2">
                <h3 className="font-semibold text-xl text-gray-900 dark:text-white">
                  {hotel.name}
                </h3>
                {hotel.property_type && (
                  <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
                    <BuildingOfficeIcon className="h-3 w-3 mr-1" />
                    {hotel.property_type}
                  </span>
                )}
              </div>

              <div className="flex items-center space-x-3 mb-2">
                <div className="flex items-center space-x-1">
                  <div className="flex">
                    {[...Array(hotel.stars || hotel.star_rating || 3)].map((_, i) => (
                      <StarIcon key={i} className="h-4 w-4 text-yellow-400" />
                    ))}
                  </div>
                  {hotel.star_rating_display && (
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {hotel.star_rating_display}
                    </span>
                  )}
                </div>

                {(hotel.rating || hotel.guest_rating) && (
                  <div className="flex items-center space-x-1">
                    <span className="px-2 py-1 bg-green-600 text-white text-xs font-bold rounded">
                      {(hotel.rating || hotel.guest_rating || 0).toFixed(1)}
                    </span>
                    {hotel.review_count && (
                      <span className="text-xs text-gray-600 dark:text-gray-400">
                        ({hotel.review_count} reviews)
                      </span>
                    )}
                  </div>
                )}

                {hotel.location_rating && hotel.location_rating > 0 && (
                  <span className="text-xs text-gray-600 dark:text-gray-400">
                    Location: {hotel.location_rating.toFixed(1)}/10
                  </span>
                )}
              </div>

              {/* Location and Description */}
              <div className="flex items-center space-x-1 text-gray-600 dark:text-gray-400 mb-2">
                <MapPinIcon className="h-4 w-4" />
                <span className="text-sm">{hotel.city}, {hotel.country}</span>
                {hotel.distanceFromCenter && (
                  <span className="text-sm">• {formatDistance(hotel.distanceFromCenter)} from center</span>
                )}
              </div>

              {hotel.description && (
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                  {hotel.description}
                </p>
              )}

              {/* Check-in/Check-out Times */}
              {(hotel.check_in_time || hotel.check_out_time) && (
                <div className="flex items-center gap-4 mb-3 text-xs text-gray-600 dark:text-gray-400">
                  {hotel.check_in_time && (
                    <div className="flex items-center gap-1">
                      <ClockIcon className="h-3 w-3" />
                      <span>Check-in: {hotel.check_in_time}</span>
                    </div>
                  )}
                  {hotel.check_out_time && (
                    <div className="flex items-center gap-1">
                      <ClockIcon className="h-3 w-3" />
                      <span>Check-out: {hotel.check_out_time}</span>
                    </div>
                  )}
                </div>
              )}

              {/* Nearby Places */}
              {hotel.nearby_places && hotel.nearby_places.length > 0 && (
                <div className="mb-3">
                  <p className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Nearby:</p>
                  <div className="flex flex-wrap gap-1">
                    {hotel.nearby_places.slice(0, 3).map((place, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center px-2 py-0.5 rounded-md text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                      >
                        <MapPinIcon className="h-3 w-3 mr-1" />
                        {place.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Essential Info */}
              {hotel.essential_info && hotel.essential_info.length > 0 && (
                <div className="mb-3">
                  <div className="flex flex-wrap gap-1">
                    {hotel.essential_info.slice(0, 3).map((info, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-yellow-50 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200"
                      >
                        <InformationCircleIcon className="h-3 w-3 mr-1" />
                        {info}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Amenities */}
              <div className="flex flex-wrap gap-2 mb-4">
                {hotel.amenities.slice(0, 4).map((amenity) => (
                  <span
                    key={amenity}
                    className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded"
                  >
                    {amenity}
                  </span>
                ))}
                {hotel.amenities.length > 4 && (
                  <span className="px-2 py-1 text-xs text-gray-500 dark:text-gray-400">
                    +{hotel.amenities.length - 4} more
                  </span>
                )}
              </div>

              {/* Utility Score */}
              {hotel.utilityScore && recommendationColor && (
                <div className={cn('p-2 rounded-lg inline-block', recommendationColor.bg, recommendationColor.border, 'border')}>
                  <span className={cn('text-xs font-medium', recommendationColor.text)}>
                    {hotel.utilityScore.recommendation.toUpperCase()} • Score: {hotel.utilityScore.totalScore.toFixed(2)}
                  </span>
                </div>
              )}
            </div>

            {/* Price and Book */}
            <div className="ml-6 text-right">
              <p className="text-3xl font-bold text-gray-900 dark:text-white mb-1">
                {formatCurrency(hotel.pricePerNight, hotel.currency)}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">per night</p>
              <Button onClick={handleBookClick}>Book Now</Button>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default HotelCard;
