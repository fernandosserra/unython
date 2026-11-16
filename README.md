# Unython — Gestão Estruturada para Organizações de Impacto

Sistema de organização, rastreabilidade e operação por evento (feirinhas, bazares, cultos, mutirões e atendimentos) em Python com API FastAPI e **Frontend SPA moderno (React, TypeScript, Tailwind CSS, PWA)**.

---

## 🏛️ Arquitetura do Sistema

```
Unython
 ├── app/                  # Orquestração e endpoints REST (FastAPI / Uvicorn)
 │     ├── api_main.py     # Ponto de entrada FastAPI com lifespan, CORS e montagem da SPA
 │     ├── main.py         # Orquestrador de serviços (API + SPA / Dev Server)
 │     └── routers/        # Rotas da API (vendas, caixas, agendamentos, estoque, etc.)
 │
 ├── frontend-web/         # Frontend Moderno SPA (React + TypeScript + Vite + Tailwind CSS)
 │     ├── src/components/ # Telas: PDV Express, Recepção/Atendimentos, Caixa/Turno, Relatórios
 │     ├── src/store/      # Gerenciamento de estado reativo (Zustand: Carrinho e Auth JWT)
 │     └── dist/           # Build estático otimizado (servido diretamente pelo FastAPI em produção)
 │
 ├── frontend/             # Interface analítica legada (Streamlit para dashboards)
 │
 ├── src/modules/          # Regras de Negócio e Serviços de Domínio
 │     ├── venda.py        # Transações atômicas de venda com baixa de estoque
 │     ├── estoque.py      # Movimentações e cálculo consolidado de saldo
 │     ├── caixas.py       # Abertura, fechamento e sessões de caixa
 │     ├── evento.py       # Gestão do Dia Fiscal / Evento centralizador
 │     ├── agendamento.py  # Acolhimento e confirmação de presença de assistidos
 │     └── relatorio.py    # Análise financeira, DRE e inventário sem N+1 queries
 │
 ├── src/utils/            # Infraestrutura de persistência, segurança e modelos
 │     ├── database_manager.py  # Pool de conexões PostgreSQL (ThreadedConnectionPool)
 │     ├── security.py          # Hashing bcrypt direto e tokens JWT com expiração
 │     └── schemas.py           # Validações Pydantic com precisão monetária (Decimal)
 │
 └── tests/                # Testes de integração automatizados
```

---

## 🗄️ Banco de Dados (PostgreSQL)

O Unython requer **PostgreSQL 14+**.
Configure as credenciais em `config/secrets.toml`:

```toml
[database]
type = "postgres"
host = "localhost"
dbname = "unython"
user = "postgres"
password = "sua_senha_aqui"
port = 5432
```

> **Dica:** O `DatabaseManager` cria todas as tabelas e índices automaticamente no primeiro arranque com ordenação estrita de chaves estrangeiras.

---

## 🚀 Como Executar

### 1. Modo Padrão Recomendado (API + SPA React Embutida)
Sobe o servidor FastAPI que atende a API e entrega a SPA React pronta em uma única porta:
```bash
python app/main.py
```
Acesse no navegador: **`http://127.0.0.1:8000/`**

### 2. Modo Desenvolvimento com Hot-Reload da SPA (Vite)
Sobe a API no backend (porta 8000) e o Vite com Hot Module Reload no frontend (porta 3000):
```bash
python app/main.py --spa-dev
```
Acesse o frontend em: **`http://127.0.0.1:3000/`**

### 3. Modo Dashboard Streamlit (Opcional)
```bash
python app/main.py --streamlit
```
Acesse em: **`http://127.0.0.1:8501/`**

---

## 🔐 Autenticação e Primeiro Acesso

* **Superusuário Padrão:** `admin@unython.local`
* **Senha Inicial:** `change-me-now`
* O sistema força a alteração de senha no primeiro login.
* Na tela de login da SPA, há um botão de **Acesso Rápido Bootstrap** para facilitar o desenvolvimento.

---

## 📦 Compilando a SPA (Build Frontend)

Caso faça alterações no código de `frontend-web/`:
```bash
cd frontend-web
npm install
npm run build
```
O build compilado em `dist/` é instantaneamente reconhecido pelo FastAPI.

---

## 🧪 Testes Automatizados

Com o PostgreSQL ativo e configurado em `config/secrets.toml`:
```bash
pytest -vv tests/teste_fluxo_geral.py
```

---

## 📄 Licença
Licenciado sob a **GNU General Public License v3.0 (GPL-3.0)**.
Desenvolvido para apoiar organizações de impacto social, ONGs e projetos comunitários.
