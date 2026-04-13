import api, { handleApiResponse } from './api';
import { API_ENDPOINTS } from '@/utils/constants';
import type { Booking, PaginatedResponse } from '@/types';

/**
 * Get all bookings for current user
 */
export const getBookings = async (
  page: number = 1,
  pageSize: number = 10,
  status?: string
): Promise<PaginatedResponse<Booking>> => {
  let url = `${API_ENDPOINTS.BOOKINGS.LIST}?page=${page}&pageSize=${pageSize}`;
  if (status) {
    url += `&status=${status}`;
  }
  const response = await api.get(url);
  return handleApiResponse(response);
};

/**
 * Get booking details by ID
 */
export const getBookingDetails = async (bookingId: string): Promise<Booking> => {
  const response = await api.get(`${API_ENDPOINTS.BOOKINGS.DETAILS}/${bookingId}/`);
  return handleApiResponse(response);
};

/**
 * Update booking
 */
export const updateBooking = async (
  bookingId: string,
  data: Partial<Booking>
): Promise<Booking> => {
  const response = await api.put(`${API_ENDPOINTS.BOOKINGS.UPDATE}/${bookingId}/`, data);
  return handleApiResponse(response);
};

/**
 * Cancel booking
 */
export const cancelBooking = async (
  bookingId: string,
  reason?: string
): Promise<{ success: boolean; refundAmount?: number }> => {
  const response = await api.post(`${API_ENDPOINTS.BOOKINGS.CANCEL}/${bookingId}/cancel/`, {
    reason,
  });
  return handleApiResponse(response);
};

/**
 * Get booking confirmation PDF
 */
export const getBookingConfirmationPDF = async (bookingId: string): Promise<Blob> => {
  const response = await api.get(
    `${API_ENDPOINTS.BOOKINGS.DETAILS}/${bookingId}/confirmation`,
    {
      responseType: 'blob',
    }
  );
  return response.data;
};

/**
 * Send booking confirmation email
 */
export const sendBookingConfirmationEmail = async (
  bookingId: string
): Promise<void> => {
  const response = await api.post(
    `${API_ENDPOINTS.BOOKINGS.DETAILS}/${bookingId}/send-confirmation`
  );
  return handleApiResponse(response);
};

/**
 * Get booking statistics
 */
export const getBookingStatistics = async (): Promise<{
  totalBookings: number;
  upcomingTrips: number;
  completedTrips: number;
  cancelledBookings: number;
  totalSpent: number;
}> => {
  const response = await api.get(`${API_ENDPOINTS.BOOKINGS.LIST}/statistics`);
  return handleApiResponse(response);
};

/**
 * Request booking modification
 */
export const requestBookingModification = async (
  bookingId: string,
  modifications: {
    type: 'date' | 'passenger' | 'room' | 'other';
    details: string;
  }
): Promise<{ requestId: string }> => {
  const response = await api.post(
    `${API_ENDPOINTS.BOOKINGS.DETAILS}/${bookingId}/modification-request`,
    modifications
  );
  return handleApiResponse(response);
};

/**
 * Add special request to booking
 */
export const addSpecialRequest = async (
  bookingId: string,
  request: string
): Promise<Booking> => {
  const response = await api.post(
    `${API_ENDPOINTS.BOOKINGS.DETAILS}/${bookingId}/special-request`,
    { request }
  );
  return handleApiResponse(response);
};

/**
 * Get cancellation policy
 */
export const getCancellationPolicy = async (
  bookingId: string
): Promise<{
  canCancel: boolean;
  refundAmount: number;
  deadline: string;
  penalty: number;
}> => {
  const response = await api.get(
    `${API_ENDPOINTS.BOOKINGS.DETAILS}/${bookingId}/cancellation-policy`
  );
  return handleApiResponse(response);
};
