import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

const AUTH_API = import.meta.env.VITE_AUTH_API || 'http://localhost:8182';
const NIPUNI_API = import.meta.env.VITE_NIPUNI_API_URL || 'http://localhost:8000';

interface User {
  id: number;
  email: string;
  name: string;
  picture?: string;
  provider: string;
  is_active: boolean;
  created_at: string;
  last_login: string;
  // Candidate profile fields
  candidate_id?: string;
  current_role?: string;
  major?: string;
  interests?: string;
  personality?: string;
  skills?: string;
  target_role?: string;
  // Analysis results
  readiness_score?: number;
  ai_explanation?: string;
  analysis_summary?: string;
  latest_analysis_date?: string;
  matched_skills?: any[];
  missing_skills?: any[];
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
      const response = await fetch(`${AUTH_API}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const userData = await response.json();
        
        // Fetch candidate profile to get skills, major, interests, etc.
        try {
          const profileResponse = await fetch(`${NIPUNI_API}/candidate/me`, {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          });
          
          if (profileResponse.ok) {
            const profileData = await profileResponse.json();
            const candidate = profileData.data;
            
            if (candidate) {
              // Merge candidate profile data with user data
              userData.candidate_id = candidate.candidate_id;
              userData.current_role = candidate.current_role;
              userData.major = candidate.major;
              userData.interests = candidate.interests;
              userData.personality = candidate.personality;
              userData.skills = candidate.skills;
              userData.target_role = candidate.target_role;
              
              // Merge analysis results if available
              if (candidate.analysis) {
                userData.readiness_score = candidate.analysis.readiness_score;
                userData.ai_explanation = candidate.analysis.ai_explanation;
                userData.analysis_summary = candidate.analysis.analysis_summary;
                userData.latest_analysis_date = candidate.analysis.latest_analysis_date;
                userData.matched_skills = candidate.analysis.matched_skills;
                userData.missing_skills = candidate.analysis.missing_skills;
              }
            }
          }
        } catch (profileError) {
          console.log('Could not fetch candidate profile:', profileError);
          // Continue with basic user data
        }
        
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
    window.location.href = `${AUTH_API}/auth/login/google`;
  };

  // Logout
  const logout = async () => {
    try {
      const token = getToken();
      if (token) {
        // Call backend logout endpoint (optional)
        await fetch(`${AUTH_API}/auth/logout`, {
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
