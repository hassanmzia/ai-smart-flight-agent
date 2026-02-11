import axios from 'axios';
import authService from './authService';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8109';

export interface Restaurant {
  id: string;
  name: string;
  cuisine_type: string;
  city: string;
  address: string;
  rating: number;
  review_count: number;
  price_level: number;
  price_range: string;
  average_cost_per_person: number;
  currency: string;
  phone?: string;
  website?: string;
  thumbnail?: string;
  primary_image?: string;
  has_delivery?: boolean;
  has_takeout?: boolean;
  has_reservation?: boolean;
  hours?: string;
  utility_score?: number;
  rating_utility_score?: number;
  price_utility_score?: number;
  combined_utility_score?: number;
  recommendation?: string;
}

export interface RestaurantSearchParams {
  city: string;
  cuisine?: string;
  price_level?: number;
}

export interface RestaurantSearchResponse {
  success: boolean;
  restaurants: Restaurant[];
  error?: string;
  search_parameters?: RestaurantSearchParams;
}

class RestaurantService {
  private getAuthHeader() {
    const token = authService.getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  async searchRestaurants(params: RestaurantSearchParams): Promise<RestaurantSearchResponse> {
    try {
      const response = await axios.get(`${API_URL}/api/restaurants/search/`, {
        params: {
          city: params.city,
          cuisine: params.cuisine,
          price_level: params.price_level,
        },
        headers: this.getAuthHeader(),
      });

      return {
        success: true,
        restaurants: response.data.results || response.data.restaurants || [],
        search_parameters: params,
      };
    } catch (error: any) {
      console.error('Error searching restaurants:', error);
      return {
        success: false,
        restaurants: [],
        error: error.response?.data?.message || error.message || 'Failed to search restaurants',
      };
    }
  }

  async getRestaurantById(id: string): Promise<Restaurant | null> {
    try {
      const response = await axios.get(`${API_URL}/api/restaurants/restaurants/${id}/`, {
        headers: this.getAuthHeader(),
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching restaurant:', error);
      return null;
    }
  }

  async getFeaturedRestaurants(): Promise<Restaurant[]> {
    try {
      const response = await axios.get(`${API_URL}/api/restaurants/restaurants/featured/`, {
        headers: this.getAuthHeader(),
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching featured restaurants:', error);
      return [];
    }
  }
}

export default new RestaurantService();
