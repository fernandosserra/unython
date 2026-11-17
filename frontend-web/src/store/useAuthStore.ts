import { create } from 'zustand';
import { apiClient } from '../api/client';
import type { Usuario } from '../types';

interface AuthState {
  token: string | null;
  user: Usuario | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  authReady: boolean;
  error: string | null;
  notice: string | null;
  login: (email: string, password: string) => Promise<boolean>;
  refreshUser: (blockUntilVerified?: boolean) => Promise<boolean>;
  logout: () => void;
  setUser: (user: Usuario) => void;
  setNotice: (notice: string) => void;
  clearNotice: () => void;
  clearError: () => void;
}

let refreshInFlight: Promise<boolean> | null = null;

export const useAuthStore = create<AuthState>((set, get) => {
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
    authReady: false,
    error: null,
    notice: null,

    login: async (email: string, password: string) => {
      set({ isLoading: true, error: null, notice: null });
      try {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        const response = await apiClient.post('/token', formData, {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        });

        const { access_token } = response.data;
        localStorage.setItem('unython_auth_token', access_token);
        set({
          token: access_token,
          user: null,
          isAuthenticated: true,
          authReady: false,
        });
        if (!await get().refreshUser(true)) {
          get().logout();
          set({ error: 'Não foi possível verificar sua sessão. Tente novamente.', isLoading: false });
          return false;
        }
        set({ isLoading: false });
        return true;
      } catch (err: any) {
        const message = err.response?.data?.detail || 'Erro ao realizar login. Verifique as credenciais.';
        set({ error: message, isLoading: false });
        return false;
      }
    },

    refreshUser: async (blockUntilVerified = false) => {
      const token = get().token;
      if (!token) return false;
      if (blockUntilVerified) set({ authReady: false });
      if (refreshInFlight) return refreshInFlight;
      const request = (async () => {
        try {
          const { data } = await apiClient.get<Usuario>('/auth/me');
          if (get().token !== token) return false;
          if (!data || (data.permissoes !== null &&
              (!Array.isArray(data.permissoes) || !data.permissoes.every((permission) => typeof permission === 'string'))) ||
              typeof data.id !== 'number' || typeof data.email !== 'string' ||
              typeof data.role !== 'string' || typeof data.status !== 'string') {
            set({ authReady: false });
            return false;
          }
          if (data.status !== 'Ativo') {
            get().logout();
            get().setNotice('Sua conta foi desativada. Entre em contato com um administrador.');
            return false;
          }
          localStorage.setItem('unython_user_data', JSON.stringify(data));
          set({ user: data, authReady: true });
          return true;
        } catch {
          if (get().token === token) set({ authReady: false });
          return false;
        }
      })();
      refreshInFlight = request;
      try {
        return await request;
      } finally {
        if (refreshInFlight === request) refreshInFlight = null;
      }
    },

    logout: () => {
      refreshInFlight = null;
      localStorage.removeItem('unython_auth_token');
      localStorage.removeItem('unython_user_data');
      set({ token: null, user: null, isAuthenticated: false, authReady: false, error: null });
    },

    setUser: (user: Usuario) => {
      localStorage.setItem('unython_user_data', JSON.stringify(user));
      set({ user });
    },

    setNotice: (notice: string) => set({ notice }),
    clearNotice: () => set({ notice: null }),
    clearError: () => set({ error: null }),
  };
});
