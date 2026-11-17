# Unython - (C) 2025 siegrfried@gmail.com
# Este programa e software livre: voce pode redistribui-lo e/ou modifica-lo
# sob os termos da GNU General Public License como publicada pela Free Software Foundation,
# na versao 3 da Licenca, ou (a seu criterio) qualquer versao posterior.
"""
Orquestrador do Unython:
- Padrão: Sobe API FastAPI que serve a SPA React/PWA diretamente em http://127.0.0.1:8000
- Flags:
    python app/main.py                    # Modo padrão integrado (FastAPI + SPA React embutida)
    python app/main.py --spa-dev          # Sobe API (8000) + Vite React Dev Server com HMR (3000)
    python app/main.py --api-only         # Apenas API sem interfaces
"""

import argparse
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import List


ROOT = Path(__file__).resolve().parents[1]
FRONTEND_WEB = ROOT / "frontend-web"


def _get_local_ip() -> str:
    """Detecta o IP local da máquina na rede Wi-Fi."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def _base_env() -> dict:
    """Garante PYTHONPATH configurado para imports de src/app e nodejs no PATH."""
    env = os.environ.copy()
    python_path = env.get("PYTHONPATH", "")
    paths = [str(ROOT)]
    if python_path:
        paths.append(python_path)
    env["PYTHONPATH"] = os.pathsep.join(paths)

    # Garante Node.js acessível se instalado no padrão do Windows
    node_path = r"C:\Program Files\nodejs"
    if os.path.exists(node_path) and node_path not in env.get("PATH", ""):
        env["PATH"] = f"{node_path};" + env.get("PATH", "")

    return env


def _get_python_executable() -> str:
    """Prefere o executável Python do venv do projeto se existir."""
    if sys.prefix != getattr(sys, "base_prefix", sys.prefix):
        return sys.executable

    venv_win = ROOT / "venv" / "Scripts" / "python.exe"
    venv_unix = ROOT / "venv" / "bin" / "python"
    if venv_win.exists():
        return str(venv_win)
    if venv_unix.exists():
        return str(venv_unix)
    return sys.executable


def start_api(host: str, port: int, reload: bool) -> subprocess.Popen:
    cmd: List[str] = [
        _get_python_executable(),
        "-m",
        "uvicorn",
        "app.api_main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    if reload:
        cmd.append("--reload")
    return subprocess.Popen(cmd, cwd=ROOT, env=_base_env())


def start_vite_dev(port: int) -> subprocess.Popen:
    """Inicia o servidor de desenvolvimento do Vite (React com HMR)."""
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    cmd: List[str] = [npm_cmd, "run", "dev", "--", "--port", str(port)]
    return subprocess.Popen(cmd, cwd=FRONTEND_WEB, env=_base_env())


def main():
    parser = argparse.ArgumentParser(description="Orquestrador Unython - Sistema de Gestão para ONGs.")
    parser.add_argument("--api-only", action="store_true", help="Inicia apenas o servidor de API.")
    parser.add_argument("--spa-dev", action="store_true", help="Inicia Vite Dev Server (React) com HMR.")
    parser.add_argument("--api-host", default="0.0.0.0", help="Host da API (0.0.0.0 para acesso via celular/Wi-Fi).")
    parser.add_argument("--api-port", type=int, default=8000, help="Porta da API.")
    parser.add_argument("--spa-port", type=int, default=3000, help="Porta do Vite Dev Server.")
    parser.add_argument("--no-reload", action="store_true", help="Desabilita auto-reload do Uvicorn.")
    args = parser.parse_args()

    procs: List[subprocess.Popen] = []
    local_ip = _get_local_ip()

    try:
        # 1. API FastAPI (que já serve a SPA embutida se compilada)
        print(f"[orquestrador] Subindo Unython API na rede...")
        print(f"[orquestrador] 💻 No computador: http://127.0.0.1:{args.api_port}/")
        print(f"[orquestrador] 📱 No celular (mesmo Wi-Fi): http://{local_ip}:{args.api_port}/")

        procs.append(start_api(args.api_host, args.api_port, reload=not args.no_reload))

        # 2. Vite Dev Server (Opcional para desenvolvimento ativo da SPA)
        if args.spa_dev:
            print(f"[orquestrador] Subindo Vite Dev Server em http://127.0.0.1:{args.spa_port}")
            procs.append(start_vite_dev(args.spa_port))

        # Aguarda interrupção
        while True:
            alive = [p for p in procs if p.poll() is None]
            if not alive:
                break
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[orquestrador] Encerrando serviços...")
    finally:
        for p in procs:
            if p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    p.kill()
        print("[orquestrador] Todos os serviços foram finalizados.")


if __name__ == "__main__":
    main()
