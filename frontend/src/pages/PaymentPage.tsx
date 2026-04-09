import { useRequireAuth } from '@/hooks/useAuth';
import { Card } from '@/components/common';

const PaymentPage = () => {
  useRequireAuth();

  return (
    <div className="min-h-screen">
      <div className="relative overflow-hidden bg-gradient-to-br from-indigo-500 via-purple-600 to-pink-600 dark:from-indigo-800 dark:via-purple-800 dark:to-pink-800">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute -top-10 -right-20 w-64 h-64 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 left-1/4 w-40 h-40 bg-purple-300 rounded-full blur-3xl"></div>
        </div>
        <div className="relative max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
          <h1 className="text-3xl md:text-4xl font-extrabold text-white mb-2">
            Payment
          </h1>
          <p className="text-purple-100 text-lg">Secure payment processing</p>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6 relative z-10 pb-12">
      <Card variant="glass">
        <p className="text-center text-gray-600 dark:text-gray-400 py-12">
          Stripe payment integration will be implemented here
        </p>
      </Card>
      </div>
    </div>
  );
};

export default PaymentPage;
