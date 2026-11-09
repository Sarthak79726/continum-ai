import React, { createContext, useContext, useState, useEffect } from 'react';
import { User } from '../types';
import { authApi } from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string, role?: string) => Promise<void>;
  loginDemo: () => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('continuum_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('continuum_token');
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const checkAuth = async () => {
      const storedToken = localStorage.getItem('continuum_token');
      if (storedToken) {
        try {
          const profile = await authApi.getCurrentUser();
          setUser(profile);
          localStorage.setItem('continuum_user', JSON.stringify(profile));
        } catch (err) {
          localStorage.removeItem('continuum_token');
          localStorage.removeItem('continuum_user');
          setUser(null);
          setToken(null);
        }
      }
      setIsLoading(false);
    };
    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    const res = await authApi.login({ email, password });
    localStorage.setItem('continuum_token', res.access_token);
    localStorage.setItem('continuum_user', JSON.stringify(res.user));
    setToken(res.access_token);
    setUser(res.user);
  };

  const register = async (name: string, email: string, password: string, role?: string) => {
    const res = await authApi.register({ name, email, password, role });
    localStorage.setItem('continuum_token', res.access_token);
    localStorage.setItem('continuum_user', JSON.stringify(res.user));
    setToken(res.access_token);
    setUser(res.user);
  };

  const loginDemo = async () => {
    await login('demo@continuum.ai', 'password123');
  };

  const logout = () => {
    localStorage.removeItem('continuum_token');
    localStorage.removeItem('continuum_user');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token,
        isLoading,
        login,
        register,
        loginDemo,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

