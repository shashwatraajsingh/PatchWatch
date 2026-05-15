'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';

interface User {
  id: number;
  username: string;
  avatar_url: string | null;
  github_id: number;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: () => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  loading: true,
  login: () => {},
  logout: () => {},
});

export function useAuth() {
  return useContext(AuthContext);
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load token from localStorage on mount
    const saved = localStorage.getItem('patchwatch_token');
    if (saved) {
      setToken(saved);
      // Verify token is still valid
      fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${saved}` },
      })
        .then((res) => {
          if (res.ok) return res.json();
          throw new Error('Invalid token');
        })
        .then((data) => {
          setUser(data);
          setToken(saved);
        })
        .catch(() => {
          localStorage.removeItem('patchwatch_token');
          setToken(null);
          setUser(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = () => {
    // Redirect to backend which redirects to GitHub
    window.location.href = `${API_BASE}/auth/github`;
  };

  const logout = () => {
    localStorage.removeItem('patchwatch_token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
