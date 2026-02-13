import api, { handleApiResponse } from './api';
import { API_ENDPOINTS } from '@/utils/constants';
import type { Itinerary, Activity } from '@/types';

/**
 * Get all itineraries
 */
export const getItineraries = async (status?: string): Promise<Itinerary[]> => {
  let url = `${API_ENDPOINTS.ITINERARY.LIST}/`;
  if (status) {
    url += `?status=${status}`;
  }
  const response = await api.get(url);
  const data = handleApiResponse(response) as any;

  // Debug logging
  console.log('Itineraries API response:', data);
  console.log('Is array:', Array.isArray(data));
  console.log('Has results:', data?.results);
  console.log('Has items:', data?.items);

  // Handle both paginated and non-paginated responses
  if (Array.isArray(data)) {
    return data;
  }

  if (data && typeof data === 'object') {
    if (Array.isArray(data.results)) {
      return data.results;
    }
    if (Array.isArray(data.items)) {
      return data.items;
    }
  }

  // Fallback to empty array if data format is unexpected
  console.warn('Unexpected itineraries data format:', data);
  return [];
};

/**
 * Get itinerary by ID
 */
export const getItinerary = async (itineraryId: string): Promise<Itinerary> => {
  const response = await api.get(`${API_ENDPOINTS.ITINERARY.LIST}/${itineraryId}/`);
  return handleApiResponse(response);
};

/**
 * Create itinerary
 */
export const createItinerary = async (data: {
  title: string;
  destination: string;
  start_date: string;
  end_date: string;
  status?: string;
  description?: string;
  ai_narrative?: string;
  number_of_travelers?: number;
  estimated_budget?: string;
  currency?: string;
}): Promise<Itinerary> => {
  console.log('Creating itinerary with data:', data);
  console.log('POST URL:', `${API_ENDPOINTS.ITINERARY.CREATE}/`);

  const response = await api.post(`${API_ENDPOINTS.ITINERARY.CREATE}/`, data);

  console.log('Create itinerary response:', response);

  const result = handleApiResponse<Itinerary>(response);
  console.log('Create itinerary result:', result);

  return result as Itinerary;
};

/**
 * Update itinerary
 */
export const updateItinerary = async (
  itineraryId: string,
  data: any
): Promise<Itinerary> => {
  const response = await api.put(
    `${API_ENDPOINTS.ITINERARY.UPDATE}/${itineraryId}/`,
    data
  );
  return handleApiResponse(response);
};

/**
 * Delete itinerary
 */
export const deleteItinerary = async (itineraryId: string): Promise<void> => {
  const response = await api.delete(`${API_ENDPOINTS.ITINERARY.DELETE}/${itineraryId}/`);
  return handleApiResponse(response);
};

/**
 * Add activity to itinerary
 */
export const addActivity = async (
  itineraryId: string,
  activity: Omit<Activity, 'id'>
): Promise<Activity> => {
  const response = await api.post(
    `${API_ENDPOINTS.ITINERARY.LIST}/${itineraryId}/activities`,
    activity
  );
  return handleApiResponse(response);
};

/**
 * Update activity
 */
export const updateActivity = async (
  itineraryId: string,
  activityId: string,
  data: Partial<Activity>
): Promise<Activity> => {
  const response = await api.put(
    `${API_ENDPOINTS.ITINERARY.LIST}/${itineraryId}/activities/${activityId}`,
    data
  );
  return handleApiResponse(response);
};

/**
 * Delete activity
 */
export const deleteActivity = async (
  itineraryId: string,
  activityId: string
): Promise<void> => {
  const response = await api.delete(
    `${API_ENDPOINTS.ITINERARY.LIST}/${itineraryId}/activities/${activityId}`
  );
  return handleApiResponse(response);
};

/**
 * Reorder activities
 */
export const reorderActivities = async (
  itineraryId: string,
  activityIds: string[]
): Promise<Itinerary> => {
  const response = await api.post(
    `${API_ENDPOINTS.ITINERARY.LIST}/${itineraryId}/activities/reorder`,
    { activityIds }
  );
  return handleApiResponse(response);
};

/**
 * Add booking to itinerary
 */
export const addBookingToItinerary = async (
  itineraryId: string,
  bookingId: string
): Promise<Itinerary> => {
  const response = await api.post(
    `${API_ENDPOINTS.ITINERARY.LIST}/${itineraryId}/bookings`,
    { bookingId }
  );
  return handleApiResponse(response);
};

/**
 * Remove booking from itinerary
 */
export const removeBookingFromItinerary = async (
  itineraryId: string,
  bookingId: string
): Promise<Itinerary> => {
  const response = await api.delete(
    `${API_ENDPOINTS.ITINERARY.LIST}/${itineraryId}/bookings/${bookingId}`
  );
  return handleApiResponse(response);
};

/**
 * Share itinerary
 */
export const shareItinerary = async (
  itineraryId: string,
  email: string
): Promise<{ shareLink: string }> => {
  const response = await api.post(
    `${API_ENDPOINTS.ITINERARY.LIST}/${itineraryId}/share`,
    { email }
  );
  return handleApiResponse(response);
};

/**
 * Export itinerary as PDF
 */
export const exportItineraryPDF = async (itineraryId: string): Promise<Blob> => {
  const response = await api.get(
    `${API_ENDPOINTS.ITINERARY.LIST}/${itineraryId}/export-pdf/`,
    {
      responseType: 'blob',
    }
  );
  return response.data;
};

// ==================== Day Management ====================

export interface ItineraryDayData {
  id?: number;
  itinerary: number;
  day_number: number;
  date: string;
  title?: string;
  description?: string;
  notes?: string;
  items?: ItineraryItemData[];
}

export interface ItineraryItemData {
  id?: number;
  day: number;
  item_type: 'flight' | 'hotel' | 'restaurant' | 'attraction' | 'activity' | 'transport' | 'note';
  order?: number;
  title: string;
  description?: string;
  start_time?: string;
  end_time?: string;
  duration_minutes?: number;
  location_name?: string;
  location_address?: string;
  estimated_cost?: number;
  notes?: string;
  url?: string;
}

/**
 * Create an itinerary day
 */
export const createItineraryDay = async (data: Omit<ItineraryDayData, 'id' | 'items'>): Promise<ItineraryDayData> => {
  const response = await api.post(`${API_ENDPOINTS.ITINERARY.DAYS}/`, data);
  return handleApiResponse(response);
};

/**
 * Update an itinerary day
 */
export const updateItineraryDay = async (dayId: number, data: Partial<ItineraryDayData>): Promise<ItineraryDayData> => {
  const response = await api.patch(`${API_ENDPOINTS.ITINERARY.DAYS}/${dayId}/`, data);
  return handleApiResponse(response);
};

/**
 * Delete an itinerary day
 */
export const deleteItineraryDay = async (dayId: number): Promise<void> => {
  const response = await api.delete(`${API_ENDPOINTS.ITINERARY.DAYS}/${dayId}/`);
  return handleApiResponse(response);
};

/**
 * Create an itinerary item
 */
export const createItineraryItem = async (data: Omit<ItineraryItemData, 'id'>): Promise<ItineraryItemData> => {
  const response = await api.post(`${API_ENDPOINTS.ITINERARY.ITEMS}/`, data);
  return handleApiResponse(response);
};

/**
 * Update an itinerary item
 */
export const updateItineraryItem = async (itemId: number, data: Partial<ItineraryItemData>): Promise<ItineraryItemData> => {
  const response = await api.patch(`${API_ENDPOINTS.ITINERARY.ITEMS}/${itemId}/`, data);
  return handleApiResponse(response);
};

/**
 * Delete an itinerary item
 */
export const deleteItineraryItem = async (itemId: number): Promise<void> => {
  const response = await api.delete(`${API_ENDPOINTS.ITINERARY.ITEMS}/${itemId}/`);
  return handleApiResponse(response);
};
