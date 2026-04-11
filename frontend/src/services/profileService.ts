import api from './api';

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
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone_number?: string;
  is_active: boolean;
  is_verified: boolean;
  date_joined: string;
  last_login?: string;
  profile: UserProfile;
  created_at: string;
  updated_at: string;
}

export interface UpdateUserData {
  first_name?: string;
  last_name?: string;
  phone_number?: string;
}

export interface UpdateProfileData {
  date_of_birth?: string;
  nationality?: string;
  passport_number?: string;
  passport_expiry?: string;
  preferred_currency?: string;
  preferred_language?: string;
  preferred_travel_class?: string;
  preferred_airlines?: string[];
  preferred_hotel_chains?: string[];
  seat_preference?: string;
  dietary_restrictions?: string[];
  accessibility_needs?: string;
  email_notifications?: boolean;
  sms_notifications?: boolean;
  push_notifications?: boolean;
  avatar?: string;
  bio?: string;
}

export interface ChangePasswordData {
  old_password: string;
  new_password: string;
  new_password_confirm: string;
}

class ProfileService {
  async getCurrentUser(): Promise<User> {
    const response = await api.get('/api/users/me/');
    return response.data;
  }

  async updateUser(data: UpdateUserData): Promise<User> {
    const response = await api.patch('/api/users/me/', data);
    return response.data;
  }

  async getCurrentUserProfile(): Promise<UserProfile> {
    const response = await api.get('/api/users/profiles/me/');
    return response.data;
  }

  async updateProfile(data: UpdateProfileData): Promise<UserProfile> {
    const response = await api.patch('/api/users/profiles/me/', data);
    return response.data;
  }

  async changePassword(data: ChangePasswordData): Promise<{ message: string }> {
    const response = await api.post('/api/users/change_password/', data);
    return response.data;
  }

  async uploadAvatar(file: File): Promise<{ avatar_url: string }> {
    const formData = new FormData();
    formData.append('avatar', file);

    const response = await api.post('/api/users/profiles/upload_avatar/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }
}

export default new ProfileService();
