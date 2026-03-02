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
        <footer className="bg-navy-900 mt-auto" role="contentinfo">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-10">
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6 sm:gap-8">
              <div>
                <h3 className="text-sm font-semibold text-white mb-3">About</h3>
                <p className="text-sm text-navy-300 leading-relaxed">
                  ML-powered platform for IPO analysis and risk assessment. Built for placements and final year projects.
                </p>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white mb-3">Quick Links</h3>
                <ul className="space-y-2">
                  {navItems.map((item) => (
                    <li key={item.href}>
                      <Link href={item.href} className="text-sm text-navy-300 hover:text-primary-400 transition-colors">
                        {item.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white mb-3">Technology</h3>
                <p className="text-sm text-navy-300">
                  Next.js • TypeScript • FastAPI • PostgreSQL • Machine Learning
                </p>
              </div>
            </div>
            <div className="mt-8 pt-6 border-t border-navy-700">
              <div className="flex flex-col sm:flex-row items-center justify-center gap-2">
                <Image
                  src="/logo.png"
                  alt="NexIPO Logo"
                  width={20}
                  height={20}
                  className="rounded"
                />
                <p className="text-sm text-navy-400">
                  © {new Date().getFullYear()} NexIPO. Built for educational purposes.
                </p>
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
