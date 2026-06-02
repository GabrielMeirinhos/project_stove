import React, { useState } from 'react';
import { Apple, ArrowRight, Eye, EyeOff, Leaf, LockKeyhole, MoonStar, SunMedium, User } from 'lucide-react';
import { cn } from '../../lib/utils';
import loginGreenhouse from '../../assents/login-greenhouse.png';

type AppLanguage = 'pt-BR' | 'en-US';
type ThemeMode = 'light' | 'dark';

interface LoginScreenProps {
  language: AppLanguage;
  theme: ThemeMode;
  onToggleTheme: () => void;
  onLogin: (credentials: { email: string; password: string; rememberMe: boolean }) => Promise<void>;
}

const copy = {
  'pt-BR': {
    brand: 'Gaia',
    subtitle: 'Monitore sua planta com calma e precisão.',
    welcome: 'Bem vindo',
    email: 'Usuário',
    password: 'Senha',
    rememberMe: 'Manter acesso neste dispositivo',
    forgot: 'Esqueceu a senha?',
    submit: 'Entrar',
    continueWith: 'Ou continue com',
    google: 'Google',
    apple: 'Apple',
    signupQuestion: 'Novo na plataforma?',
    signupAction: 'Crie uma conta',
    imageCardTitle: 'Vitalidade da planta',
    imageCardText:
      'Acompanhe luz, agua, temperatura e saude da planta em uma interface serena e focada.',
    pulseLabel: 'Monitoramento ao vivo ativo',
    demoHint: '',
  },
  'en-US': {
    brand: 'Gaia',
    subtitle: 'Monitor your real plant with calm and precision.',
    welcome: 'Welcome',
    email: 'Username',
    password: 'Password',
    rememberMe: 'Keep me signed in on this device',
    forgot: 'Forgot Password?',
    submit: 'Sign in',
    continueWith: 'Or continue with',
    google: 'Google',
    apple: 'Apple',
    signupQuestion: 'New to the platform?',
    signupAction: 'Create an account',
    imageCardTitle: 'Plant vitality',
    imageCardText:
      'Track light, water, temperature, and plant health in a calm, focused interface.',
    pulseLabel: 'Live monitoring active',
    demoHint: '',
  },
} as const;

export function LoginScreen({ language, theme, onToggleTheme, onLogin }: LoginScreenProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);
  const isEnglish = language === 'en-US';
  const content = copy[language];

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoginError(null);
    setIsSubmitting(true);
    try {
      await onLogin({ email: email.trim(), password, rememberMe });
    } catch (error) {
      const fallback = isEnglish ? 'Invalid email or password.' : 'Email ou senha inválidos.';
      setLoginError(error instanceof Error ? error.message || fallback : fallback);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="relative h-screen min-h-screen overflow-hidden bg-[#f8faf8] text-[#22302a] dark:bg-[#0b0f0e] dark:text-[#d6e0d8]">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_10%,rgba(73,102,75,0.14),transparent_36%),radial-gradient(circle_at_82%_84%,rgba(202,235,201,0.18),transparent_34%)]" />

      <div className="relative grid h-screen min-h-screen grid-rows-[38svh_1fr] lg:grid-cols-[1.12fr_0.88fr] lg:grid-rows-1">
        <section className="relative overflow-hidden bg-[#d9e1dc]">
          <img
            src={loginGreenhouse}
            alt={isEnglish ? 'Botanical greenhouse' : 'Estufa botanica'}
            className="absolute inset-0 h-full w-full object-cover object-center"
          />
          <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(7,16,11,0.04),rgba(7,16,11,0.22)),radial-gradient(circle_at_50%_10%,rgba(255,255,255,0.16),transparent_30%)]" />

          <div className="relative flex h-full flex-col justify-between p-4 sm:p-6 lg:p-8 xl:p-10">
            <div className="inline-flex w-fit items-center gap-2 rounded-full bg-[rgba(248,250,248,0.34)] px-3 py-2 text-[11px] font-semibold tracking-[0.05rem] text-[#f5fff3] backdrop-blur-xl">
              <Leaf size={14} />
              Gaia
            </div>

            <div className="max-w-[520px] rounded-[24px] bg-[rgba(248,250,248,0.78)] p-4 text-[#26352d] backdrop-blur-2xl sm:p-5 lg:p-6">
              <p className="font-display text-xl font-semibold tracking-tight sm:text-2xl xl:text-[2.1rem]">{content.imageCardTitle}</p>
              <p className="mt-3 text-sm leading-6 text-[#3a4a43] xl:text-[0.95rem]">{content.imageCardText}</p>
              <p className="mt-4 text-[11px] font-semibold uppercase tracking-[0.08rem] text-[#4d5d56]">{content.pulseLabel}</p>
            </div>
          </div>
        </section>

        <section className="relative flex h-full items-center justify-center overflow-hidden px-5 py-5 sm:px-8 lg:px-10">
            <button
              onClick={onToggleTheme}
            className="absolute right-5 top-5 flex h-10 w-10 items-center justify-center rounded-full bg-[rgba(255,255,255,0.65)] text-[#3c4e45] backdrop-blur-lg transition hover:bg-[rgba(255,255,255,0.95)] hover:text-[#233229]"
              aria-label={theme === 'dark' ? (isEnglish ? 'Enable light mode' : 'Ativar modo claro') : (isEnglish ? 'Enable dark mode' : 'Ativar modo escuro')}
              title={theme === 'dark' ? (isEnglish ? 'Enable light mode' : 'Ativar modo claro') : (isEnglish ? 'Enable dark mode' : 'Ativar modo escuro')}
            >
              {theme === 'dark' ? <SunMedium size={18} /> : <MoonStar size={18} />}
            </button>

          <div className="w-full max-w-[430px] rounded-[28px] bg-[rgba(248,250,248,0.78)] p-5 shadow-[0_24px_70px_rgba(45,52,50,0.08)] backdrop-blur-2xl sm:p-7 lg:rounded-[32px] lg:p-8">
            <div className="mb-8 text-center lg:text-left">
              <p className="text-[11px] font-semibold uppercase tracking-[0.05rem] text-[#627066]">{content.brand}</p>
              <h1 className="mt-2 font-display text-[2.2rem] font-semibold tracking-tight text-[#27332a] dark:text-[#fffff]">{content.welcome}</h1>
              <p className="mt-2 text-sm leading-6 text-[#607168] dark:text-[#59615f]">{content.subtitle}</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <label className="block">
                <span className="mb-2.5 block text-[11px] font-semibold uppercase tracking-[0.05rem] text-[#59615f]">
                  {content.email}
                </span>
                <div className="group relative">
                  <User size={16} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[#7d8884]" />
                  <input
                    type="text"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    className="h-[3.1rem] w-full rounded-full bg-[#dde4e1] pl-11 pr-4 text-sm text-[#1f2f27] outline-none transition-all placeholder:text-[#9aa59f] focus:bg-[#ffffff] focus:shadow-[0_12px_24px_rgba(45,52,50,0.08)]"
                    placeholder={isEnglish ? 'username' : 'nome_de_usuario'}
                    autoComplete="username"
                  />
                  <div className="pointer-events-none absolute inset-0 rounded-full bg-[linear-gradient(15deg,rgba(73,102,75,0.08),rgba(202,235,201,0.03))] opacity-0 transition-opacity group-focus-within:opacity-100" />
                </div>
              </label>

              <label className="block">
                <div className="mb-2.5 flex items-center justify-between gap-3">
                  <span className="text-[11px] font-semibold uppercase tracking-[0.05rem] text-[#59615f]">{content.password}</span>
                  <a href="#" onClick={(event) => event.preventDefault()} className="text-[11px] font-semibold text-[#5a7260] transition hover:text-[#3a5241]">
                    {content.forgot}
                  </a>
                </div>
                <div className="group relative">
                  <LockKeyhole size={16} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[#7d8884]" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    className="h-[3.1rem] w-full rounded-full bg-[#dde4e1] pl-11 pr-12 text-sm text-[#1f2f27] outline-none transition-all placeholder:text-[#9aa59f] focus:bg-[#ffffff] focus:shadow-[0_12px_24px_rgba(45,52,50,0.08)]"
                    placeholder="********"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((current) => !current)}
                    className={cn(
                      'absolute right-2 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full text-[#77857f] transition hover:bg-[rgba(255,255,255,0.8)] hover:text-[#364740]',
                    )}
                    aria-label={showPassword ? (isEnglish ? 'Hide password' : 'Ocultar senha') : (isEnglish ? 'Show password' : 'Mostrar senha')}
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                  <div className="pointer-events-none absolute inset-0 rounded-full bg-[linear-gradient(15deg,rgba(73,102,75,0.08),rgba(202,235,201,0.03))] opacity-0 transition-opacity group-focus-within:opacity-100" />
                </div>
              </label>

              <label className="inline-flex items-center gap-2 text-sm text-[#4e5f57]">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(event) => setRememberMe(event.target.checked)}
                  className="h-4 w-4 rounded-sm accent-[#49664b]"
                />
                {content.rememberMe}
              </label>

              <button
                type="submit"
                disabled={isSubmitting}
                className="group flex h-[3.1rem] w-full items-center justify-center gap-2 rounded-full bg-[linear-gradient(15deg,#49664b,#5f7b60)] px-5 text-sm font-semibold text-[#e9ffe6] shadow-[0_18px_30px_rgba(45,52,50,0.16)] transition-all hover:brightness-110 focus:outline-none focus:ring-4 focus:ring-[#49664b]/20"
              >
                {isSubmitting ? (isEnglish ? 'Signing in...' : 'Entrando...') : content.submit}
                <ArrowRight size={17} className="transition-transform group-hover:translate-x-0.5" />
              </button>
            </form>

            {loginError && (
              <div className="mt-4 rounded-xl bg-red-100/90 px-4 py-2 text-sm font-medium text-red-700">
                {loginError}
              </div>
            )}

            <p className="mt-5 text-center text-[11px] font-semibold uppercase tracking-[0.08rem] text-[#829189]">
              {content.continueWith}
            </p>

            <div className="mt-3 grid grid-cols-2 gap-3">
              <button
                type="button"
                className="h-10 rounded-full bg-[rgba(255,255,255,0.65)] px-3 text-sm font-semibold text-[#425449] backdrop-blur-lg transition hover:bg-[rgba(255,255,255,0.92)]"
              >
                {content.google}
              </button>
              <button
                type="button"
                className="inline-flex h-10 items-center justify-center gap-2 rounded-full bg-[rgba(255,255,255,0.65)] px-3 text-sm font-semibold text-[#425449] backdrop-blur-lg transition hover:bg-[rgba(255,255,255,0.92)]"
              >
                <Apple size={15} />
                {content.apple}
              </button>
            </div>

            <div className="mt-5 text-center text-sm text-[#5f6f67]">
              <span>{content.signupQuestion} </span>
              <button type="button" className="font-semibold text-[#3d5544] transition hover:text-[#2b3f31]">
                {content.signupAction}
              </button>
            </div>

            <div> 
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}