from fastapi import APIRouter, HTTPException, status
from datetime import date
from typing import List, Optional

from src.utils.dependencies import DBDependency
from src.modules.evento import EventoService
from src.utils.models import Evento

router = APIRouter(prefix="/eventos", tags=["Eventos"])


@router.get("/aberto")
def evento_aberto(db: DBDependency):
    service = EventoService(db)
    ev = service.buscar_evento_aberto()
    if not ev:
        raise HTTPException(status_code=404, detail="Nenhum evento aberto.")
    return ev.__dict__


@router.get("/")
def listar_eventos(db: DBDependency, data_inicio: Optional[date] = None, data_fim: Optional[date] = None) -> List[dict]:
    service = EventoService(db)
    eventos = service.buscar_eventos(data_inicio, data_fim)
    return [e.__dict__ for e in eventos]


@router.post("/abrir", status_code=status.HTTP_201_CREATED)
def abrir_evento(nome: str = None, tipo: str = "Operacao", db: DBDependency = None):
    """Abre um evento/dia de trabalho; se já houver aberto, retorna-o."""
    service = EventoService(db)
    aberto = service.buscar_evento_aberto()
    if aberto:
        return aberto.__dict__
    hoje = date.today()
    nome_final = nome or f"Operacao {hoje}"
    ev = Evento(nome=nome_final, data_evento=hoje, tipo=tipo)
    ev_id = service.registrar_evento(ev)
    return {"id": ev_id, "nome": nome_final, "data_evento": str(hoje), "tipo": tipo}


@router.post("/{evento_id}/fechar")
def fechar_evento(evento_id: int, db: DBDependency):
    """Fecha um evento aberto."""
    service = EventoService(db)
    ok = service.fechar_evento(evento_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Não foi possível fechar o evento.")
    return {"status": "fechado", "id": evento_id}
