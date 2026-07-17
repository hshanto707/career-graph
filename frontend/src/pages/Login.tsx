import { useEffect, useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { GraduationCap, ArrowRight, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/hooks/useAuth';
import { ApiError, NetworkError } from '@/lib/apiClient';

const loginSchema = z.object({
  email: z
    .string()
    .trim()
    .min(1, 'Email is required.')
    .email('Enter a valid email address.'),
  password: z
    .string()
    .trim()
    .min(1, 'Password is required.'),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function Login() {
  const navigate = useNavigate();
  const { login, isAuthenticated } = useAuth();
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  });

  // Already-authenticated user navigating to "/" goes straight to the
  // dashboard instead of seeing the login form again.
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const onSubmit = async (values: LoginFormValues) => {
    if (isSubmitting) return; // guards against double-submit races
    setSubmitError(null);
    setIsSubmitting(true);
    try {
      await login({ email: values.email, password: values.password });
      navigate('/dashboard');
    } catch (err) {
      if (err instanceof NetworkError) {
        setSubmitError("Couldn't reach the server. Please check your connection and try again.");
      } else if (err instanceof ApiError) {
        setSubmitError(err.message || 'Invalid email or password.');
      } else {
        setSubmitError('Something went wrong. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col lg:flex-row">
      {/* Left panel - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-primary p-8 xl:p-12 flex-col justify-between">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary-foreground/10 rounded-lg">
              <GraduationCap className="h-6 w-6 xl:h-8 xl:w-8 text-primary-foreground" />
            </div>
            <span className="text-lg xl:text-xl font-bold text-primary-foreground">
              Career Intelligence
            </span>
          </div>
        </div>

        <div className="space-y-4 xl:space-y-6">
          <h1 className="text-2xl xl:text-4xl font-bold text-primary-foreground leading-tight">
            Agentic Labor Market<br />Intelligence Platform
          </h1>
          <p className="text-base xl:text-lg text-primary-foreground/80 max-w-md">
            Data-driven career guidance using live labor market intelligence
          </p>
          <div className="flex gap-6 xl:gap-8 pt-4 xl:pt-6">
            <div>
              <p className="text-2xl xl:text-3xl font-bold text-primary-foreground">10K+</p>
              <p className="text-xs xl:text-sm text-primary-foreground/70">Job Listings</p>
            </div>
            <div>
              <p className="text-2xl xl:text-3xl font-bold text-primary-foreground">500+</p>
              <p className="text-xs xl:text-sm text-primary-foreground/70">Skills Tracked</p>
            </div>
            <div>
              <p className="text-2xl xl:text-3xl font-bold text-primary-foreground">95%</p>
              <p className="text-xs xl:text-sm text-primary-foreground/70">Match Accuracy</p>
            </div>
          </div>
        </div>

        <p className="text-xs xl:text-sm text-primary-foreground/60">
          University Career Development Program
        </p>
      </div>

      {/* Right panel - Login */}
      <div className="flex-1 flex items-center justify-center p-6 md:p-8">
        <div className="w-full max-w-md space-y-6 md:space-y-8">
          {/* Mobile header */}
          <div className="lg:hidden mb-6 md:mb-8 text-center">
            <div className="flex items-center justify-center gap-3 mb-4">
              <div className="p-2 bg-primary rounded-lg">
                <GraduationCap className="h-5 w-5 md:h-6 md:w-6 text-primary-foreground" />
              </div>
              <span className="text-base md:text-lg font-bold text-foreground">
                Career Intelligence
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              Labor Market Intelligence Platform
            </p>
          </div>

          <div className="space-y-2 text-center lg:text-left">
            <h2 className="text-xl md:text-2xl font-bold text-foreground">Welcome back</h2>
            <p className="text-sm md:text-base text-muted-foreground">
              Sign in to access your personalized career dashboard
            </p>
          </div>

          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)} noValidate>
            {submitError && (
              <div
                role="alert"
                className="rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive"
              >
                {submitError}
              </div>
            )}

            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium text-foreground">
                University Email
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="student@university.edu"
                aria-invalid={Boolean(errors.email)}
                className="w-full px-3 md:px-4 py-2.5 md:py-3 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring text-sm md:text-base"
                {...register('email')}
              />
              {errors.email && (
                <p className="text-xs text-destructive">{errors.email.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium text-foreground">
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                placeholder="••••••••"
                aria-invalid={Boolean(errors.password)}
                className="w-full px-3 md:px-4 py-2.5 md:py-3 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring text-sm md:text-base"
                {...register('password')}
              />
              {errors.password && (
                <p className="text-xs text-destructive">{errors.password.message}</p>
              )}
            </div>

            <Button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-5 md:py-6 text-sm md:text-base font-medium"
            >
              {isSubmitting ? (
                <>
                  Signing in...
                  <Loader2 className="ml-2 h-4 w-4 md:h-5 md:w-5 animate-spin" />
                </>
              ) : (
                <>
                  Sign In
                  <ArrowRight className="ml-2 h-4 w-4 md:h-5 md:w-5" />
                </>
              )}
            </Button>
          </form>

          <p className="text-center text-xs md:text-sm text-muted-foreground">
            Use your registered university email and password to sign in.
          </p>
        </div>
      </div>
    </div>
  );
}
