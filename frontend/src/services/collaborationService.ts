import api, { handleApiResponse } from './api';
import { API_ENDPOINTS } from '@/utils/constants';

const BASE = API_ENDPOINTS.ITINERARY.LIST; // "/api/itineraries/itineraries"

export interface SharedTrip {
  id: number | string;
  title: string;
  destination: string;
  start_date: string;
  end_date: string;
  status: string;
  status_display?: string;
  is_shared: boolean;
  shared_with: string[];
  number_of_travelers?: number;
  estimated_budget?: string;
  currency?: string;
  user?: number | string;
}

const unwrap = <T,>(d: any): T[] => {
  if (!d) return [];
  if (Array.isArray(d)) return d as T[];
  if (Array.isArray(d.results)) return d.results as T[];
  if (Array.isArray(d.items)) return d.items as T[];
  return [];
};

/**
 * List the current user's own trips that they have shared with collaborators.
 */
export const getMyShared = async (): Promise<SharedTrip[]> => {
  const res = await api.get(`${BASE}/my-shared/`);
  return unwrap<SharedTrip>(handleApiResponse(res));
};

/**
 * List trips where the current user has been invited as a collaborator
 * (i.e. their email is in shared_with but they are not the owner).
 */
export const getSharedWithMe = async (): Promise<SharedTrip[]> => {
  const res = await api.get(`${BASE}/shared-with-me/`);
  return unwrap<SharedTrip>(handleApiResponse(res));
};

/**
 * Invite one or more emails to collaborate on a trip.
 */
export const inviteCollaborators = async (
  itineraryId: string | number,
  emails: string[],
): Promise<{
  added: string[];
  already_invited: string[];
  shared_with: string[];
}> => {
  const res = await api.post(`${BASE}/${itineraryId}/invite/`, { emails });
  return handleApiResponse(res);
};

/**
 * Remove a collaborator from a shared trip (owner-only).
 */
export const removeCollaborator = async (
  itineraryId: string | number,
  email: string,
): Promise<{ shared_with: string[] }> => {
  const res = await api.post(`${BASE}/${itineraryId}/remove-collaborator/`, {
    email,
  });
  return handleApiResponse(res);
};

/**
 * Generate (or fetch) a signed invite link for a trip.
 */
export const getInviteLink = async (
  itineraryId: string | number,
): Promise<{ code: string; url: string }> => {
  const res = await api.get(`${BASE}/${itineraryId}/invite-link/`);
  return handleApiResponse(res);
};

/**
 * Join a shared trip using an invite code.
 */
export const joinByCode = async (
  code: string,
): Promise<{ message: string; itinerary: SharedTrip }> => {
  const res = await api.post(`${BASE}/join-by-code/`, { code });
  return handleApiResponse(res);
};

/**
 * Create a new trip that is immediately marked as shared.
 *
 * The backend's normal create endpoint accepts ``is_shared`` and ``shared_with``,
 * so we just call it with those flags pre-set.
 */
export const createSharedTrip = async (data: {
  title: string;
  destination: string;
  start_date: string;
  end_date: string;
  description?: string;
  invite_emails?: string[];
}): Promise<SharedTrip> => {
  const payload: any = {
    title: data.title,
    destination: data.destination,
    start_date: data.start_date,
    end_date: data.end_date,
    description: data.description || '',
    status: 'planned',
    is_shared: true,
    shared_with: (data.invite_emails || [])
      .map((e) => e.trim().toLowerCase())
      .filter((e) => e && e.includes('@')),
  };
  const res = await api.post(`${BASE}/`, payload);
  return handleApiResponse(res);
};
