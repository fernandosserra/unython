# src/modules/backup.py
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
    return os.path.join(base_dir, 'app', filename)


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

def fazer_backup_google_drive(db_path: str):
    """Executa a Autenticação e faz o upload/atualização do arquivo DB."""
    
    # 1. Autenticação
    drive_service = autenticar_google_drive()

    if drive_service is None:
        return

    try:
        db_filename = os.path.basename(db_path)
        file_metadata = {
            'name': db_filename,
            'mimeType': 'application/x-sqlite3' 
        }
        
        # 2. Protocolo de Update da Washu: Checa se o arquivo já existe no Drive
        # Pesquisa por arquivos com o mesmo nome e escopo do app
        results = drive_service.files().list(
            q=f"name='{db_filename}' and trashed=false",
            spaces='drive',
            fields='nextPageToken, files(id, name)'
        ).execute()
        
        items = results.get('files', [])
        
        media = MediaFileUpload(db_path, mimetype='application/x-sqlite3', resumable=True)

        if items:
            # Arquivo existe: Atualiza (Patch Quântico)
            file_id = items[0]['id']
            drive_service.files().update(
                fileId=file_id,
                media_body=media
            ).execute()
            print(f" -> Backup de '{db_filename}' ATUALIZADO com sucesso no Google Drive (ID: {file_id}).")
        else:
            # Arquivo NÃO existe: Cria (Invenção Genial)
            drive_file = drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            print(f" -> Backup de '{db_filename}' CRIADO com sucesso no Google Drive (ID: {drive_file.get('id')}).")

    except HttpError as error:
        print(f" (Alerta Washu HTTP): Ocorreu um erro no upload: {error}")
    except Exception as e:
        print(f" (Alerta Washu): Erro inesperado no backup: {e}")