import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { saveBackendProfile, fetchBackendProfile, mergeBackendProfile } from '@/services/profileService';

export type UserType = 'student' | 'expert';

export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  bio?: string;
  role?: string;
  userType: UserType;
  // Academic / skill profile fields
  current_role?: string;
  major?: string;
  interests?: string;
  personality?: string;
  skills?: string;
  joinedAt: string;
}

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string, userType: UserType) => Promise<void>;
  logout: () => void;
  updateProfile: (data: Partial<Pick<User, 'name' | 'bio' | 'role' | 'current_role' | 'major' | 'interests' | 'personality' | 'skills'>>) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const STORAGE_KEY = 'auth_user';
const ACCOUNTS_KEY = 'auth_accounts';

interface StoredAccount {
  id: string;
  name: string;
  email: string;
  passwordHash: string;
  userType: UserType;
  bio?: string;
  role?: string;
  current_role?: string;
  major?: string;
  interests?: string;
  personality?: string;
  skills?: string;
  joinedAt: string;
}

// Simple deterministic hash for demo purposes (NOT production-safe)
function simpleHash(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash |= 0;
  }
  return hash.toString(16);
}

function getAccounts(): StoredAccount[] {
  try {
    return JSON.parse(localStorage.getItem(ACCOUNTS_KEY) || '[]');
  } catch {
    return [];
  }
}

function saveAccounts(accounts: StoredAccount[]) {
  localStorage.setItem(ACCOUNTS_KEY, JSON.stringify(accounts));
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const persistUser = useCallback((u: User | null) => {
    setUser(u);
    if (u) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(u));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  const register = useCallback(async (name: string, email: string, password: string, userType: UserType = 'student') => {
    const accounts = getAccounts();
    if (accounts.find(a => a.email.toLowerCase() === email.toLowerCase())) {
      throw new Error('An account with this email already exists.');
    }
    const newAccount: StoredAccount = {
      id: crypto.randomUUID(),
      name,
      email,
      passwordHash: simpleHash(password),
      userType,
      joinedAt: new Date().toISOString(),
    };
    saveAccounts([...accounts, newAccount]);

    const newUser: User = {
      id: newAccount.id,
      name: newAccount.name,
      email: newAccount.email,
      userType: newAccount.userType,
      joinedAt: newAccount.joinedAt,
    };
    persistUser(newUser);
    // Sync the new profile to the backend JSONL store (best-effort)
    saveBackendProfile(newUser).catch(err =>
      console.warn('[profile sync] register failed:', err),
    );
  }, [persistUser]);

  const login = useCallback(async (email: string, password: string) => {
    const accounts = getAccounts();
    const account = accounts.find(
      a => a.email.toLowerCase() === email.toLowerCase() && a.passwordHash === simpleHash(password),
    );
    if (!account) {
      throw new Error('Invalid email or password.');
    }
    const loggedInUser: User = {
      id: account.id,
      name: account.name,
      email: account.email,
      userType: account.userType ?? 'student',
      bio: account.bio,
      role: account.role,
      current_role: account.current_role,
      major: account.major,
      interests: account.interests,
      personality: account.personality,
      skills: account.skills,
      joinedAt: account.joinedAt,
    };
    persistUser(loggedInUser);
    // Pull any enriched profile data from the backend JSONL store (best-effort)
    fetchBackendProfile(loggedInUser.id)
      .then(backend => {
        if (backend) {
          const merged = mergeBackendProfile(loggedInUser, backend);
          persistUser(merged);
          // Keep the stored account in sync too
          const fresh = getAccounts();
          const i = fresh.findIndex(a => a.id === merged.id);
          if (i !== -1) {
            fresh[i] = {
              ...fresh[i],
              current_role: merged.current_role,
              major: merged.major,
              interests: merged.interests,
              personality: merged.personality,
              skills: merged.skills,
            };
            saveAccounts(fresh);
          }
        }
      })
      .catch(err => console.warn('[profile sync] login fetch failed:', err));
  }, [persistUser]);

  const logout = useCallback(() => {
    persistUser(null);
  }, [persistUser]);

  const updateProfile = useCallback((data: Partial<Pick<User, 'name' | 'bio' | 'role' | 'current_role' | 'major' | 'interests' | 'personality' | 'skills'>>) => {
    if (!user) return;
    const accounts = getAccounts();
    const idx = accounts.findIndex(a => a.id === user.id);
    if (idx !== -1) {
      accounts[idx] = { ...accounts[idx], ...data };
      saveAccounts(accounts);
    }
    const updated: User = { ...user, ...data };
    persistUser(updated);
    // Sync updated profile to backend JSONL store (best-effort)
    saveBackendProfile(updated).catch(err =>
      console.warn('[profile sync] updateProfile failed:', err),
    );
  }, [user, persistUser]);

  // Keep in-memory user in sync if storage changes in another tab
  useEffect(() => {
    const handler = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY) {
        try {
          setUser(e.newValue ? JSON.parse(e.newValue) : null);
        } catch {
          setUser(null);
        }
      }
    };
    window.addEventListener('storage', handler);
    return () => window.removeEventListener('storage', handler);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, register, logout, updateProfile }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}
