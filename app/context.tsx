// context.tsx
import React, { createContext, useContext, useState } from 'react';

const AuthContext = createContext({
  token: null as string | null,
  setToken: (token: string | null) => {},
});

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [token, setToken] = useState<string | null>(null);

  return (
    <AuthContext.Provider value={{ token, setToken }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);