import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useGuestOnly } from '@/hooks/useAuth';
import useAuthStore from '@/store/authStore';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import { Card } from '@/components/common';
import { ROUTES } from '@/utils/constants';
import { useToast } from '@/hooks/useNotifications';

/**
 * Extract field-level errors from a DRF validation response.
 * DRF returns errors as { field: ["msg", ...], ... }
 */
function parseFieldErrors(error: any): Record<string, string> {
  const responseData = error?.response?.data;
  if (!responseData || typeof responseData !== 'object') return {};

  const parsed: Record<string, string> = {};
  for (const [field, errors] of Object.entries(responseData)) {
    if (Array.isArray(errors) && errors.length > 0) {
      parsed[field] = errors[0] as string;
    } else if (typeof errors === 'string') {
      parsed[field] = errors;
    }
  }
  return parsed;
}

function extractErrorMessage(error: any): string {
  const fields = parseFieldErrors(error);
  const messages = Object.values(fields);
  if (messages.length > 0) return messages[0];
  return error?.message || 'Registration failed. Please try again.';
}

const RegisterPage = () => {
  useGuestOnly();
  const navigate = useNavigate();
  const { register } = useAuthStore();
  const { showSuccess, showError } = useToast();

  const [first_name, setFirstName] = useState('');
  const [last_name, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFieldErrors({});

    if (password !== confirmPassword) {
      setFieldErrors({ password: 'Passwords do not match' });
      showError('Passwords do not match');
      return;
    }

    setIsLoading(true);

    try {
      await register({
        first_name,
        last_name,
        email,
        password,
        password_confirm: confirmPassword
      });
      showSuccess('Account created! A verification email has been sent to your inbox.');
      // Full page navigation to ensure clean state after auth change
      window.location.href = ROUTES.DASHBOARD;
    } catch (error: any) {
      const errors = parseFieldErrors(error);
      setFieldErrors(errors);
      showError(extractErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-emerald-600 via-teal-700 to-cyan-800 dark:from-emerald-900 dark:via-teal-900 dark:to-cyan-950 py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
      <div className="absolute inset-0 opacity-10">
        <div className="absolute -top-20 -left-20 w-72 h-72 bg-white rounded-full blur-3xl"></div>
        <div className="absolute bottom-10 right-1/4 w-48 h-48 bg-emerald-300 rounded-full blur-3xl"></div>
      </div>
      <Card variant="glass" className="max-w-md w-full relative z-10">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 text-white text-2xl mb-4 shadow-lg shadow-emerald-500/25">🌍</div>
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
            Create your account
          </h2>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            Already have an account?{' '}
            <Link
              to={ROUTES.LOGIN}
              className="font-medium text-primary-600 dark:text-primary-400 hover:underline"
            >
              Sign in
            </Link>
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="First Name"
              type="text"
              value={first_name}
              onChange={(e) => { setFirstName(e.target.value); setFieldErrors((prev) => ({ ...prev, first_name: '' })); }}
              placeholder="John"
              error={fieldErrors.first_name}
              required
            />
            <Input
              label="Last Name"
              type="text"
              value={last_name}
              onChange={(e) => { setLastName(e.target.value); setFieldErrors((prev) => ({ ...prev, last_name: '' })); }}
              placeholder="Doe"
              error={fieldErrors.last_name}
              required
            />
          </div>

          <Input
            label="Email address"
            type="email"
            value={email}
            onChange={(e) => { setEmail(e.target.value); setFieldErrors((prev) => ({ ...prev, email: '' })); }}
            placeholder="you@example.com"
            error={fieldErrors.email}
            required
          />

          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) => { setPassword(e.target.value); setFieldErrors((prev) => ({ ...prev, password: '' })); }}
            placeholder="••••••••"
            error={fieldErrors.password}
            required
          />

          <Input
            label="Confirm Password"
            type="password"
            value={confirmPassword}
            onChange={(e) => { setConfirmPassword(e.target.value); setFieldErrors((prev) => ({ ...prev, password_confirm: '' })); }}
            placeholder="••••••••"
            error={fieldErrors.password_confirm}
            required
          />

          <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-semibold shadow-lg shadow-emerald-500/25 hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Creating account...' : 'Sign up'}
              </button>
        </form>
      </Card>
    </div>
  );
};

export default RegisterPage;
