# Unython - (C) 2025 siegrfried@gmail.com
# Este programa e software livre: voce pode redistribui-lo e/ou modifica-lo
# sob os termos da GNU General Public License como publicada pela Free Software Foundation,
# na versao 3 da Licenca, ou (a seu criterio) qualquer versao posterior.
# frontend/interface.py
import streamlit as st

# Fonte única para URL da API
from utils.components import API_BASE_URL, set_page

# Páginas
from modules.home import home_page, login_form, logout, change_password_page
from modules.caixas import caixas_page
from modules.movimentos import movimentos_page
from modules.vendas import vendas_page


def main_app():
    # Estado inicial
    if "auth_token" not in st.session_state:
        st.session_state["auth_token"] = None
    if "page" not in st.session_state:
        st.session_state["page"] = "Home"
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = 1

    # Autenticação
    if not st.session_state["auth_token"]:
        login_form(API_BASE_URL)
        return

    # Painel lateral
    st.sidebar.title("Unython")
    st.sidebar.markdown(f"**Usuário ID:** {st.session_state['user_id']}")
    st.sidebar.button("Voltar para Home", on_click=lambda: set_page("Home"), use_container_width=True)
    st.sidebar.button("Alterar senha", on_click=lambda: set_page("ChangePassword"), use_container_width=True)
    role = st.session_state.get("user_role", "")
    if role == "Administrador":
        st.sidebar.button("Gestão de Caixas", on_click=lambda: set_page("Caixas"), use_container_width=True)
        st.sidebar.button("Movimentos", on_click=lambda: set_page("Movimentos"), use_container_width=True)
    st.sidebar.button("Sair", on_click=logout, use_container_width=True)
    st.sidebar.markdown("---")

    # Roteamento simples
    if st.session_state["page"] == "Home":
        home_page(set_page)
    elif st.session_state["page"] == "Vendas":
        vendas_page()
    elif st.session_state["page"] == "Relatorios":
        st.title("Módulo de Relatórios (Em Construção)")
    elif st.session_state["page"] == "ChangePassword":
        change_password_page(API_BASE_URL)
    elif st.session_state["page"] == "Caixas":
        caixas_page(API_BASE_URL)
    elif st.session_state["page"] == "Movimentos":
        movimentos_page(API_BASE_URL)
    # ... outros módulos


if __name__ == "__main__":
    main_app()
