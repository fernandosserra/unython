import streamlit as st
import requests
from decimal import Decimal
from typing import Dict, Any, List
from utils.components import API_BASE_URL, set_page


@st.cache_data(ttl=300)
def get_grouped_catalog(auth_token: str) -> Dict[str, List[Dict[str, Any]]]:
    GRUPO_ENDPOINT = f"{API_BASE_URL}/catalogo/grupos"
    headers = {"Authorization": f"Bearer {auth_token}"}
    try:
        response = requests.get(GRUPO_ENDPOINT, headers=headers)
        if response.status_code == 200:
            return response.json()
        st.error(f"Falha ao carregar catálogo. Código: {response.status_code}.")
        return {}
    except requests.exceptions.ConnectionError:
        st.error("Erro de conexão com a API.")
        return {}


def get_item_data_map(grouped_catalog: Dict[str, List[Dict[str, Any]]]) -> Dict[int, Dict[str, Any]]:
    item_map = {}
    for items in grouped_catalog.values():
        for item in items:
            item_map[item['id']] = item
    return item_map


def update_cart(item_id: int, item_name: str, item_price: float, delta_quantity: int):
    if 'cart' not in st.session_state:
        st.session_state['cart'] = {}
    current_quantity = st.session_state['cart'].get(item_id, {}).get('quantity', 0)
    new_quantity = max(0, current_quantity + delta_quantity)
    if new_quantity > 0:
        st.session_state['cart'][item_id] = {'name': item_name, 'price': item_price, 'quantity': new_quantity}
    elif item_id in st.session_state['cart']:
        del st.session_state['cart'][item_id]
    st.rerun()


def clear_cart():
    st.session_state['cart'] = {}
    st.rerun()


def post_sale(auth_token: str, user_id: int, movimento_id: int, evento_id: int):
    cart = st.session_state.get('cart', {})
    if not cart:
        st.error("O carrinho está vazio.")
        return False

    venda_payload = {
        "eventoId": evento_id,
        "responsavelId": user_id,
        "pessoaId": 1,
        "movimentoCaixaId": movimento_id,
        "itens": [],
    }
    for item_id, item_data in cart.items():
        item_price_float = float(item_data['price'])
        venda_payload['itens'].append({
            "itemId": item_id,
            "quantidade": item_data['quantity'],
            "valor_unitario": item_price_float
        })

    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    try:
        response = requests.post(f"{API_BASE_URL}/vendas", headers=headers, json=venda_payload)
        if response.status_code in (200, 201):
            st.success("Venda registrada com sucesso!")
            clear_cart()
            return True
        error_detail = response.json().get('detail', f"Falha desconhecida. Código: {response.status_code}")
        st.error(f"Falha ao finalizar venda: {error_detail}")
        return False
    except requests.exceptions.ConnectionError:
        st.error("Erro de conexão com a API.")
        return False


def render_item_buttons_by_category(grouped_catalog: Dict[str, List[Dict[str, Any]]]):
    st.subheader("1. Seleção Rápida de Produtos por Categoria")
    category_names = list(grouped_catalog.keys())
    tabs = st.tabs(category_names)
    for tab_index, category_name in enumerate(category_names):
        with tabs[tab_index]:
            items_in_category = grouped_catalog[category_name]
            cols = st.columns(3)
            for index, item in enumerate(items_in_category):
                col = cols[index % 3]
                if col.button(f"{item['nome']}\n(R$ {item['valor_venda']:.2f})", key=f"item_btn_{item['id']}", use_container_width=True):
                    update_cart(item['id'], item['nome'], item['valor_venda'], 1)


def render_quantity_controls(item_data_map: Dict[int, Dict[str, Any]]):
    st.subheader("2. Ajuste de Quantidade Rápido")
    cart = st.session_state.get('cart', {})
    if not cart:
        st.info("Carrinho vazio. Selecione um produto para ajustar a quantidade.")
        return
    last_item_id = list(cart.keys())[-1]
    cart_item = cart[last_item_id]
    st.markdown(f"**Ajustando:** **{cart_item['name']}** (Qtde atual: {cart_item['quantity']})")
    q_cols = st.columns(4)
    if q_cols[0].button("+1", key="q_plus_1", use_container_width=True):
        update_cart(last_item_id, cart_item['name'], cart_item['price'], 1)
    if q_cols[1].button("+5", key="q_plus_5", use_container_width=True):
        update_cart(last_item_id, cart_item['name'], cart_item['price'], 5)
    if q_cols[2].button("-1", key="q_minus_1", use_container_width=True):
        update_cart(last_item_id, cart_item['name'], cart_item['price'], -1)
    if q_cols[3].button("Zerar", key="q_zero", use_container_width=True):
        update_cart(last_item_id, cart_item['name'], cart_item['price'], -cart_item['quantity'])


def render_cart_summary(movimento_id: int, evento_id: int):
    st.subheader("3. Carrinho de Compras")
    cart = st.session_state.get('cart', {})
    if not cart:
        st.info("Nenhum item no carrinho.")
        return
    total_value = Decimal(0)
    st.markdown("---")
    for item_id, item_data in cart.items():
        subtotal = Decimal(item_data['quantity']) * Decimal(item_data['price'])
        total_value += subtotal
        st.markdown(f"**{item_data['quantity']}x {item_data['name']}** *(R$ {subtotal:.2f})*")
    st.markdown("---")
    st.metric(label="Total a Pagar", value=f"R$ {total_value:.2f}")
    if st.button("FINALIZAR VENDA", key="btn_checkout", use_container_width=True, type="primary"):
        auth_token = st.session_state.get('auth_token')
        user_id = st.session_state.get('user_id')
        if auth_token and user_id and movimento_id:
            post_sale(auth_token, user_id, movimento_id, evento_id)
        else:
            st.error("Sessão inválida ou movimento não encontrado.")


def vendas_page():
    st.title("Frente de Caixa")
    auth_token = st.session_state.get('auth_token')
    user_id = st.session_state.get('user_id')
    if not auth_token:
        st.error("Erro de sessão: Token não encontrado. Faça login novamente.")
        return

    # Caixa e movimento
    headers = {"Authorization": f"Bearer {auth_token}"}
    caixas_resp = requests.get(f"{API_BASE_URL}/caixas/", headers=headers)
    caixas = caixas_resp.json() if caixas_resp.status_code == 200 else []
    caixa_options = {f"{c.get('id')} - {c.get('nome')}": c.get('id') for c in caixas}
    selected_label = st.selectbox("Selecione o caixa", list(caixa_options.keys())) if caixa_options else None
    selected_caixa = caixa_options.get(selected_label) if selected_label else None

    movimento_id = None
    if selected_caixa:
        mov_resp = requests.get(f"{API_BASE_URL}/caixas/{selected_caixa}/movimento-ativo", headers=headers)
        if mov_resp.status_code == 200:
            mov = mov_resp.json()
            movimento_id = mov.get('id')
            st.success(f"Movimento aberto: ID {movimento_id}")
        else:
            st.warning("Nenhum movimento aberto para este caixa.")
            valor = st.number_input("Valor de abertura", min_value=0.0, value=0.0, step=10.0)
            if st.button("Abrir movimento", use_container_width=True):
                open_resp = requests.post(
                    f"{API_BASE_URL}/caixas/{selected_caixa}/abrir",
                    headers=headers,
                    params={"usuario_id": user_id, "valor_abertura": valor},
                )
                if open_resp.status_code in (200, 201):
                    st.success("Movimento aberto. Recarregue a página se necessário.")
                    st.rerun()
                else:
                    st.error("Falha ao abrir movimento.")
    else:
        st.info("Selecione um caixa ou crie um na página de Gestão de Caixas.")
        return

    grouped_catalog = get_grouped_catalog(auth_token)
    if not grouped_catalog:
        st.warning("Não foi possível carregar o catálogo de itens.")
        return

    item_data_map = get_item_data_map(grouped_catalog)
    left_col, right_col = st.columns([2, 1])
    with left_col:
        render_item_buttons_by_category(grouped_catalog)
        st.markdown("---")
        render_quantity_controls(item_data_map)
    with right_col:
        if movimento_id:
            render_cart_summary(movimento_id, evento_id=1)
        else:
            st.info("Abra um movimento para habilitar a venda.")