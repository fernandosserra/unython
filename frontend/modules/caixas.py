import streamlit as st
import requests

from utils.components import API_BASE_URL

def caixas_page(api_base_url: str):
    st.title("Gestão de Caixas")
    auth_token = st.session_state.get('auth_token')
    if not auth_token:
        st.error("Sessão inválida. Faça login.")
        return
    headers = {"Authorization": f"Bearer {auth_token}"}

    st.subheader("Criar novo caixa")
    with st.form("criar_caixa_form"):
        nome = st.text_input("Nome do caixa")
        descricao = st.text_input("Descrição")
        submitted = st.form_submit_button("Criar")
        if submitted:
            resp = requests.post(
                f"{api_base_url}/caixas/",
                headers=headers,
                json={"nome": nome, "descricao": descricao, "status": "Ativo"},
            )
            if resp.status_code == 201:
                st.success("Caixa criado.")
            else:
                st.error(f"Falha ao criar caixa: {resp.text}")

    st.markdown("---")
    st.subheader("Caixas existentes")
    resp_list = requests.get(f"{api_base_url}/caixas/", headers=headers)
    if resp_list.status_code == 200:
        for c in resp_list.json():
            st.write(f"ID {c.get('id')}: {c.get('nome')} - {c.get('status')}")
    else:
        st.error("Falha ao carregar caixas.")
