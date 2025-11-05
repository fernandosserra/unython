# src/modules/backup.py (ORQUESTRADOR CORRETO)

import os
from src.utils.database_manager import DB_CONFIG # Importa as configurações
# Usamos .backup_sqlite e .backup_postgres para garantir a importação relativa
from .backup_postgres import fazer_backup_google_drive_postgres

def fazer_backup_google_drive(db_path: str):
    """
    Decide qual rotina de backup usar com base no tipo de banco de dados configurado.
    """
    db_type = DB_CONFIG.get('type', 'sqlite')

    if db_type == 'postgres':
        print("\n--- Protocolo de Backup (PostgreSQL) Ativado ---")
        fazer_backup_google_drive_postgres(db_path)
    else:
        print(f" (Alerta Washu Backup): Tipo de DB desconhecido '{db_type}'. Backup cancelado.")

# OBSERVAÇÃO: A lógica de autenticação (autenticar_google_drive) DEVE ser movida 
# para um arquivo utilitário (ex: src/utils/google_auth.py) ou duplicada em ambos os módulos de backup.