import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../common/Card';
import type { TouristAttraction } from '../../services/touristAttractionService';

interface TouristAttractionCardProps {
  attraction: TouristAttraction;
}

const getCategoryIcon = (category: string) => {
  const icons: { [key: string]: string } = {
    museums: '🏛️',
    parks: '🌳',
    landmarks: '🗽',
    entertainment: '🎢',
    religious: '⛪',
    shopping: '🛍️',
    beaches: '🏖️',
    general: '📍',
  };
  return icons[category] || '📍';
};

const TouristAttractionCard: React.FC<TouristAttractionCardProps> = ({ attraction }) => {
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardContent className="p-0">
        <div className="flex flex-col md:flex-row">
          {/* Image */}
          {(attraction.thumbnail || attraction.primary_image) && (
            <div className="md:w-48 h-48 md:h-auto flex-shrink-0">
              <img
                src={attraction.thumbnail || attraction.primary_image}
                alt={attraction.name}
                className="w-full h-full object-cover rounded-t-lg md:rounded-l-lg md:rounded-tr-none"
                onError={(e) => {
                  // Hide image if it fails to load
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
            </div>
          )}

          {/* Content */}
          <div className="flex-1 p-4">
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-2xl">{getCategoryIcon(attraction.category)}</span>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {attraction.name}
                  </h3>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 capitalize">
                  {attraction.category}
                </p>
              </div>

              {/* Rating */}
              {attraction.rating > 0 && (
                <div className="flex items-center gap-1 ml-3">
                  <span className="text-yellow-500">⭐</span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {attraction.rating.toFixed(1)}
                  </span>
                  {attraction.review_count > 0 && (
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      ({attraction.review_count})
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* Description */}
            {attraction.description && (
              <p className="text-sm text-gray-700 dark:text-gray-300 mb-3 line-clamp-2">
                {attraction.description}
              </p>
            )}

            {/* Details Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm mb-3">
              {/* Address */}
              {attraction.address && (
                <div className="flex items-start gap-2">
                  <span className="text-gray-500 dark:text-gray-400">📍</span>
                  <span className="text-gray-700 dark:text-gray-300 line-clamp-1">
                    {attraction.address}
                  </span>
                </div>
              )}

              {/* Price */}
              <div className="flex items-center gap-2">
                <span className="text-gray-500 dark:text-gray-400">💰</span>
                <span className="font-semibold text-green-600 dark:text-green-400">
                  {attraction.price_level === 'free' ? 'Free Entry' : attraction.price_level}
                </span>
              </div>

              {/* Hours */}
              {attraction.hours && (
                <div className="flex items-start gap-2">
                  <span className="text-gray-500 dark:text-gray-400">🕒</span>
                  <span className="text-gray-700 dark:text-gray-300 line-clamp-1">
                    {attraction.hours}
                  </span>
                </div>
              )}

              {/* Phone */}
              {attraction.phone && (
                <div className="flex items-center gap-2">
                  <span className="text-gray-500 dark:text-gray-400">📞</span>
                  <a
                    href={`tel:${attraction.phone}`}
                    className="text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    {attraction.phone}
                  </a>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-2 pt-3 border-t border-gray-200 dark:border-gray-700">
              {attraction.website && (
                <a
                  href={attraction.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
                >
                  🌐 Visit Website
                </a>
              )}
              {attraction.latitude && attraction.longitude && (
                <a
                  href={`https://www.google.com/maps/search/?api=1&query=${attraction.latitude},${attraction.longitude}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-primary-600 dark:text-primary-400 bg-primary-50 dark:bg-primary-900/20 hover:bg-primary-100 dark:hover:bg-primary-900/30 rounded-lg transition-colors"
                >
                  🗺️ View on Map
                </a>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default TouristAttractionCard;
