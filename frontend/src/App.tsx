import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { lazy, Suspense, useEffect } from 'react';

import Header from './components/layout/Header';
import Footer from './components/layout/Footer';
import AgentChat from './components/booking/AgentChat';
import Loading from './components/common/Loading';
import RequireAuth from './components/common/RequireAuth';
import { ROUTES } from './utils/constants';
import { getTheme, setTheme } from './utils/helpers';

// Lazy load pages
const HomePage = lazy(() => import('./pages/HomePage'));
const SearchPage = lazy(() => import('./pages/SearchPage'));
const FlightSearchPage = lazy(() => import('./pages/FlightSearchPage'));
const HotelSearchPage = lazy(() => import('./pages/HotelSearchPage'));
const AIPlannerPage = lazy(() => import('./pages/AIPlannerPage'));
const FlightResultsPage = lazy(() => import('./pages/FlightResultsPage'));
const HotelResultsPage = lazy(() => import('./pages/HotelResultsPage'));
const CarRentalSearchPage = lazy(() => import('./pages/CarRentalSearchPage'));
const RestaurantSearchPage = lazy(() => import('./pages/RestaurantSearchPage'));
const TouristAttractionSearchPage = lazy(() => import('./pages/TouristAttractionSearchPage'));
const WeatherPage = lazy(() => import('./pages/WeatherPage'));
const EventsPage = lazy(() => import('./pages/EventsPage'));
const ShoppingPage = lazy(() => import('./pages/ShoppingPage'));
const SafetyPage = lazy(() => import('./pages/SafetyPage'));
const CommutePage = lazy(() => import('./pages/CommutePage'));
const BookingPage = lazy(() => import('./pages/BookingPage'));
const FlightBookingPage = lazy(() => import('./pages/FlightBookingPage'));
const HotelBookingPage = lazy(() => import('./pages/HotelBookingPage'));
const RentalBookingPage = lazy(() => import('./pages/RentalBookingPage'));
const PaymentPage = lazy(() => import('./pages/PaymentPage'));
const ItineraryPage = lazy(() => import('./pages/ItineraryPage'));
const ItineraryDetailPage = lazy(() => import('./pages/ItineraryDetailPage'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const AdminDashboardPage = lazy(() => import('./pages/AdminDashboardPage'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));
const ChatPage = lazy(() => import('./pages/ChatPage'));
const CollaboratePage = lazy(() => import('./pages/CollaboratePage'));
const NotificationsPage = lazy(() => import('./pages/NotificationsPage'));
const AboutPage = lazy(() => import('./pages/AboutPage'));
const ContactPage = lazy(() => import('./pages/ContactPage'));
const FAQPage = lazy(() => import('./pages/FAQPage'));
const TermsPage = lazy(() => import('./pages/TermsPage'));
const PrivacyPage = lazy(() => import('./pages/PrivacyPage'));
const PricingPage = lazy(() => import('./pages/PricingPage'));
const PredictionsPage = lazy(() => import('./pages/PredictionsPage'));
const TripMapPage = lazy(() => import('./pages/TripMapPage'));
const CommunityPage = lazy(() => import('./pages/CommunityPage'));
const TravelProfilePage = lazy(() => import('./pages/TravelProfilePage'));
const SafetyDashboardPage = lazy(() => import('./pages/SafetyDashboardPage'));
const AIRatingsPage = lazy(() => import('./pages/AIRatingsPage'));
const LanguageToolPage = lazy(() => import('./pages/LanguageToolPage'));
const DestinationGuidePage = lazy(() => import('./pages/DestinationGuidePage'));
const AgentHubPage = lazy(() => import('./pages/AgentHubPage'));
const TripMemoryPage = lazy(() => import('./pages/TripMemoryPage'));
const PartnershipsPage = lazy(() => import('./pages/PartnershipsPage'));
const DestinationKBPage = lazy(() => import('./pages/DestinationKBPage'));
const TravelStoriesPage = lazy(() => import('./pages/TravelStoriesPage'));
const TripGalleryPage = lazy(() => import('./pages/TripGalleryPage'));
const ContentHubPage = lazy(() => import('./pages/ContentHubPage'));
const FaithTravelPage = lazy(() => import('./pages/FaithTravelPage'));
const HealthTravelPage = lazy(() => import('./pages/HealthTravelPage'));
const MyBookingsPage = lazy(() => import('./pages/MyBookingsPage'));
const BookingDetailPage = lazy(() => import('./pages/BookingDetailPage'));

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
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col overflow-x-hidden">
          <Header />

          <main className="flex-1 max-w-full">
            <Suspense fallback={<Loading fullScreen size="lg" text="Loading..." />}>
              <Routes>
                {/* Public routes */}
                <Route path={ROUTES.HOME} element={<HomePage />} />
                <Route path={ROUTES.LOGIN} element={<LoginPage />} />
                <Route path={ROUTES.REGISTER} element={<RegisterPage />} />
                <Route path="/about" element={<AboutPage />} />
                <Route path="/contact" element={<ContactPage />} />
                <Route path="/faq" element={<FAQPage />} />
                <Route path="/help" element={<FAQPage />} />
                <Route path="/terms" element={<TermsPage />} />
                <Route path="/privacy" element={<PrivacyPage />} />
                <Route path={ROUTES.PRICING} element={<PricingPage />} />

                {/* Protected routes — require login */}
                <Route path={ROUTES.SEARCH} element={<RequireAuth><SearchPage /></RequireAuth>} />
                <Route path={ROUTES.FLIGHT_SEARCH} element={<RequireAuth><FlightSearchPage /></RequireAuth>} />
                <Route path={ROUTES.HOTEL_SEARCH} element={<RequireAuth><HotelSearchPage /></RequireAuth>} />
                <Route path={ROUTES.AI_PLANNER} element={<RequireAuth><AIPlannerPage /></RequireAuth>} />
                <Route path={ROUTES.CHAT} element={<RequireAuth><ChatPage /></RequireAuth>} />
                <Route path={ROUTES.FLIGHT_RESULTS} element={<RequireAuth><FlightResultsPage /></RequireAuth>} />
                <Route path={ROUTES.HOTEL_RESULTS} element={<RequireAuth><HotelResultsPage /></RequireAuth>} />
                <Route path={ROUTES.RENTAL_SEARCH} element={<RequireAuth><HotelSearchPage /></RequireAuth>} />
                <Route path={ROUTES.RENTAL_RESULTS} element={<RequireAuth><HotelResultsPage /></RequireAuth>} />
                <Route path="/cars" element={<RequireAuth><CarRentalSearchPage /></RequireAuth>} />
                <Route path="/restaurants" element={<RequireAuth><RestaurantSearchPage /></RequireAuth>} />
                <Route path="/attractions" element={<RequireAuth><TouristAttractionSearchPage /></RequireAuth>} />
                <Route path="/weather" element={<RequireAuth><WeatherPage /></RequireAuth>} />
                <Route path="/events" element={<RequireAuth><EventsPage /></RequireAuth>} />
                <Route path="/shopping" element={<RequireAuth><ShoppingPage /></RequireAuth>} />
                <Route path="/safety" element={<RequireAuth><SafetyPage /></RequireAuth>} />
                <Route path="/commute" element={<RequireAuth><CommutePage /></RequireAuth>} />
                <Route path="/booking/flight" element={<RequireAuth><FlightBookingPage /></RequireAuth>} />
                <Route path="/booking/hotel" element={<RequireAuth><HotelBookingPage /></RequireAuth>} />
                <Route path="/booking/rental" element={<RequireAuth><RentalBookingPage /></RequireAuth>} />
                <Route path={ROUTES.MY_BOOKINGS} element={<RequireAuth><MyBookingsPage /></RequireAuth>} />
                <Route path={ROUTES.BOOKING} element={<RequireAuth><BookingPage /></RequireAuth>} />
                <Route path="/booking/:type/:id" element={<RequireAuth><BookingPage /></RequireAuth>} />
                <Route path="/booking/:id" element={<RequireAuth><BookingDetailPage /></RequireAuth>} />
                <Route path={ROUTES.PAYMENT} element={<RequireAuth><PaymentPage /></RequireAuth>} />
                <Route path={ROUTES.ITINERARY} element={<RequireAuth><ItineraryPage /></RequireAuth>} />
                <Route path="/itineraries/:id" element={<RequireAuth><ItineraryDetailPage /></RequireAuth>} />
                <Route path={ROUTES.PROFILE} element={<RequireAuth><ProfilePage /></RequireAuth>} />
                <Route path={ROUTES.DASHBOARD} element={<RequireAuth><DashboardPage /></RequireAuth>} />
                <Route path={ROUTES.ADMIN_DASHBOARD} element={<RequireAuth><AdminDashboardPage /></RequireAuth>} />
                <Route path="/notifications" element={<RequireAuth><NotificationsPage /></RequireAuth>} />
                <Route path={ROUTES.COLLABORATE} element={<RequireAuth><CollaboratePage /></RequireAuth>} />
                <Route path={ROUTES.PREDICTIONS} element={<RequireAuth><PredictionsPage /></RequireAuth>} />
                <Route path={ROUTES.TRIP_MAP} element={<RequireAuth><TripMapPage /></RequireAuth>} />
                <Route path={ROUTES.COMMUNITY} element={<RequireAuth><CommunityPage /></RequireAuth>} />
                <Route path={ROUTES.TRAVEL_PROFILE} element={<RequireAuth><TravelProfilePage /></RequireAuth>} />
                <Route path={ROUTES.SAFETY_DASHBOARD} element={<RequireAuth><SafetyDashboardPage /></RequireAuth>} />
                <Route path={ROUTES.AI_RATINGS} element={<RequireAuth><AIRatingsPage /></RequireAuth>} />
                <Route path={ROUTES.LANGUAGE_TOOL} element={<RequireAuth><LanguageToolPage /></RequireAuth>} />
                <Route path={ROUTES.DESTINATION_GUIDE} element={<RequireAuth><DestinationGuidePage /></RequireAuth>} />
                <Route path={ROUTES.AGENT_HUB} element={<RequireAuth><AgentHubPage /></RequireAuth>} />
                <Route path={ROUTES.TRIP_MEMORY} element={<RequireAuth><TripMemoryPage /></RequireAuth>} />
                <Route path={ROUTES.PARTNERSHIPS} element={<PartnershipsPage />} />
                <Route path={ROUTES.DESTINATION_KB} element={<DestinationKBPage />} />
                <Route path={ROUTES.TRAVEL_STORIES} element={<TravelStoriesPage />} />
                <Route path={ROUTES.TRIP_GALLERY} element={<TripGalleryPage />} />
                <Route path={ROUTES.CONTENT_HUB} element={<ContentHubPage />} />
                <Route path={ROUTES.FAITH_TRAVEL} element={<RequireAuth><FaithTravelPage /></RequireAuth>} />
                <Route path={ROUTES.HEALTH_TRAVEL} element={<RequireAuth><HealthTravelPage /></RequireAuth>} />

                {/* 404 */}
                <Route
                  path="*"
                  element={
                    <div className="flex items-center justify-center min-h-[60dvh]">
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
