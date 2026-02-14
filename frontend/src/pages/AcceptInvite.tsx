/**
 * Accept Team Invitation Page
 * Create account from invitation link
 */

import React, { useState, useEffect } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { UserPlus, ArrowLeft, Loader2, CheckCircle, AlertCircle, Eye, EyeOff, Building2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { api } from '../services/api';

export default function AcceptInvite() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isValidating, setIsValidating] = useState(true);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState('');
  const [validationError, setValidationError] = useState('');
  const [inviteData, setInviteData] = useState<{
    email: string;
    org_name: string;
    role: string;
    inviter_name: string;
  } | null>(null);

  useEffect(() => {
    if (!token) {
      setValidationError('Invalid or missing invitation token');
      setIsValidating(false);
      return;
    }

    // Validate token
    const validateToken = async () => {
      try {
        const response = await api.get(`/team/invitations/validate/${token}`);
        if (response.data.valid) {
          setInviteData({
            email: response.data.email,
            org_name: response.data.org_name,
            role: response.data.role,
            inviter_name: response.data.inviter_name
          });
        } else {
          setValidationError(response.data.error || 'Invalid or expired invitation');
        }
      } catch (err: any) {
        setValidationError('Invalid or expired invitation link');
      } finally {
        setIsValidating(false);
      }
    };

    validateToken();
  }, [token]);

  const validatePassword = (pass: string): string | null => {
    if (pass.length < 8) return 'Password must be at least 8 characters';
    if (!/[A-Z]/.test(pass)) return 'Password must contain at least one uppercase letter';
    if (!/[a-z]/.test(pass)) return 'Password must contain at least one lowercase letter';
    if (!/[0-9]/.test(pass)) return 'Password must contain at least one number';
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (name.length < 2) {
      setError('Name must be at least 2 characters');
      return;
    }

    const passwordError = validatePassword(password);
    if (passwordError) {
      setError(passwordError);
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setIsLoading(true);

    try {
      const response = await api.post('/team/invitations/accept', {
        token,
        name,
        password
      });
      
      // Store auth token
      localStorage.setItem('mercura_token', response.data.token);
      setIsSuccess(true);
      
      // Redirect to dashboard after 2 seconds
      setTimeout(() => {
        navigate('/today');
      }, 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create account. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const roleDisplay: Record<string, string> = {
    viewer: 'Viewer',
    sales_rep: 'Sales Rep',
    manager: 'Manager',
    admin: 'Admin'
  };

  if (isValidating) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-orange-600 mx-auto mb-4" />
          <p className="text-slate-600">Validating your invitation...</p>
        </div>
      </div>
    );
  }

  if (validationError) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
        <div className="max-w-md w-full">
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 text-center">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <AlertCircle className="w-8 h-8 text-red-600" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900 mb-4">
              Invalid Invitation
            </h1>
            <p className="text-slate-600 mb-6">
              {validationError}
            </p>
            <Link
              to="/"
              className="inline-flex items-center justify-center px-6 py-2.5 bg-slate-900 text-white rounded-lg font-medium hover:bg-slate-800 transition-colors"
            >
              Go Home
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (isSuccess) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
        <div className="max-w-md w-full">
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900 mb-4">
              Welcome to Mercura!
            </h1>
            <p className="text-slate-600 mb-6">
              Your account has been created successfully. You're now part of <strong>{inviteData?.org_name}</strong>.
            </p>
            <Link
              to="/today"
              className="inline-flex items-center justify-center px-6 py-2.5 bg-slate-900 text-white rounded-lg font-medium hover:bg-slate-800 transition-colors"
            >
              Go to Dashboard
            </Link>
            <p className="text-sm text-slate-500 mt-4">
              Redirecting in 2 seconds...
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2">
            <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-red-600 rounded-xl flex items-center justify-center">
              <span className="text-white font-bold text-lg">M</span>
            </div>
            <span className="text-xl font-bold text-slate-900">Mercura</span>
          </Link>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8">
          <div className="text-center mb-6">
            <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <UserPlus className="w-6 h-6 text-orange-600" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900 mb-2">
              Join Your Team
            </h1>
            <div className="flex items-center justify-center gap-2 text-slate-600 mb-4">
              <Building2 className="w-4 h-4" />
              <span>{inviteData?.org_name}</span>
            </div>
            <p className="text-sm text-slate-500">
              You've been invited by <strong>{inviteData?.inviter_name}</strong> as a{' '}
              <strong>{inviteData?.role ? roleDisplay[inviteData.role] : 'team member'}</strong>
            </p>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Email
              </label>
              <Input
                type="email"
                value={inviteData?.email || ''}
                disabled
                className="h-11 bg-slate-50"
              />
              <p className="text-xs text-slate-500 mt-1">Email cannot be changed</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Full Name
              </label>
              <Input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="John Doe"
                required
                className="h-11"
                autoComplete="name"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Password
              </label>
              <div className="relative">
                <Input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="h-11 pr-10"
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <div className="mt-2 text-xs text-slate-500 space-y-1">
                <p className={password.length >= 8 ? 'text-green-600' : ''}>
                  ✓ At least 8 characters
                </p>
                <p className={/[A-Z]/.test(password) ? 'text-green-600' : ''}>
                  ✓ One uppercase letter
                </p>
                <p className={/[a-z]/.test(password) ? 'text-green-600' : ''}>
                  ✓ One lowercase letter
                </p>
                <p className={/[0-9]/.test(password) ? 'text-green-600' : ''}>
                  ✓ One number
                </p>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Confirm Password
              </label>
              <Input
                type={showPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="h-11"
                autoComplete="new-password"
              />
            </div>

            <Button
              type="submit"
              disabled={isLoading || !name || !password || !confirmPassword}
              className="w-full h-11 bg-slate-900 hover:bg-slate-800"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creating Account...
                </>
              ) : (
                'Accept Invitation'
              )}
            </Button>
          </form>

          <div className="mt-6 pt-6 border-t border-slate-100 text-center">
            <p className="text-sm text-slate-600">
              Already have an account?{' '}
              <Link to="/login" className="text-orange-600 hover:text-orange-700 font-medium">
                Sign In
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
