# frontend/interface.py
import sys
import os
import streamlit as st
import requests
import json
from decimal import Decimal

# Importa as funções auxiliares
from utils.components import set_page, API_BASE_URL

# Importa as funções de página da nova pasta 'pages'
from modules.home import home_page, login_form, logout
from modules.vendas import vendas_page
# from frontend.pages.vendas import vendas_page # Será implementado depois

# --- CONFIGURAÇÃO DE BASE ---
API_BASE_URL = "http://127.0.0.1:8000" 

# --- FUNÇÕES GLOBAIS DE ESTADO/NAVEGAÇÃO ---

def main_app():
    # 1. Inicializa o controle de estado
    if 'auth_token' not in st.session_state:
        st.session_state['auth_token'] = None
    if 'page' not in st.session_state:
        st.session_state['page'] = 'Home'
    if 'user_id' not in st.session_state:
        st.session_state['user_id'] = 1 

    # 2. AUTENTICAÇÃO
    if not st.session_state['auth_token']:
        login_form(API_BASE_URL) # Passamos a URL para o módulo de login
        return

    # 3. PAINEL LATERAL (Fixo)
    st.sidebar.title("Unython")
    st.sidebar.markdown(f"**Usuário ID:** {st.session_state['user_id']}")
    st.sidebar.button("Voltar para Home", on_click=lambda: set_page('Home'), use_container_width=True)
    st.sidebar.button("Sair", on_click=logout, use_container_width=True)
    st.sidebar.markdown("---")
    
    # 4. ROTEAMENTO
    if st.session_state['page'] == 'Home':
        # Passamos o set_page para que os botões de home.py possam navegar
        home_page(set_page)
    elif st.session_state['page'] == 'Vendas':
        vendas_page()
    elif st.session_state['page'] == 'Relatorios':
        st.title("📈 Módulo de Relatórios (Em Construção)")
    # ... outros módulos
    
if __name__ == "__main__":
    main_app()