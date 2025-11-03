# 📖 Unython - Visão Geral da Arquitetura e Decisões de Design

Este documento detalha as decisões de engenharia que moldaram o Unython, garantindo sua escalabilidade, manutenibilidade e coerência de dados.

## 1. Visão Geral da Arquitetura de Camadas

O Unython segue o princípio do **Domínio Orientado a Serviços** com forte separação de preocupações (Separation of Concerns). O fluxo de controle sempre passa de cima para baixo.

| Camada | Pasta | Responsabilidade | Tecnologias Chave |
| :--- | :--- | :--- | :--- |
| **Apresentação** | `app/` | Ponto de entrada (CLI/Web). Orquestra a execução. | Python, `main.py` |
| **Serviço/Lógica** | `src/modules/` | Contém as **regras de negócio** (Ex: Registrar uma Venda, Calcular Saldo de Estoque). **Não sabe como os dados são salvos.** | Python Classes (Services) |
| **Utilidade/Infra** | `src/utils/` | Contém a **estrutura de dados** (`models.py`) e o **mecanismo de persistência** (`database_manager.py`). | `dataclasses`, `sqlite3` |
| **Persistência** | `data/` | Armazenamento físico do banco de dados. | `unython.db` (SQLite) |

---

## 2. Decisões Críticas de Design

### 2.1. Injeção de Dependência e Coerência de Conexão

**Decisão:** Todos os *Services* (Venda, Estoque, Relatório) **recebem** o `DatabaseManager` no seu construtor (`__init__`) e **NÃO** chamam `connect()` ou `disconnect()`.

* **Vantagem:** O `main.py` torna-se o **Guardião Único da Conexão**. A conexão é aberta uma única vez e fechada no `finally` (Protocolo de Segurança).
* **Aplicações:** Evita o erro de `Cannot operate on a closed database` e garante que todas as operações dentro do `main.py` (como Vendas, Estoque e Agendamento) compartilhem a mesma transação, se necessário.

### 2.2. Atomicidade e Transações (Vendas e Estoque)

**Decisão:** Implementar a lógica **Tudo ou Nada** no `VendaService`.

* O método `registrar_venda_completa()` coordena: 1) Checagem de Estoque, 2) Registro do Cabeçalho da Venda, 3) Registro dos Detalhes, e 4) Registro da **Saída de Estoque**.
* **Atomicidade:** Os métodos auxiliares (`registrar_venda`, `registrar_item_venda`) usam `commit=False`. O `commit` só é chamado no final do `registrar_venda_completa`. Se houver uma falha (ex: Estoque Insuficiente), o `try/except` aciona o `rollback()`, revertendo todas as operações parciais.

### 2.3. Rastreabilidade por Contexto (Domínio Evento)

**Decisão:** Introduzir a tabela **`Eventos`** para ligar Agendamentos e Vendas.

* **Finalidade:** O `id_evento` funciona como um **Dia Fiscal Universal**, permitindo relatórios que agregam todas as movimentações dentro de um período específico de trabalho (Feirinha, Culto, etc.).
* **Implementação:** O `main.py` assegura a criação ou busca do evento aberto antes de qualquer transação.

### 2.4. Integridade de Dados

* **Chaves Estrangeiras:** O `DatabaseManager` ativa o `PRAGMA foreign_keys = ON;`, garantindo a integridade dos relacionamentos (Ex: uma Venda não pode ser registrada se o `id_evento` não existir).
* **Regras de Unicidade:** Implementação de lógica de **UPSERT** (busca ou insere/atualiza) para `Usuários` e `Itens` para evitar falhas de `UNIQUE constraint failed` em execuções repetidas.