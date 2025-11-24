import streamlit as st
import requests

from utils.components import API_BASE_URL, set_page


def logout():
    st.session_state['auth_token'] = None
    st.session_state['page'] = 'Home'
    st.session_state.pop('pending_password_change', None)
    st.session_state.pop('pending_email', None)
    st.session_state.pop('pending_old_password', None)
    st.rerun()


def _password_change_form(api_base_url: str, email: str, old_password: str):
    st.info("Alteração de senha obrigatória para o primeiro acesso.")
    with st.form("change_password_form"):
        new_password = st.text_input("Nova senha", type="password")
        confirm_password = st.text_input("Confirme a nova senha", type="password")
        submitted = st.form_submit_button("Atualizar senha")
        if submitted:
            if new_password != confirm_password or not new_password:
                st.error("As senhas não conferem ou estão vazias.")
                return
            resp = requests.post(
                f"{api_base_url}/change-password",
                json={
                    "email": email,
                    "old_password": old_password,
                    "new_password": new_password,
                },
            )
            if resp.status_code == 200:
                st.success("Senha atualizada com sucesso. Faça login novamente.")
                st.session_state['pending_password_change'] = False
                st.session_state['auth_token'] = None
                st.session_state['pending_email'] = None
                st.session_state['pending_old_password'] = None
                st.session_state['user_role'] = ''
                st.rerun()
            else:
                st.error("Falha ao atualizar senha. Verifique a senha atual e tente novamente.")


def login_form(api_base_url):
    st.title("Login Unython")

    if 'auth_token' not in st.session_state:
        st.session_state['auth_token'] = None

    if st.session_state.get('pending_password_change') and st.session_state.get('pending_email'):
        _password_change_form(api_base_url, st.session_state['pending_email'], st.session_state.get('pending_old_password', ''))
        return

    if st.session_state['auth_token']:
        st.success("Logado com sucesso!")
        return

    with st.form("login_form"):
        email = st.text_input("Email", placeholder="admin@unython.local")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")

        if submitted:
            login_data = {"username": email, "password": password}
            try:
                response = requests.post(f"{api_base_url}/token", data=login_data)
                if response.status_code == 200:
                    token_data = response.json()
                    if token_data.get("require_password_change"):
                        st.session_state['pending_password_change'] = True
                        st.session_state['pending_email'] = email
                        st.session_state['pending_old_password'] = password
                        st.info("Primeiro acesso: altere a senha para continuar.")
                        st.rerun()
                        return
                    st.session_state['auth_token'] = token_data['access_token']
                    st.session_state['user_id'] = token_data.get('user_id', 1)
                    st.session_state['user_email'] = email
                    st.session_state['user_role'] = token_data.get('role', '')
                    st.success("Login bem-sucedido! Reiniciando...")
                    st.rerun()
                else:
                    st.error("Falha no login: Credenciais inválidas.")
            except requests.exceptions.ConnectionError:
                st.error("Erro de conexão com a API. Certifique-se de que o uvicorn esteja rodando.")


def home_page(set_page_func):
    st.title("Central de Gerenciamento")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Caixa/Vendas", key="btn_vendas", help="Lançamento de vendas e checagem de estoque.", use_container_width=True):
            set_page_func('Vendas')
    with col2:
        if st.button("Ver Relatórios", key="btn_relat", help="Verificar lucro, faturamento e saldo de caixa.", use_container_width=True):
            set_page_func('Relatorios')
    with col3:
        if st.button("Gerenciar Estoque", key="btn_estoque", help="Entrada de produtos e ajuste de inventário.", use_container_width=True):
            set_page_func('Estoque')

    st.markdown("---")
    if st.button("Atendimento / Agendamentos", key="btn_agend_full", use_container_width=True):
        set_page_func('Agendamentos')


def change_password_page(api_base_url: str):
    st.title("Alterar senha")
    email = st.session_state.get('user_email')
    if not email:
        st.error("Email do usuário não encontrado. Faça login novamente.")
        return

    with st.form("change_password_form_logged"):
        old_password = st.text_input("Senha atual", type="password")
        new_password = st.text_input("Nova senha", type="password")
        confirm_password = st.text_input("Confirme a nova senha", type="password")
        submitted = st.form_submit_button("Atualizar senha")
        if submitted:
            if new_password != confirm_password or not new_password:
                st.error("As senhas não conferem ou estão vazias.")
                return
            resp = requests.post(
                f"{api_base_url}/change-password",
                json={"email": email, "old_password": old_password, "new_password": new_password},
            )
            if resp.status_code == 200:
                st.success("Senha atualizada. Faça login novamente.")
                logout()
            else:
                st.error("Falha ao atualizar senha. Verifique a senha atual e tente novamente.")
