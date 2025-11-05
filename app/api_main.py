# app/api_main.py
from fastapi import FastAPI, Depends, HTTPException, status
from typing import Annotated, Generator
import sys
import os
import uvicorn

# Adiciona o diretório 'src' ao PATH para imports modulares
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Importa a infraestrutura do back-end
from src.utils.database_manager import DatabaseManager
from src.utils.dependencies import DBDependency

# Importa os routers
from app.routers import estoque, vendas

# Cria a instância da API
app = FastAPI(
    title="Unython - Gestão API",
    description="API REST para gerenciamento de ONGs e Fluxo de Eventos.",
    version="1.0.0"
)

# ----------------------------------------------------
# 1. ENDPOINTS BÁSICOS
# ----------------------------------------------------

@app.get("/")
def read_root():
    """Confirma que a API está operacional."""
    return {"message": "Unython API Operational. Data source: PostgreSQL."}

@app.get("/db-status")
def get_db_status(db: DBDependency):
    """Teste para garantir que a conexão está ativa."""
    # Se a conexão foi bem-sucedida pelo get_db, a API retorna OK
    return {"status": "connected", "database": db.DB_NAME}

# ----------------------------------------------------
# 2. INCLUSÃO DE ROUTERS
# ----------------------------------------------------

app.include_router(estoque.router)
app.include_router(vendas.router)

# ----------------------------------------------------


if __name__ == "__main__":
    # Comando para rodar o servidor Uvicorn localmente
    uvicorn.run(app, host="127.0.0.1", port=8000)
    
    
