# Unython - (C) 2025 fsserra@gmail.com
# Este programa e software livre: voce pode redistribui-lo e/ou modifica-lo
# sob os termos da GNU General Public License como publicada pela Free Software Foundation,
# na versao 3 da Licenca, ou (a seu criterio) qualquer versao posterior.
"""
Ponto de orquestração em desenvolvimento: sobe API (FastAPI/Uvicorn) e
Interface (Streamlit). Use as flags para escolher qual serviço iniciar.

Exemplos:
  python app/main.py --api-only
  python app/main.py --ui-only
  python app/main.py --api-port 8000 --ui-port 8501
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List


ROOT = Path(__file__).resolve().parents[1]


def _base_env() -> dict:
    """Garante PYTHONPATH configurado para imports de src/app."""
    env = os.environ.copy()
    python_path = env.get("PYTHONPATH", "")
    paths = [str(ROOT)]
    if python_path:
        paths.append(python_path)
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return env


def start_api(host: str, port: int, reload: bool) -> subprocess.Popen:
    cmd: List[str] = [
        sys.executable,
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


def start_ui(port: int) -> subprocess.Popen:
    cmd: List[str] = [
        "streamlit",
        "run",
        str(ROOT / "frontend" / "interface.py"),
        "--server.port",
        str(port),
        "--server.headless",
        "true",
    ]
    return subprocess.Popen(cmd, cwd=ROOT, env=_base_env())


def main():
    parser = argparse.ArgumentParser(description="Orquestra API e Interface da Unython.")
    parser.add_argument("--api-only", action="store_true", help="Inicia apenas a API.")
    parser.add_argument("--ui-only", action="store_true", help="Inicia apenas a Interface (Streamlit).")
    parser.add_argument("--api-host", default="127.0.0.1", help="Host da API.")
    parser.add_argument("--api-port", type=int, default=8000, help="Porta da API.")
    parser.add_argument("--ui-port", type=int, default=8501, help="Porta da Interface.")
    parser.add_argument("--no-reload", action="store_true", help="Desabilita reload automático do Uvicorn.")
    args = parser.parse_args()

    start_api_flag = not args.ui_only
    start_ui_flag = not args.api_only

    procs: List[subprocess.Popen] = []

    try:
        if start_api_flag:
            print(f"[orquestrador] Subindo API em http://{args.api_host}:{args.api_port}")
            procs.append(start_api(args.api_host, args.api_port, reload=not args.no_reload))

        if start_ui_flag:
            print(f"[orquestrador] Subindo Interface em http://127.0.0.1:{args.ui_port}")
            procs.append(start_ui(args.ui_port))

        if not procs:
            print("Nada para iniciar (verifique as flags --api-only / --ui-only).")
            return

        # Aguarda até interrupção (Ctrl+C) com pooling simples
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
                # SIGINT não funciona bem no Windows para subprocess; use terminate
                p.terminate()
        for p in procs:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()


if __name__ == "__main__":
    main()
