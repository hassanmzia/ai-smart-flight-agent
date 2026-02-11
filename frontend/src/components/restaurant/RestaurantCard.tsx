import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/common';
import type { Restaurant } from '@/services/restaurantService';

interface RestaurantCardProps {
  restaurant: Restaurant;
}

const RestaurantCard: React.FC<RestaurantCardProps> = ({ restaurant }) => {
  const getCuisineIcon = (cuisine: string) => {
    const icons: { [key: string]: string } = {
      Italian: '🍝',
      Chinese: '🥢',
      Japanese: '🍱',
      Mexican: '🌮',
      Indian: '🍛',
      Thai: '🍜',
      French: '🥐',
      American: '🍔',
      Mediterranean: '🥗',
      Seafood: '🦞',
    };
    return icons[cuisine] || '🍽️';
  };

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <span className="text-2xl">{getCuisineIcon(restaurant.cuisine_type)}</span>
            <span className="text-lg">{restaurant.name}</span>
          </span>
          {restaurant.utility_score !== undefined && (
            <span className="text-sm px-2 py-1 bg-blue-100 dark:bg-blue-900 rounded">
              Score: {restaurant.utility_score}
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {/* Image */}
          {restaurant.thumbnail && (
            <img
              src={restaurant.thumbnail}
              alt={restaurant.name}
              className="w-full h-48 object-cover rounded-lg"
            />
          )}

          {/* Cuisine and Price */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {restaurant.cuisine_type}
            </span>
            <span className="text-lg font-bold text-green-600 dark:text-green-400">
              {restaurant.price_range}
            </span>
          </div>

          {/* Rating */}
          {restaurant.rating > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-yellow-500">★</span>
              <span className="font-semibold">{restaurant.rating.toFixed(1)}</span>
              {restaurant.review_count > 0 && (
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  ({restaurant.review_count} reviews)
                </span>
              )}
            </div>
          )}

          {/* Average Cost */}
          <div className="text-sm">
            <span className="text-gray-600 dark:text-gray-400">Average cost: </span>
            <span className="font-semibold">
              ${restaurant.average_cost_per_person} per person
            </span>
          </div>

          {/* Address */}
          {restaurant.address && (
            <div className="text-sm text-gray-600 dark:text-gray-400">
              📍 {restaurant.address}
            </div>
          )}

          {/* Utility Score Breakdown */}
          {restaurant.utility_score !== undefined && (
            <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg space-y-1">
              <div className="text-xs font-semibold text-gray-700 dark:text-gray-300">
                Utility Score Breakdown:
              </div>
              {restaurant.rating_utility_score !== undefined && (
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  • Rating: {restaurant.rating_utility_score > 0 ? '+' : ''}
                  {restaurant.rating_utility_score}
                </div>
              )}
              {restaurant.price_utility_score !== undefined && (
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  • Price: {restaurant.price_utility_score > 0 ? '+' : ''}
                  {restaurant.price_utility_score}
                </div>
              )}
            </div>
          )}

          {/* Services */}
          <div className="flex flex-wrap gap-2">
            {restaurant.has_delivery && (
              <span className="text-xs px-2 py-1 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded">
                🚚 Delivery
              </span>
            )}
            {restaurant.has_takeout && (
              <span className="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded">
                🥡 Takeout
              </span>
            )}
            {restaurant.has_reservation && (
              <span className="text-xs px-2 py-1 bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 rounded">
                📅 Reservations
              </span>
            )}
          </div>

          {/* Recommendation */}
          {restaurant.recommendation && (
            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
              <p className="text-sm text-blue-800 dark:text-blue-200">
                💡 {restaurant.recommendation}
              </p>
            </div>
          )}

          {/* Contact */}
          <div className="flex gap-2 text-sm">
            {restaurant.phone && (
              <a
                href={`tel:${restaurant.phone}`}
                className="text-blue-600 dark:text-blue-400 hover:underline"
              >
                📞 Call
              </a>
            )}
            {restaurant.website && (
              <a
                href={restaurant.website}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 dark:text-blue-400 hover:underline"
              >
                🌐 Website
              </a>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default RestaurantCard;
