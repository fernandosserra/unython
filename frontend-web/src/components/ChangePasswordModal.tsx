import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { AlertCircle, CheckCircle2, KeyRound, LogOut, X } from 'lucide-react';
import { apiClient } from '../api/client';
import { useAuthStore } from '../store/useAuthStore';

interface ChangePasswordModalProps {
  isOpen: boolean;
  required?: boolean;
  onClose?: () => void;
}

export function ChangePasswordModal({
  isOpen,
  required = false,
  onClose,
}: ChangePasswordModalProps) {
  const { user, setUser, setNotice, logout } = useAuthStore();
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setError('');
      setSuccess('');
    }
  }, [isOpen]);

  if (!isOpen || !user) return null;

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError('');
    setSuccess('');

    if (!oldPassword || !newPassword) {
      setError('Preencha a senha atual e a nova senha.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('A confirmação não corresponde à nova senha.');
      return;
    }

    setIsSubmitting(true);
    try {
      await apiClient.post('/change-password', {
        email: user.email,
        old_password: oldPassword,
        new_password: newPassword,
      });

      if (required) {
        setNotice('Senha alterada com sucesso. Entre novamente com a nova senha.');
        logout();
        return;
      }

      setUser({ ...user, require_password_change: false });
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setSuccess('Senha alterada com sucesso.');
    } catch (requestError: any) {
      setError(
        requestError.response?.data?.detail ||
          'Não foi possível alterar a senha. Confira a senha atual e tente novamente.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="change-password-title"
    >
      <div className="bg-white rounded-3xl max-w-md w-full shadow-2xl border border-slate-100 p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 id="change-password-title" className="font-black text-lg text-slate-900 flex items-center gap-2">
            <KeyRound className="w-5 h-5 text-emerald-600" />
            {required ? 'Troca de senha obrigatória' : 'Alterar senha'}
          </h2>
          {!required && (
            <button type="button" onClick={onClose} aria-label="Fechar" className="p-1 text-slate-400 hover:text-slate-700">
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {required && (
          <p className="text-sm text-slate-600 mb-4">
            Para continuar, defina uma nova senha para sua conta.
          </p>
        )}
        {error && (
          <p role="alert" className="mb-4 p-3 rounded-xl bg-rose-50 text-rose-800 text-sm flex gap-2">
            <AlertCircle className="w-5 h-5 shrink-0" />
            {error}
          </p>
        )}
        {success && (
          <p role="status" className="mb-4 p-3 rounded-xl bg-emerald-50 text-emerald-800 text-sm flex gap-2">
            <CheckCircle2 className="w-5 h-5 shrink-0" />
            {success}
          </p>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block text-xs font-bold text-slate-700">
            Senha atual
            <input
              type="password"
              autoComplete="current-password"
              required
              value={oldPassword}
              onChange={(event) => setOldPassword(event.target.value)}
              className="mt-1 block w-full border border-slate-200 rounded-xl p-3 text-sm"
            />
          </label>
          <label className="block text-xs font-bold text-slate-700">
            Nova senha
            <input
              type="password"
              autoComplete="new-password"
              required
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
              className="mt-1 block w-full border border-slate-200 rounded-xl p-3 text-sm"
            />
          </label>
          <label className="block text-xs font-bold text-slate-700">
            Confirmar nova senha
            <input
              type="password"
              autoComplete="new-password"
              required
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              className="mt-1 block w-full border border-slate-200 rounded-xl p-3 text-sm"
            />
          </label>
          <div className="flex justify-end gap-2 pt-1">
            {required ? (
              <button
                type="button"
                onClick={logout}
                className="px-4 py-2 rounded-xl border border-slate-200 text-slate-700 text-sm font-bold inline-flex items-center gap-2"
              >
                <LogOut className="w-4 h-4" />
                Sair
              </button>
            ) : (
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-xl border border-slate-200 text-slate-700 text-sm font-bold"
              >
                Cancelar
              </button>
            )}
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 rounded-xl bg-emerald-700 text-white text-sm font-bold disabled:opacity-50"
            >
              {isSubmitting ? 'Salvando...' : 'Atualizar senha'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
