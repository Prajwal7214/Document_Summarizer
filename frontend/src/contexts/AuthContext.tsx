import React, { createContext, useContext, useState, useEffect } from 'react';

export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem('summarix_user');
    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        localStorage.removeItem('summarix_user');
      }
    }
  }, []);

  const login = async (email: string, password: string): Promise<void> => {
    // Check stored users from localStorage (simulated backend)
    const usersRaw = localStorage.getItem('summarix_users');
    const users: (User & { password: string })[] = usersRaw ? JSON.parse(usersRaw) : [];
    const found = users.find((u) => u.email === email && u.password === password);
    if (!found) {
      throw new Error('Invalid email or password.');
    }
    const { password: _pw, ...userData } = found;
    setUser(userData);
    localStorage.setItem('summarix_user', JSON.stringify(userData));
  };

  const signup = async (name: string, email: string, password: string): Promise<void> => {
    const usersRaw = localStorage.getItem('summarix_users');
    const users: (User & { password: string })[] = usersRaw ? JSON.parse(usersRaw) : [];
    if (users.find((u) => u.email === email)) {
      throw new Error('An account with this email already exists.');
    }
    const newUser: User & { password: string } = {
      id: Date.now().toString(),
      name,
      email,
      password,
    };
    users.push(newUser);
    localStorage.setItem('summarix_users', JSON.stringify(users));
    const { password: _pw, ...userData } = newUser;
    setUser(userData);
    localStorage.setItem('summarix_user', JSON.stringify(userData));
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('summarix_user');
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
