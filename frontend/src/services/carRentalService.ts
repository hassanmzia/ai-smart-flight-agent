import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://108.48.39.238:3090';

export interface CarRental {
  id?: number;
  rental_company: string;
  car_type: string;
  vehicle: string;
  price_per_day: number;
  total_price: number;
  currency: string;
  pickup_location: string;
  rating: number;
  reviews: number;
  features: string[];
  phone?: string;
  website?: string;
  thumbnail?: string;
  rental_days: number;
  pickup_date: string;
  dropoff_date: string;
  mileage: string;
  deposit: number;
  insurance_available: boolean;
  utility_score?: number;
  price_utility_score?: number;
  type_utility_score?: number;
  rating_utility_score?: number;
  combined_utility_score?: number;
  recommendation?: string;
}

export interface CarRentalSearchParams {
  pickup_location: string;
  pickup_date: string;
  dropoff_date: string;
  car_type?: string;
}

export interface CarRentalSearchResponse {
  success: boolean;
  cars: CarRental[];
  search_parameters?: {
    pickup_location: string;
    pickup_date: string;
    dropoff_date: string;
  };
  error?: string;
}

class CarRentalService {
  private getAuthHeader() {
    const token = localStorage.getItem('access_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  async searchCarRentals(params: CarRentalSearchParams): Promise<CarRentalSearchResponse> {
    try {
      const response = await axios.get(`${API_URL}/api/car-rentals/search/`, {
        params: {
          pickup_city: params.pickup_location,
          pickup_date: params.pickup_date,
          return_date: params.dropoff_date,
          car_type: params.car_type,
        },
        headers: this.getAuthHeader(),
      });

      return {
        success: true,
        cars: response.data.results || response.data.cars || [],
        search_parameters: params,
      };
    } catch (error: any) {
      console.error('Error searching car rentals:', error);
      return {
        success: false,
        cars: [],
        error: error.response?.data?.message || error.message || 'Failed to search car rentals',
      };
    }
  }

  async getCarRental(id: number): Promise<CarRental | null> {
    try {
      const response = await axios.get(`${API_URL}/api/car-rentals/${id}/`, {
        headers: this.getAuthHeader(),
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching car rental:', error);
      return null;
    }
  }

  async getCarTypes(): Promise<any[]> {
    try {
      const response = await axios.get(`${API_URL}/api/car-types/`, {
        headers: this.getAuthHeader(),
      });
      return response.data.results || response.data || [];
    } catch (error) {
      console.error('Error fetching car types:', error);
      return [];
    }
  }

  async createRentalBooking(bookingData: any): Promise<any> {
    try {
      const response = await axios.post(
        `${API_URL}/api/rental-bookings/`,
        bookingData,
        { headers: this.getAuthHeader() }
      );
      return response.data;
    } catch (error: any) {
      console.error('Error creating rental booking:', error);
      throw new Error(error.response?.data?.message || 'Failed to create booking');
    }
  }

  async getRentalBookings(): Promise<any[]> {
    try {
      const response = await axios.get(`${API_URL}/api/rental-bookings/`, {
        headers: this.getAuthHeader(),
      });
      return response.data.results || response.data || [];
    } catch (error) {
      console.error('Error fetching rental bookings:', error);
      return [];
    }
  }

  async cancelRentalBooking(bookingId: number): Promise<boolean> {
    try {
      await axios.post(
        `${API_URL}/api/rental-bookings/${bookingId}/cancel/`,
        {},
        { headers: this.getAuthHeader() }
      );
      return true;
    } catch (error) {
      console.error('Error cancelling rental booking:', error);
      return false;
    }
  }
}

export default new CarRentalService();
