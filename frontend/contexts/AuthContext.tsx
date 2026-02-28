import React, { createContext, useState, useContext, useEffect } from 'react';
import { apiService } from '@/services/api';

interface User {
  id: number;
  email: string;
  username: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (identifier: string, password: string) => Promise<void>;
  signup: (data: SignupData) => Promise<void>;
  logout: () => void;
  updateProfile: (data: ProfileUpdate) => Promise<void>;
}

interface SignupData {
  email: string;
  username: string;
  password: string;
  confirm_password: string;
  full_name?: string;
}

interface ProfileUpdate {
  full_name?: string;
  phone?: string;
  company?: string;
  designation?: string;
  bio?: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Load user from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');

    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
      // Set token in API service
      apiService.setAuthToken(storedToken);
    }

    setLoading(false);
  }, []);

  const login = async (identifier: string, password: string) => {
    try {
      const response = await apiService.login(identifier, password);

      setToken(response.access_token);
      setUser(response.user);

      // Store in localStorage
      localStorage.setItem('token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));

      // Set token in API service
      apiService.setAuthToken(response.access_token);
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Login failed');
    }
  };

  const signup = async (data: SignupData) => {
    try {
      const response = await apiService.signup(data);

      setToken(response.access_token);
      setUser(response.user);

      // Store in localStorage
      localStorage.setItem('token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));

      // Set token in API service
      apiService.setAuthToken(response.access_token);
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Signup failed');
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);

    // Clear localStorage
    localStorage.removeItem('token');
    localStorage.removeItem('user');

    // Clear token from API service
    apiService.setAuthToken(null);
  };

  const updateProfile = async (data: ProfileUpdate) => {
    try {
      const response = await apiService.updateProfile(data);

      setUser(response);
      localStorage.setItem('user', JSON.stringify(response));
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Profile update failed');
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        signup,
        logout,
        updateProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
