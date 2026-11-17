from fastapi import APIRouter, HTTPException, Request, status, Depends
from typing import List, Optional

from src.utils.dependencies import DBDependency, require_role
from src.utils.audit import record_audit
from src.modules.usuario import UsuarioService
from src.utils.models import Usuario
from src.utils.schemas import UsuarioResponse, UsuarioCreate, UsuarioUpdate, RoleUpdate, PermissoesUpdate

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

ADMIN_ONLY = require_role({"Administrador"})


@router.get("/", response_model=List[UsuarioResponse])
def listar_usuarios(
    db: DBDependency,
    current_user: Usuario = Depends(ADMIN_ONLY),
):
    """Lista todos os usuários sem expor hashes de senha."""
    service = UsuarioService(db)
    usuarios = service.buscar_usuarios()
    return [
        UsuarioResponse(
            id=u.id,
            nome=u.nome,
            email=u.email,
            funcao=u.funcao,
            role=u.role,
            status=u.status,
            require_password_change=u.require_password_change,
            permissoes=u.permissoes,
        )
        for u in usuarios
    ]


@router.post("/", status_code=status.HTTP_201_CREATED)
def criar_usuario(
    payload: UsuarioCreate,
    db: DBDependency,
    request: Request,
    current_user: Usuario = Depends(ADMIN_ONLY),
):
    """Cria um novo usuário recebendo as credenciais de forma segura no corpo JSON."""
    service = UsuarioService(db)
    usuario = Usuario(
        nome=payload.nome,
        email=payload.email,
        funcao=payload.funcao or "Operador",
        role=payload.role,
        status=payload.status,
        require_password_change=payload.require_password_change,
        permissoes=payload.permissoes,
    )
    try:
        existente = service.buscar_usuario_por_email(payload.email)
        if existente:
            db.execute_query("SELECT id FROM usuarios WHERE id = %s FOR UPDATE", (existente.id,), fetch_one=True)
            existente = service.buscar_usuario_por_id(existente.id)
            if not existente:
                raise HTTPException(status_code=409, detail="Usuário foi alterado; tente novamente.")
        uid = service.registrar_usuario(
            usuario,
            payload.senha,
            require_password_change=payload.require_password_change,
            commit=False,
            update_existing=bool(existente),
        )
        if not uid:
            raise HTTPException(status_code=400, detail="Não foi possível criar/atualizar usuário.")
        if existente and "permissoes" in payload.model_fields_set:
            if not service.atualizar_permissoes(uid, payload.permissoes, commit=False):
                raise HTTPException(status_code=400, detail="Não foi possível atualizar permissões.")
        anterior_permissoes = existente.permissoes if existente else None
        if payload.permissoes != anterior_permissoes and "permissoes" in payload.model_fields_set:
            record_audit(db, user_id=current_user.id, acao="alterar_permissoes",
                         entidade="usuario", entidade_id=uid,
                         detalhes={"permissoes_anteriores": anterior_permissoes, "permissoes_novas": payload.permissoes},
                         request_id=request.state.request_id)
        if existente:
            record_audit(db, user_id=current_user.id, acao="atualizar_usuario_existente",
                         entidade="usuario", entidade_id=uid,
                         detalhes={"role_anterior": existente.role, "role_nova": payload.role,
                                   "status_anterior": existente.status, "status_novo": existente.status},
                         request_id=request.state.request_id)
        db.conn.commit()
    except Exception:
        db.conn.rollback()
        raise
    return {"id": uid}


@router.put("/{user_id}")
def atualizar_usuario(
    user_id: int,
    payload: UsuarioUpdate,
    db: DBDependency,
    request: Request,
    current_user: Usuario = Depends(ADMIN_ONLY),
):
    """Atualiza papel, função, status e permissões em uma única transação."""
    service = UsuarioService(db)
    try:
        db.execute_query("SELECT id FROM usuarios WHERE id = %s FOR UPDATE", (user_id,), fetch_one=True)
        anterior = service.buscar_usuario_por_id(user_id)
        if not anterior:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        funcao = payload.funcao or payload.role
        if not service.atualizar_role_status(user_id, payload.role, payload.status, funcao, commit=False):
            raise HTTPException(status_code=400, detail="Não foi possível atualizar usuário.")
        if not service.atualizar_permissoes(user_id, payload.permissoes, commit=False):
            raise HTTPException(status_code=400, detail="Não foi possível atualizar permissões.")
        record_audit(db, user_id=current_user.id, acao="alterar_role_status",
                     entidade="usuario", entidade_id=user_id,
                     detalhes={"role_anterior": anterior.role, "role_nova": payload.role,
                               "status_anterior": anterior.status, "status_novo": payload.status,
                               "funcao_anterior": anterior.funcao, "funcao_nova": funcao},
                     request_id=request.state.request_id)
        if anterior.permissoes != payload.permissoes:
            record_audit(db, user_id=current_user.id, acao="alterar_permissoes",
                         entidade="usuario", entidade_id=user_id,
                         detalhes={"permissoes_anteriores": anterior.permissoes,
                                   "permissoes_novas": payload.permissoes},
                         request_id=request.state.request_id)
        db.conn.commit()
    except Exception:
        db.conn.rollback()
        raise
    return {"id": user_id, "role": payload.role, "status": payload.status, "permissoes": payload.permissoes}


@router.put("/{user_id}/role")
def atualizar_role(
    user_id: int,
    payload: RoleUpdate,
    db: DBDependency,
    request: Request,
    current_user: Usuario = Depends(ADMIN_ONLY),
):
    """Atualiza o papel e status do usuário."""
    service = UsuarioService(db)
    try:
        db.execute_query("SELECT id FROM usuarios WHERE id = %s FOR UPDATE", (user_id,), fetch_one=True)
        anterior = service.buscar_usuario_por_id(user_id)
        if not anterior:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        ok = service.atualizar_role_status(
            user_id, payload.role, payload.status, payload.funcao or payload.role, commit=False
        )
        if not ok:
            raise HTTPException(status_code=400, detail="Não foi possível atualizar usuário.")
        record_audit(db, user_id=current_user.id, acao="alterar_role_status",
                     entidade="usuario", entidade_id=user_id,
                     detalhes={"role_anterior": anterior.role, "role_nova": payload.role,
                               "status_anterior": anterior.status, "status_novo": payload.status,
                               "funcao_anterior": anterior.funcao, "funcao_nova": payload.funcao or payload.role},
                     request_id=request.state.request_id)
        db.conn.commit()
    except Exception:
        db.conn.rollback()
        raise
    return {"id": user_id, "role": payload.role, "status": payload.status}


@router.put("/{user_id}/permissoes")
def atualizar_permissoes(
    user_id: int,
    payload: PermissoesUpdate,
    db: DBDependency,
    request: Request,
    current_user: Usuario = Depends(ADMIN_ONLY),
):
    service = UsuarioService(db)
    try:
        db.execute_query("SELECT id FROM usuarios WHERE id = %s FOR UPDATE", (user_id,), fetch_one=True)
        anterior = service.buscar_usuario_por_id(user_id)
        if not anterior:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        if not service.atualizar_permissoes(user_id, payload.permissoes, commit=False):
            raise HTTPException(status_code=400, detail="Não foi possível atualizar permissões.")
        record_audit(db, user_id=current_user.id, acao="alterar_permissoes",
                     entidade="usuario", entidade_id=user_id,
                     detalhes={"permissoes_anteriores": anterior.permissoes, "permissoes_novas": payload.permissoes},
                     request_id=request.state.request_id)
        db.conn.commit()
    except Exception:
        db.conn.rollback()
        raise
    return {"id": user_id, "permissoes": payload.permissoes}
