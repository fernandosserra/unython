# Unython — Gestão Estruturada para Organizações de Impacto

Organização, rastreabilidade e operação por evento (feirinhas, cultos, atendimentos) em Python, com API FastAPI e interface Streamlit.

## Arquitetura
- Orquestração: `app/main.py` sobe API (FastAPI/Uvicorn) e Interface (Streamlit).
- API: `app/api_main.py` + `app/routers/*`.
- Frontend: `frontend/interface.py` (Streamlit) + `frontend/modules`.
- Domínio/serviços: `src/modules/*` (pessoas, usuários, agendamentos, vendas, estoque, relatórios, fluxo de caixa, caixas, backup).
- Infra/utilitários: `src/utils/*` (models, database manager, segurança, config).
- Testes: `tests/` (fluxo geral de integração).

## Banco de Dados
- PostgreSQL configurado em `config/secrets.toml`:
  ```toml
  [database]
  type = "postgres"
  host = "localhost"
  dbname = "unython_db"
  user = "postgres"
  password = "sua_senha"
  port = 5432
  ```
- Use `config/secrets.toml.example` como modelo e copie para `config/secrets.toml`.
- `DatabaseManager` cria/verifica tabelas ao iniciar. Em desenvolvimento, use um banco descartável.

## Requisitos
- Python 3.10+ (testado em 3.13)
- PostgreSQL
- `pip install -r requirements.txt`

## Como rodar

### Orquestrador (API + UI)
```bash
# Windows (PowerShell)
python app/main.py                   # API:127.0.0.1:8000, UI:127.0.0.1:8501
python app/main.py --api-only        # Só API
python app/main.py --ui-only         # Só UI
python app/main.py --api-port 8001 --ui-port 8502 --no-reload
```

### API isolada
```bash
python -m uvicorn app.api_main:app --host 127.0.0.1 --port 8000 --reload
```

### Interface Streamlit isolada
```bash
streamlit run frontend/interface.py --server.port 8501 --server.headless true
```

## Testes
- Use o Python do venv:
  ```bash
  .\venv\Scripts\python.exe -m pytest -vv tests/teste_fluxo_geral.py
  ```
- Fixture `cleanup_db` faz TRUNCATE/RESTART IDENTITY antes/depois de cada teste (usa o Postgres de `secrets.toml`).
- Discovery configurado em `pytest.ini` (`test_*.py` e `teste_*.py`).

## Notas de desenvolvimento
- Setup rápido:
  ```bash
  python -m venv venv
  .\venv\Scripts\activate
  pip install -r requirements.txt
  ```
- Imports: o orquestrador ajusta `PYTHONPATH`; evite `sys.path.append` em novos módulos.
- Valores monetários usam `Decimal` nos models.
- Prefira `logging` em vez de `print` em produção.

## Roadmap curto
- Cancelamento de vendas com permissão.
- Tela de abertura/fechamento de movimento de caixa.
- CORS/logging estruturado na API e schemas Pydantic por rota.

## Roadmap longo
- Interface de Agendamento (validação de presença/ausência).
- Relatórios para administradores.
- Relatórios de fechamento de caixa.
- Relatórios de estoque na interface.

## Licença
Este projeto é licenciado sob GPL-3.0. Veja `LICENSE` para detalhes. Contato do desenvolvedor: fsserra@gmail.com.
