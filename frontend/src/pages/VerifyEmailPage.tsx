import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { AuthLayout } from '../layouts/AuthLayout';
import { authApi } from '../api/auth';
import { CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';

export const VerifyEmailPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [success, setSuccess] = useState<boolean>(false);
  const [message, setMessage] = useState<string>('');

  useEffect(() => {
    let isMounted = true;

    const verify = async () => {
      if (!token) {
        setIsLoading(false);
        setSuccess(false);
        setMessage('Verification token is missing from the link.');
        return;
      }

      try {
        const response = await authApi.verifyEmail({ token });
        if (isMounted) {
          setSuccess(true);
          setMessage(response.message);
        }
      } catch (err: unknown) {
        if (isMounted) {
          setSuccess(false);
          const msg = err instanceof Error ? err.message : 'Verification failed.';
          setMessage(msg);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    verify();

    return () => {
      isMounted = false;
    };
  }, [token]);

  return (
    <AuthLayout
      title="Email Verification"
      subtitle="Confirming your DayFlow account email address"
    >
      <div className="text-center py-4 space-y-6">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-8 text-slate-400">
            <Loader2 className="w-10 h-10 text-emerald-400 animate-spin mb-4" />
            <span className="text-sm">Verifying your token with DayFlow...</span>
          </div>
        ) : success ? (
          <div className="space-y-4">
            <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-8 h-8" />
            </div>
            <h3 className="text-xl font-bold text-white">Email Verified!</h3>
            <p className="text-sm text-slate-300">{message}</p>
            <div className="pt-4">
              <Link
                to="/login"
                className="inline-block w-full py-2.5 px-4 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-medium text-sm transition shadow-lg shadow-emerald-500/20"
              >
                Continue to Sign In
              </Link>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="w-14 h-14 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center mx-auto">
              <AlertCircle className="w-8 h-8" />
            </div>
            <h3 className="text-xl font-bold text-white">Verification Failed</h3>
            <p className="text-sm text-rose-300">{message}</p>
            <div className="pt-4 space-y-3">
              <Link
                to="/login"
                className="inline-block w-full py-2.5 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium text-sm transition"
              >
                Back to Sign In
              </Link>
            </div>
          </div>
        )}
      </div>
    </AuthLayout>
  );
};

