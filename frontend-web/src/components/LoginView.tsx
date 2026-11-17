import React, { useState } from 'react';
import { HeartHandshake, Lock, Mail, ArrowRight, AlertCircle, Sparkles } from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';

export const LoginView: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login, isLoading, error, notice, clearError, clearNotice } = useAuthStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;
    await login(email, password);
  };

  const handleQuickLogin = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    clearError();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-emerald-950 to-slate-900 flex items-center justify-center p-4 sm:p-6 lg:p-8">
      <div className="w-full max-w-md">
        {/* Card do Login */}
        <div className="bg-white/95 backdrop-blur-md rounded-3xl shadow-2xl border border-white/20 p-8 sm:p-10 text-slate-800">
          {/* Logo e Cabeçalho */}
          <div className="flex flex-col items-center text-center mb-8">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-500 text-white flex items-center justify-center shadow-lg shadow-emerald-600/30 mb-4">
              <HeartHandshake className="w-9 h-9" />
            </div>
            <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Unython</h1>
            <p className="text-sm font-medium text-emerald-700 mt-1">Plataforma de Impacto & Gestão para ONGs</p>
            <p className="text-xs text-slate-500 mt-0.5">Gestão de eventos, serviços e atendimentos</p>
          </div>

          {notice && (
            <div role="status" className="mb-6 p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm">
              <div className="flex items-start justify-between gap-3">
                <span>{notice}</span>
                <button type="button" onClick={clearNotice} aria-label="Dispensar aviso" className="font-bold">
                  ×
                </button>
              </div>
            </div>
          )}

          {error && (
            <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-start gap-3 animate-fade-in">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                E-mail do Operador / Admin
              </label>
              <div className="relative">
                <Mail className="w-5 h-5 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@unython.local"
                  className="w-full pl-11 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-emerald-500 focus:bg-white transition-all text-sm font-medium"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Senha
              </label>
              <div className="relative">
                <Lock className="w-5 h-5 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-11 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-emerald-500 focus:bg-white transition-all text-sm font-medium"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3.5 px-4 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white rounded-xl font-bold shadow-lg shadow-emerald-600/25 hover:shadow-xl transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 text-sm mt-2 cursor-pointer"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <span>Entrar no Sistema</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Atalho para ambiente de desenvolvimento/bootstrap */}
          <div className="mt-8 pt-6 border-t border-slate-100">
            <div className="flex items-center gap-2 mb-3 text-xs font-semibold text-slate-500">
              <Sparkles className="w-3.5 h-3.5 text-amber-500" />
              <span>Acesso Rápido Bootstrap (Admin Padrão):</span>
            </div>
            <button
              type="button"
              onClick={() => handleQuickLogin('admin@unython.local', 'change-me-now')}
              className="w-full text-left p-2.5 rounded-lg border border-dashed border-emerald-300 bg-emerald-50/50 hover:bg-emerald-50 text-xs text-emerald-800 font-mono transition-colors flex items-center justify-between cursor-pointer"
            >
              <span>admin@unython.local</span>
              <span className="text-[10px] bg-emerald-200/60 px-1.5 py-0.5 rounded text-emerald-900">Preencher</span>
            </button>
          </div>
        </div>

        {/* Rodapé institucional */}
        <p className="text-center text-xs text-emerald-200/70 mt-6 font-medium">
          Software Livre & Aberto sob licença GPL-3.0 • Feito para Organizações de Impacto
        </p>
      </div>
    </div>
  );
};
