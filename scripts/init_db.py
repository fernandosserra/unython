"""
Script de Inicialização do Banco de Dados - Unython
Verifica/cria o banco de dados 'unython' no PostgreSQL e cria todas as tabelas.

Uso:
  python scripts/init_db.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils.database_manager import DatabaseManager, ensure_database_exists, load_db_config
from src.modules.usuario import UsuarioService
from src.utils.models import Usuario


def main():
    print("=" * 60)
    print("🚀 Unython - Inicializador de Banco de Dados PostgreSQL")
    print("=" * 60)

    cfg = load_db_config()
    print(f"-> Servidor: {cfg.get('host')}:{cfg.get('port')}")
    print(f"-> Usuário:  {cfg.get('user')}")
    print(f"-> Banco:    {cfg.get('dbname')}")
    print("-" * 60)

    # 1. Garante que o banco exista (conecta ao 'postgres' e cria se necessário)
    print("1. Verificando existência do banco de dados...")
    ok = ensure_database_exists()
    if not ok:
        print("❌ Não foi possível verificar/criar o banco de dados.")
        print("   Verifique se o serviço do PostgreSQL está rodando e a senha em config/secrets.toml está correta.")
        sys.exit(1)

    # 2. Conecta ao banco 'unython' e cria as tabelas
    print("\n2. Conectando ao banco e criando/verificando tabelas...")
    db = DatabaseManager()
    try:
        db.connect()
        db.create_tables()
    except Exception as e:
        print(f"❌ Falha ao criar tabelas: {e}")
        sys.exit(1)

    # 3. Garante o superusuário padrão
    print("\n3. Verificando superusuário padrão (admin@unython.local)...")
    try:
        user_srv = UsuarioService(db)
        admin = user_srv.buscar_usuario_por_email("admin@unython.local")
        if not admin:
            u = Usuario(
                nome="Super Usuário",
                email="admin@unython.local",
                funcao="Administrador",
                role="Administrador",
                status="Ativo",
                require_password_change=True,
            )
            user_srv.registrar_usuario(u, "change-me-now", require_password_change=True)
            print("   ✅ Superusuário bootstrap criado: admin@unython.local (senha: change-me-now)")
        else:
            print("   ✅ Superusuário já existe e está ativo.")
    except Exception as e:
        print(f"   ⚠️ Aviso ao verificar superusuário: {e}")
    finally:
        db.disconnect()

    print("\n" + "=" * 60)
    print("🎉 Banco de dados inicializado com sucesso e 100% pronto!")
    print("   Agora você pode iniciar o sistema com: python app/main.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
