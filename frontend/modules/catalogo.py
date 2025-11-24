import streamlit as st
import requests
from utils.components import API_BASE_URL


def catalogo_page(api_base_url: str):
    st.title("Catálogo")
    auth_token = st.session_state.get('auth_token')
    if not auth_token:
        st.error("Sessão inválida. Faça login.")
        return
    headers = {"Authorization": f"Bearer {auth_token}"}

    st.subheader("Criar Categoria")
    with st.form("form_categoria"):
        nome_cat = st.text_input("Nome da categoria")
        desc_cat = st.text_input("Descrição")
        submitted = st.form_submit_button("Salvar categoria")
        if submitted:
            resp = requests.post(f"{api_base_url}/catalogo/categorias", headers=headers, json={"nome": nome_cat, "descricao": desc_cat, "status": "Ativo"})
            if resp.status_code in (200, 201):
                st.success("Categoria salva.")
            else:
                st.error("Falha ao salvar categoria.")

    st.markdown("---")
    st.subheader("Criar Item")
    cats_resp = requests.get(f"{api_base_url}/catalogo/categorias", headers=headers)
    cats = cats_resp.json() if cats_resp.status_code == 200 else []
    cat_options = {f"{c.get('id')} - {c.get('nome')}": c.get('id') for c in cats}
    selected_cat_label = st.selectbox("Categoria", list(cat_options.keys())) if cat_options else None
    selected_cat = cat_options.get(selected_cat_label) if selected_cat_label else None
    with st.form("form_item"):
        nome_item = st.text_input("Nome do item")
        valor_compra = st.number_input("Valor de compra", min_value=0.0, value=0.0, step=0.5)
        valor_venda = st.number_input("Valor de venda", min_value=0.0, value=0.0, step=0.5)
        submitted = st.form_submit_button("Salvar item")
        if submitted:
            if not selected_cat:
                st.error("Selecione uma categoria.")
            else:
                payload = {
                    "nome": nome_item,
                    "valor_compra": valor_compra,
                    "valor_venda": valor_venda,
                    "id_categoria": selected_cat,
                    "status": "Ativo",
                }
                resp = requests.post(f"{api_base_url}/catalogo/itens", headers=headers, json=payload)
                if resp.status_code in (200, 201):
                    st.success("Item salvo.")
                else:
                    st.error("Falha ao salvar item.")

    st.markdown("---")
    st.subheader("Categorias e Itens")
    grupos_resp = requests.get(f"{api_base_url}/catalogo/grupos", headers=headers)
    if grupos_resp.status_code == 200:
        grupos = grupos_resp.json()
        for cat, itens in grupos.items():
            st.write(f"### {cat}")
            for it in itens:
                st.write(f"- {it.get('nome')} (R$ {it.get('valor_venda')})")
    else:
        st.warning("Não foi possível carregar o catálogo.")