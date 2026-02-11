import axios from 'axios';
import { API_BASE_URL } from '../utils/constants';

export interface ShoppingVenue {
  name: string;
  category: string;
  icon: string;
  description: string;
  location: string;
  address: string;
  price_level: string;
  store_count: number;
  opening_hours: string;
  features: string[];
  popular_for: string[];
  payment_methods: string[];
  rating: number;
  review_count: number;
  busy_hours: string;
  distance_from_center: number;
}

export interface ShoppingSearchParams {
  city: string;
  category?: string;
  start_date?: string;
  end_date?: string;
}

export interface ShoppingResponse {
  success: boolean;
  results: ShoppingVenue[];
  total: number;
  location: string;
  error?: string;
}

class ShoppingService {
  private apiUrl = `${API_BASE_URL}/api/shopping`;

  async searchShopping(params: ShoppingSearchParams): Promise<ShoppingResponse> {
    try {
      const response = await axios.get(`${this.apiUrl}/search/`, {
        params: {
          city: params.city,
          category: params.category,
          start_date: params.start_date,
          end_date: params.end_date,
        },
      });

      return response.data;
    } catch (error: any) {
      console.error('Error searching shopping venues:', error);
      throw new Error(error.response?.data?.error || error.message || 'Failed to search shopping venues');
    }
  }
}

const shoppingService = new ShoppingService();
export default shoppingService;
