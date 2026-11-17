# 📖 Unython - Visão Geral da Arquitetura e Decisões de Design

Este documento detalha as decisões de engenharia que moldaram o Unython, garantindo sua escalabilidade, manutenibilidade e integridade de dados.

## 1. Visão Geral da Arquitetura de Camadas

O Unython segue o princípio do **Domínio Orientado a Serviços** com forte separação de preocupações (*Separation of Concerns*). O fluxo de controle sempre passa de cima para baixo.

| Camada | Pasta | Responsabilidade | Tecnologias Chave |
| :--- | :--- | :--- | :--- |
| **Apresentação / API** | `app/` | API REST e orquestração de processos; entrega a SPA em produção. | FastAPI, Uvicorn, Pydantic |
| **Frontend / Interface** | `frontend-web/` | SPA web e PDV para operadores e administradores. | React, TypeScript, Vite |
| **Serviço/Lógica** | `src/modules/` | Regras de negócio puras (Vendas, Estoque, Relatórios, etc.). **Desacoplado de persistência.** | Python Classes (Domain Services) |
| **Utilidade/Infra** | `src/utils/` | Estruturas de dados (`models.py`), schemas (`schemas.py`), segurança (`security.py`) e persistência (`database_manager.py`). | `dataclasses`, `psycopg2`, `pyjwt`, `bcrypt` |
| **Persistência** | PostgreSQL | Armazenamento relacional ACID com constraints de Foreign Keys e índices. | PostgreSQL 14+ |

---

## 2. Decisões Críticas de Design

### 2.1. Injeção de Dependência e Pool de Conexões
* **Decisão:** Todos os *Services* (Venda, Estoque, Relatório) recebem o `DatabaseManager` em seu construtor (`__init__`).
* **Conexões Gerenciadas:** A API FastAPI gerencia o ciclo de vida via dependência `DBDependency`, utilizando `ThreadedConnectionPool` do PostgreSQL para reaproveitamento rápido de conexões.

### 2.2. Atomicidade e Transações (Vendas e Estoque)
* **Decisão:** Implementação de protocolo **Tudo ou Nada** no `VendaService.registrar_venda_completa()`.
* **Atomicidade:** Valida saldo de estoque antecipadamente, grava o cabeçalho da venda e os itens sem commit individual e emite saída de estoque na mesma transação. Se qualquer etapa falhar, o `rollback()` é disparado e nenhuma alteração parcial é persistida.

### 2.3. Rastreabilidade por Contexto (Domínio Evento)
* **Decisão:** A tabela `eventos` centraliza agendamentos, vendas e fluxo de caixa.
* **Finalidade:** O `id_evento` funciona como um **Dia Fiscal Universal**, permitindo relatórios consolidados que agregam todas as movimentações de uma feirinha, culto ou dia de atendimento.

### 2.4. Integridade de Dados
* **Chaves Estrangeiras:** O PostgreSQL impõe integridade referencial nativa entre `vendas` (comprador em `pessoas(id)` e sessão em `movimentos_caixa(id)`), `itens` e `categorias`.
* **Precisão Financeira:** Valores monetários são estritamente manipulados como `Decimal` em models e schemas para prevenir erros de ponto flutuante.
* **Segurança Criptográfica:** Senhas usam `bcrypt` e sessões de API utilizam tokens `JWT` assinados digitalmente.
