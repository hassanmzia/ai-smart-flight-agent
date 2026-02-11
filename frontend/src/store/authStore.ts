import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import * as authService from '@/services/authService';
import { storage } from '@/utils/helpers';
import { STORAGE_KEYS } from '@/utils/constants';
import type { AuthState, User, LoginCredentials, RegisterData, AuthTokens } from '@/types';

const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      (set, get) => ({
        user: storage.get<User>(STORAGE_KEYS.USER_DATA),
        tokens: {
          accessToken: storage.get<string>(STORAGE_KEYS.AUTH_TOKEN) || '',
          refreshToken: storage.get<string>(STORAGE_KEYS.REFRESH_TOKEN) || '',
        },
        isAuthenticated: !!storage.get<string>(STORAGE_KEYS.AUTH_TOKEN),
        isLoading: false,
        error: null,

        login: async (credentials: LoginCredentials) => {
          set({ isLoading: true, error: null });
          try {
            const { user, tokens } = await authService.login(credentials);

            // Store tokens and user data
            storage.set(STORAGE_KEYS.AUTH_TOKEN, tokens.accessToken);
            storage.set(STORAGE_KEYS.REFRESH_TOKEN, tokens.refreshToken);
            storage.set(STORAGE_KEYS.USER_DATA, user);

            set({
              user,
              tokens,
              isAuthenticated: true,
              isLoading: false,
              error: null,
            });
          } catch (error: any) {
            set({
              error: error.message || 'Login failed',
              isLoading: false,
            });
            throw error;
          }
        },

        register: async (data: RegisterData) => {
          set({ isLoading: true, error: null });
          try {
            const { user, tokens } = await authService.register(data);

            // Store tokens and user data
            storage.set(STORAGE_KEYS.AUTH_TOKEN, tokens.accessToken);
            storage.set(STORAGE_KEYS.REFRESH_TOKEN, tokens.refreshToken);
            storage.set(STORAGE_KEYS.USER_DATA, user);

            set({
              user,
              tokens,
              isAuthenticated: true,
              isLoading: false,
              error: null,
            });
          } catch (error: any) {
            set({
              error: error.message || 'Registration failed',
              isLoading: false,
            });
            throw error;
          }
        },

        logout: () => {
          // Clear storage
          storage.remove(STORAGE_KEYS.AUTH_TOKEN);
          storage.remove(STORAGE_KEYS.REFRESH_TOKEN);
          storage.remove(STORAGE_KEYS.USER_DATA);

          // Reset state
          set({
            user: null,
            tokens: null,
            isAuthenticated: false,
            error: null,
          });

          // Call logout endpoint (fire and forget)
          authService.logout().catch(console.error);
        },

        refreshToken: async () => {
          const { tokens } = get();
          if (!tokens?.refreshToken) {
            throw new Error('No refresh token available');
          }

          try {
            const newTokens = await authService.refreshToken(tokens.refreshToken);

            storage.set(STORAGE_KEYS.AUTH_TOKEN, newTokens.accessToken);
            storage.set(STORAGE_KEYS.REFRESH_TOKEN, newTokens.refreshToken);

            set({ tokens: newTokens });
          } catch (error: any) {
            // If refresh fails, logout user
            get().logout();
            throw error;
          }
        },

        updateUser: async (data: Partial<User>) => {
          set({ isLoading: true, error: null });
          try {
            const updatedUser = await authService.updateProfile(data);

            storage.set(STORAGE_KEYS.USER_DATA, updatedUser);

            set({
              user: updatedUser,
              isLoading: false,
              error: null,
            });
          } catch (error: any) {
            set({
              error: error.message || 'Update failed',
              isLoading: false,
            });
            throw error;
          }
        },

        refreshUser: async () => {
          try {
            const user = await authService.getCurrentUser();
            storage.set(STORAGE_KEYS.USER_DATA, user);
            set({ user });
          } catch (error: any) {
            console.error('Failed to refresh user:', error);
            throw error;
          }
        },
      }),
      {
        name: 'auth-storage',
        partialize: (state) => ({
          user: state.user,
          isAuthenticated: state.isAuthenticated,
        }),
      }
    ),
    { name: 'AuthStore' }
  )
);

export default useAuthStore;
