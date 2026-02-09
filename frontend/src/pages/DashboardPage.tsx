import { useQuery } from '@tanstack/react-query';
import { useRequireAuth } from '@/hooks/useAuth';
import { getBookings } from '@/services/bookingService';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common';
import Loading from '@/components/common/Loading';
import { QUERY_KEYS } from '@/utils/constants';
import { formatCurrency, formatDate } from '@/utils/formatters';

const DashboardPage = () => {
  useRequireAuth();

  const { data: bookingsData, isLoading, error } = useQuery({
    queryKey: QUERY_KEYS.BOOKINGS,
    queryFn: () => getBookings(),
  });

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Loading size="lg" text="Loading your bookings..." />
      </div>
    );
  }

  // Handle different response structures and errors
  let bookings: any[] = [];
  if (bookingsData) {
    // Check if it has items property (paginated response)
    if (Array.isArray(bookingsData.items)) {
      bookings = bookingsData.items;
    }
    // Check if it's directly an array
    else if (Array.isArray(bookingsData)) {
      bookings = bookingsData;
    }
    // Check if it has results property
    else if (Array.isArray(bookingsData.results)) {
      bookings = bookingsData.results;
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-8">
        My Dashboard
      </h1>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardHeader>
            <CardTitle>Total Bookings</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-primary-600 dark:text-primary-400">
              {bookings.length}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Upcoming Trips</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-primary-600 dark:text-primary-400">
              {bookings.filter((b) => b.status === 'confirmed').length}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Total Spent</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-primary-600 dark:text-primary-400">
              {formatCurrency(
                bookings.reduce((sum, b) => sum + b.totalAmount, 0)
              )}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Bookings */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Bookings</CardTitle>
        </CardHeader>
        <CardContent>
          {bookings.length > 0 ? (
            <div className="space-y-4">
              {bookings.map((booking) => (
                <div
                  key={booking.id}
                  className="flex justify-between items-center p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                >
                  <div>
                    <p className="font-semibold text-gray-900 dark:text-white">
                      {booking.type === 'flight' ? 'Flight Booking' : 'Hotel Booking'}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {formatDate(booking.createdAt)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-gray-900 dark:text-white">
                      {formatCurrency(booking.totalAmount, booking.currency)}
                    </p>
                    <span
                      className={`text-xs px-2 py-1 rounded ${
                        booking.status === 'confirmed'
                          ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                          : booking.status === 'pending'
                          ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
                          : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400'
                      }`}
                    >
                      {booking.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-gray-600 dark:text-gray-400 py-8">
              No bookings yet. Start planning your next trip!
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default DashboardPage;
