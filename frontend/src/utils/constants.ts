export const API_BASE_URL = import.meta.env.VITE_API_URL || '';
export const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'wss://demo.eminencetechsolutions.com:3090';
export const STRIPE_PUBLIC_KEY = import.meta.env.VITE_STRIPE_PUBLIC_KEY || '';

export const APP_NAME = import.meta.env.VITE_APP_NAME || 'AI Travel Agent';
export const APP_VERSION = import.meta.env.VITE_APP_VERSION || '1.0.0';

// Route paths
export const ROUTES = {
  HOME: '/',
  SEARCH: '/search',
  FLIGHT_SEARCH: '/flights/search',
  HOTEL_SEARCH: '/hotels/search',
  AI_PLANNER: '/ai-planner',
  FLIGHT_RESULTS: '/flights',
  HOTEL_RESULTS: '/hotels',
  BOOKING: '/booking',
  PAYMENT: '/payment',
  ITINERARY: '/itinerary',
  PROFILE: '/profile',
  DASHBOARD: '/dashboard',
  ADMIN_DASHBOARD: '/admin',
  CHAT: '/chat',
  COLLABORATE: '/collaborate',
  LOGIN: '/login',
  REGISTER: '/register',
  PRICING: '/pricing',
  PREDICTIONS: '/predictions',
  TRIP_MAP: '/my-travel',
  COMMUNITY: '/community',
  TRAVEL_PROFILE: '/travel-profile',
  SAFETY_DASHBOARD: '/safety-dashboard',
  AI_RATINGS: '/ai-ratings',
  LANGUAGE_TOOL: '/language-tool',
  DESTINATION_GUIDE: '/destination-guide',
  AGENT_HUB: '/agent-hub',
  TRIP_MEMORY: '/trip-memory',
  PARTNERSHIPS: '/partnerships',
  DESTINATION_KB: '/destination-kb',
  TRAVEL_STORIES: '/travel-stories',
  TRIP_GALLERY: '/trip-gallery',
  CONTENT_HUB: '/content-hub',
  FAITH_TRAVEL: '/faith-travel',
  HEALTH_TRAVEL: '/health-travel',
  RENTAL_SEARCH: '/rentals/search',
  RENTAL_RESULTS: '/rentals',
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
    LIST: '/api/bookings/bookings',
    DETAILS: '/api/bookings/bookings',
    CANCEL: '/api/bookings/bookings',
    UPDATE: '/api/bookings/bookings',
  },
  PAYMENTS: {
    CREATE_INTENT: '/api/payments/create-intent',
    CONFIRM: '/api/payments/confirm',
    METHODS: '/api/payments/methods',
  },
  AGENT: {
    CHAT: '/api/agents/chat',
    CONTEXT: '/api/agents/context',
    PLAN: '/api/agents/plan',
    DOCUMENTS: '/api/agents/documents',
    VOICE_TO_TRIP: '/api/agents/voice-to-trip',
    IMAGE_TO_TRIP: '/api/agents/image-to-trip',
    AUTONOMOUS_BOOK: '/api/agents/autonomous-book',
    DEBATE: '/api/agents/debate',
    PREDICT_PRICES: '/api/agents/predict-prices',
    BEST_TIME: '/api/agents/best-time',
    TRENDS: '/api/agents/trends',
    TRAVEL_DNA: '/api/agents/travel-dna',
    RECOMMENDATIONS: '/api/agents/recommendations',
    SUBSCRIPTION: '/api/agents/subscription',
    AFFILIATE_LINK: '/api/agents/affiliate/link',
    AFFILIATE_REPORT: '/api/agents/affiliate/report',
    AFFILIATE_PARTNERS: '/api/agents/affiliate/partners',
    PRICE_WATCH_CREATE: '/api/agents/price-watch/create',
    PRICE_WATCH_LIST: '/api/agents/price-watch/list',
    CONFIRM_BOOKING: '/api/agents/confirm-booking',
    ANALYZE_SCREENSHOT: '/api/agents/analyze-screenshot',
    CHECK_FEATURE: '/api/agents/check-feature',
    AUTO_BUILD: '/api/agents/auto-build',
    TRANSLATE: '/api/agents/translate',
    COMMON_PHRASES: '/api/agents/common-phrases',
    LIVE_CONTEXT: '/api/agents/live-context',
    CROWD_LEVELS_DETAIL: '/api/agents/crowd-levels-detail',
    // Phase 5: Partnerships & Destination KB
    COUPONS: '/api/agents/coupons',
    COUPONS_CREATE: '/api/agents/coupons/create',
    COUPONS_REDEEM: '/api/agents/coupons/redeem',
    REFERRAL: '/api/agents/referral',
    REFERRAL_SEND: '/api/agents/referral/send',
    PARTNER_REGISTER: '/api/agents/partners/register',
    PARTNER_DASHBOARD: '/api/agents/partners/dashboard',
    SAVINGS_CALCULATE: '/api/agents/savings/calculate',
    DESTINATION_KB: '/api/agents/destinations/knowledge',
    DESTINATION_CULTURAL_INFO: '/api/agents/destinations/cultural-info',
    DESTINATION_TIPS_SUBMIT: '/api/agents/destinations/tips/submit',
    DESTINATION_TIPS_VOTE: '/api/agents/destinations/tips/vote',
    DESTINATION_SEARCH: '/api/agents/destinations/search',
    DESTINATION_FESTIVALS: '/api/agents/destinations/festivals',
    DESTINATION_ETIQUETTE: '/api/agents/destinations/etiquette',
    // Phase 6: Social & Viral Growth
    STORIES_GENERATE: '/api/agents/stories/generate',
    STORIES_SOCIAL_CARDS: '/api/agents/stories/social-cards',
    STORIES_MINE: '/api/agents/stories/mine',
    STORIES_PUBLIC: '/api/agents/stories/public',
    STORIES_LIKE: '/api/agents/stories/like',
    STORIES_COMMENT: '/api/agents/stories/comment',
    STORIES_PUBLISH: '/api/agents/stories/publish',
    TEMPLATES_CREATE: '/api/agents/templates/create',
    TEMPLATES_GENERATE: '/api/agents/templates/generate',
    TEMPLATES_BROWSE: '/api/agents/templates/browse',
    TEMPLATES_FEATURED: '/api/agents/templates/featured',
    TEMPLATES_MINE: '/api/agents/templates/mine',
    TEMPLATES_CLONE: '/api/agents/templates/clone',
    TEMPLATES_LIKE: '/api/agents/templates/like',
    TEMPLATES_RATE: '/api/agents/templates/rate',
    CONTENT_SUBMIT: '/api/agents/content/submit',
    CONTENT_DESTINATION: '/api/agents/content/destination',
    CONTENT_VOTE: '/api/agents/content/vote',
    CONTENT_TRENDING: '/api/agents/content/trending',
    CONTENT_MINE: '/api/agents/content/mine',
    CONTENT_STATS: '/api/agents/content/stats',
    // Voice & Offline Language
    VOICE_TRANSLATE: '/api/agents/voice-translate',
    OFFLINE_PHRASES: '/api/agents/offline-phrases',
    // Collaborative Filtering
    SIMILAR_USERS: '/api/agents/community/similar-users',
    PEOPLE_LIKE_YOU: '/api/agents/community/people-like-you',
    SOCIAL_PROOF: '/api/agents/community/social-proof',
    ENJOYMENT_PREDICTION: '/api/agents/community/enjoyment-prediction',
    // Phase 7: Faith & Health Awareness
    FAITH_PRAYER_TIMES: '/api/agents/faith/prayer-times',
    FAITH_WORSHIP_PLACES: '/api/agents/faith/worship-places',
    FAITH_SPIRITUAL_SITES: '/api/agents/faith/spiritual-sites',
    FAITH_DIETARY: '/api/agents/faith/dietary-restaurants',
    FAITH_RAMADAN: '/api/agents/faith/ramadan-schedule',
    FAITH_SUMMARY: '/api/agents/faith/summary',
    HEALTH_MEDICAL: '/api/agents/health/medical-facilities',
    HEALTH_ACCESSIBILITY: '/api/agents/health/accessibility',
    HEALTH_ACCESSIBILITY_RATE: '/api/agents/health/accessibility/rate',
    HEALTH_MEDICATION: '/api/agents/health/medication-reminders',
    HEALTH_MED_ADJUST: '/api/agents/health/medication-adjust',
    HEALTH_INSURANCE: '/api/agents/health/insurance',
    HEALTH_FATIGUE: '/api/agents/health/fatigue-itinerary',
    HEALTH_SUMMARY: '/api/agents/health/summary',
    // Vacation Rentals
    RENTAL_SEARCH: '/api/hotels/rentals/search',
    RENTAL_FEATURED: '/api/hotels/rentals/featured',
  },
  COMMUNITY: {
    CURATED_GUIDES_GENERATE: '/api/community/curated-guides/generate/',
  },
  PRICE_ALERTS: {
    CREATE: '/api/price-alerts',
    LIST: '/api/price-alerts',
    DELETE: '/api/price-alerts',
  },
  ITINERARY: {
    LIST: '/api/itineraries/itineraries',
    CREATE: '/api/itineraries/itineraries',
    UPDATE: '/api/itineraries/itineraries',
    DELETE: '/api/itineraries/itineraries',
    DAYS: '/api/itineraries/days',
    ITEMS: '/api/itineraries/items',
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
  RAG_DOCUMENTS: ['rag-documents'],
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
