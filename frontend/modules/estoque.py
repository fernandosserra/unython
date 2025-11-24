import streamlit as st
import requests
from utils.components import API_BASE_URL


def estoque_page(api_base_url: str):
    st.title("Gestão de Estoque")
    auth_token = st.session_state.get("auth_token")
    user_id = st.session_state.get("user_id")
    if not auth_token:
        st.error("Sessão inválida. Faça login.")
        return
    headers = {"Authorization": f"Bearer {auth_token}"}

    itens_resp = requests.get(f"{api_base_url}/catalogo/itens", headers=headers)
    itens = itens_resp.json() if itens_resp.status_code == 200 else []
    item_options = {f"{i.get('id')} - {i.get('nome')}": i.get("id") for i in itens}
    selected_label = st.selectbox("Selecione o item", list(item_options.keys())) if item_options else None
    selected_item = item_options.get(selected_label) if selected_label else None

    tipo_mov = st.selectbox("Tipo de movimento", ["Entrada", "Saida"])
    quantidade = st.number_input("Quantidade", min_value=1, value=1, step=1)
    origem = st.text_input("Origem/Observação", value="Ajuste")
    evento_id = st.number_input("ID do evento/dia", min_value=1, value=1, step=1)

    if st.button("Registrar movimento de estoque", use_container_width=True):
        if not selected_item:
            st.error("Selecione um item.")
        else:
            payload = {
                "itemId": selected_item,
                "quantidade": quantidade,
                "origem_recurso": origem,
                "usuarioId": user_id,
                "eventoId": evento_id,
            }
            url = f"{api_base_url}/estoque/entrada" if tipo_mov == "Entrada" else f"{api_base_url}/estoque/saida"
            resp = requests.post(
                url, headers={**headers, "Content-Type": "application/json"}, json=payload
            )
            if resp.status_code in (200, 201):
                st.success("Movimento registrado.")
            else:
                st.error(f"Falha ao registrar movimento. Código: {resp.status_code} - {resp.text}")
