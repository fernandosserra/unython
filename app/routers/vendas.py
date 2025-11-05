# app/routers/vendas.py

from fastapi import APIRouter, Depends, status, HTTPException
from typing import List
from src.utils.dependencies import DBDependency
from src.utils.schemas import VendaCreate, VendaResponse 
from src.modules.venda import VendaService
from src.utils.models import Venda, ItemVenda

router = APIRouter(
    prefix="/vendas",
    tags=["Vendas (Transação Atômica)"]
)

@router.post("/", status_code=status.HTTP_201_CREATED)
def registrar_venda_completa(venda_data: VendaCreate, db: DBDependency):
    """
    Registra uma venda atômica completa, checa estoque, e debita os itens.
    """
    venda_service = VendaService(db)
    
    # 1. Preparar o Cabeçalho (Venda Model)
    # Note: Assumimos que o 'responsavel' no Venda Model é uma string (ID do usuário)
    cabecalho = Venda(
        id_pessoa=venda_data.id_pessoa,
        responsavel=str(venda_data.responsavel_id),
        id_evento=venda_data.id_evento,
        # data_venda será preenchida pelo Model/DB
    )
    
    # 2. Preparar os Detalhes (ItemVenda Models)
    detalhes = [
        ItemVenda(
            id_item=item.item_id,
            quantidade=item.quantidade,
            valor_unitario=item.valor_unitario,
            id_venda=0 # Será preenchido pelo service
        )
        for item in venda_data.itens
    ]
    
    # 3. Executar a Transação Atômica
    id_venda = venda_service.registrar_venda_completa(cabecalho, detalhes)
    
    if id_venda is None:
        # Se o service retornar None, é porque houve um rollback (estoque ou FK)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A transação falhou. Estoque insuficiente ou dados inválidos."
        )

    return {"message": "Venda registrada com sucesso.", "id_venda": id_venda}

@router.get("/", response_model=List[VendaResponse], status_code=status.HTTP_200_OK)
def listar_vendas(db: DBDependency):
    """Lista todas as vendas registradas no sistema."""
    venda_service = VendaService(db)
    
    vendas = venda_service.buscar_vendas()
    
    if not vendas:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhuma venda registrada.")
        
    # O Pydantic fará a conversão do Dataclass Venda para VendaResponse
    return vendas