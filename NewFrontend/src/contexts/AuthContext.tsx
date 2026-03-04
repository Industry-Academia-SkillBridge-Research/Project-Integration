import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface User {
  id: number;
  email: string;
  name: string;
  picture?: string;
  provider: string;
  is_active: boolean;
  created_at: string;
  last_login: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: () => void;
  logout: () => void;
  checkAuth: () => Promise<void>;
  getAuthHeader: () => { Authorization: string } | {};
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const isAuthenticated = !!user;

  // Get token from localStorage
  const getToken = () => localStorage.getItem('access_token');

  // Set token to localStorage
  const setToken = (token: string) => localStorage.setItem('access_token', token);

  // Remove token from localStorage
  const removeToken = () => localStorage.removeItem('access_token');

  // Check authentication status by calling /auth/me
  const checkAuth = async () => {
    const token = getToken();
    
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${API_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        // Token is invalid or expired
        removeToken();
        setUser(null);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      removeToken();
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  // Initialize auth state on mount
  useEffect(() => {
    checkAuth();
  }, []);

  // Login - redirect to backend Google OAuth
  const login = () => {
    window.location.href = `${API_URL}/auth/login/google`;
  };

  // Logout
  const logout = async () => {
    try {
      const token = getToken();
      if (token) {
        // Call backend logout endpoint (optional)
        await fetch(`${API_URL}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Always clear local state
      removeToken();
      setUser(null);
      toast.success('Logged out successfully');
      navigate('/');
    }
  };

  // Get authorization header for API requests
  const getAuthHeader = () => {
    const token = getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated,
        login,
        logout,
        checkAuth,
        getAuthHeader,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Export setToken for use in callback page
export const setAuthToken = (token: string) => {
  localStorage.setItem('access_token', token);
};
