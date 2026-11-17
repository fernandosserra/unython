import React, { useState, useEffect } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { Smartphone, X, Wifi, Copy, Check } from 'lucide-react';
import { apiClient } from '../api/client';

interface ConnectMobileModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ConnectMobileModal: React.FC<ConnectMobileModalProps> = ({ isOpen, onClose }) => {
  const [networkUrl, setNetworkUrl] = useState<string>('');
  const [networkError, setNetworkError] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    let active = true;
    setNetworkUrl('');
    setNetworkError(false);
    apiClient
      .get('/rede')
      .then((res) => {
        if (!active) return;
        if (typeof res.data?.url === 'string' && res.data.url) {
          setNetworkUrl(res.data.url);
        } else {
          setNetworkError(true);
          setNetworkUrl(window.location.origin);
        }
      })
      .catch(() => {
        if (!active) return;
        setNetworkError(true);
        setNetworkUrl(window.location.origin);
      });
    return () => { active = false; };
  }, [isOpen]);

  if (!isOpen) return null;

  let localOnly = false;
  try {
    const hostname = new URL(networkUrl).hostname;
    localOnly = hostname === 'localhost' || hostname === '0.0.0.0' ||
      hostname === '[::1]' || hostname.startsWith('127.');
  } catch {
    localOnly = Boolean(networkUrl);
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(networkUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 animate-fade-in">
      <div className="bg-white rounded-3xl max-w-sm w-full max-h-[90dvh] overflow-y-auto shadow-2xl border border-slate-100 p-6 text-center">
        {/* Cabeçalho */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2 text-slate-900 font-black text-base">
            <Smartphone className="w-5 h-5 text-emerald-600" />
            <span>Abrir no Celular</span>
          </div>
          <button
            onClick={onClose}
            aria-label="Fechar conexão mobile"
            className="min-h-11 min-w-11 inline-flex items-center justify-center rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {(networkError || localOnly) && (
          <p role="alert" className="mb-4 rounded-xl bg-amber-50 p-3 text-left text-xs text-amber-900">
            {localOnly
              ? 'O endereço exibido aponta para este computador e não funciona no celular. Consulte o IP da rede local no computador e acesse http://IP-DA-REDE:8000.'
              : 'Não foi possível detectar o IP da rede. Verifique se o endereço exibido é acessível pelo celular.'}
          </p>
        )}

        <div className="mb-4 rounded-xl border border-emerald-100 bg-emerald-50 p-3 text-left text-xs text-emerald-900">
          Acesse pelo IP da rede local na porta 8000, por exemplo <strong>http://192.168.1.10:8000</strong>.
          Se não conectar, pode ser necessário liberar a porta 8000 no Firewall do Windows.
        </div>

        {/* QR Code */}
        <div className="my-6 flex flex-col items-center">
          <div className="p-4 bg-white rounded-2xl shadow-md border-2 border-emerald-500/30">
            {networkUrl ? (
              <QRCodeSVG
                value={networkUrl}
                size={190}
                level="M"
                includeMargin={false}
              />
            ) : (
              <div className="w-[190px] h-[190px] flex items-center justify-center text-xs text-slate-400">
                Gerando QR Code...
              </div>
            )}
          </div>

          <div className="mt-4 flex items-center gap-1.5 text-xs text-emerald-800 font-bold bg-emerald-50 px-3 py-1.5 rounded-full border border-emerald-200">
            <Wifi className="w-3.5 h-3.5 text-emerald-600" />
            <span>Conecte no mesmo Wi-Fi deste computador</span>
          </div>
        </div>

        {/* Link e botão de copiar */}
        <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between gap-2 text-left mb-4">
          <div className="min-w-0 flex-1">
            <span className="text-[10px] uppercase font-bold text-slate-400 block">Link de Acesso</span>
            <span className="text-xs font-mono font-bold text-slate-800 truncate block">
              {networkUrl || 'Carregando...'}
            </span>
          </div>
          <button
            onClick={handleCopy}
            title="Copiar link"
            className="p-2 rounded-lg bg-white border border-slate-200 text-slate-600 hover:text-emerald-700 hover:bg-emerald-50 transition-colors cursor-pointer shrink-0"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
          </button>
        </div>

        {/* Instruções PWA */}
        <div className="text-[11px] text-slate-500 text-left space-y-1.5 bg-slate-50/60 p-3 rounded-xl border border-slate-100">
          <p className="font-bold text-slate-700">📱 Dica para Voluntários:</p>
          <p>
            1. Aponte a câmera do celular para o código QR acima para abrir o caixa.
          </p>
          <p>
            2. No navegador do celular, toque em <span className="font-semibold text-slate-800">"Compartilhar"</span> e selecione <span className="font-semibold text-slate-800">"Adicionar à Tela de Início"</span> para instalar como app.
          </p>
        </div>
      </div>
    </div>
  );
};
