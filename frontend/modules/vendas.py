# frontend/modules/vendas.py

import streamlit as st
import requests
import json
from decimal import Decimal
from typing import Dict, Any, List

# Importações de Infraestrutura (Ajuste a importação se seu utils.py estiver em outro lugar)
# Assumindo que set_page e API_BASE_URL estão em 'frontend.utils' (ou equivalente)
from utils.components import API_BASE_URL, set_page 

# --- FUNÇÕES DE DADOS (Catálogo) ---

@st.cache_data(ttl=300) # Cache por 5 minutos
def get_item_catalog(auth_token: str) -> List[Dict[str, Any]]:
    """Busca o catálogo de itens da API (GET /estoque/itens) usando o token."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    try:
        response = requests.get(f"{API_BASE_URL}/estoque/itens", headers=headers)
        if response.status_code == 200:
            return response.json() 
        st.error(f"Falha ao carregar catálogo: {response.status_code}. Token inválido?")
        return []
    except requests.exceptions.ConnectionError:
        st.error("Erro de conexão com a API. O servidor FastAPI está rodando?")
        return []

def get_item_data_map(catalog: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """Cria um mapa seguro de ID -> Item Completo."""
    return {item['id']: item for item in catalog}


# --- FUNÇÕES DE MANIPULAÇÃO DO CARRINHO ---

def update_cart(item_id: int, item_name: str, item_price: float, delta_quantity: int):
    """
    Adiciona ou remove a quantidade de um item no carrinho usando argumentos explícitos.
    """
    if 'cart' not in st.session_state:
        st.session_state['cart'] = {}
        
    current_quantity = st.session_state['cart'].get(item_id, {}).get('quantity', 0)
    new_quantity = max(0, current_quantity + delta_quantity) 

    if new_quantity > 0:
        st.session_state['cart'][item_id] = {
            'name': item_name,
            'price': item_price,
            'quantity': new_quantity
        }
    elif item_id in st.session_state['cart']:
        del st.session_state['cart'][item_id]
    
    st.rerun()

def clear_cart():
    st.session_state['cart'] = {}
    st.rerun()

# --- FUNÇÃO CRÍTICA: POST DE VENDA ---

def post_sale(auth_token: str, user_id: int):
    """Formata o carrinho e envia a requisição POST para a API /vendas."""
    
    cart = st.session_state.get('cart', {})
    if not cart:
        st.error("Erro: O carrinho está vazio.")
        return False

    # 1. Formata o payload para o endpoint POST /vendas
    venda_payload = {
        "eventoId": 1, # FIXO para MVP, pois não temos um seletor de evento
        "responsavelId": user_id,
        "pessoaId": 1, # FIXO para MVP (Fernando, O Aprendiz)
        "itens": []
    }
    
    for item_id, item_data in cart.items():
        # Converte o Decimal (price) para float para a transmissão JSON
        item_price_float = float(item_data['price']) 
        
        venda_payload['itens'].append({
            "itemId": item_id,
            "quantidade": item_data['quantity'],
            "valor_unitario": item_price_float
        })

    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }

    try:
        # 2. Faz a requisição POST
        response = requests.post(
            f"{API_BASE_URL}/vendas",
            headers=headers,
            json=venda_payload
        )
        
        # 3. Trata a resposta
        if response.status_code == 200 or response.status_code == 201:
            st.success("✅ Venda registrada com sucesso!")
            clear_cart() 
            return True
        else:
            # Captura a mensagem de erro (ex: Estoque Insuficiente)
            error_detail = response.json().get('detail', f"Falha desconhecida. Código: {response.status_code}")
            st.error(f"Falha ao finalizar venda: {error_detail}")
            return False

    except requests.exceptions.ConnectionError:
        st.error("Erro de conexão com a API. Verifique o servidor FastAPI.")
        return False


# --- LAYOUT E RENDERIZAÇÃO (FUNÇÕES AUXILIARES - DEFINIDAS ANTES DA CHAMADA) ---

def render_item_buttons(catalog: List[Dict[str, Any]]):
    """Renderiza os botões de seleção de produtos."""
    st.subheader("1. Seleção Rápida de Produtos")
    
    # Usamos 3 colunas para garantir responsividade.
    cols = st.columns(3)
    
    for index, item in enumerate(catalog):
        col = cols[index % 3] 
        
        # Botão Principal do Produto
        if col.button(f"🛒 {item['nome']}\n(R$ {item['valor_venda']:.2f})", 
                      key=f"item_btn_{item['id']}", 
                      use_container_width=True):
            # Ação: Adiciona 1 item (usando os dados do catálogo)
            update_cart(item['id'], item['nome'], item['valor_venda'], 1)

def render_quantity_controls(item_data_map: Dict[int, Dict[str, Any]]):
    """Renderiza os botões de ajuste de quantidade e o display de item selecionado."""
    st.subheader("2. Ajuste de Quantidade Rápido")
    
    cart = st.session_state.get('cart', {})
    if not cart:
        st.info("Carrinho vazio. Selecione um produto para ajustar a quantidade.")
        return

    # Foca no item mais recentemente adicionado
    last_item_id = list(cart.keys())[-1]
    cart_item = cart[last_item_id]
    
    st.markdown(f"**Ajustando:** **{cart_item['name']}** (Qtde atual: {cart_item['quantity']})")
    
    q_cols = st.columns(4) 
    
    # Botões de Ajuste Rápido (Soma/Subtração)
    if q_cols[0].button("+1", key="q_plus_1", use_container_width=True):
        update_cart(last_item_id, cart_item['name'], cart_item['price'], 1)
    if q_cols[1].button("+5", key="q_plus_5", use_container_width=True):
        update_cart(last_item_id, cart_item['name'], cart_item['price'], 5)
    if q_cols[2].button("-1", key="q_minus_1", use_container_width=True):
        update_cart(last_item_id, cart_item['name'], cart_item['price'], -1)
    if q_cols[3].button("Zerar", key="q_zero", use_container_width=True):
        update_cart(last_item_id, cart_item['name'], cart_item['price'], -cart_item['quantity'])
        
def render_cart_summary(catalog: List[Dict[str, Any]]):
    """Renderiza a lista de itens no carrinho, total e o botão de checkout."""
    st.subheader("3. Carrinho de Compras")
    
    cart = st.session_state.get('cart', {})
    if not cart:
        st.info("Nenhum item no carrinho.")
        return
        
    total_value = Decimal(0)
    
    st.markdown("---")
    
    # Renderiza cada item
    for item_id, item_data in cart.items():
        subtotal = Decimal(item_data['quantity']) * Decimal(item_data['price'])
        total_value += subtotal
        
        st.markdown(f"**{item_data['quantity']}x {item_data['name']}** *(R$ {subtotal:.2f})*")

    st.markdown("---")
    st.metric(label="Total a Pagar", value=f"R$ {total_value:.2f}")
    
    # Botão de Checkout (Ligado ao POST)
    if st.button("✅ FINALIZAR VENDA", key="btn_checkout", use_container_width=True, type="primary"):
        auth_token = st.session_state.get('auth_token')
        user_id = st.session_state.get('user_id')
        
        if auth_token and user_id:
            # Chama a função de postagem ao clicar
            post_sale(auth_token, user_id) 
        else:
            st.error("Sessão inválida. Por favor, refaça o login.")

# ------------------------------------------------------------------

def vendas_page():
    """Função principal do módulo de vendas."""
    st.title("🛒 PDV - Ponto de Venda Rápida")
    
    auth_token = st.session_state.get('auth_token')
    if not auth_token:
        st.error("Erro de sessão: Token não encontrado. Faça login novamente.")
        return

    # A função de catálogo requer o token para autenticação GET
    catalog = get_item_catalog(auth_token)
    
    if not catalog:
        return
        
    item_data_map = get_item_data_map(catalog)

    # Layout de duas colunas (Produtos + Controles | Carrinho)
    left_col, right_col = st.columns([2, 1]) 
    
    with left_col:
        render_item_buttons(catalog) # CHAMADA CORRETA
        st.markdown("---")
        render_quantity_controls(item_data_map) # CHAMADA CORRETA
        
    with right_col:
        render_cart_summary(catalog)