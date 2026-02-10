import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '@/store/authStore';
import { ROUTES } from '@/utils/constants';

/**
 * Hook to access auth state and actions
 */
export const useAuth = () => {
  const authStore = useAuthStore();

  return {
    user: authStore.user,
    isAuthenticated: authStore.isAuthenticated,
    isLoading: authStore.isLoading,
    error: authStore.error,
    login: authStore.login,
    register: authStore.register,
    logout: authStore.logout,
    updateUser: authStore.updateUser,
  };
};

/**
 * Hook to require authentication - redirects to login if not authenticated
 */
export const useRequireAuth = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      // Show a message to the user (you can use toast here if available)
      const currentPath = window.location.pathname;
      navigate(ROUTES.LOGIN, {
        replace: true,
        state: { from: currentPath, message: 'Please log in to continue' }
      });
    }
  }, [isAuthenticated, isLoading, navigate]);

  return { user, isAuthenticated, isLoading };
};

/**
 * Hook to require admin role
 */
export const useRequireAdmin = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        navigate(ROUTES.LOGIN, { replace: true });
      } else if (user?.role !== 'admin') {
        navigate(ROUTES.HOME, { replace: true });
      }
    }
  }, [user, isAuthenticated, isLoading, navigate]);

  return { user, isAuthenticated, isLoading };
};

/**
 * Hook to redirect if already authenticated
 */
export const useGuestOnly = () => {
  const navigate = useNavigate();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      navigate(ROUTES.DASHBOARD, { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate]);

  return { isLoading };
};
