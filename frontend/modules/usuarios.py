import streamlit as st
import requests

from utils.components import API_BASE_URL


def usuarios_page(api_base_url: str):
    st.title("Gestão de Usuários")
    auth_token = st.session_state.get("auth_token")
    if not auth_token:
        st.error("Sessão inválida. Faça login.")
        return
    headers = {"Authorization": f"Bearer {auth_token}"}

    st.subheader("Criar usuário")
    with st.form("form_usuario"):
        nome = st.text_input("Nome")
        email = st.text_input("Email")
        funcao = st.text_input("Função", value="Operador")
        role = st.selectbox("Role", ["Administrador", "Operador", "Recepcionista"])
        senha = st.text_input("Senha temporária", type="password")
        require_change = st.checkbox("Exigir troca de senha no primeiro login", value=True)
        submitted = st.form_submit_button("Salvar usuário")
        if submitted:
            payload = {
                "nome": nome,
                "email": email,
                "funcao": funcao,
                "role": role,
                "status": "Ativo",
            }
            resp = requests.post(
                f"{api_base_url}/usuarios/",
                headers={**headers, "Content-Type": "application/json"},
                params={"senha": senha, "require_password_change": require_change},
                json=payload,
            )
            if resp.status_code in (200, 201):
                st.success("Usuário criado/atualizado.")
            else:
                st.error(f"Falha ao salvar usuário: {resp.text}")

    st.markdown("---")
    st.subheader("Usuários cadastrados")
    list_resp = requests.get(f"{api_base_url}/usuarios/", headers=headers)
    if list_resp.status_code == 200:
        for u in list_resp.json():
            st.write(f"- {u.get('nome')} | {u.get('email')} | Role: {u.get('role')} | Status: {u.get('status')}")
    else:
        st.warning("Não foi possível carregar usuários.")
