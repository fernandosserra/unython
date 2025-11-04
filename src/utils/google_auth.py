# src/utils/google_auth.py

import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from typing import Optional

# ----------------------------------------------------
# CONFIGURAÇÃO DE SEGURANÇA E CAMINHOS
# ----------------------------------------------------

# O escopo (permissão) exigido. Permite apenas gerenciar arquivos criados pelo app.
SCOPES = ['https://www.googleapis.com/auth/drive.file'] 
TOKEN_FILENAME = 'token.json'        # Nome do arquivo de token
CREDS_FILENAME = 'credentials.json'  # Nome do arquivo de credenciais baixado

def _get_app_path(filename: str) -> str:
    """
    Calcula o caminho absoluto para os arquivos que DEVEM estar na pasta 'app/', 
    resolvendo a inconsistência dimensional do caminho.
    """
    # Navega para o ROOT do projeto (Unython) e desce para 'app'
    # __file__ -> src/modules/backup.py
    # sobe 1 -> src/modules/
    # sobe 2 -> src/
    # sobe 3 -> Unython/ (ROOT)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, 'config', filename)


def autenticar_google_drive() -> Optional[object]:
    """Lida com o fluxo de autenticação OAuth2 e retorna o objeto Drive Service."""
    creds = None
    
    TOKEN_PATH = _get_app_path(TOKEN_FILENAME)
    CREDS_PATH = _get_app_path(CREDS_FILENAME)
    
    # 1. Tenta carregar as credenciais salvas (após o 1º login)
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # 2. Se não houver credenciais válidas ou se elas expiraram:
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Tenta renovar o token
            creds.refresh(Request())
        else:
            # Se não, inicia o fluxo de login no navegador (primeira vez)
            if not os.path.exists(CREDS_PATH):
                print(f" (Alerta Washu: Arquivo '{CREDS_FILENAME}' não encontrado em app/!)")
                print(" -> Obtê-lo no Google Cloud Console e garantir que esteja em 'app/'.")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        # 3. Salva as novas credenciais
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
            
    # Constrói e retorna o objeto Service para usar a API do Drive
    # Retorna o objeto Service para o Drive API v3
    return build('drive', 'v3', credentials=creds)