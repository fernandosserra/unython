# src/modules/backup_postgres.py
# Gerencia o backup de bancos de dados PostgreSQL.

import os
import subprocess
import time
from datetime import datetime
from typing import Optional, Any

# Importações para o Postgres e o Google Drive
from src.utils.database_manager import DB_CONFIG 
from src.utils.google_auth import autenticar_google_drive 
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# IMPORTANTE: Requer que 'pg_dump' e 'pg_restore' estejam no PATH do sistema.

def fazer_backup_google_drive_postgres(db_path: str):
    """
    Executa o comando pg_dump para criar um arquivo de backup do Postgres (.sql)
    e faz o upload/atualização desse arquivo para o Google Drive.
    """
    
    # 1. Definição de Nomes e Caminhos Temporários
    backup_filename = f"unython_postgres_dump_{datetime.now().strftime('%Y%m%d')}.sql"
    # Salva o arquivo de dump temporariamente na pasta 'data' (irmã de 'src')
    TEMP_BACKUP_PATH = os.path.join(os.path.dirname(db_path), backup_filename)
    
    # Obter credenciais do secrets.toml via DB_CONFIG
    PG_USER = DB_CONFIG['user']
    PG_DBNAME = DB_CONFIG['dbname']
    
    # 2. Comando pg_dump (CRÍTICO)
    # Define as variáveis de ambiente para a senha, evitando mostrá-la no comando.
    env = os.environ.copy()
    env['PGPASSWORD'] = DB_CONFIG['password']
    
    # Comando para despejar o banco de dados (formato plain text SQL)
    pg_dump_command = [
        'pg_dump',
        '-h', DB_CONFIG['host'],
        '-p', str(DB_CONFIG['port']),
        '-U', PG_USER,
        '-d', PG_DBNAME,
        '-F', 'p', # Formato plain text (SQL)
        '-f', TEMP_BACKUP_PATH # Arquivo de saída
    ]
    
    try:
        print(f" -> Iniciando despejo (pg_dump) do banco de dados '{PG_DBNAME}'...")
        
        # Executa o comando de sistema
        subprocess.run(pg_dump_command, env=env, check=True, capture_output=True)
        
        print(f" -> Arquivo de dump '{backup_filename}' criado com sucesso.")
        
        # 3. Autenticação e Upload para o Google Drive
        drive_service = autenticar_google_drive()
        
        if drive_service is None:
            # Garante que a limpeza seja executada no bloco finally
            return 
            
        # 3.1. Metadata do Arquivo
        file_metadata = {
            'name': backup_filename,
            'mimeType': 'application/sql' # MIME Type para arquivos SQL
        }
        
        # 3.2. Checa se o arquivo de backup SQL já existe (Washu Update Protocol)
        results = drive_service.files().list(
            q=f"name='{backup_filename}' and trashed=false",
            spaces='drive',
            fields='nextPageToken, files(id, name)'
        ).execute()
        
        items = results.get('files', [])
        
        media = MediaFileUpload(TEMP_BACKUP_PATH, 
                                mimetype='application/sql', 
                                resumable=True)

        if items:
            # Arquivo existe: Atualiza
            file_id = items[0]['id']
            drive_service.files().update(
                fileId=file_id,
                media_body=media
            ).execute()
            print(f" -> Backup de '{backup_filename}' ATUALIZADO (PostgreSQL Dump) com sucesso no Google Drive.")
        else:
            # Arquivo NÃO existe: Cria
            drive_file = drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            print(f" -> Backup de '{backup_filename}' CRIADO (PostgreSQL Dump) com sucesso no Google Drive (ID: {drive_file.get('id')}).")
                
    except subprocess.CalledProcessError as e:
        # Falha do pg_dump
        print(f" (Alerta Postgres): Falha crítica no pg_dump. Verifique o PATH e as credenciais. Erro: {e.stderr.decode()}")
        return
    except HttpError as error:
        print(f" (Alerta Washu HTTP): Ocorreu um erro no upload para o Drive: {error}")
        return
    except Exception as e:
        print(f" (Alerta Postgres): Erro inesperado durante o backup: {e}")
        return
        
    finally:
        # 4. Limpeza (Remoção do arquivo temporário com retries)
        if os.path.exists(TEMP_BACKUP_PATH):
            MAX_RETRIES = 3
            
            for attempt in range(MAX_RETRIES):
                try:
                    os.remove(TEMP_BACKUP_PATH)
                    print(" -> Arquivo temporário de dump removido com sucesso.")
                    break # Sai do loop se o remove for bem-sucedido
                except PermissionError:
                    if attempt < MAX_RETRIES - 1:
                        # Tenta novamente em 1 segundo
                        print(f" (Alerta Limpeza): Permissão negada. Tentando novamente em 1 segundo... Tentativa {attempt + 1}")
                        time.sleep(1)
                    else:
                        # Se todas as tentativas falharem, reporta e segue
                        print(f" (Alerta Limpeza): FALHA FINAL ao remover o arquivo temporário após {MAX_RETRIES} tentativas. Remova manualmente: {TEMP_BACKUP_PATH}")
                        # Não faz nada, apenas sai do loop