// components/Layout.tsx (updated with Auth)
import React, { useState } from 'react';
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
    { label: 'Dashboard', href: '/' },
    { label: 'Active IPOs', href: '/active' },
    { label: 'Upcoming', href: '/upcoming' },
    { label: 'All IPOs', href: '/ipos' },
  ];

  const handleAuthClick = (view: 'login' | 'signup') => {
    setAuthModalView(view);
    setAuthModalOpen(true);
  };

  return (
    <>
      <Head>
        <title>{title}</title>
        <meta name="description" content={description} />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" type="image/png" href="/logo.png" />
      </Head>

      <div className="min-h-screen flex flex-col bg-navy-50">
        {/* Header */}
        <header className="bg-navy-900 shadow-nav sticky top-0 z-40">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              {/* Logo */}
              <Link href="/" className="flex items-center space-x-2">
                <Image
                  src="/logo.png"
                  alt="NexIPO Logo"
                  width={36}
                  height={36}
                  className="rounded-lg"
                  priority
                />
                <span className="text-xl font-bold text-white">
                  Nex<span className="text-primary-400">IPO</span>
                </span>
              </Link>

              {/* Desktop Navigation */}
              <nav className="hidden md:flex space-x-1">
                {navItems.map((item) => {
                  const isActive = router.pathname === item.href;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${isActive
                        ? 'text-white bg-primary-600'
                        : 'text-navy-300 hover:text-white hover:bg-navy-800'
                        }`}
                    >
                      {item.label}
                    </Link>
                  );
                })}
              </nav>

              {/* Auth Buttons */}
              <div className="hidden md:flex items-center space-x-3">
                {user ? (
                  <div className="flex items-center space-x-3">
                    <Link href="/profile">
                      <button className="flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-navy-800 transition-colors">
                        <div className="w-8 h-8 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center">
                          <span className="text-white font-bold text-sm">{user.username[0].toUpperCase()}</span>
                        </div>
                        <span className="text-sm font-medium text-navy-200">
                          {user.username}
                        </span>
                      </button>
                    </Link>
                  </div>
                ) : (
                  <>
                    <button
                      onClick={() => handleAuthClick('login')}
                      className="px-4 py-2 text-sm font-medium text-navy-300 hover:text-white transition-colors"
                    >
                      Sign In
                    </button>
                    <button
                      onClick={() => handleAuthClick('signup')}
                      className="px-4 py-2 rounded-lg text-sm font-medium bg-primary-500 text-white hover:bg-primary-600 transition-colors"
                    >
                      Sign Up
                    </button>
                  </>
                )}
              </div>

              {/* Mobile menu button */}
              <div className="md:hidden">
                <button
                  onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                  className="text-navy-300 hover:text-white"
                >
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    {mobileMenuOpen ? (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    ) : (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                    )}
                  </svg>
                </button>
              </div>
            </div>

            {/* Mobile Menu */}
            {mobileMenuOpen && (
              <div className="md:hidden py-4 border-t border-navy-700">
                <div className="space-y-1">
                  {navItems.map((item) => (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className="block px-3 py-2 rounded-lg text-base font-medium text-navy-200 hover:text-white hover:bg-navy-800"
                    >
                      {item.label}
                    </Link>
                  ))}

                  <div className="pt-4 border-t border-navy-700 space-y-1">
                    {user ? (
                      <>
                        <Link
                          href="/profile"
                          onClick={() => setMobileMenuOpen(false)}
                          className="block px-3 py-2 rounded-lg text-base font-medium text-navy-200 hover:text-white hover:bg-navy-800"
                        >
                          Profile
                        </Link>
                      </>
                    ) : (
                      <>
                        <button
                          onClick={() => {
                            handleAuthClick('login');
                            setMobileMenuOpen(false);
                          }}
                          className="block w-full text-left px-3 py-2 rounded-lg text-base font-medium text-navy-200 hover:text-white hover:bg-navy-800"
                        >
                          Sign In
                        </button>
                        <button
                          onClick={() => {
                            handleAuthClick('signup');
                            setMobileMenuOpen(false);
                          }}
                          className="block w-full mt-2 px-4 py-2 rounded-lg text-base font-medium bg-primary-500 text-white hover:bg-primary-600"
                        >
                          Sign Up
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1">
          {children}
        </main>

        {/* Footer */}
        <footer className="bg-navy-900 mt-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
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
            <div className="mt-8 pt-8 border-t border-navy-700">
              <div className="flex items-center justify-center space-x-2">
                <Image
                  src="/logo.png"
                  alt="NexIPO Logo"
                  width={24}
                  height={24}
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
