import React from 'react';
import { Card, CardContent } from '../common/Card';
import type { Event } from '../../services/eventService';

interface EventCardProps {
  event: Event;
}

const EventCard: React.FC<EventCardProps> = ({ event }) => {
  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardContent className="p-0">
        <div className="flex flex-col md:flex-row">
          {/* Date Badge */}
          <div className="md:w-24 flex-shrink-0 bg-primary-600 dark:bg-primary-700 text-white p-4 flex flex-col items-center justify-center">
            <div className="text-4xl mb-2">{event.icon}</div>
            <div className="text-center">
              <div className="text-xs uppercase">
                {new Date(event.start_date).toLocaleDateString('en-US', { month: 'short' })}
              </div>
              <div className="text-2xl font-bold">
                {new Date(event.start_date).getDate()}
              </div>
              {event.is_multi_day && (
                <div className="text-xs mt-1">
                  {event.duration_days} days
                </div>
              )}
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 p-4">
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                  {event.name}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 capitalize">
                  {event.category} • {event.venue}
                </p>
              </div>

              {/* Rating */}
              {event.rating > 0 && (
                <div className="flex items-center gap-1 ml-3">
                  <span className="text-yellow-500">⭐</span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {event.rating.toFixed(1)}
                  </span>
                  {event.review_count > 0 && (
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      ({event.review_count})
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* Description */}
            <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">
              {event.description}
            </p>

            {/* Details Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm mb-3">
              {/* Date */}
              <div>
                <p className="text-xs text-gray-600 dark:text-gray-400">Date</p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {formatDate(event.start_date)}
                  {event.is_multi_day && (
                    <span className="text-xs text-gray-500"> - {formatDate(event.end_date)}</span>
                  )}
                </p>
              </div>

              {/* Price */}
              <div>
                <p className="text-xs text-gray-600 dark:text-gray-400">Price</p>
                <p className="font-semibold text-green-600 dark:text-green-400">
                  {event.ticket_price === 0
                    ? 'Free'
                    : `$${event.ticket_price}`
                  }
                </p>
              </div>

              {/* Attendance */}
              <div>
                <p className="text-xs text-gray-600 dark:text-gray-400">Expected</p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {event.expected_attendance >= 1000
                    ? `${(event.expected_attendance / 1000).toFixed(1)}K`
                    : event.expected_attendance
                  } people
                </p>
              </div>

              {/* Organizer */}
              <div>
                <p className="text-xs text-gray-600 dark:text-gray-400">Organizer</p>
                <p className="font-medium text-gray-900 dark:text-white truncate">
                  {event.organizer}
                </p>
              </div>
            </div>

            {/* Tags */}
            {event.tags && event.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-3">
                {event.tags.map((tag, index) => (
                  <span
                    key={index}
                    className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-2 py-1 rounded-full"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}

            {/* Action */}
            {event.website && (
              <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
                <a
                  href={event.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
                >
                  🎫 Get Tickets / More Info
                </a>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default EventCard;
