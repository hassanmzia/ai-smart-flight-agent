import { useRequireAdmin } from '@/hooks/useAuth';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common';

const AdminDashboardPage = () => {
  useRequireAdmin();

  return (
    <div className="min-h-screen">
      <div className="relative overflow-hidden bg-gradient-to-br from-gray-700 via-gray-800 to-gray-900 dark:from-gray-800 dark:via-gray-900 dark:to-black">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute -top-10 -right-20 w-64 h-64 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 left-1/4 w-40 h-40 bg-gray-400 rounded-full blur-3xl"></div>
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
          <h1 className="text-3xl md:text-4xl font-extrabold text-white mb-2">
            Admin Dashboard
          </h1>
          <p className="text-gray-300 text-lg">System overview and management</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6 relative z-10 pb-12">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card variant="glass" className="overflow-hidden">
          <div className="p-6">
            <p className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-1">Total Users</p>
            <p className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">0</p>
          </div>
        </Card>

        <Card variant="glass" className="overflow-hidden">
          <div className="p-6">
            <p className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-1">Total Bookings</p>
            <p className="text-4xl font-bold bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">0</p>
          </div>
        </Card>

        <Card variant="glass" className="overflow-hidden">
          <div className="p-6">
            <p className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-1">Total Revenue</p>
            <p className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">$0</p>
          </div>
        </Card>
      </div>
      </div>
    </div>
  );
};

export default AdminDashboardPage;
