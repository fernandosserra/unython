# app/routers/organizacao.py

from fastapi import APIRouter, HTTPException, status, Depends
from src.utils.dependencies import DBDependency
from src.modules.organizacao import OrganizacaoService
from src.utils.schemas import OrganizacaoConfigSchema

router = APIRouter(prefix="/organizacao", tags=["Configurações da Organização"])


@router.get("/config", response_model=OrganizacaoConfigSchema)
def get_config(db: DBDependency):
    """Retorna os parâmetros de vocabulário e tipo da organização ativa."""
    service = OrganizacaoService(db)
    config = service.obter_configuracoes()
    return OrganizacaoConfigSchema(
        nome_organizacao=config.nome_organizacao,
        tipo_organizacao=config.tipo_organizacao,
        termo_assistido=config.termo_assistido,
        termo_assistido_plural=config.termo_assistido_plural,
        termo_atendente=config.termo_atendente,
        termo_servico=config.termo_servico,
        termo_atividade=config.termo_atividade,
    )


@router.put("/config", status_code=status.HTTP_200_OK)
def update_config(payload: OrganizacaoConfigSchema, db: DBDependency):
    """Atualiza o vocabulário e tipo da organização (ex: Terreiro, Igreja, Albergue, Clínica)."""
    service = OrganizacaoService(db)
    if "termo_atividade" not in payload.model_fields_set:
        payload = payload.model_copy(update={"termo_atividade": service.obter_configuracoes().termo_atividade})
    ok = service.salvar_configuracoes(
        nome_organizacao=payload.nome_organizacao,
        tipo_organizacao=payload.tipo_organizacao,
        termo_assistido=payload.termo_assistido,
        termo_assistido_plural=payload.termo_assistido_plural,
        termo_atendente=payload.termo_atendente,
        termo_servico=payload.termo_servico,
        termo_atividade=payload.termo_atividade,
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível salvar as configurações da organização.",
        )
    return {"message": "Configurações atualizadas com sucesso!", "config": payload}
