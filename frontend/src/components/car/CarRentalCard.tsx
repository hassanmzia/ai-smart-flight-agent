import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { CarRental } from '../../services/carRentalService';

interface CarRentalCardProps {
  car: CarRental;
  onSelect?: (car: CarRental) => void;
  showUtilityScore?: boolean;
}

const CarRentalCard: React.FC<CarRentalCardProps> = ({ car, onSelect, showUtilityScore = false }) => {
  const getCarTypeIcon = (carType: string) => {
    const type = carType.toLowerCase();
    if (type.includes('suv')) return '🚙';
    if (type.includes('luxury')) return '🚗';
    if (type.includes('van')) return '🚐';
    if (type.includes('economy') || type.includes('compact')) return '🚘';
    return '🚗';
  };

  const getUtilityColor = (score: number) => {
    if (score >= 40) return 'text-green-600 dark:text-green-400';
    if (score >= 15) return 'text-blue-600 dark:text-blue-400';
    if (score >= -15) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getCarTypeDisplay = (type: string) => {
    return type.charAt(0).toUpperCase() + type.slice(1);
  };

  return (
    <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => onSelect?.(car)}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{getCarTypeIcon(car.car_type)}</span>
            <div>
              <div className="text-lg font-bold">{car.rental_company}</div>
              <div className="text-sm font-normal text-gray-600 dark:text-gray-400">
                {car.vehicle || getCarTypeDisplay(car.car_type)}
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-primary-600 dark:text-primary-400">
              ${car.price_per_day}
              <span className="text-sm font-normal text-gray-600">/day</span>
            </div>
            <div className="text-sm text-gray-500">
              Total: ${car.total_price}
            </div>
          </div>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Car Type Badge */}
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full text-sm font-semibold">
            {getCarTypeDisplay(car.car_type)}
          </span>
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {car.rental_days} {car.rental_days === 1 ? 'day' : 'days'}
          </span>
        </div>

        {/* Rating */}
        {car.rating > 0 && (
          <div className="flex items-center gap-2">
            <div className="flex items-center">
              <span className="text-yellow-500">⭐</span>
              <span className="ml-1 font-semibold">{car.rating.toFixed(1)}</span>
            </div>
            {car.reviews > 0 && (
              <span className="text-sm text-gray-600 dark:text-gray-400">
                ({car.reviews} reviews)
              </span>
            )}
          </div>
        )}

        {/* Features */}
        {car.features && car.features.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {car.features.slice(0, 4).map((feature, index) => (
              <span
                key={index}
                className="px-2 py-1 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded text-xs"
              >
                {feature}
              </span>
            ))}
          </div>
        )}

        {/* Rental Details */}
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="flex items-center gap-1">
            <span>📍</span>
            <span className="text-gray-600 dark:text-gray-400 truncate">
              {car.pickup_location}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <span>🛣️</span>
            <span className="text-gray-600 dark:text-gray-400">{car.mileage}</span>
          </div>
          {car.deposit > 0 && (
            <>
              <div className="flex items-center gap-1">
                <span>💳</span>
                <span className="text-gray-600 dark:text-gray-400">
                  ${car.deposit} deposit
                </span>
              </div>
              <div className="flex items-center gap-1">
                <span>🛡️</span>
                <span className="text-gray-600 dark:text-gray-400">
                  {car.insurance_available ? 'Insurance available' : 'No insurance'}
                </span>
              </div>
            </>
          )}
        </div>

        {/* Utility Score */}
        {showUtilityScore && car.utility_score !== undefined && (
          <div className="border-t pt-3 mt-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold">Utility Score:</span>
              <span className={`text-lg font-bold ${getUtilityColor(car.utility_score)}`}>
                {car.utility_score}
              </span>
            </div>
            {car.recommendation && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                {car.recommendation}
              </p>
            )}
            {/* Breakdown */}
            {(car.price_utility_score !== undefined ||
              car.type_utility_score !== undefined ||
              car.rating_utility_score !== undefined) && (
              <div className="mt-2 text-xs text-gray-500 space-y-1">
                {car.price_utility_score !== undefined && (
                  <div className="flex justify-between">
                    <span>Price:</span>
                    <span className={car.price_utility_score >= 0 ? 'text-green-600' : 'text-red-600'}>
                      {car.price_utility_score > 0 ? '+' : ''}
                      {car.price_utility_score}
                    </span>
                  </div>
                )}
                {car.type_utility_score !== undefined && (
                  <div className="flex justify-between">
                    <span>Type:</span>
                    <span className={car.type_utility_score >= 0 ? 'text-green-600' : 'text-red-600'}>
                      {car.type_utility_score > 0 ? '+' : ''}
                      {car.type_utility_score}
                    </span>
                  </div>
                )}
                {car.rating_utility_score !== undefined && (
                  <div className="flex justify-between">
                    <span>Rating:</span>
                    <span className={car.rating_utility_score >= 0 ? 'text-green-600' : 'text-red-600'}>
                      {car.rating_utility_score > 0 ? '+' : ''}
                      {car.rating_utility_score}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Dates */}
        <div className="text-xs text-gray-500 border-t pt-2">
          <div>Pickup: {new Date(car.pickup_date).toLocaleDateString()}</div>
          <div>Drop-off: {new Date(car.dropoff_date).toLocaleDateString()}</div>
        </div>

        {/* Action Button */}
        {onSelect && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onSelect(car);
            }}
            className="w-full mt-4 bg-primary-600 hover:bg-primary-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
          >
            Select This Car
          </button>
        )}
      </CardContent>
    </Card>
  );
};

export default CarRentalCard;
