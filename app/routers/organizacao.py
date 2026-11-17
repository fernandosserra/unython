# app/routers/organizacao.py

from fastapi import APIRouter, HTTPException, status, Depends
from src.utils.dependencies import DBDependency, require_role
from src.utils.models import Usuario
from src.modules.organizacao import OrganizacaoService
from src.utils.schemas import OrganizacaoConfigSchema

router = APIRouter(prefix="/organizacao", tags=["Configurações da Organização"])
ADMIN_ONLY = require_role({"Administrador"})


@router.get("/config", response_model=OrganizacaoConfigSchema)
def get_config(db: DBDependency):
    """Retorna os parâmetros de vocabulário e tipo da organização ativa."""
    service = OrganizacaoService(db)
    config = service.obter_configuracoes()
    return OrganizacaoConfigSchema.model_validate(config, from_attributes=True)


@router.put("/config", status_code=status.HTTP_200_OK)
def update_config(
    payload: OrganizacaoConfigSchema,
    db: DBDependency,
    current_user: Usuario = Depends(ADMIN_ONLY),
):
    """Atualiza o vocabulário e tipo da organização (ex: Terreiro, Igreja, Albergue, Clínica)."""
    service = OrganizacaoService(db)
    campos_omitidos = {
        "termo_atividade", "alias_evento", "subtitulo", "registro", "cidade_uf",
        "telefone_contato", "termo_atendente_plural", "termo_atividade_plural",
        "alias_evento_plural", "habilitar_pdv", "habilitar_atendimentos",
        "habilitar_doacoes", "exigir_documento_atendimento",
    } - payload.model_fields_set
    if campos_omitidos:
        atual = service.obter_configuracoes()
        payload = payload.model_copy(update={campo: getattr(atual, campo) for campo in campos_omitidos})
    ok = service.salvar_configuracoes(**payload.model_dump())
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível salvar as configurações da organização.",
        )
    return {"message": "Configurações atualizadas com sucesso!", "config": payload}
