// components/Layout.tsx
import React, { useState, useEffect, useCallback } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/router';
import { useAuth } from '@/contexts/AuthContext';
import AuthModal from './AuthModal';

interface LayoutProps {
  children: React.ReactNode;
  title?: string;
  description?: string;
}

const Layout: React.FC<LayoutProps> = ({
  children,
  title = 'NexIPO',
  description = 'ML-Powered IPO Analysis and Risk Assessment'
}) => {
  const router = useRouter();
  const { user, logout } = useAuth();
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authModalView, setAuthModalView] = useState<'login' | 'signup'>('login');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    {
      label: 'Dashboard', href: '/', icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" /></svg>
      )
    },
    {
      label: 'Active IPOs', href: '/active', icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
      )
    },
    {
      label: 'Upcoming', href: '/upcoming', icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
      )
    },
    {
      label: 'All IPOs', href: '/ipos', icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" /></svg>
      )
    },
  ];

  const handleAuthClick = (view: 'login' | 'signup') => {
    setAuthModalView(view);
    setAuthModalOpen(true);
  };

  // Close mobile menu on route change
  useEffect(() => {
    const handleRouteChange = () => setMobileMenuOpen(false);
    router.events.on('routeChangeStart', handleRouteChange);
    return () => router.events.off('routeChangeStart', handleRouteChange);
  }, [router.events]);

  // Lock body scroll when mobile menu is open
  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [mobileMenuOpen]);

  return (
    <>
      <Head>
        <title>{title}</title>
        <meta name="description" content={description} />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" type="image/png" href="/logo.png" />
      </Head>

      <div className="min-h-screen flex flex-col bg-navy-50">
        {/* ─── Header ─── */}
        <header className="bg-navy-900 shadow-nav sticky top-0 z-40" role="banner">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-14 sm:h-16">
              {/* Logo */}
              <Link href="/" className="flex items-center space-x-2 flex-shrink-0" aria-label="NexIPO Home">
                <Image
                  src="/logo.png"
                  alt="NexIPO Logo"
                  width={32}
                  height={32}
                  className="rounded-lg"
                  priority
                />
                <span className="text-lg sm:text-xl font-bold text-white">
                  Nex<span className="text-primary-400">IPO</span>
                </span>
              </Link>

              {/* Desktop Navigation */}
              <nav className="hidden md:flex items-center space-x-1" aria-label="Main navigation">
                {navItems.map((item) => {
                  const isActive = router.pathname === item.href;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`flex items-center gap-1.5 px-3 lg:px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${isActive
                        ? 'text-white bg-primary-600'
                        : 'text-navy-300 hover:text-white hover:bg-navy-800'
                        }`}
                      aria-current={isActive ? 'page' : undefined}
                    >
                      {item.icon}
                      <span>{item.label}</span>
                    </Link>
                  );
                })}
              </nav>

              {/* Auth Buttons (Desktop) */}
              <div className="hidden md:flex items-center space-x-2 lg:space-x-3">
                {user ? (
                  <Link href="/profile">
                    <button className="flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-navy-800 transition-colors" aria-label="View profile">
                      <div className="w-8 h-8 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center">
                        <span className="text-white font-bold text-sm">{user.username[0].toUpperCase()}</span>
                      </div>
                      <span className="text-sm font-medium text-navy-200 hidden lg:inline">
                        {user.username}
                      </span>
                    </button>
                  </Link>
                ) : (
                  <>
                    <button
                      onClick={() => handleAuthClick('login')}
                      className="px-3 lg:px-4 py-2 text-sm font-medium text-navy-300 hover:text-white transition-colors rounded-lg"
                    >
                      Sign In
                    </button>
                    <button
                      onClick={() => handleAuthClick('signup')}
                      className="px-3 lg:px-4 py-2 rounded-lg text-sm font-medium bg-primary-500 text-white hover:bg-primary-600 transition-colors active:scale-[0.98]"
                    >
                      Sign Up
                    </button>
                  </>
                )}
              </div>

              {/* Mobile menu button */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="md:hidden p-2 rounded-lg text-navy-300 hover:text-white hover:bg-navy-800 transition-colors"
                aria-expanded={mobileMenuOpen}
                aria-controls="mobile-menu"
                aria-label={mobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  {mobileMenuOpen ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  )}
                </svg>
              </button>
            </div>
          </div>

          {/* ─── Mobile Menu (slide-down overlay) ─── */}
          {mobileMenuOpen && (
            <>
              {/* Backdrop */}
              <div
                className="fixed inset-0 bg-black/40 z-40 md:hidden animate-fade-in"
                onClick={() => setMobileMenuOpen(false)}
                aria-hidden="true"
              />
              {/* Menu Panel */}
              <div
                id="mobile-menu"
                className="absolute top-full left-0 right-0 bg-navy-900 border-t border-navy-700 z-50 md:hidden animate-slide-down shadow-modal"
                role="navigation"
                aria-label="Mobile navigation"
              >
                <div className="max-w-7xl mx-auto px-4 py-4 space-y-1">
                  {navItems.map((item) => {
                    const isActive = router.pathname === item.href;
                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        onClick={() => setMobileMenuOpen(false)}
                        className={`flex items-center gap-3 px-4 py-3 rounded-lg text-base font-medium transition-colors ${isActive
                            ? 'text-white bg-primary-600'
                            : 'text-navy-200 hover:text-white hover:bg-navy-800'
                          }`}
                        aria-current={isActive ? 'page' : undefined}
                      >
                        {item.icon}
                        {item.label}
                      </Link>
                    );
                  })}

                  <div className="pt-4 mt-3 border-t border-navy-700 space-y-2">
                    {user ? (
                      <Link
                        href="/profile"
                        onClick={() => setMobileMenuOpen(false)}
                        className="flex items-center gap-3 px-4 py-3 rounded-lg text-base font-medium text-navy-200 hover:text-white hover:bg-navy-800"
                      >
                        <div className="w-8 h-8 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center">
                          <span className="text-white font-bold text-sm">{user.username[0].toUpperCase()}</span>
                        </div>
                        Profile
                      </Link>
                    ) : (
                      <>
                        <button
                          onClick={() => {
                            handleAuthClick('login');
                            setMobileMenuOpen(false);
                          }}
                          className="flex items-center w-full px-4 py-3 rounded-lg text-base font-medium text-navy-200 hover:text-white hover:bg-navy-800"
                        >
                          Sign In
                        </button>
                        <button
                          onClick={() => {
                            handleAuthClick('signup');
                            setMobileMenuOpen(false);
                          }}
                          className="w-full px-4 py-3 rounded-lg text-base font-medium bg-primary-500 text-white hover:bg-primary-600 text-center"
                        >
                          Sign Up
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </>
          )}
        </header>

        {/* ─── Main Content ─── */}
        <main className="flex-1" role="main">
          {children}
        </main>

        {/* ─── Footer ─── */}
        <footer className="bg-navy-950 border-t border-navy-800 py-12" role="contentinfo">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-8">
              <div className="max-w-sm">
                <Link href="/" className="flex items-center space-x-2 mb-4">
                  <Image
                    src="/logo.png"
                    alt="NexIPO Logo"
                    width={28}
                    height={28}
                    className="rounded-lg"
                  />
                  <span className="text-2xl font-black text-white tracking-tighter">
                    Nex<span className="text-primary-400">IPO</span>
                  </span>
                </Link>
                <p className="text-sm text-navy-400 leading-relaxed">
                  Advanced ML-powered platform for retail IPO intelligence and deep-dive risk assessment.
                </p>
              </div>

              <div className="flex flex-wrap gap-x-12 gap-y-6">
                <div>
                  <h3 className="text-xs font-bold text-navy-500 uppercase tracking-[0.2em] mb-4">Explore</h3>
                  <ul className="grid grid-cols-2 gap-x-8 gap-y-2">
                    {navItems.map((item) => (
                      <li key={item.href}>
                        <Link href={item.href} className="text-sm text-navy-300 hover:text-white transition-colors">
                          {item.label}
                        </Link>
                      </li>
                    ))}
                  </ul>
                </div>
                
                <div className="hidden sm:block w-px h-16 bg-navy-800 self-center"></div>

                <div className="max-w-[240px]">
                  <h3 className="text-xs font-bold text-navy-500 uppercase tracking-[0.2em] mb-4">Project Note</h3>
                  <p className="text-[11px] text-navy-500 leading-tight italic">
                    Academic Research Initiative v1.0 • Built for institutional-grade volatility forecasting and NLP analysis.
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-12 pt-8 border-t border-navy-900 flex flex-col sm:flex-row justify-between items-center gap-4">
              <p className="text-xs text-navy-600 font-medium tracking-wide">
                © {new Date().getFullYear()} NexIPO Intelligence. All rights reserved.
              </p>
              <div className="flex items-center gap-6">
                <span className="px-2 py-0.5 rounded bg-primary-950/20 text-[10px] font-bold text-primary-500/80 border border-primary-500/10">STABLE v3.1</span>
              </div>
            </div>
          </div>
        </footer>
      </div>

      {/* Auth Modal */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        defaultView={authModalView}
      />
    </>
  );
};

export default Layout;
