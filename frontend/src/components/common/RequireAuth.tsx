import { Navigate, useLocation } from 'react-router-dom';
import useAuthStore from '@/store/authStore';
import { ROUTES } from '@/utils/constants';

interface RequireAuthProps {
  children: React.ReactNode;
}

const RequireAuth = ({ children }: RequireAuthProps) => {
  const { isAuthenticated } = useAuthStore();
  const location = useLocation();

  if (!isAuthenticated) {
    return (
      <Navigate
        to={ROUTES.LOGIN}
        replace
        state={{ from: location.pathname, message: 'Please log in to continue' }}
      />
    );
  }

  return <>{children}</>;
};

export default RequireAuth;
