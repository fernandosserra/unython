# src/modules/backup_sqlite.py
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from typing import Optional
from src.utils.google_auth import autenticar_google_drive


def fazer_backup_google_drive_sqlite(db_path: str):
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