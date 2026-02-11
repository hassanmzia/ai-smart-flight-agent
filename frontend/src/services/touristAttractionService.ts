import axios from 'axios';
import { API_BASE_URL } from '../utils/constants';

export interface TouristAttraction {
  name: string;
  description: string;
  category: string;
  address: string;
  city: string;
  rating: number;
  review_count: number;
  price_level: string;
  hours: string;
  phone: string;
  website: string;
  latitude?: number;
  longitude?: number;
  thumbnail: string;
  primary_image: string;
  type: string;
  place_id: string;
}

export interface AttractionSearchParams {
  city: string;
  category?: string;
}

export interface AttractionSearchResponse {
  success: boolean;
  results: TouristAttraction[];
  total: number;
  error?: string;
}

class TouristAttractionService {
  private apiUrl = `${API_BASE_URL}/api/tourist-attractions`;

  async searchAttractions(params: AttractionSearchParams): Promise<AttractionSearchResponse> {
    try {
      const response = await axios.get(`${this.apiUrl}/search/`, {
        params: {
          city: params.city,
          category: params.category,
        },
      });

      return {
        success: true,
        results: response.data.results || [],
        total: response.data.total || 0,
      };
    } catch (error: any) {
      console.error('Error searching tourist attractions:', error);
      return {
        success: false,
        results: [],
        total: 0,
        error: error.response?.data?.error || error.message || 'Failed to search attractions',
      };
    }
  }
}

const touristAttractionService = new TouristAttractionService();
export default touristAttractionService;
