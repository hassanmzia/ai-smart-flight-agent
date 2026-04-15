import { ShoppingVenue } from '@/services/shoppingService';

interface ShoppingVenueCardProps {
  venue: ShoppingVenue;
}

const ShoppingVenueCard = ({ venue }: ShoppingVenueCardProps) => {
  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      malls: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      markets: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      boutiques: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
      outlets: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
      souvenirs: 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200',
      local_crafts: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
    };
    return colors[category] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
  };

  const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
      malls: 'Shopping Mall',
      markets: 'Market',
      boutiques: 'Boutique',
      outlets: 'Outlet',
      souvenirs: 'Souvenirs',
      local_crafts: 'Local Crafts',
    };
    return labels[category] || category;
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
      <div className="p-6">
        {/* Header with icon and name */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="text-4xl">{venue.icon}</div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {venue.name}
              </h3>
              <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full mt-1 ${getCategoryColor(venue.category)}`}>
                {getCategoryLabel(venue.category)}
              </span>
            </div>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-1">
              <span className="text-yellow-500">⭐</span>
              <span className="font-semibold text-gray-900 dark:text-white">
                {venue.rating}
              </span>
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              {venue.review_count} reviews
            </div>
          </div>
        </div>

        {/* Description */}
        <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
          {venue.description}
        </p>

        {/* Location and Details */}
        <div className="space-y-2 mb-4">
          <div className="flex items-start gap-2 text-sm">
            <span className="text-gray-500 dark:text-gray-400">📍</span>
            <div>
              <div className="text-gray-900 dark:text-white font-medium">{venue.location}</div>
              <div className="text-gray-600 dark:text-gray-400">{venue.address}</div>
            </div>
          </div>

          <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-300">
            <div className="flex items-center gap-1">
              <span>🏪</span>
              <span>{venue.store_count} stores</span>
            </div>
            <div className="flex items-center gap-1">
              <span>💰</span>
              <span>{venue.price_level}</span>
            </div>
            <div className="flex items-center gap-1">
              <span>📏</span>
              <span>{venue.distance_from_center} km from center</span>
            </div>
          </div>

          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-500 dark:text-gray-400">🕐</span>
            <span className="text-gray-700 dark:text-gray-300">{venue.opening_hours}</span>
          </div>

          <div className="flex items-start gap-2 text-sm">
            <span className="text-gray-500 dark:text-gray-400">⏰</span>
            <span className="text-gray-700 dark:text-gray-300">
              <span className="font-medium">Busy Hours:</span> {venue.busy_hours}
            </span>
          </div>
        </div>

        {/* Popular Items */}
        {venue.popular_for && venue.popular_for.length > 0 && (
          <div className="mb-4">
            <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Popular for:
            </div>
            <div className="flex flex-wrap gap-2">
              {venue.popular_for.map((item, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-primary-50 dark:bg-primary-900 text-primary-700 dark:text-primary-200 text-xs rounded-full"
                >
                  {item}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Features */}
        {venue.features && venue.features.length > 0 && (
          <div className="mb-4">
            <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Amenities:
            </div>
            <div className="flex flex-wrap gap-2">
              {venue.features.slice(0, 6).map((feature, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs rounded"
                >
                  {feature}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Payment Methods */}
        <div className="border-t border-gray-200 dark:border-gray-700 pt-3">
          <div className="text-xs text-gray-500 dark:text-gray-400">
            Payment: {venue.payment_methods.join(', ')}
          </div>
        </div>

        {/* Reference / Find-Online Actions.
            Shopping venues don't ship with a bookable website, so we link
            users out to Google Search (for the venue's own homepage) and
            Google Maps (for directions + hours). Matches the pattern used
            by TouristAttractionCard / EventCard. */}
        <div className="flex flex-wrap gap-2 pt-3 mt-2 border-t border-gray-200 dark:border-gray-700">
          {(venue as any).website ? (
            <a
              href={(venue as any).website}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
              title="Opens the venue's website in a new tab"
            >
              🔗 Visit Website
            </a>
          ) : (
            <a
              href={`https://www.google.com/search?q=${encodeURIComponent(
                `${venue.name} ${venue.location || ''}`.trim()
              )}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
              title="Search for this venue online"
            >
              🔍 Find Online
            </a>
          )}
          <a
            href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
              `${venue.name} ${venue.address || venue.location || ''}`.trim()
            )}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-primary-600 dark:text-primary-400 bg-primary-50 dark:bg-primary-900/20 hover:bg-primary-100 dark:hover:bg-primary-900/30 rounded-lg transition-colors"
          >
            🗺️ View on Map
          </a>
        </div>
      </div>
    </div>
  );
};

export default ShoppingVenueCard;
