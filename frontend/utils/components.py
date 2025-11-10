# frontend/utils.py

import streamlit as st

# --- CONFIGURAÇÃO DE BASE (Constante que home.py precisa) ---
API_BASE_URL = "http://127.0.0.1:8000"

# --- FUNÇÃO DE NAVEGAÇÃO ---
# Esta função (setter) DEVE estar em um módulo neutro para que home.py e interface.py possam usá-la.
def set_page(page_name):
    """Função para alterar o estado da página e forçar o rerender."""
    st.session_state['page'] = page_name