import streamlit as st
import requests
from utils.components import API_BASE_URL


def movimentos_page(api_base_url: str):
    st.title("Movimentos de Caixa")
    auth_token = st.session_state.get('auth_token')
    user_id = st.session_state.get('user_id')
    if not auth_token:
        st.error("Sessão inválida. Faça login.")
        return
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Evento ativo
    evento_resp = requests.get(f"{api_base_url}/eventos/aberto", headers=headers)
    evento = evento_resp.json() if evento_resp.status_code == 200 else None
    if not evento:
        st.warning("Nenhum evento/dia aberto. Abra um antes.")
        if st.button("Abrir evento/dia", use_container_width=True):
            open_ev = requests.post(f"{api_base_url}/eventos/abrir", headers=headers)
            if open_ev.status_code in (200, 201):
                st.success("Evento aberto. Recarregue a página.")
                st.rerun()
        return
    st.info(f"Evento aberto: {evento.get('nome')} (ID {evento.get('id')})")

    caixas_resp = requests.get(f"{api_base_url}/caixas/", headers=headers)
    caixas = caixas_resp.json() if caixas_resp.status_code == 200 else []
    caixa_options = {f"{c.get('id')} - {c.get('nome')}": c.get('id') for c in caixas}
    selected_label = st.selectbox("Selecione um caixa", list(caixa_options.keys())) if caixa_options else None
    selected_caixa = caixa_options.get(selected_label) if selected_label else None

    if not selected_caixa:
        st.info("Crie um caixa antes.")
        return

    st.markdown("---")
    st.subheader("Movimento atual")
    mov_resp = requests.get(f"{api_base_url}/caixas/{selected_caixa}/movimento-ativo", headers=headers)
    if mov_resp.status_code == 200:
        mov = mov_resp.json()
        st.success(f"Movimento ABERTO ID {mov.get('id')} - Valor abertura: {mov.get('valor_abertura')}")
        if st.button("Fechar movimento", use_container_width=True):
            close_resp = requests.post(f"{api_base_url}/caixas/{mov.get('id')}/fechar", headers=headers)
            if close_resp.status_code == 200:
                st.success("Movimento fechado.")
                st.rerun()
            else:
                st.error("Falha ao fechar movimento.")
    else:
        st.warning("Nenhum movimento aberto.")
        valor = st.number_input("Valor de abertura", min_value=0.0, value=0.0, step=10.0)
        if st.button("Abrir movimento", use_container_width=True):
            params = {"usuario_id": user_id, "valor_abertura": valor, "id_evento": evento.get('id')}
            open_resp = requests.post(
                f"{api_base_url}/caixas/{selected_caixa}/abrir",
                headers=headers,
                params=params,
            )
            if open_resp.status_code in (200, 201):
                st.success("Movimento aberto.")
                st.rerun()
            else:
                st.error("Falha ao abrir movimento.")
