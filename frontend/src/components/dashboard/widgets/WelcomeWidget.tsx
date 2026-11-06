import React, { useState } from 'react';
import { useAuth } from '../../../hooks/useAuth';
import { WidgetContainer } from '../WidgetContainer';
import { WidgetProps } from '../../../types/dashboard';
import {
  User as UserIcon,
  Mail,
  ShieldCheck,
  ShieldAlert,
  Sparkles,
} from 'lucide-react';

export const WelcomeWidget: React.FC<WidgetProps> = ({ widgetConfig }) => {
  const { user, resendVerification } = useAuth();
  const [resendStatus, setResendStatus] = useState<string | null>(null);
  const [isResending, setIsResending] = useState<boolean>(false);

  const handleResend = async () => {
    if (!user?.email) return;
    setIsResending(true);
    setResendStatus(null);
    try {
      const msg = await resendVerification(user.email);
      setResendStatus(msg);
    } catch {
      setResendStatus('Failed to send verification link.');
    } finally {
      setIsResending(false);
    }
  };

  return (
    <WidgetContainer
      title={`Welcome back, ${user?.display_name || 'Member'}!`}
      description="Personal command center overview"
      size={widgetConfig.size}
      headerAction={
        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
          <Sparkles className="w-3 h-3" />
          <span>Active Session</span>
        </div>
      }
    >
      <div className="space-y-4">
        {/* Unverified Email Warning Banner */}
        {user && !user.is_verified && (
          <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-start gap-2.5">
              <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <div className="font-semibold text-xs text-white">Email unverified</div>
                <div className="text-xs text-amber-300/80">
                  Verify your email to secure your account.
                </div>
                {resendStatus && (
                  <div className="text-xs text-emerald-400 font-medium mt-1">{resendStatus}</div>
                )}
              </div>
            </div>
            <button
              onClick={handleResend}
              disabled={isResending}
              className="px-3 py-1 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 border border-amber-500/40 text-xs font-medium transition shrink-0 disabled:opacity-50"
            >
              {isResending ? 'Sending...' : 'Resend Verification'}
            </button>
          </div>
        )}

        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-slate-950/40 border border-slate-800/80">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 shrink-0">
              <UserIcon className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <div className="text-sm font-bold text-white truncate">{user?.display_name}</div>
              <div className="flex items-center gap-1.5 text-xs text-slate-400 truncate">
                <Mail className="w-3 h-3" />
                <span className="truncate">{user?.email}</span>
              </div>
            </div>
          </div>

          <div>
            {user?.is_verified ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
                <ShieldCheck className="w-3.5 h-3.5" />
                Verified
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs font-medium">
                <ShieldAlert className="w-3.5 h-3.5" />
                Unverified
              </span>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
            <div className="text-slate-400 text-[11px] mb-0.5">User Identifier</div>
            <div className="font-mono text-slate-300 truncate select-all">{user?.id}</div>
          </div>

          <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
            <div className="text-slate-400 text-[11px] mb-0.5">Member Since</div>
            <div className="text-slate-300">
              {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
            </div>
          </div>
        </div>
      </div>
    </WidgetContainer>
  );
};

