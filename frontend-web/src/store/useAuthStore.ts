import { create } from 'zustand';
import { apiClient } from '../api/client';
import type { Usuario } from '../types';

interface AuthState {
  token: string | null;
  user: Usuario | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  setUser: (user: Usuario) => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => {
  const savedToken = localStorage.getItem('unython_auth_token');
  const savedUser = localStorage.getItem('unython_user_data');

  let initialUser: Usuario | null = null;
  if (savedUser) {
    try {
      initialUser = JSON.parse(savedUser);
    } catch {
      initialUser = null;
    }
  }

  return {
    token: savedToken,
    user: initialUser,
    isAuthenticated: !!savedToken,
    isLoading: false,
    error: null,

    login: async (email: string, password: string) => {
      set({ isLoading: true, error: null });
      try {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        const response = await apiClient.post('/token', formData, {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        });

        const { access_token, user_id, role, require_password_change } = response.data;
        const loggedUser: Usuario = {
          id: user_id,
          email,
          nome: email.split('@')[0],
          role,
          status: 'Ativo',
          require_password_change,
        };

        localStorage.setItem('unython_auth_token', access_token);
        localStorage.setItem('unython_user_data', JSON.stringify(loggedUser));

        set({
          token: access_token,
          user: loggedUser,
          isAuthenticated: true,
          isLoading: false,
        });
        return true;
      } catch (err: any) {
        const message = err.response?.data?.detail || 'Erro ao realizar login. Verifique as credenciais.';
        set({ error: message, isLoading: false });
        return false;
      }
    },

    logout: () => {
      localStorage.removeItem('unython_auth_token');
      localStorage.removeItem('unython_user_data');
      set({ token: null, user: null, isAuthenticated: false, error: null });
    },

    setUser: (user: Usuario) => {
      localStorage.setItem('unython_user_data', JSON.stringify(user));
      set({ user });
    },

    clearError: () => set({ error: null }),
  };
});
