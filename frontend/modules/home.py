# frontend/pages/home.py
import streamlit as st
import requests
import json
from decimal import Decimal
from utils.components import API_BASE_URL, set_page

# --- FUNÇÕES DE LOGIN/LOGOUT ---

def logout():
    st.session_state['auth_token'] = None
    st.session_state['page'] = 'Home'
    st.rerun()

def login_form(api_base_url):
    """Desenha e processa o formulário de login."""
    st.title("🔐 Login Unython")
    
    # Certifique-se de que os estados existem antes de usá-los
    if 'auth_token' not in st.session_state:
        st.session_state['auth_token'] = None

    if st.session_state['auth_token']:
        st.success("Logado com sucesso!")
        return
    
    with st.form("login_form"):
        email = st.text_input("Email (e.g., washu@unython.com)")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")
        
        if submitted:
            login_data = {
                "username": email,
                "password": password
            }
            
            try:
                # O AuthRouter espera dados de formulário POST
                response = requests.post(
                    f"{api_base_url}/token",
                    data=login_data 
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    st.session_state['auth_token'] = token_data['access_token']
                    st.session_state['user_id'] = 1 # Simulação, no futuro virá do JWT
                    st.success("Login bem-sucedido! Reiniciando...")
                    st.rerun()
                else:
                    st.error("Falha no login: Credenciais inválidas.")
                    
            except requests.exceptions.ConnectionError:
                st.error("Erro de conexão com a API. Certifique-se de que o uvicorn esteja rodando.")

# --- HOMEPAGE MODULAR ---

def home_page(set_page_func):
    """Desenha a homepage com os botões de navegação grandes."""
    st.title("🏡 Central de Gerenciamento")
    
    # Criamos 3 colunas para garantir que mesmo em telas largas os botões sejam grandes
    col1, col2, col3 = st.columns(3) 
    
    # --- COLUNA 1: Vendas e Agendamentos ---
    with col1:
        # Botão Vendas: Usa \n para dar espaçamento vertical
        if st.button("🛒\nREGISTRAR VENDA", key="btn_vendas", 
                     help="Lançamento de vendas e checagem de estoque.", 
                     use_container_width=True):
            set_page_func('Vendas')
            
    with col2:
        # Botão Relatórios
        if st.button("📊\nVER RELATÓRIOS", key="btn_relat",
                     help="Verificar lucro, faturamento e saldo de caixa.",
                     use_container_width=True):
            set_page_func('Relatorios')
            
    with col3:
        # Botão Estoque
        if st.button("📦\nGERENCIAR ESTOQUE", key="btn_estoque",
                     help="Entrada de produtos e ajuste de inventário.",
                     use_container_width=True):
            set_page_func('Estoque')
            
    # Adicionamos uma linha separada para agendamentos (opcional)
    st.markdown("---")
    if st.button("📅 Atendimento / Agendamentos", key="btn_agend_full", use_container_width=True):
         set_page_func('Agendamentos')