# React + TypeScript + Vite

## Permissões

Em Administração → Usuários & Permissões, administradores podem combinar módulos livremente ou usar perfis rápidos no cadastro e na edição. A lista vazia bloqueia todos os módulos. Usuários com acesso legado continuam funcionando; ao editá-los, as seleções são salvas como permissões explícitas e podem alterar seus acessos. Administradores mantêm acesso à configuração, mesmo com módulos desabilitados pela organização. A sessão é verificada no login, na restauração, periodicamente, ao recuperar o foco e após respostas 403.

Os testes de navegação por permissão podem ser executados com `node --test tests/permissions.test.ts` (Node.js com suporte a TypeScript).

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend enabling type-aware lint rules by installing `oxlint-tsgolint` and editing `.oxlintrc.json`:

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["react", "typescript", "oxc"],
  "options": {
    "typeAware": true
  },
  "rules": {
    "react/rules-of-hooks": "error",
    "react/only-export-components": ["warn", { "allowConstantExport": true }]
  }
}
```

See the [Oxlint rules documentation](https://oxc.rs/docs/guide/usage/linter/rules) for the full list of rules and categories.
