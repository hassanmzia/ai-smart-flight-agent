import { useState, useEffect } from 'react';
import { BellIcon, CheckCircleIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common';
import Button from '@/components/common/Button';
import Loading from '@/components/common/Loading';

interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  read: boolean;
  created_at: string;
}

const NotificationsPage = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  useEffect(() => {
    // Sample notifications for now
    const sampleNotifications: Notification[] = [
      {
        id: '1',
        type: 'success',
        title: 'Booking Confirmed',
        message: 'Your flight booking to New York has been confirmed.',
        read: false,
        created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: '2',
        type: 'info',
        title: 'Price Alert',
        message: 'Flight prices to London have dropped by 15%.',
        read: false,
        created_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: '3',
        type: 'warning',
        title: 'Flight Delay',
        message: 'Your flight AA123 is delayed by 30 minutes.',
        read: true,
        created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: '4',
        type: 'info',
        title: 'Travel Tip',
        message: 'Check-in online to save time at the airport.',
        read: true,
        created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      },
    ];
    setNotifications(sampleNotifications);
  }, []);

  const unreadCount = notifications.filter(n => !n.read).length;

  const filteredNotifications = filter === 'unread'
    ? notifications.filter(n => !n.read)
    : notifications;

  const markAsRead = (id: string) => {
    setNotifications(prev =>
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev =>
      prev.map(n => ({ ...n, read: true }))
    );
  };

  const deleteNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const getNotificationIcon = (type: string) => {
    const baseClass = "h-10 w-10 rounded-full flex items-center justify-center";
    switch (type) {
      case 'success':
        return (
          <div className={`${baseClass} bg-green-100 dark:bg-green-900/20`}>
            <CheckCircleIcon className="h-6 w-6 text-green-600 dark:text-green-400" />
          </div>
        );
      case 'warning':
        return (
          <div className={`${baseClass} bg-yellow-100 dark:bg-yellow-900/20`}>
            <BellIcon className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
          </div>
        );
      case 'error':
        return (
          <div className={`${baseClass} bg-red-100 dark:bg-red-900/20`}>
            <XMarkIcon className="h-6 w-6 text-red-600 dark:text-red-400" />
          </div>
        );
      default:
        return (
          <div className={`${baseClass} bg-blue-100 dark:bg-blue-900/20`}>
            <BellIcon className="h-6 w-6 text-blue-600 dark:text-blue-400" />
          </div>
        );
    }
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(hours / 24);

    if (hours < 1) return 'Just now';
    if (hours < 24) return `${hours}h ago`;
    if (days === 1) return 'Yesterday';
    return `${days}d ago`;
  };

  if (loading) {
    return <Loading fullScreen size="lg" text="Loading notifications..." />;
  }

  return (
    <div className="min-h-screen">
      <div className="relative overflow-hidden bg-gradient-to-br from-amber-500 via-orange-500 to-red-500 dark:from-amber-800 dark:via-orange-800 dark:to-red-800">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute -top-10 -right-20 w-64 h-64 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 left-1/4 w-40 h-40 bg-amber-300 rounded-full blur-3xl"></div>
        </div>
        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
          <h1 className="text-2xl md:text-3xl font-bold text-white mb-2">
            Notifications
          </h1>
          <p className="text-amber-100 text-lg">
            Stay updated with your travel activities
          </p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6 relative z-10 pb-12">

        <Card className="mb-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setFilter('all')}
                className={`px-4 py-2 rounded-xl font-medium transition-all duration-200 ${
                  filter === 'all'
                    ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg shadow-amber-500/25'
                    : 'bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm text-gray-700 dark:text-gray-300 border border-gray-200/60 dark:border-gray-700/50'
                }`}
              >
                All ({notifications.length})
              </button>
              <button
                onClick={() => setFilter('unread')}
                className={`px-4 py-2 rounded-xl font-medium transition-all duration-200 ${
                  filter === 'unread'
                    ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg shadow-amber-500/25'
                    : 'bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm text-gray-700 dark:text-gray-300 border border-gray-200/60 dark:border-gray-700/50'
                }`}
              >
                Unread ({unreadCount})
              </button>
            </div>

            {unreadCount > 0 && (
              <Button onClick={markAllAsRead} variant="ghost" size="sm">
                Mark all as read
              </Button>
            )}
          </div>
        </Card>

        {filteredNotifications.length === 0 ? (
          <Card>
            <div className="text-center py-12">
              <BellIcon className="h-16 w-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                No notifications
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                {filter === 'unread'
                  ? "You're all caught up!"
                  : "You don't have any notifications yet."}
              </p>
            </div>
          </Card>
        ) : (
          <div className="space-y-4">
            {filteredNotifications.map((notification) => (
              <Card
                key={notification.id}
                className={`transition-all ${
                  !notification.read
                    ? 'border-l-4 border-l-primary-500 bg-primary-50/30 dark:bg-primary-900/10'
                    : ''
                }`}
              >
                <div className="flex items-start gap-4">
                  {getNotificationIcon(notification.type)}

                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-1">
                          {notification.title}
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {notification.message}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-500 mt-2">
                          {formatTime(notification.created_at)}
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        {!notification.read && (
                          <button
                            onClick={() => markAsRead(notification.id)}
                            className="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium whitespace-nowrap"
                          >
                            Mark read
                          </button>
                        )}
                        <button
                          onClick={() => deleteNotification(notification.id)}
                          className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                          title="Delete notification"
                        >
                          <XMarkIcon className="h-5 w-5" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default NotificationsPage;
