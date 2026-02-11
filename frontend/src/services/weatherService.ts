import axios from 'axios';
import { API_BASE_URL } from '../utils/constants';

export interface WeatherForecast {
  date: string;
  day_of_week: string;
  temp_min: number;
  temp_max: number;
  temp_avg: number;
  condition: string;
  description: string;
  humidity: number;
  wind_speed: number;
  precipitation_mm: number;
  precipitation_chance: number;
  icon: string;
  uv_index: number;
}

export interface WeatherLocation {
  city: string;
  country: string;
  latitude: number;
  longitude: number;
}

export interface WeatherData {
  success: boolean;
  location: WeatherLocation;
  start_date: string;
  end_date: string;
  forecasts: WeatherForecast[];
  total_days: number;
  note?: string;
  error?: string;
}

export interface WeatherSearchParams {
  city: string;
  start_date?: string;
  end_date?: string;
}

class WeatherService {
  private apiUrl = `${API_BASE_URL}/api/weather`;

  async getWeatherForecast(params: WeatherSearchParams): Promise<WeatherData> {
    try {
      const response = await axios.get(`${this.apiUrl}/forecast/`, {
        params: {
          city: params.city,
          start_date: params.start_date,
          end_date: params.end_date,
        },
      });

      return response.data;
    } catch (error: any) {
      console.error('Error fetching weather forecast:', error);
      throw new Error(error.response?.data?.error || error.message || 'Failed to fetch weather forecast');
    }
  }
}

const weatherService = new WeatherService();
export default weatherService;
