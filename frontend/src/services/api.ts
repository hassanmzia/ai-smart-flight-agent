import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { API_BASE_URL, STORAGE_KEYS } from '@/utils/constants';
import { storage } from '@/utils/helpers';
import type { ApiResponse, ApiError } from '@/types';

/**
 * Determine the base URL for API requests.
 * In production (served via nginx reverse proxy), use relative URLs so requests
 * go through the same origin and nginx proxies /api/ to the backend.
 * In development (Vite dev server), also use relative URLs so the Vite proxy handles them.
 * Only use absolute API_BASE_URL when explicitly set to a different host.
 */
function getBaseURL(): string {
  // If running in browser and the API URL matches the current origin, use relative URLs
  if (typeof window !== 'undefined') {
    const currentOrigin = window.location.origin;
    if (!API_BASE_URL || API_BASE_URL === currentOrigin) {
      return '';  // relative URLs - let the browser/proxy handle routing
    }
  }
  return API_BASE_URL;
}

/**
 * Create axios instance with base configuration
 */
const api: AxiosInstance = axios.create({
  baseURL: getBaseURL(),
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor to add auth token
 */
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = storage.get<string>(STORAGE_KEYS.AUTH_TOKEN);

    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor to handle errors and token refresh
 */
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // Handle 401 Unauthorized - attempt token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = storage.get<string>(STORAGE_KEYS.REFRESH_TOKEN);

        if (refreshToken) {
          const response = await axios.post(`${getBaseURL()}/api/auth/refresh`, {
            refreshToken,
          });

          const { accessToken } = response.data;

          storage.set(STORAGE_KEYS.AUTH_TOKEN, accessToken);

          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${accessToken}`;
          }

          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, clear auth and redirect to login
        storage.remove(STORAGE_KEYS.AUTH_TOKEN);
        storage.remove(STORAGE_KEYS.REFRESH_TOKEN);
        storage.remove(STORAGE_KEYS.USER_DATA);
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // Handle 502/503/504 - backend unavailable
    if (error.response?.status && [502, 503, 504].includes(error.response.status)) {
      const apiError: ApiError = {
        message: 'The server is temporarily unavailable. Please try again in a moment.',
        code: 'BACKEND_UNAVAILABLE',
        status: error.response.status,
      };
      if (error.response) {
        (apiError as any).response = error.response;
      }
      return Promise.reject(apiError);
    }

    // Format error response but preserve original response for debugging
    const apiError: ApiError = {
      message: error.response?.data?.message || error.response?.data?.detail || error.message || 'An unexpected error occurred',
      code: error.code,
      status: error.response?.status,
      errors: error.response?.data?.errors,
    };

    // Preserve the original response for detailed error handling
    if (error.response) {
      (apiError as any).response = error.response;
    }

    return Promise.reject(apiError);
  }
);

/**
 * Helper function to handle API responses
 */
export const handleApiResponse = <T>(response: any): T => {
  if (response.data?.success !== false) {
    return response.data?.data || response.data;
  }
  throw new Error(response.data?.message || 'API request failed');
};

/**
 * Helper function to handle API errors
 */
export const handleApiError = (error: any): never => {
  if (error.response?.data?.message) {
    throw new Error(error.response.data.message);
  }
  throw error;
};

export default api;
