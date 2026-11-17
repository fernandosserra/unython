import { useCallback, useEffect, useState } from 'react';
import { AlertTriangle, WifiOff } from 'lucide-react';
import { apiClient } from '../api/client';

export function ConnectivityBanner() {
  const [isOnline, setIsOnline] = useState(() => navigator.onLine);
  const [apiUnavailable, setApiUnavailable] = useState(false);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    const handleApiUnavailable = () => setApiUnavailable(true);
    const handleApiReachable = () => setApiUnavailable(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    window.addEventListener('unython_api_unavailable', handleApiUnavailable);
    window.addEventListener('unython_api_reachable', handleApiReachable);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      window.removeEventListener('unython_api_unavailable', handleApiUnavailable);
      window.removeEventListener('unython_api_reachable', handleApiReachable);
    };
  }, []);

  const checkApi = useCallback(async () => {
    try {
      await apiClient.get('/health');
    } catch {
      setApiUnavailable(true);
    }
  }, []);

  if (isOnline && !apiUnavailable) return null;

  const isOffline = !isOnline;

  return (
    <div
      role="status"
      aria-live="polite"
      className={`flex items-center justify-between gap-3 px-4 py-2 text-sm font-semibold ${
        isOffline ? 'bg-amber-100 text-amber-950' : 'bg-rose-100 text-rose-950'
      }`}
    >
      <div className="flex min-w-0 items-center gap-2">
        {isOffline ? <WifiOff className="h-4 w-4 shrink-0" /> : <AlertTriangle className="h-4 w-4 shrink-0" />}
        <span>
          {isOffline
            ? 'Sem conexão com a internet. Confirme o resultado antes de repetir qualquer operação.'
            : 'A API está indisponível. Confirme o resultado antes de repetir qualquer operação.'}
        </span>
      </div>
      {!isOffline && (
        <button
          type="button"
          onClick={() => void checkApi()}
          className="min-h-11 shrink-0 rounded-lg px-3 text-xs font-bold underline underline-offset-2"
        >
          Tentar novamente
        </button>
      )}
    </div>
  );
}
