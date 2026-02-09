export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://172.168.1.95:8109';
export const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://172.168.1.95:8109';
export const STRIPE_PUBLIC_KEY = import.meta.env.VITE_STRIPE_PUBLIC_KEY || '';

export const APP_NAME = import.meta.env.VITE_APP_NAME || 'AI Travel Agent';
export const APP_VERSION = import.meta.env.VITE_APP_VERSION || '1.0.0';

// Route paths
export const ROUTES = {
  HOME: '/',
  SEARCH: '/search',
  FLIGHT_RESULTS: '/flights',
  HOTEL_RESULTS: '/hotels',
  BOOKING: '/booking',
  PAYMENT: '/payment',
  ITINERARY: '/itinerary',
  PROFILE: '/profile',
  DASHBOARD: '/dashboard',
  ADMIN_DASHBOARD: '/admin',
  LOGIN: '/login',
  REGISTER: '/register',
} as const;

// Local storage keys
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'auth_token',
  REFRESH_TOKEN: 'refresh_token',
  USER_DATA: 'user_data',
  THEME: 'theme',
  SEARCH_HISTORY: 'search_history',
} as const;

// API endpoints
export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/api/auth/login',
    REGISTER: '/api/auth/register',
    LOGOUT: '/api/auth/logout',
    REFRESH: '/api/auth/refresh',
    ME: '/api/auth/me',
  },
  FLIGHTS: {
    SEARCH: '/api/flights/search',
    DETAILS: '/api/flights',
    BOOK: '/api/flights/book',
  },
  HOTELS: {
    SEARCH: '/api/hotels/search',
    DETAILS: '/api/hotels',
    BOOK: '/api/hotels/book',
  },
  BOOKINGS: {
    LIST: '/api/bookings',
    DETAILS: '/api/bookings',
    CANCEL: '/api/bookings',
    UPDATE: '/api/bookings',
  },
  PAYMENTS: {
    CREATE_INTENT: '/api/payments/create-intent',
    CONFIRM: '/api/payments/confirm',
    METHODS: '/api/payments/methods',
  },
  AGENT: {
    CHAT: '/api/agent/chat',
    CONTEXT: '/api/agent/context',
  },
  PRICE_ALERTS: {
    CREATE: '/api/price-alerts',
    LIST: '/api/price-alerts',
    DELETE: '/api/price-alerts',
  },
  ITINERARY: {
    LIST: '/api/itineraries',
    CREATE: '/api/itineraries',
    UPDATE: '/api/itineraries',
    DELETE: '/api/itineraries',
  },
  NOTIFICATIONS: {
    LIST: '/api/notifications',
    MARK_READ: '/api/notifications/read',
  },
  ANALYTICS: {
    SUMMARY: '/api/analytics/summary',
  },
} as const;

// Flight classes
export const FLIGHT_CLASSES = [
  { value: 'economy', label: 'Economy' },
  { value: 'premium_economy', label: 'Premium Economy' },
  { value: 'business', label: 'Business' },
  { value: 'first', label: 'First Class' },
] as const;

// Hotel amenities
export const HOTEL_AMENITIES = [
  'WiFi',
  'Parking',
  'Pool',
  'Gym',
  'Restaurant',
  'Bar',
  'Spa',
  'Room Service',
  'Airport Shuttle',
  'Pet Friendly',
  'Air Conditioning',
  'Breakfast Included',
] as const;

// Recommendation colors
export const RECOMMENDATION_COLORS = {
  excellent: {
    bg: 'bg-green-100 dark:bg-green-900/20',
    text: 'text-green-800 dark:text-green-300',
    border: 'border-green-300 dark:border-green-700',
  },
  good: {
    bg: 'bg-blue-100 dark:bg-blue-900/20',
    text: 'text-blue-800 dark:text-blue-300',
    border: 'border-blue-300 dark:border-blue-700',
  },
  fair: {
    bg: 'bg-yellow-100 dark:bg-yellow-900/20',
    text: 'text-yellow-800 dark:text-yellow-300',
    border: 'border-yellow-300 dark:border-yellow-700',
  },
  poor: {
    bg: 'bg-red-100 dark:bg-red-900/20',
    text: 'text-red-800 dark:text-red-300',
    border: 'border-red-300 dark:border-red-700',
  },
} as const;

// Query keys for React Query
export const QUERY_KEYS = {
  USER: ['user'],
  FLIGHTS: ['flights'],
  HOTELS: ['hotels'],
  BOOKINGS: ['bookings'],
  BOOKING: (id: string) => ['booking', id],
  PRICE_ALERTS: ['price-alerts'],
  ITINERARIES: ['itineraries'],
  ITINERARY: (id: string) => ['itinerary', id],
  NOTIFICATIONS: ['notifications'],
  ANALYTICS: ['analytics'],
} as const;

// Pagination
export const DEFAULT_PAGE_SIZE = 20;
export const DEFAULT_PAGE = 1;

// Date formats
export const DATE_FORMATS = {
  DISPLAY: 'MMM dd, yyyy',
  DISPLAY_WITH_TIME: 'MMM dd, yyyy HH:mm',
  API: 'yyyy-MM-dd',
  API_WITH_TIME: "yyyy-MM-dd'T'HH:mm:ss",
} as const;

// Currency symbols
export const CURRENCY_SYMBOLS: Record<string, string> = {
  USD: '$',
  EUR: '€',
  GBP: '£',
  JPY: '¥',
  CAD: 'C$',
  AUD: 'A$',
  INR: '₹',
};

// WebSocket events
export const WS_EVENTS = {
  CONNECT: 'connect',
  DISCONNECT: 'disconnect',
  NOTIFICATION: 'notification',
  PRICE_UPDATE: 'price_update',
  BOOKING_UPDATE: 'booking_update',
  CHAT_MESSAGE: 'chat_message',
} as const;

// Toast durations (ms)
export const TOAST_DURATION = {
  SHORT: 2000,
  NORMAL: 3000,
  LONG: 5000,
} as const;

// Breakpoints (matching Tailwind)
export const BREAKPOINTS = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536,
} as const;
