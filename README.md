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

O schema é gerenciado por migrações Alembic; a API não cria nem altera tabelas no startup. Aplique as migrações antes de iniciar a API.

### Migrações versionadas

Para criar ou atualizar o schema do banco configurado em `config/secrets.toml` ou nas variáveis PostgreSQL:
```bash
alembic upgrade head
```

Em bancos existentes, faça backup antes de atualizar. A revisão inicial usa DDL idempotente para preservar tabelas e dados existentes. Se o schema já corresponde exatamente ao baseline, registre apenas essa revisão e aplique as seguintes:
```bash
alembic stamp 20261117_01
alembic upgrade head
```

A revisão baseline pode ser revertida com `alembic downgrade base`, mas isso remove as tabelas e os dados; execute somente após backup e com um plano de restauração.

A configuração da organização inclui `alias_evento`, com padrão `Evento`. O endpoint `GET /api/organizacao/config` permanece acessível; `PUT /api/organizacao/config` exige administrador. Payloads antigos que omitem o campo preservam o valor já configurado.

Em **Usuários & Permissões**, administradores podem conceder módulos individualmente. Administradores têm acesso irrestrito; para usuários antigos, `permissoes = NULL` preserva o acesso operacional legado, enquanto `[]` não concede nenhum módulo. Alterações são registradas em `audit_logs` e aplicadas nas requisições seguintes. As configurações da organização também permitem definir identidade, vocabulário e módulos operacionais; quando exigido, o documento é validado no servidor antes do atendimento.

Ao atualizar uma instalação existente, faça backup do PostgreSQL antes de iniciar a nova versão. Na inicialização, o estoque mínimo dos produtos existentes é definido como zero e os facilitadores anteriormente vinculados a usuários são copiados para o novo cadastro, preservando os agendamentos.

Na Administração, defina o estoque mínimo de cada produto e mantenha seu preço de custo atualizado. O preço pode ficar em branco quando for desconhecido; zero representa um custo conhecido de zero. O relatório de estoque avisa sobre preços ausentes e calcula a reposição com os preços cadastrados, não com um histórico automático de compras.

Em Atendimentos, configure os termos de pessoas atendidas, atendentes e entidades ou serviços. Na Administração, mantenha cadastros independentes para atendentes e para entidades ou serviços; ambos podem ser selecionados nos agendamentos. Cadastros antigos de facilitadores permanecem como estavam e não são classificados automaticamente. A inativação preserva os vínculos anteriores.

A seção Doações registra receitas com data, valor e dados opcionais do doador, forma de pagamento e evento, sem exigir evento ou caixa aberto. As doações ativas integram o saldo do fluxo financeiro; o cancelamento preserva o histórico e remove o valor do saldo. Elas não são lançadas automaticamente em uma sessão de caixa físico.

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

---

## 🔐 Autenticação e Primeiro Acesso

Em desenvolvimento, o bootstrap cria `admin@unython.local` com senha `change-me-now` quando a conta não existe. A troca de senha é exigida nas rotas autenticadas antes de prosseguir.

Em produção, defina `APP_ENV=production`, `JWT_SECRET_KEY` com pelo menos 32 caracteres aleatórios e `CORS_ORIGINS` com origens HTTPS explícitas, separadas por vírgula. Exemplo para gerar um segredo: `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Não registre ou compartilhe esse valor. Configure TLS no proxy de confiança e transmita o esquema HTTPS corretamente à aplicação.

O bootstrap de produção é ignorado se `BOOTSTRAP_ADMIN_PASSWORD` não estiver definida; uma senha configurada deve ter pelo menos 12 caracteres e não pode ser a senha padrão. O startup também recusa o administrador padrão existente se ele ainda utilizar `change-me-now`. Antes do primeiro acesso, provisione um administrador seguro ou configure essa variável temporariamente. A API não utiliza cookies de autenticação: a SPA guarda o token em `localStorage`, que continua exposto caso haja execução de JavaScript malicioso na origem.

As operações críticas registram auditoria transacional em `audit_logs`; cada entrada inclui o identificador da requisição. `/api/health` verifica o PostgreSQL, e os logs HTTP estruturados usam `X-Request-ID` sem registrar credenciais ou corpos das requisições. A reversão da migração de auditoria remove a tabela e seu histórico; preserve um backup antes de executá-la.

---

## 📦 Compilando a SPA (Build Frontend)

Caso faça alterações no código de `frontend-web/`:
```bash
cd frontend-web
npm install
npm run build
```
O build compilado em `dist/` é instantaneamente reconhecido pelo FastAPI.

A SPA é instalável como PWA: em produção, sirva-a por HTTPS (ou `localhost`) e use a opção **Instalar aplicativo** do navegador. O Service Worker precacheia apenas arquivos estáticos do build; requisições `/api` não são armazenadas em cache.

---

## 🧪 Testes Automatizados

Os testes de integração **apagam os dados das tabelas antes e depois de cada teste**. Eles exigem `TEST_DATABASE_URL` apontando para um banco PostgreSQL dedicado cujo nome termine em `_test`; não usam `secrets.toml`, não criam o banco automaticamente e abortam antes de conectar se a variável estiver ausente ou for insegura. Crie o banco de testes isolado e aplique o baseline:
```bash
createdb unython_test
```

No PowerShell:
```powershell
$env:TEST_DATABASE_URL = "postgresql://test_user:senha@localhost:5432/unython_test"
alembic upgrade head
pytest -vv tests/teste_fluxo_geral.py
```

O `alembic upgrade head` usa `TEST_DATABASE_URL` quando essa variável está definida. Nunca aponte essa URL para bancos de desenvolvimento ou produção.

Os testes isolados de projeção e facilitadores não usam PostgreSQL:
```bash
python -m pytest -q unit_tests
```

---

## 📄 Licença
Licenciado sob a **GNU General Public License v3.0 (GPL-3.0)**.
Desenvolvido para apoiar organizações de impacto social, ONGs e projetos comunitários.
