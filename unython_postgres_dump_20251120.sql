--
-- PostgreSQL database dump
--

\restrict ZQmX7jHAIXjwb3BaIg8jXLTa3YVNlbAvtkb3VxQemXzrXHNKlEhyi7wCCH2eATX

-- Dumped from database version 18.0
-- Dumped by pg_dump version 18.0

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: agendamentos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.agendamentos (
    id integer NOT NULL,
    id_pessoa integer NOT NULL,
    id_facilitador integer,
    data_hora timestamp without time zone NOT NULL,
    tipo_servico character varying(100),
    status character varying(50) DEFAULT 'Agendado'::character varying,
    id_evento integer NOT NULL,
    compareceu character varying(50) DEFAULT 'Pendente'::character varying NOT NULL
);


ALTER TABLE public.agendamentos OWNER TO postgres;

--
-- Name: agendamentos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.agendamentos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.agendamentos_id_seq OWNER TO postgres;

--
-- Name: agendamentos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.agendamentos_id_seq OWNED BY public.agendamentos.id;


--
-- Name: caixas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.caixas (
    id integer NOT NULL,
    nome character varying(100) NOT NULL,
    descricao character varying(255),
    status character varying(50) DEFAULT 'Ativo'::character varying
);


ALTER TABLE public.caixas OWNER TO postgres;

--
-- Name: caixas_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.caixas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.caixas_id_seq OWNER TO postgres;

--
-- Name: caixas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.caixas_id_seq OWNED BY public.caixas.id;


--
-- Name: categorias; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.categorias (
    id integer NOT NULL,
    nome character varying(100) NOT NULL,
    descricao text,
    status character varying(50) DEFAULT 'Ativo'::character varying
);


ALTER TABLE public.categorias OWNER TO postgres;

--
-- Name: categorias_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.categorias_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.categorias_id_seq OWNER TO postgres;

--
-- Name: categorias_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.categorias_id_seq OWNED BY public.categorias.id;


--
-- Name: estoque; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.estoque (
    id integer NOT NULL,
    id_item integer NOT NULL,
    quantidade integer NOT NULL,
    tipo_movimento character varying(50) NOT NULL,
    data_movimento date DEFAULT now() NOT NULL,
    origem_recurso character varying(100) DEFAULT 'Doação'::character varying,
    id_usuario integer,
    id_evento integer
);


ALTER TABLE public.estoque OWNER TO postgres;

--
-- Name: estoque_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.estoque_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.estoque_id_seq OWNER TO postgres;

--
-- Name: estoque_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.estoque_id_seq OWNED BY public.estoque.id;


--
-- Name: eventos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.eventos (
    id integer NOT NULL,
    nome character varying(255) NOT NULL,
    data_evento date NOT NULL,
    tipo character varying(100),
    status character varying(50) DEFAULT 'Aberto'::character varying
);


ALTER TABLE public.eventos OWNER TO postgres;

--
-- Name: eventos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.eventos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.eventos_id_seq OWNER TO postgres;

--
-- Name: eventos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.eventos_id_seq OWNED BY public.eventos.id;


--
-- Name: itens; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.itens (
    id integer NOT NULL,
    nome character varying(255) NOT NULL,
    valor_compra numeric(10,2) NOT NULL,
    valor_venda numeric(10,2) NOT NULL,
    status character varying(50) DEFAULT 'Ativo'::character varying,
    id_categoria integer
);


ALTER TABLE public.itens OWNER TO postgres;

--
-- Name: itens_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.itens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.itens_id_seq OWNER TO postgres;

--
-- Name: itens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.itens_id_seq OWNED BY public.itens.id;


--
-- Name: itens_venda; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.itens_venda (
    id integer NOT NULL,
    id_venda integer NOT NULL,
    id_item integer NOT NULL,
    quantidade integer NOT NULL,
    valor_unitario numeric(10,2) NOT NULL
);


ALTER TABLE public.itens_venda OWNER TO postgres;

--
-- Name: itens_venda_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.itens_venda_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.itens_venda_id_seq OWNER TO postgres;

--
-- Name: itens_venda_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.itens_venda_id_seq OWNED BY public.itens_venda.id;


--
-- Name: movimentos_caixa; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.movimentos_caixa (
    id integer NOT NULL,
    id_caixa integer NOT NULL,
    id_usuario_abertura integer NOT NULL,
    valor_abertura numeric(10,2) DEFAULT 0.00 NOT NULL,
    status character varying(50) DEFAULT 'Aberto'::character varying NOT NULL,
    data_abertura timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    data_fechamento timestamp without time zone
);


ALTER TABLE public.movimentos_caixa OWNER TO postgres;

--
-- Name: movimentos_caixa_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.movimentos_caixa_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.movimentos_caixa_id_seq OWNER TO postgres;

--
-- Name: movimentos_caixa_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.movimentos_caixa_id_seq OWNED BY public.movimentos_caixa.id;


--
-- Name: movimentos_financeiros; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.movimentos_financeiros (
    id integer NOT NULL,
    data_registro timestamp without time zone DEFAULT now() NOT NULL,
    id_usuario integer NOT NULL,
    tipo_movimento character varying(50) NOT NULL,
    valor numeric(10,2) NOT NULL,
    descricao text,
    categoria character varying(100),
    id_evento integer,
    status character varying(50) DEFAULT 'Ativo'::character varying NOT NULL,
    CONSTRAINT movimentos_financeiros_tipo_movimento_check CHECK (((tipo_movimento)::text = ANY ((ARRAY['Receita'::character varying, 'Despesa'::character varying])::text[])))
);


ALTER TABLE public.movimentos_financeiros OWNER TO postgres;

--
-- Name: movimentos_financeiros_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.movimentos_financeiros_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.movimentos_financeiros_id_seq OWNER TO postgres;

--
-- Name: movimentos_financeiros_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.movimentos_financeiros_id_seq OWNED BY public.movimentos_financeiros.id;


--
-- Name: pessoas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pessoas (
    id integer NOT NULL,
    nome character varying(255) NOT NULL,
    telefone character varying(50),
    data_cadastro date DEFAULT now() NOT NULL
);


ALTER TABLE public.pessoas OWNER TO postgres;

--
-- Name: pessoas_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.pessoas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pessoas_id_seq OWNER TO postgres;

--
-- Name: pessoas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.pessoas_id_seq OWNED BY public.pessoas.id;


--
-- Name: usuarios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usuarios (
    id integer NOT NULL,
    nome character varying(255) NOT NULL,
    email character varying(255),
    funcao character varying(100),
    status character varying(50) DEFAULT 'Ativo'::character varying,
    role character varying(50) DEFAULT 'Vendedor'::character varying NOT NULL,
    hashed_password character varying(128)
);


ALTER TABLE public.usuarios OWNER TO postgres;

--
-- Name: usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.usuarios_id_seq OWNER TO postgres;

--
-- Name: usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.usuarios_id_seq OWNED BY public.usuarios.id;


--
-- Name: vendas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.vendas (
    id integer NOT NULL,
    id_pessoa integer,
    data_venda date DEFAULT now() NOT NULL,
    id_evento integer NOT NULL,
    responsavel character varying(255)
);


ALTER TABLE public.vendas OWNER TO postgres;

--
-- Name: vendas_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.vendas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.vendas_id_seq OWNER TO postgres;

--
-- Name: vendas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.vendas_id_seq OWNED BY public.vendas.id;


--
-- Name: agendamentos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.agendamentos ALTER COLUMN id SET DEFAULT nextval('public.agendamentos_id_seq'::regclass);


--
-- Name: caixas id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.caixas ALTER COLUMN id SET DEFAULT nextval('public.caixas_id_seq'::regclass);


--
-- Name: categorias id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categorias ALTER COLUMN id SET DEFAULT nextval('public.categorias_id_seq'::regclass);


--
-- Name: estoque id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estoque ALTER COLUMN id SET DEFAULT nextval('public.estoque_id_seq'::regclass);


--
-- Name: eventos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.eventos ALTER COLUMN id SET DEFAULT nextval('public.eventos_id_seq'::regclass);


--
-- Name: itens id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itens ALTER COLUMN id SET DEFAULT nextval('public.itens_id_seq'::regclass);


--
-- Name: itens_venda id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itens_venda ALTER COLUMN id SET DEFAULT nextval('public.itens_venda_id_seq'::regclass);


--
-- Name: movimentos_caixa id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movimentos_caixa ALTER COLUMN id SET DEFAULT nextval('public.movimentos_caixa_id_seq'::regclass);


--
-- Name: movimentos_financeiros id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movimentos_financeiros ALTER COLUMN id SET DEFAULT nextval('public.movimentos_financeiros_id_seq'::regclass);


--
-- Name: pessoas id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pessoas ALTER COLUMN id SET DEFAULT nextval('public.pessoas_id_seq'::regclass);


--
-- Name: usuarios id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);


--
-- Name: vendas id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vendas ALTER COLUMN id SET DEFAULT nextval('public.vendas_id_seq'::regclass);


--
-- Data for Name: agendamentos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.agendamentos (id, id_pessoa, id_facilitador, data_hora, tipo_servico, status, id_evento, compareceu) FROM stdin;
3	15	1	2025-11-04 01:30:39	Passe e Aconselhamento	Agendado	1	Pendente
4	16	1	2025-11-04 01:32:00	Passe e Aconselhamento	Agendado	1	Pendente
5	17	1	2025-11-04 01:33:00	Passe e Aconselhamento	Agendado	1	Pendente
6	19	1	2025-11-05 00:50:00	Passe e Aconselhamento	Agendado	1	Pendente
7	20	1	2025-11-05 21:36:00	Passe e Aconselhamento	Agendado	1	Pendente
1	13	1	2025-11-04 01:28:03	Passe e Aconselhamento	Agendado	1	Sim
2	14	1	2025-11-04 01:29:23	Passe e Aconselhamento	Agendado	1	Não
8	21	1	2025-11-08 23:10:00	Passe e Aconselhamento	Agendado	1	Pendente
9	22	1	2025-11-09 00:00:00	Passe e Aconselhamento	Agendado	1	Pendente
10	23	1	2025-11-09 00:34:00	Passe e Aconselhamento	Agendado	1	Pendente
11	24	1	2025-11-09 00:39:00	Passe e Aconselhamento	Agendado	1	Pendente
12	25	1	2025-11-09 01:21:00	Passe e Aconselhamento	Agendado	1	Pendente
13	26	1	2025-11-09 01:24:00	Passe e Aconselhamento	Agendado	1	Pendente
14	27	1	2025-11-10 17:29:00	Passe e Aconselhamento	Agendado	1	Pendente
15	28	1	2025-11-10 17:32:00	Passe e Aconselhamento	Agendado	1	Pendente
16	29	1	2025-11-20 13:37:00	Passe e Aconselhamento	Agendado	1	Pendente
17	30	1	2025-11-20 13:38:00	Passe e Aconselhamento	Agendado	1	Pendente
18	31	1	2025-11-20 13:39:00	Passe e Aconselhamento	Agendado	1	Pendente
19	32	1	2025-11-20 23:23:00	Passe e Aconselhamento	Agendado	1	Pendente
20	33	1	2025-11-20 23:26:00	Passe e Aconselhamento	Agendado	1	Pendente
\.


--
-- Data for Name: caixas; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.caixas (id, nome, descricao, status) FROM stdin;
\.


--
-- Data for Name: categorias; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.categorias (id, nome, descricao, status) FROM stdin;
1	Bebidas	Refrigerantes, Água, Sucos	Ativo
2	Esotéricos	Velas, Incensos, Banhos	Ativo
\.


--
-- Data for Name: estoque; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.estoque (id, id_item, quantidade, tipo_movimento, data_movimento, origem_recurso, id_usuario, id_evento) FROM stdin;
1	1	20	Entrada	2025-11-04	Doação Inicial	1	1
2	2	10	Entrada	2025-11-04	Compra com Fundo de Feirinha	1	1
3	1	2	Saída	2025-11-04	Venda em Feirinha	1	1
4	2	1	Saída	2025-11-04	Venda em Feirinha	1	1
5	1	20	Entrada	2025-11-04	Doação Inicial	1	1
6	2	10	Entrada	2025-11-04	Compra com Fundo de Feirinha	1	1
7	1	2	Saída	2025-11-04	Venda em Feirinha	1	1
8	2	1	Saída	2025-11-04	Venda em Feirinha	1	1
9	1	20	Entrada	2025-11-04	Doação Inicial	1	1
10	2	10	Entrada	2025-11-04	Compra com Fundo de Feirinha	1	1
11	1	2	Saída	2025-11-04	Venda em Feirinha	1	1
12	2	1	Saída	2025-11-04	Venda em Feirinha	1	1
13	1	20	Entrada	2025-11-04	Doação Inicial	1	1
14	2	10	Entrada	2025-11-04	Compra com Fundo de Feirinha	1	1
15	1	2	Saída	2025-11-04	Venda em Feirinha	1	1
16	2	1	Saída	2025-11-04	Venda em Feirinha	1	1
17	1	20	Entrada	2025-11-04	Doação Inicial	1	1
18	2	10	Entrada	2025-11-04	Compra com Fundo de Feirinha	1	1
19	1	2	Saída	2025-11-04	Venda em Feirinha	1	1
20	2	1	Saída	2025-11-04	Venda em Feirinha	1	1
21	1	20	Entrada	2025-11-04	Doação Inicial	1	1
22	2	10	Entrada	2025-11-04	Compra com Fundo de Feirinha	1	1
23	1	2	Saída	2025-11-04	Venda em Feirinha	1	1
24	2	1	Saída	2025-11-04	Venda em Feirinha	1	1
25	1	100	Saída	2025-11-04	Venda em Feirinha	1	1
26	1	20	Entrada	2025-11-04	Doação Inicial	1	1
27	2	10	Entrada	2025-11-04	Compra com Fundo de Feirinha	1	1
28	1	2	Saída	2025-11-04	Venda em Feirinha	1	1
29	2	1	Saída	2025-11-04	Venda em Feirinha	1	1
30	1	20	Entrada	2025-11-04	Doação Inicial	1	1
31	2	10	Entrada	2025-11-04	Compra com Fundo de Feirinha	1	1
32	1	2	Saída	2025-11-04	Venda em Feirinha	1	1
33	2	1	Saída	2025-11-04	Venda em Feirinha	1	1
34	1	20	Entrada	2025-11-04	Doação Inicial	1	1
35	2	10	Entrada	2025-11-04	Compra com Fundo de Feirinha	1	1
36	1	2	Saída	2025-11-04	Venda em Feirinha	1	1
37	2	1	Saída	2025-11-04	Venda em Feirinha	1	1
38	1	20	Entrada	2025-11-04	Doação Inicial	1	1
39	2	10	Entrada	2025-11-04	Compra com Fundo de Feirinha	1	1
40	1	2	Saída	2025-11-04	Venda em Feirinha	1	1
41	2	1	Saída	2025-11-04	Venda em Feirinha	1	1
42	1	20	Entrada	2025-11-04	Doação Inicial	1	1
43	2	10	Entrada	2025-11-04	Compra com Fundo de Feirinha	1	1
44	1	2	Saída	2025-11-04	Venda em Feirinha	1	1
45	2	1	Saída	2025-11-04	Venda em Feirinha	1	1
46	1	20	Entrada	2025-11-04	Doação Inicial	1	1
47	2	10	Entrada	2025-11-04	Compra com Fundo de Feirinha	1	1
48	1	2	Saída	2025-11-04	Venda em Feirinha	1	1
49	2	1	Saída	2025-11-04	Venda em Feirinha	1	1
50	1	100	Saída	2025-11-04	Venda em Feirinha	1	1
51	1	20	Entrada	2025-11-04	Doação Inicial	1	1
52	2	10	Entrada	2025-11-04	Compra com Fundo de Feirinha	1	1
53	1	2	Saída	2025-11-04	Venda em Feirinha	1	1
54	2	1	Saída	2025-11-04	Venda em Feirinha	1	1
55	1	20	Entrada	2025-11-04	Doação Inicial	1	1
56	2	10	Entrada	2025-11-04	Compra com Fundo de Feirinha	1	1
57	1	2	Saída	2025-11-04	Venda em Feirinha	1	1
58	2	1	Saída	2025-11-04	Venda em Feirinha	1	1
59	1	20	Entrada	2025-11-05	Doação Inicial	1	1
60	2	10	Entrada	2025-11-05	Compra com Fundo de Feirinha	1	1
61	1	2	Saída	2025-11-05	Venda em Feirinha	1	1
62	2	1	Saída	2025-11-05	Venda em Feirinha	1	1
63	1	20	Entrada	2025-11-05	Doação Inicial	1	1
64	2	10	Entrada	2025-11-05	Compra com Fundo de Feirinha	1	1
65	1	2	Saída	2025-11-05	Venda em Feirinha	1	1
66	2	1	Saída	2025-11-05	Venda em Feirinha	1	1
67	1	2	Saída	2025-11-05	Venda em Feirinha	1	1
68	2	1	Saída	2025-11-05	Venda em Feirinha	1	1
69	1	20	Entrada	2025-11-05	Doação Inicial	1	1
70	2	10	Entrada	2025-11-05	Compra com Fundo de Feirinha	1	1
71	1	2	Saída	2025-11-05	Venda em Feirinha	1	1
72	2	1	Saída	2025-11-05	Venda em Feirinha	1	1
73	1	100	Saída	2025-11-05	Venda em Feirinha	1	1
74	1	20	Entrada	2025-11-08	Doação Inicial	1	1
75	2	10	Entrada	2025-11-08	Compra com Fundo de Feirinha	1	1
76	1	2	Saída	2025-11-08	Venda em Feirinha	1	1
77	2	1	Saída	2025-11-08	Venda em Feirinha	1	1
78	1	20	Entrada	2025-11-09	Doação Inicial	1	1
79	2	10	Entrada	2025-11-09	Compra com Fundo de Feirinha	1	1
80	1	2	Saída	2025-11-09	Venda em Feirinha	1	1
81	2	1	Saída	2025-11-09	Venda em Feirinha	1	1
82	1	20	Entrada	2025-11-09	Doação Inicial	1	1
83	2	10	Entrada	2025-11-09	Compra com Fundo de Feirinha	1	1
84	1	2	Saída	2025-11-09	Venda em Feirinha	1	1
85	2	1	Saída	2025-11-09	Venda em Feirinha	1	1
86	1	20	Entrada	2025-11-09	Doação Inicial	1	1
87	2	10	Entrada	2025-11-09	Compra com Fundo de Feirinha	1	1
88	1	2	Saída	2025-11-09	Venda em Feirinha	1	1
89	2	1	Saída	2025-11-09	Venda em Feirinha	1	1
90	1	20	Entrada	2025-11-09	Doação Inicial	1	1
91	2	10	Entrada	2025-11-09	Compra com Fundo de Feirinha	1	1
92	1	2	Saída	2025-11-09	Venda em Feirinha	1	1
93	2	1	Saída	2025-11-09	Venda em Feirinha	1	1
94	1	20	Entrada	2025-11-09	Doação Inicial	1	1
95	2	10	Entrada	2025-11-09	Compra com Fundo de Feirinha	1	1
96	1	2	Saída	2025-11-09	Venda em Feirinha	1	1
97	2	1	Saída	2025-11-09	Venda em Feirinha	1	1
98	1	100	Saída	2025-11-09	Venda em Feirinha	1	1
99	1	1	Saída	2025-11-09	Venda em Feirinha	1	1
100	1	1	Saída	2025-11-09	Venda em Feirinha	1	1
101	2	1	Saída	2025-11-09	Venda em Feirinha	1	1
102	2	2	Saída	2025-11-09	Venda em Feirinha	1	1
103	1	1	Saída	2025-11-09	Venda em Feirinha	1	1
104	1	20	Entrada	2025-11-10	Doação Inicial	1	1
105	2	10	Entrada	2025-11-10	Compra com Fundo de Feirinha	1	1
106	1	2	Saída	2025-11-10	Venda em Feirinha	1	1
107	2	1	Saída	2025-11-10	Venda em Feirinha	1	1
108	1	20	Entrada	2025-11-20	Doação Inicial	1	1
109	2	10	Entrada	2025-11-20	Compra com Fundo de Feirinha	1	1
110	1	2	Saída	2025-11-20	Venda em Feirinha	1	1
111	2	1	Saída	2025-11-20	Venda em Feirinha	1	1
112	1	20	Entrada	2025-11-20	Doação Inicial	1	1
113	2	10	Entrada	2025-11-20	Compra com Fundo de Feirinha	1	1
114	1	2	Saída	2025-11-20	Venda em Feirinha	1	1
115	2	1	Saída	2025-11-20	Venda em Feirinha	1	1
116	1	20	Entrada	2025-11-20	Doação Inicial	1	1
117	2	10	Entrada	2025-11-20	Compra com Fundo de Feirinha	1	1
118	1	2	Saída	2025-11-20	Venda em Feirinha	1	1
119	2	1	Saída	2025-11-20	Venda em Feirinha	1	1
120	1	1	Saída	2025-11-20	Venda em Feirinha	1	1
121	1	6	Saída	2025-11-20	Venda em Feirinha	1	1
122	2	7	Saída	2025-11-20	Venda em Feirinha	1	1
123	1	20	Entrada	2025-11-20	Doação Inicial	1	1
124	2	10	Entrada	2025-11-20	Compra com Fundo de Feirinha	1	1
125	1	2	Saída	2025-11-20	Venda em Feirinha	1	1
126	2	1	Saída	2025-11-20	Venda em Feirinha	1	1
127	1	20	Entrada	2025-11-20	Doação Inicial	1	1
128	2	10	Entrada	2025-11-20	Compra com Fundo de Feirinha	1	1
129	1	2	Saída	2025-11-20	Venda em Feirinha	1	1
130	2	1	Saída	2025-11-20	Venda em Feirinha	1	1
131	1	100	Saída	2025-11-20	Venda em Feirinha	1	1
\.


--
-- Data for Name: eventos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.eventos (id, nome, data_evento, tipo, status) FROM stdin;
1	Atendimento e Feirinha 2025-11-04	2025-11-04	Atendimento e Venda	Aberto
\.


--
-- Data for Name: itens; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.itens (id, nome, valor_compra, valor_venda, status, id_categoria) FROM stdin;
1	Coca Cola Lata	1.50	2.50	Ativo	1
2	Vela 7 Dias	5.00	10.00	Ativo	2
\.


--
-- Data for Name: itens_venda; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.itens_venda (id, id_venda, id_item, quantidade, valor_unitario) FROM stdin;
1	1	1	2	2.50
2	1	2	1	10.00
3	2	1	2	2.50
4	2	2	1	10.00
5	3	1	2	2.50
6	3	2	1	10.00
7	4	1	2	2.50
8	4	2	1	10.00
9	5	1	2	2.50
10	5	2	1	10.00
11	6	1	2	2.50
12	6	2	1	10.00
13	7	1	100	2.50
14	8	1	2	2.50
15	8	2	1	10.00
16	9	1	2	2.50
17	9	2	1	10.00
18	10	1	2	2.50
19	10	2	1	10.00
20	11	1	2	2.50
21	11	2	1	10.00
22	12	1	2	2.50
23	12	2	1	10.00
24	13	1	2	2.50
25	13	2	1	10.00
26	14	1	100	2.50
27	15	1	2	2.50
28	15	2	1	10.00
29	16	1	2	2.50
30	16	2	1	10.00
31	17	1	2	2.50
32	17	2	1	10.00
33	18	1	2	2.50
34	18	2	1	10.00
35	19	1	2	2.50
36	19	2	1	10.00
37	20	1	2	2.50
38	20	2	1	10.00
39	21	1	100	2.50
40	22	1	2	2.50
41	22	2	1	10.00
42	23	1	2	2.50
43	23	2	1	10.00
44	24	1	2	2.50
45	24	2	1	10.00
46	25	1	2	2.50
47	25	2	1	10.00
48	26	1	2	2.50
49	26	2	1	10.00
50	27	1	2	2.50
51	27	2	1	10.00
52	28	1	100	2.50
53	29	1	1	2.50
54	30	1	1	2.50
55	30	2	1	10.00
56	31	2	2	10.00
57	31	1	1	2.50
58	32	1	2	2.50
59	32	2	1	10.00
60	33	1	2	2.50
61	33	2	1	10.00
62	34	1	2	2.50
63	34	2	1	10.00
64	35	1	2	2.50
65	35	2	1	10.00
66	36	1	1	2.50
67	37	1	6	2.50
68	38	2	7	10.00
69	39	1	2	2.50
70	39	2	1	10.00
71	40	1	2	2.50
72	40	2	1	10.00
73	41	1	100	2.50
\.


--
-- Data for Name: movimentos_caixa; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.movimentos_caixa (id, id_caixa, id_usuario_abertura, valor_abertura, status, data_abertura, data_fechamento) FROM stdin;
\.


--
-- Data for Name: movimentos_financeiros; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.movimentos_financeiros (id, data_registro, id_usuario, tipo_movimento, valor, descricao, categoria, id_evento, status) FROM stdin;
1	2025-11-04 00:21:40	1	Receita	250.00	Doação espontânea de um fiel	Doação	1	Ativo
2	2025-11-04 00:21:40	1	Despesa	50.00	Compra de material de limpeza	Material	1	Ativo
3	2025-11-04 00:36:41	1	Receita	250.00	Doação espontânea de um fiel	Doação	1	Ativo
4	2025-11-04 00:36:41	1	Despesa	50.00	Compra de material de limpeza	Material	1	Ativo
5	2025-11-04 00:45:49	1	Receita	250.00	Doação espontânea de um fiel	Doação	1	Ativo
6	2025-11-04 00:45:49	1	Despesa	50.00	Compra de material de limpeza	Material	1	Ativo
7	2025-11-04 00:55:34	1	Receita	250.00	Doação espontânea de um fiel	Doação	1	Ativo
8	2025-11-04 00:55:34	1	Despesa	50.00	Compra de material de limpeza	Material	1	Ativo
9	2025-11-04 01:03:03	1	Receita	250.00	Doação espontânea de um fiel	Doação	1	Ativo
10	2025-11-04 01:03:03	1	Despesa	50.00	Compra de material de limpeza	Material	1	Ativo
11	2025-11-04 01:05:07	1	Receita	250.00	Doação espontânea de um fiel	Doação	1	Ativo
12	2025-11-04 01:05:07	1	Despesa	50.00	Compra de material de limpeza	Material	1	Ativo
13	2025-11-04 01:08:23	1	Receita	250.00	Doação espontânea de um fiel	Doação	1	Ativo
14	2025-11-04 01:08:23	1	Despesa	50.00	Compra de material de limpeza	Material	1	Ativo
15	2025-11-04 01:09:49	1	Receita	250.00	Doação espontânea de um fiel	Doação	1	Ativo
16	2025-11-04 01:09:49	1	Despesa	50.00	Compra de material de limpeza	Material	1	Ativo
17	2025-11-04 01:11:15	1	Receita	250.00	Doação espontânea de um fiel	Doação	1	Ativo
18	2025-11-04 01:11:15	1	Despesa	50.00	Compra de material de limpeza	Material	1	Ativo
19	2025-11-04 01:20:09	1	Receita	250.00	Doação espontânea de um fiel	Doação	1	Ativo
20	2025-11-04 01:20:09	1	Despesa	50.00	Compra de material de limpeza	Material	1	Ativo
21	2025-11-04 01:29:21	1	Receita	250.00	Doação espontânea de um fiel	Doação	1	Ativo
22	2025-11-04 01:29:21	1	Despesa	50.00	Compra de material de limpeza	Material	1	Ativo
23	2025-11-04 01:32:07	1	Receita	250.00	Doação espontânea de um fiel	Doação	1	Ativo
24	2025-11-04 01:32:07	1	Despesa	50.00	Compra de material de limpeza	Material	1	Ativo
25	2025-11-04 01:33:18	1	Receita	250.00	Doação espontânea de um fiel	Doação	1	Ativo
26	2025-11-04 01:33:18	1	Despesa	50.00	Compra de material de limpeza	Material	1	Ativo
27	2025-11-05 00:49:59	1	Receita	250.00	Doação espontânea de um fiel	Doação	1	Ativo
28	2025-11-05 00:49:59	1	Despesa	50.00	Compra de material de limpeza	Material	1	Ativo
29	2025-11-05 00:50:41	1	Receita	250.00	Doação espontânea de um fiel	Doação	1	Ativo
30	2025-11-05 00:50:41	1	Despesa	50.00	Compra de material de limpeza	Material	1	Ativo
31	2025-11-05 21:36:34.73456	1	Receita	250.00	Doação espontânea de um fiel	Doação	1	Ativo
32	2025-11-05 21:36:34.73456	1	Despesa	50.00	Compra de material de limpeza	Material	1	Ativo
33	2025-11-08 23:10:35.339106	1	Receita	250.00	Doação espontânea de um fiel	Doação	1	Ativo
34	2025-11-08 23:10:35.339106	1	Despesa	50.00	Compra de material de limpeza	Material	1	Ativo
35	2025-11-09 00:00:00.084431	1	Receita	250.00	Doação espontânea de um fiel	Doação	1	Ativo
36	2025-11-09 00:00:00.084431	1	Despesa	50.00	Compra de material de limpeza	Material	1	Ativo
37	2025-11-09 00:34:31.724537	1	Receita	250.00	Doação espontânea de um fiel	Doação	1	Ativo
38	2025-11-09 00:34:31.724537	1	Despesa	50.00	Compra de material de limpeza	Material	1	Ativo
39	2025-11-09 00:39:23.881125	1	Receita	250.00	Doação espontânea de um fiel	Doação	1	Ativo
40	2025-11-09 00:39:23.881125	1	Despesa	50.00	Compra de material de limpeza	Material	1	Ativo
41	2025-11-09 01:21:43.70328	1	Receita	250.00	Doação espontânea de um fiel	Doação	1	Ativo
42	2025-11-09 01:21:43.70328	1	Despesa	50.00	Compra de material de limpeza	Material	1	Ativo
43	2025-11-09 01:23:59.097103	1	Receita	250.00	Doação espontânea de um fiel	Doação	1	Ativo
44	2025-11-09 01:23:59.097103	1	Despesa	50.00	Compra de material de limpeza	Material	1	Ativo
45	2025-11-10 17:32:38.380326	1	Receita	250.00	Doação espontânea de um fiel	Doação	1	Ativo
46	2025-11-10 17:32:38.380326	1	Despesa	50.00	Compra de material de limpeza	Material	1	Ativo
47	2025-11-20 13:37:41.453408	1	Receita	250.00	Doação espontânea de um fiel	Doação	1	Ativo
48	2025-11-20 13:37:41.453408	1	Despesa	50.00	Compra de material de limpeza	Material	1	Ativo
49	2025-11-20 13:38:20.290359	1	Receita	250.00	Doação espontânea de um fiel	Doação	1	Ativo
50	2025-11-20 13:38:20.290359	1	Despesa	50.00	Compra de material de limpeza	Material	1	Ativo
51	2025-11-20 13:39:25.956232	1	Receita	250.00	Doação espontânea de um fiel	Doação	1	Ativo
52	2025-11-20 13:39:25.956232	1	Despesa	50.00	Compra de material de limpeza	Material	1	Ativo
53	2025-11-20 23:23:33.479257	1	Receita	250.00	Doação espontânea de um fiel	Doação	1	Ativo
54	2025-11-20 23:23:33.479257	1	Despesa	50.00	Compra de material de limpeza	Material	1	Ativo
55	2025-11-20 23:26:07.700018	1	Receita	250.00	Doação espontânea de um fiel	Doação	1	Ativo
56	2025-11-20 23:26:07.700018	1	Despesa	50.00	Compra de material de limpeza	Material	1	Ativo
\.


--
-- Data for Name: pessoas; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.pessoas (id, nome, telefone, data_cadastro) FROM stdin;
1	Fernando, O Aprendiz	551199887766	2025-11-04
2	Fernando, O Aprendiz	551199887766	2025-11-04
3	Fernando, O Aprendiz	551199887766	2025-11-04
4	Fernando, O Aprendiz	551199887766	2025-11-04
5	Fernando, O Aprendiz	551199887766	2025-11-04
6	Fernando, O Aprendiz	551199887766	2025-11-04
7	Fernando, O Aprendiz	551199887766	2025-11-04
8	Fernando, O Aprendiz	551199887766	2025-11-04
9	Fernando, O Aprendiz	551199887766	2025-11-04
10	Fernando, O Aprendiz	551199887766	2025-11-04
11	Fernando, O Aprendiz	551199887766	2025-11-04
12	Fernando, O Aprendiz	551199887766	2025-11-04
13	Fernando, O Aprendiz	551199887766	2025-11-04
14	Fernando, O Aprendiz	551199887766	2025-11-04
15	Fernando, O Aprendiz	551199887766	2025-11-04
16	Fernando, O Aprendiz	551199887766	2025-11-04
17	Fernando, O Aprendiz	551199887766	2025-11-04
18	Fernando, O Aprendiz	551199887766	2025-11-05
19	Fernando, O Aprendiz	551199887766	2025-11-05
20	Fernando, O Aprendiz	551199887766	2025-11-05
21	Fernando, O Aprendiz	551199887766	2025-11-08
22	Fernando, O Aprendiz	551199887766	2025-11-09
23	Fernando, O Aprendiz	551199887766	2025-11-09
24	Fernando, O Aprendiz	551199887766	2025-11-09
25	Fernando, O Aprendiz	551199887766	2025-11-09
26	Fernando, O Aprendiz	551199887766	2025-11-09
27	Fernando, O Aprendiz	551199887766	2025-11-10
28	Fernando, O Aprendiz	551199887766	2025-11-10
29	Fernando, O Aprendiz	551199887766	2025-11-20
30	Fernando, O Aprendiz	551199887766	2025-11-20
31	Fernando, O Aprendiz	551199887766	2025-11-20
32	Fernando, O Aprendiz	551199887766	2025-11-20
33	Fernando, O Aprendiz	551199887766	2025-11-20
\.


--
-- Data for Name: usuarios; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.usuarios (id, nome, email, funcao, status, role, hashed_password) FROM stdin;
1	Dra. Washu Hakubi	washu@unython.com	Médium	Ativo	Administrador	$2b$12$6CVtPrUF8VV4U2DVGMIuke.2i45BOSQPUT8Gl4MhUxo8GS64BzgeW
\.


--
-- Data for Name: vendas; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.vendas (id, id_pessoa, data_venda, id_evento, responsavel) FROM stdin;
1	1	2025-11-04	1	1
2	2	2025-11-04	1	1
3	3	2025-11-04	1	1
4	4	2025-11-04	1	1
5	5	2025-11-04	1	1
6	6	2025-11-04	1	1
7	6	2025-11-04	1	1
8	7	2025-11-04	1	1
9	8	2025-11-04	1	1
10	9	2025-11-04	1	1
11	10	2025-11-04	1	1
12	11	2025-11-04	1	1
13	14	2025-11-04	1	1
14	14	2025-11-04	1	1
15	16	2025-11-04	1	1
16	17	2025-11-04	1	1
17	18	2025-11-05	1	1
18	19	2025-11-05	1	1
19	1	2025-11-05	1	1
20	20	2025-11-05	1	1
21	20	2025-11-05	1	1
22	21	2025-11-08	1	1
23	22	2025-11-09	1	1
24	23	2025-11-09	1	1
25	24	2025-11-09	1	1
26	25	2025-11-09	1	1
27	26	2025-11-09	1	1
28	26	2025-11-09	1	1
29	1	2025-11-09	1	1
30	1	2025-11-09	1	1
31	1	2025-11-09	1	1
32	28	2025-11-10	1	1
33	29	2025-11-20	1	1
34	30	2025-11-20	1	1
35	31	2025-11-20	1	1
36	1	2025-11-20	1	1
37	1	2025-11-20	1	1
38	1	2025-11-20	1	1
39	32	2025-11-20	1	1
40	33	2025-11-20	1	1
41	33	2025-11-20	1	1
\.


--
-- Name: agendamentos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.agendamentos_id_seq', 20, true);


--
-- Name: caixas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.caixas_id_seq', 1, false);


--
-- Name: categorias_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.categorias_id_seq', 2, true);


--
-- Name: estoque_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.estoque_id_seq', 131, true);


--
-- Name: eventos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.eventos_id_seq', 1, true);


--
-- Name: itens_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.itens_id_seq', 2, true);


--
-- Name: itens_venda_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.itens_venda_id_seq', 73, true);


--
-- Name: movimentos_caixa_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.movimentos_caixa_id_seq', 1, false);


--
-- Name: movimentos_financeiros_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.movimentos_financeiros_id_seq', 56, true);


--
-- Name: pessoas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.pessoas_id_seq', 33, true);


--
-- Name: usuarios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.usuarios_id_seq', 1, true);


--
-- Name: vendas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.vendas_id_seq', 41, true);


--
-- Name: agendamentos agendamentos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.agendamentos
    ADD CONSTRAINT agendamentos_pkey PRIMARY KEY (id);


--
-- Name: caixas caixas_nome_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.caixas
    ADD CONSTRAINT caixas_nome_key UNIQUE (nome);


--
-- Name: caixas caixas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.caixas
    ADD CONSTRAINT caixas_pkey PRIMARY KEY (id);


--
-- Name: categorias categorias_nome_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT categorias_nome_key UNIQUE (nome);


--
-- Name: categorias categorias_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT categorias_pkey PRIMARY KEY (id);


--
-- Name: estoque estoque_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estoque
    ADD CONSTRAINT estoque_pkey PRIMARY KEY (id);


--
-- Name: eventos eventos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.eventos
    ADD CONSTRAINT eventos_pkey PRIMARY KEY (id);


--
-- Name: itens itens_nome_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itens
    ADD CONSTRAINT itens_nome_key UNIQUE (nome);


--
-- Name: itens itens_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itens
    ADD CONSTRAINT itens_pkey PRIMARY KEY (id);


--
-- Name: itens_venda itens_venda_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itens_venda
    ADD CONSTRAINT itens_venda_pkey PRIMARY KEY (id);


--
-- Name: movimentos_caixa movimentos_caixa_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movimentos_caixa
    ADD CONSTRAINT movimentos_caixa_pkey PRIMARY KEY (id);


--
-- Name: movimentos_financeiros movimentos_financeiros_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movimentos_financeiros
    ADD CONSTRAINT movimentos_financeiros_pkey PRIMARY KEY (id);


--
-- Name: pessoas pessoas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pessoas
    ADD CONSTRAINT pessoas_pkey PRIMARY KEY (id);


--
-- Name: usuarios usuarios_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_email_key UNIQUE (email);


--
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- Name: vendas vendas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vendas
    ADD CONSTRAINT vendas_pkey PRIMARY KEY (id);


--
-- Name: idx_mov_caixa_caixa_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_mov_caixa_caixa_id ON public.movimentos_caixa USING btree (id_caixa);


--
-- Name: idx_mov_caixa_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_mov_caixa_status ON public.movimentos_caixa USING btree (status);


--
-- Name: agendamentos agendamentos_id_evento_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.agendamentos
    ADD CONSTRAINT agendamentos_id_evento_fkey FOREIGN KEY (id_evento) REFERENCES public.eventos(id);


--
-- Name: agendamentos agendamentos_id_facilitador_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.agendamentos
    ADD CONSTRAINT agendamentos_id_facilitador_fkey FOREIGN KEY (id_facilitador) REFERENCES public.usuarios(id);


--
-- Name: agendamentos agendamentos_id_pessoa_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.agendamentos
    ADD CONSTRAINT agendamentos_id_pessoa_fkey FOREIGN KEY (id_pessoa) REFERENCES public.pessoas(id);


--
-- Name: estoque estoque_id_evento_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estoque
    ADD CONSTRAINT estoque_id_evento_fkey FOREIGN KEY (id_evento) REFERENCES public.eventos(id);


--
-- Name: estoque estoque_id_item_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estoque
    ADD CONSTRAINT estoque_id_item_fkey FOREIGN KEY (id_item) REFERENCES public.itens(id);


--
-- Name: estoque estoque_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.estoque
    ADD CONSTRAINT estoque_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuarios(id);


--
-- Name: itens fk_item_categoria; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itens
    ADD CONSTRAINT fk_item_categoria FOREIGN KEY (id_categoria) REFERENCES public.categorias(id) ON DELETE RESTRICT;


--
-- Name: itens_venda itens_venda_id_item_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itens_venda
    ADD CONSTRAINT itens_venda_id_item_fkey FOREIGN KEY (id_item) REFERENCES public.itens(id);


--
-- Name: itens_venda itens_venda_id_venda_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.itens_venda
    ADD CONSTRAINT itens_venda_id_venda_fkey FOREIGN KEY (id_venda) REFERENCES public.vendas(id);


--
-- Name: movimentos_caixa movimentos_caixa_id_caixa_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movimentos_caixa
    ADD CONSTRAINT movimentos_caixa_id_caixa_fkey FOREIGN KEY (id_caixa) REFERENCES public.caixas(id);


--
-- Name: movimentos_caixa movimentos_caixa_id_usuario_abertura_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movimentos_caixa
    ADD CONSTRAINT movimentos_caixa_id_usuario_abertura_fkey FOREIGN KEY (id_usuario_abertura) REFERENCES public.usuarios(id);


--
-- Name: movimentos_financeiros movimentos_financeiros_id_evento_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movimentos_financeiros
    ADD CONSTRAINT movimentos_financeiros_id_evento_fkey FOREIGN KEY (id_evento) REFERENCES public.eventos(id);


--
-- Name: movimentos_financeiros movimentos_financeiros_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.movimentos_financeiros
    ADD CONSTRAINT movimentos_financeiros_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuarios(id);


--
-- Name: vendas vendas_id_evento_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vendas
    ADD CONSTRAINT vendas_id_evento_fkey FOREIGN KEY (id_evento) REFERENCES public.eventos(id);


--
-- Name: vendas vendas_id_pessoa_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vendas
    ADD CONSTRAINT vendas_id_pessoa_fkey FOREIGN KEY (id_pessoa) REFERENCES public.pessoas(id);


--
-- PostgreSQL database dump complete
--

\unrestrict ZQmX7jHAIXjwb3BaIg8jXLTa3YVNlbAvtkb3VxQemXzrXHNKlEhyi7wCCH2eATX

