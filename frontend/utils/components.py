import os
import streamlit as st

# Fonte única para URL da API com suporte a variável de ambiente do orquestrador
API_BASE_URL = os.getenv("UNYTHON_API_URL", "http://127.0.0.1:8000")


def set_page(page_name: str):
    """Função para alterar o estado da página e navegar no Streamlit."""
    st.session_state["page"] = page_name
