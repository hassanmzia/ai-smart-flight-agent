// User & Authentication Types
export interface UserProfile {
  id: number;
  date_of_birth?: string;
  nationality?: string;
  passport_number?: string;
  passport_expiry?: string;
  preferred_currency: string;
  preferred_language: string;
  preferred_travel_class: string;
  preferred_airlines: string[];
  preferred_hotel_chains: string[];
  frequent_flyer_programs: Record<string, string>;
  hotel_loyalty_programs: Record<string, string>;
  dietary_restrictions: string[];
  accessibility_needs?: string;
  seat_preference: string;
  total_trips: number;
  total_flights: number;
  total_hotel_nights: number;
  countries_visited: string[];
  cities_visited: string[];
  email_notifications: boolean;
  sms_notifications: boolean;
  push_notifications: boolean;
  avatar?: string;
  bio?: string;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: string | number;
  email: string;
  name?: string;
  first_name?: string;
  last_name?: string;
  full_name?: string;
  phone?: string;
  phone_number?: string;
  role?: 'user' | 'admin';
  is_active?: boolean;
  is_verified?: boolean;
  is_staff?: boolean;
  date_joined?: string;
  last_login?: string;
  profile?: UserProfile;
  preferences?: UserPreferences;
  createdAt?: string;
  updatedAt?: string;
  created_at?: string;
  updated_at?: string;
}

export interface UserPreferences {
  seatPreference?: 'window' | 'aisle' | 'middle';
  mealPreference?: string;
  currency: string;
  language: string;
  notifications: {
    email: boolean;
    sms: boolean;
    push: boolean;
  };
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  password_confirm: string;
  first_name: string;
  last_name: string;
  phone_number?: string;
}

// Flight Types
export interface Flight {
  id: string;
  airline: string;
  airlineLogo?: string;
  flightNumber: string;
  origin: Airport;
  destination: Airport;
  departureTime: string;
  arrivalTime: string;
  duration: number; // in minutes
  price: number;
  currency: string;
  class: 'economy' | 'premium_economy' | 'business' | 'first';
  stops: number;
  layovers?: Layover[];
  availableSeats: number;
  aircraft?: string;
  amenities?: string[];
  carbonEmissions?: CarbonEmissions;
  oftenDelayedBy?: number;
  bookingToken?: string;
  goalEvaluation?: GoalEvaluation;
}

export interface Layover {
  airport: string;
  duration: number; // in minutes
  id: string;
}

export interface CarbonEmissions {
  this_flight: number;
  typical_for_route: number;
  difference_percent: number;
}

export interface Airport {
  code: string;
  name: string;
  city: string;
  country: string;
  timezone: string;
}

export interface GoalEvaluation {
  totalUtility: number;
  budgetConstraintMet: boolean;
  underBudget: boolean;
  overBudget: boolean;
  budgetDifference: number;
  priceScore: number;
  durationScore: number;
  stopsScore: number;
  timeScore: number;
  recommendation: 'excellent' | 'good' | 'fair' | 'poor';
}

export interface FlightSearchParams {
  origin: string;
  destination: string;
  departureDate: string;
  returnDate?: string;
  passengers: number;
  class: string;
  maxBudget?: number;
  goals?: {
    minPrice?: boolean;
    minDuration?: boolean;
    preferredDepartureTime?: string;
  };
}

export interface FlightFilters {
  priceRange: [number, number];
  stops: number[];
  airlines: string[];
  departureTimeRange: [number, number]; // hours 0-24
  arrivalTimeRange: [number, number];
  duration: [number, number]; // minutes
}

// Hotel Types
export interface Hotel {
  id: string;
  name: string;
  address: string;
  city: string;
  country: string;
  description?: string;
  coordinates?: {
    lat: number;
    lng: number;
  };
  gps_coordinates?: {
    latitude: number;
    longitude: number;
  };
  rating: number;
  stars: number;
  star_rating?: number;
  star_rating_display?: string;
  guest_rating?: number;
  location_rating?: number;
  review_count?: number;
  property_type?: string;
  hotel_class?: string;
  pricePerNight: number;
  price_range_min?: number;
  price_range_max?: number;
  extracted_price?: any;
  total_rate?: any;
  currency: string;
  primary_image?: string;
  images: string[];
  amenities: string[];
  amenity_count?: number;
  essential_info?: string[];
  nearby_places?: NearbyPlace[];
  check_in_time?: string;
  check_out_time?: string;
  link?: string;
  property_token?: string;
  roomTypes?: RoomType[];
  distanceFromCenter?: number; // in km
  utilityScore?: UtilityScore;
  reviews?: HotelReview[];
}

export interface NearbyPlace {
  name: string;
  transportations: any[];
}

export interface RoomType {
  id: string;
  name: string;
  description: string;
  capacity: number;
  pricePerNight: number;
  available: boolean;
  amenities: string[];
}

export interface UtilityScore {
  totalScore: number;
  priceValue: number;
  locationScore: number;
  ratingScore: number;
  amenitiesScore: number;
  recommendation: 'excellent' | 'good' | 'fair' | 'poor';
}

export interface HotelReview {
  id: string;
  userId: string;
  userName: string;
  rating: number;
  comment: string;
  createdAt: string;
}

export interface HotelSearchParams {
  destination: string;
  checkInDate: string;
  checkOutDate: string;
  guests: number;
  rooms: number;
  maxBudget?: number;
  minRating?: number;
  amenities?: string[];
}

export interface HotelFilters {
  priceRange: [number, number];
  stars: number[];
  rating: number;
  amenities: string[];
  distanceFromCenter: number;
}

// Booking Types
export interface Booking {
  id: string;
  userId: string;
  type: 'flight' | 'hotel' | 'package';
  status: 'pending' | 'confirmed' | 'cancelled' | 'completed';
  flightDetails?: FlightBooking;
  hotelDetails?: HotelBooking;
  totalAmount: number;
  currency: string;
  paymentStatus: 'pending' | 'paid' | 'refunded' | 'failed';
  paymentMethod?: string;
  createdAt: string;
  updatedAt: string;
}

export interface FlightBooking {
  flight: Flight;
  passengers: Passenger[];
  seatSelections?: SeatSelection[];
  specialRequests?: string;
}

export interface HotelBooking {
  hotel: Hotel;
  roomType: RoomType;
  checkInDate: string;
  checkOutDate: string;
  guests: number;
  specialRequests?: string;
}

export interface Passenger {
  id?: string;
  firstName: string;
  lastName: string;
  dateOfBirth: string;
  passportNumber?: string;
  nationality?: string;
  email?: string;
  phone?: string;
}

export interface SeatSelection {
  passengerId: string;
  seatNumber: string;
  price?: number;
}

// Payment Types
export interface PaymentIntent {
  id: string;
  clientSecret: string;
  amount: number;
  currency: string;
  status: string;
}

export interface PaymentMethod {
  id: string;
  type: 'card' | 'paypal' | 'bank_transfer';
  last4?: string;
  brand?: string;
  expiryMonth?: number;
  expiryYear?: number;
}

// Itinerary Types
export interface Itinerary {
  id: string;
  user: string;
  title: string;
  description: string;
  destination: string;
  start_date: string;
  end_date: string;
  status: 'draft' | 'planned' | 'approved' | 'booking' | 'booked' | 'active' | 'completed' | 'cancelled';
  travelers: any[];
  number_of_travelers: number;
  estimated_budget: string | null;
  actual_spent: string;
  currency: string;
  is_public: boolean;
  is_shared: boolean;
  shared_with: any[];
  cover_image: string;
  days?: any[];
  status_display?: string;
  duration_days?: number;
  created_at: string;
  updated_at: string;
}

export interface Activity {
  id: string;
  name: string;
  description: string;
  date: string;
  time?: string;
  location: string;
  price?: number;
  currency?: string;
  bookingUrl?: string;
}

// Price Alert Types
export interface PriceAlert {
  id: string;
  userId: string;
  type: 'flight' | 'hotel';
  searchParams: FlightSearchParams | HotelSearchParams;
  targetPrice: number;
  currentPrice?: number;
  status: 'active' | 'triggered' | 'expired';
  createdAt: string;
  expiresAt?: string;
}

// AI Agent Types
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: {
    flightResults?: Flight[];
    hotelResults?: Hotel[];
    suggestions?: string[];
  };
}

export interface AgentContext {
  sessionId: string;
  userGoals?: string[];
  budget?: number;
  preferences?: Record<string, any>;
}

// Notification Types
export interface Notification {
  id: string;
  userId: string;
  type: 'price_alert' | 'booking_confirmation' | 'payment_status' | 'trip_reminder' | 'system';
  title: string;
  message: string;
  read: boolean;
  data?: Record<string, any>;
  createdAt: string;
}

// Analytics Types (for Admin Dashboard)
export interface AnalyticsSummary {
  totalBookings: number;
  totalRevenue: number;
  activeUsers: number;
  averageBookingValue: number;
  bookingsByType: Record<string, number>;
  revenueByMonth: Array<{ month: string; revenue: number }>;
  topDestinations: Array<{ destination: string; count: number }>;
  conversionRate: number;
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  errors?: Record<string, string[]>;
}

export interface PaginatedResponse<T> {
  items: T[];
  results?: T[];  // Alternative field name for backward compatibility
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// WebSocket Types
export interface WebSocketMessage {
  type: 'notification' | 'price_update' | 'booking_update' | 'chat_message';
  payload: any;
  timestamp: string;
}

// Weather Types
export interface WeatherData {
  location: string;
  temperature: number;
  condition: string;
  humidity: number;
  windSpeed: number;
  forecast: Array<{
    date: string;
    high: number;
    low: number;
    condition: string;
  }>;
}

// Error Types
export interface ApiError {
  message: string;
  detail?: string;
  code?: string;
  status?: number;
  errors?: Record<string, string[]>;
}

// Form Types
export interface SearchFormData {
  origin?: string;
  destination?: string;
  departureDate?: string;
  returnDate?: string;
  checkInDate?: string;
  checkOutDate?: string;
  passengers?: number;
  guests?: number;
  rooms?: number;
  class?: string;
  maxBudget?: number;
}

// Store Types
export interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  updateUser: (data: Partial<User>) => Promise<void>;
  refreshUser: () => Promise<void>;
}

export interface SearchState {
  flightSearchParams: FlightSearchParams | null;
  hotelSearchParams: HotelSearchParams | null;
  flightResults: Flight[];
  hotelResults: Hotel[];
  isSearching: boolean;
  searchError: string | null;
  setFlightSearchParams: (params: FlightSearchParams) => void;
  setHotelSearchParams: (params: HotelSearchParams) => void;
  clearSearch: () => void;
}

export interface BookingState {
  currentBooking: Partial<Booking> | null;
  bookings: Booking[];
  isLoading: boolean;
  error: string | null;
  createBooking: (booking: Partial<Booking>) => Promise<void>;
  updateBooking: (id: string, data: Partial<Booking>) => Promise<void>;
  cancelBooking: (id: string) => Promise<void>;
  fetchBookings: () => Promise<void>;
}

export interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
  addNotification: (notification: Notification) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  removeNotification: (id: string) => void;
}
