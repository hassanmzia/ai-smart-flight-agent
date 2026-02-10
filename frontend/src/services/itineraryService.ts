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
  description?: string;
  number_of_travelers?: number;
  estimated_budget?: string;
  currency?: string;
}): Promise<Itinerary> => {
  const response = await api.post(`${API_ENDPOINTS.ITINERARY.CREATE}/`, data);
  return handleApiResponse(response);
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
    `${API_ENDPOINTS.ITINERARY.LIST}/${itineraryId}/export`,
    {
      responseType: 'blob',
    }
  );
  return response.data;
};
