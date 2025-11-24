import streamlit as st
import requests
from datetime import date
from utils.components import API_BASE_URL


def movimentos_page(api_base_url: str):
    st.title("Movimentos de Evento e Caixa")
    auth_token = st.session_state.get('auth_token')
    user_id = st.session_state.get('user_id')
    if not auth_token:
        st.error("Sessão inválida. Faça login.")
        return
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Bloco 1: Evento/dia
    st.subheader("Evento / Dia de Trabalho")
    evento_resp = requests.get(f"{api_base_url}/eventos/aberto", headers=headers)
    evento = evento_resp.json() if evento_resp.status_code == 200 else None
    if evento:
        st.success(f"Evento aberto: {evento.get('nome')} (ID {evento.get('id')}) em {evento.get('data_evento')}")
        if st.button("Fechar evento", use_container_width=True):
            close_ev = requests.post(f"{api_base_url}/eventos/{evento.get('id')}/fechar", headers=headers)
            if close_ev.status_code == 200:
                st.success("Evento fechado. Recarregue para abrir outro.")
                st.rerun()
            else:
                st.error("Falha ao fechar evento.")
    else:
        st.warning("Nenhum evento aberto.")
        nome = st.text_input("Nome do evento (opcional)", value=f"Operacao {date.today()}")
        tipo = st.text_input("Tipo (ex.: Operacao)", value="Operacao")
        if st.button("Abrir evento", use_container_width=True):
            open_ev = requests.post(f"{api_base_url}/eventos/abrir", headers=headers, params={"nome": nome, "tipo": tipo})
            if open_ev.status_code in (200, 201):
                st.success("Evento aberto.")
                st.rerun()
            else:
                st.error("Falha ao abrir evento.")

    # Filtro de eventos
    st.markdown("---")
    st.subheader("Histórico de Eventos")
    col1, col2 = st.columns(2)
    data_ini = col1.date_input("Data início", value=date.today().replace(day=1))
    data_fim = col2.date_input("Data fim", value=date.today())
    if st.button("Carregar eventos", use_container_width=True):
        resp_list = requests.get(
            f"{api_base_url}/eventos/",
            headers=headers,
            params={"data_inicio": data_ini.isoformat(), "data_fim": data_fim.isoformat()},
        )
        if resp_list.status_code == 200:
            for ev in resp_list.json():
                st.write(f"{ev.get('data_evento')} | {ev.get('nome')} | {ev.get('status')} (ID {ev.get('id')})")
        else:
            st.error("Falha ao carregar eventos.")

    # Bloco 2: Movimentos de caixa
    st.markdown("---")
    st.subheader("Movimentos de Caixa")
    evento_resp = requests.get(f"{api_base_url}/eventos/aberto", headers=headers)
    evento = evento_resp.json() if evento_resp.status_code == 200 else None
    if not evento:
        st.info("Abra um evento para gerenciar movimentos de caixa.")
        return

    caixas_resp = requests.get(f"{api_base_url}/caixas/", headers=headers)
    caixas = caixas_resp.json() if caixas_resp.status_code == 200 else []
    caixa_options = {f"{c.get('id')} - {c.get('nome')}": c.get('id') for c in caixas}
    selected_label = st.selectbox("Selecione um caixa", list(caixa_options.keys())) if caixa_options else None
    selected_caixa = caixa_options.get(selected_label) if selected_label else None

    if not selected_caixa:
        st.info("Crie um caixa na aba Gestão de Caixas.")
        return

    mov_resp = requests.get(f"{api_base_url}/caixas/{selected_caixa}/movimento-ativo", headers=headers)
    if mov_resp.status_code == 200:
        mov = mov_resp.json()
        st.success(f"Movimento ABERTO ID {mov.get('id')} - Valor abertura: {mov.get('valor_abertura')} - Evento {mov.get('id_evento')}")
        if st.button("Fechar movimento", use_container_width=True):
            close_resp = requests.post(f"{api_base_url}/caixas/{mov.get('id')}/fechar", headers=headers)
            if close_resp.status_code == 200:
                st.success("Movimento fechado.")
                st.rerun()
            else:
                st.error("Falha ao fechar movimento.")
    else:
        st.warning("Nenhum movimento aberto.")
        valor = st.number_input("Valor de abertura", min_value=0.0, value=0.0, step=10.0)
        if st.button("Abrir movimento", use_container_width=True):
            params = {"usuario_id": user_id, "valor_abertura": valor, "id_evento": evento.get('id')}
            open_resp = requests.post(
                f"{api_base_url}/caixas/{selected_caixa}/abrir",
                headers=headers,
                params=params,
            )
            if open_resp.status_code in (200, 201):
                st.success("Movimento aberto.")
                st.rerun()
            else:
                st.error("Falha ao abrir movimento.")