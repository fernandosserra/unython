import streamlit as st
import requests

from utils.components import API_BASE_URL

ROLE_OPTIONS = ["Administrador", "Operador", "Recepcionista"]


def usuarios_page(api_base_url: str):
    st.title("Gestão de Usuários")
    auth_token = st.session_state.get("auth_token")
    role = (st.session_state.get("user_role") or "").lower()
    if not auth_token:
        st.error("Sessão inválida. Faça login.")
        return
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Form de criação/edição rápida (reaproveita endpoint de criação)
    st.subheader("Criar usuário")
    with st.form("form_usuario"):
        nome = st.text_input("Nome")
        email = st.text_input("Email")
        funcao = st.text_input("Função interna", value="Operador")
        cargo = st.selectbox("Função (cargo)", ROLE_OPTIONS)
        senha = st.text_input("Senha temporária", type="password")
        require_change = st.checkbox("Exigir troca de senha no primeiro login", value=True)
        submitted = st.form_submit_button("Salvar usuário")
        if submitted:
            payload = {
                "nome": nome,
                "email": email,
                "funcao": funcao,
                "role": cargo,
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
            with st.expander(f"{u.get('nome')} | {u.get('email')}"):
                st.write(f"Status: {u.get('status')}")
                st.write(f"Função interna: {u.get('funcao')}")
                st.write(f"Função (cargo): {u.get('role')}")
                if role == "administrador":
                    nova_funcao = st.text_input(f"Função interna_{u.get('id')}", value=u.get('funcao') or u.get('role'))
                    novo_cargo = st.selectbox(
                        f"Função (cargo)_{u.get('id')}", ROLE_OPTIONS, index=ROLE_OPTIONS.index(u.get('role')) if u.get('role') in ROLE_OPTIONS else 0
                    )
                    novo_status = st.selectbox(
                        f"Status_{u.get('id')}", ["Ativo", "Inativo"], index=0 if u.get('status') == "Ativo" else 1
                    )
                    if st.button(f"Salvar alterações_{u.get('id')}", use_container_width=True):
                        upd = requests.put(
                            f"{api_base_url}/usuarios/{u.get('id')}/role",
                            headers={**headers, "Content-Type": "application/json"},
                            json={"role": novo_cargo, "status": novo_status, "funcao": nova_funcao},
                        )
                        if upd.status_code in (200, 201):
                            st.success("Atualizado.")
                        else:
                            st.error(f"Falha ao atualizar: {upd.text}")
                else:
                    st.info("Apenas administradores podem promover/demover.")
    else:
        st.warning("Não foi possível carregar usuários.")
