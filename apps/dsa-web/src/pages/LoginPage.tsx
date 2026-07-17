import type React from 'react';
import { useEffect, useState } from 'react';
import { motion, useReducedMotion } from "motion/react";
import { Lock, Loader2, ShieldCheck, Sparkles } from "lucide-react";
import { Button, Input } from '../components/common';
import { UiLanguageToggle } from '../components/i18n/UiLanguageToggle';
import { useNavigate, useSearchParams } from 'react-router-dom';
import type { ParsedApiError } from '../api/error';
import { isParsedApiError } from '../api/error';
import { useAuth } from '../hooks';
import { useUiLanguage } from '../contexts/UiLanguageContext';
import { SettingsAlert } from '../components/settings';
import { APP_BRAND } from '../config/brand';
import { BrandMark } from '../components/brand/BrandMark';

const LoginPage: React.FC = () => {
  const { login, passwordSet, setupState } = useAuth();
  const { t } = useUiLanguage();
  const navigate = useNavigate();

  // Set page title
  useEffect(() => {
    document.title = t('login.pageTitle');
  }, [t]);
  const [searchParams] = useSearchParams();
  const rawRedirect = searchParams.get('redirect') ?? '';
  const redirect =
    rawRedirect.startsWith('/') && !rawRedirect.startsWith('//') ? rawRedirect : '/';

  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | ParsedApiError | null>(null);

  const isFirstTime = setupState === 'no_password' || !passwordSet;
  const prefersReducedMotion = useReducedMotion();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (isFirstTime && password !== passwordConfirm) {
      setError(t('login.passwordMismatch'));
      return;
    }
    setIsSubmitting(true);
    try {
      const result = await login(password, isFirstTime ? passwordConfirm : undefined);
      if (result.success) {
        navigate(redirect, { replace: true });
      } else {
        setError(result.error ?? t('login.loginFailed'));
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      data-brand-theme="ruyi-tech-blue"
      className="ruyi-login relative flex min-h-screen flex-col justify-center overflow-hidden py-12 font-sans selection:bg-[var(--login-accent-soft)] sm:px-6 lg:px-8"
    >
      <div data-testid="ruyi-login-backdrop" className="ruyi-login-backdrop" aria-hidden="true" />

      <div className="absolute right-4 top-4 z-30">
        <UiLanguageToggle />
      </div>

      <div className="relative z-10 mx-auto w-full max-w-md px-4 sm:px-0 lg:ml-[54%] lg:mr-auto">
        <motion.div
          initial={prefersReducedMotion ? false : { opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="relative mb-10 flex flex-col items-center justify-center"
        >
          <BrandMark
            variant="lockup"
            className="mt-8 h-auto w-[min(86vw,26rem)] drop-shadow-[0_18px_36px_hsl(214_100%_8%_/_0.22)]"
          />

          <motion.div 
            initial={prefersReducedMotion ? false : { opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="mt-6 flex items-center gap-2 rounded-full border border-[var(--login-accent-border)] bg-[var(--login-accent-soft)] px-3 py-1 text-[10px] font-medium text-[var(--login-accent-text)] backdrop-blur-sm"
          >
            <Sparkles className="h-3 w-3" />
            <span>V3.X QUANTITATIVE SYSTEM</span>
          </motion.div>
        </motion.div>

        <motion.div
          initial={prefersReducedMotion ? false : { opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="group pointer-events-auto relative z-20"
        >
          <div className="ruyi-login-card pointer-events-auto relative flex flex-col overflow-hidden p-8">
            <div className="mb-8">
              <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight text-[var(--login-text-primary)]">
                {isFirstTime ? (
                  <>
                    <ShieldCheck className="h-6 w-6 text-emerald-400" />
                    <span>{t('login.setupTitle')}</span>
                  </>
                ) : (
                  <>
                    <Lock className="h-5 w-5 text-[var(--login-accent-text)]" />
                    <span>{t('login.adminLogin')}</span>
                  </>
                )}
              </h1>
              <p className="mt-2 text-sm text-[var(--login-text-secondary)]">
                {isFirstTime
                  ? t('login.setupDescription')
                  : t('login.loginDescription')}
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-4">
                <Input
                  id="password"
                  type="password"
                  appearance="login"
                  allowTogglePassword
                  iconType="password"
                  label={isFirstTime ? t('login.adminPassword') : t('login.loginPassword')}
                  placeholder={isFirstTime ? t('login.setupPasswordPlaceholder') : t('login.loginPasswordPlaceholder')}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isSubmitting}
                  autoFocus
                  autoComplete={isFirstTime ? 'new-password' : 'current-password'}
                />

                {isFirstTime && (
                  <Input
                    id="passwordConfirm"
                    type="password"
                    appearance="login"
                    allowTogglePassword
                    iconType="password"
                    label={t('login.confirmPassword')}
                    placeholder={t('login.confirmPasswordPlaceholder')}
                    value={passwordConfirm}
                    onChange={(e) => setPasswordConfirm(e.target.value)}
                    disabled={isSubmitting}
                    autoComplete="new-password"
                  />
                )}
              </div>

              {error && (
                <motion.div
                  initial={prefersReducedMotion ? false : { opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="overflow-hidden"
                >
                  <SettingsAlert
                    title={isFirstTime ? t('login.setupFailed') : t('login.validationFailed')}
                    message={isParsedApiError(error) ? error.message : error}
                    variant="error"
                    className="!border-[var(--login-error-border)] !bg-[var(--login-error-bg)] !text-[var(--login-error-text)]"
                  />
                </motion.div>
              )}

              <Button
                type="submit"
                variant="primary"
                size="lg"
                className="group/btn relative h-12 w-full overflow-hidden rounded-xl border-0 bg-gradient-to-r from-[var(--login-brand-button-start)] to-[var(--login-brand-button-end)] font-medium text-[var(--login-button-text)] shadow-lg shadow-[0_18px_36px_hsl(214_100%_8%_/_0.24)] hover:from-[var(--login-brand-button-start-hover)] hover:to-[var(--login-brand-button-end-hover)]"
                disabled={isSubmitting}
              >
                <div className="relative z-10 flex items-center justify-center gap-2">
                  {isSubmitting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>{isFirstTime ? t('login.setupSubmitting') : t('login.loginSubmitting')}</span>
                    </>
                  ) : (
                    <span>{isFirstTime ? t('login.setupSubmit') : t('login.loginSubmit')}</span>
                  )}
                </div>
                <div className="ruyi-shimmer pointer-events-none absolute inset-0 z-0 -translate-x-full bg-gradient-to-r from-transparent via-white/10 to-transparent group-hover:animate-[ruyi-shimmer_1.5s_infinite] motion-reduce:animate-none" />
              </Button>
            </form>
          </div>
        </motion.div>

        {/* Footer info */}
        <motion.p 
          initial={prefersReducedMotion ? false : { opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="mt-8 text-center text-xs font-medium tracking-wide text-[var(--login-text-muted)]"
        >
          {APP_BRAND.chineseName} · 作者 {APP_BRAND.author}
        </motion.p>
      </div>
    </div>
  );
};

export default LoginPage;
