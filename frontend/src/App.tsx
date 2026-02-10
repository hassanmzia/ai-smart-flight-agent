import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { lazy, Suspense, useEffect } from 'react';

import Header from './components/layout/Header';
import Footer from './components/layout/Footer';
import AgentChat from './components/booking/AgentChat';
import Loading from './components/common/Loading';
import { ROUTES } from './utils/constants';
import { getTheme, setTheme } from './utils/helpers';

// Lazy load pages
const HomePage = lazy(() => import('./pages/HomePage'));
const SearchPage = lazy(() => import('./pages/SearchPage'));
const FlightResultsPage = lazy(() => import('./pages/FlightResultsPage'));
const HotelResultsPage = lazy(() => import('./pages/HotelResultsPage'));
const BookingPage = lazy(() => import('./pages/BookingPage'));
const FlightBookingPage = lazy(() => import('./pages/FlightBookingPage'));
const HotelBookingPage = lazy(() => import('./pages/HotelBookingPage'));
const PaymentPage = lazy(() => import('./pages/PaymentPage'));
const ItineraryPage = lazy(() => import('./pages/ItineraryPage'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const AdminDashboardPage = lazy(() => import('./pages/AdminDashboardPage'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));

// Create query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function App() {
  // Initialize theme
  useEffect(() => {
    const theme = getTheme();
    setTheme(theme);
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col">
          <Header />

          <main className="flex-1">
            <Suspense fallback={<Loading fullScreen size="lg" text="Loading..." />}>
              <Routes>
                <Route path={ROUTES.HOME} element={<HomePage />} />
                <Route path={ROUTES.SEARCH} element={<SearchPage />} />
                <Route path={ROUTES.FLIGHT_RESULTS} element={<FlightResultsPage />} />
                <Route path={ROUTES.HOTEL_RESULTS} element={<HotelResultsPage />} />
                <Route path="/booking/flight" element={<FlightBookingPage />} />
                <Route path="/booking/hotel" element={<HotelBookingPage />} />
                <Route path={ROUTES.BOOKING} element={<BookingPage />} />
                <Route path="/booking/:type/:id" element={<BookingPage />} />
                <Route path={ROUTES.PAYMENT} element={<PaymentPage />} />
                <Route path={ROUTES.ITINERARY} element={<ItineraryPage />} />
                <Route path={ROUTES.PROFILE} element={<ProfilePage />} />
                <Route path={ROUTES.DASHBOARD} element={<DashboardPage />} />
                <Route path={ROUTES.ADMIN_DASHBOARD} element={<AdminDashboardPage />} />
                <Route path={ROUTES.LOGIN} element={<LoginPage />} />
                <Route path={ROUTES.REGISTER} element={<RegisterPage />} />

                {/* 404 */}
                <Route
                  path="*"
                  element={
                    <div className="flex items-center justify-center h-screen">
                      <div className="text-center">
                        <h1 className="text-6xl font-bold text-gray-900 dark:text-white mb-4">
                          404
                        </h1>
                        <p className="text-xl text-gray-600 dark:text-gray-400">
                          Page not found
                        </p>
                      </div>
                    </div>
                  }
                />
              </Routes>
            </Suspense>
          </main>

          <Footer />

          {/* AI Agent Chat Widget */}
          <AgentChat />

          {/* Toast Notifications */}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 3000,
              style: {
                background: 'var(--toast-bg)',
                color: 'var(--toast-color)',
              },
              success: {
                iconTheme: {
                  primary: '#10b981',
                  secondary: '#fff',
                },
              },
              error: {
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#fff',
                },
              },
            }}
          />
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
