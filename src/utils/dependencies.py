# src/utils/dependencies.py

from typing import Annotated, Generator
from fastapi import Depends
from ..utils.database_manager import DatabaseManager # Importação relativa corrigida

def get_db() -> Generator[DatabaseManager, None, None]:
    """
    Função geradora que cria uma conexão de banco de dados 
    e garante que ela seja fechada após a requisição.
    """
    db = DatabaseManager()
    try:
        db.connect()
        yield db
    finally:
        db.disconnect()
        
# Alias para uso nos endpoints
DBDependency = Annotated[DatabaseManager, Depends(get_db)]