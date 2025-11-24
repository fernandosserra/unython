# src/modules/usuario.py (VERSAO FINAL SANADA)
from typing import Optional, List
from src.utils.database_manager import DatabaseManager
from src.utils.models import Usuario
from src.utils.security import hash_password, verify_password


class UsuarioService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    # --- METODOS DE SEGURANCA E REGISTRO ---

    def editar_usuario_seguro(self, user_id: int, role: str, hashed_password: str, require_password_change: bool = False) -> bool:
        """Atualiza role, senha e flag de troca obrigatoria para um usuario existente."""
        query = "UPDATE usuarios SET role = %s, hashed_password = %s, require_password_change = %s WHERE id = %s"
        params = (role, hashed_password, require_password_change, user_id)
        return self.db.execute_query(query, params, commit=True)

    def registrar_usuario(self, usuario: Usuario, password: str, require_password_change: bool = False):
        """Registra um novo usuario com a senha criptografada (com UPSERT)."""
        usuario_existente = self.buscar_usuario_por_email(usuario.email)
        hashed_pwd = hash_password(password)

        if usuario_existente:
            self.editar_usuario_seguro(usuario_existente.id, usuario.role, hashed_pwd, require_password_change)
            print(f"(Alerta: Usuario '{usuario.nome}' atualizado. Usando ID: {usuario_existente.id})")
            return usuario_existente.id

        query = """
        INSERT INTO usuarios (nome, email, funcao, status, role, hashed_password, require_password_change)
        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
        """
        params = (usuario.nome, usuario.email, usuario.funcao, usuario.status, usuario.role, hashed_pwd, require_password_change)
        return self.db.execute_query(query, params, commit=True)

    # --- METODOS DE BUSCA ---

    def buscar_usuarios(self) -> List[Usuario]:
        """Busca todos os usuarios e os retorna como objetos Usuario."""
        query = "SELECT id, nome, email, funcao, status, role, hashed_password, require_password_change FROM usuarios"
        columns, results = self.db.execute_query(query, fetch_all=True)
        if results:
            return [Usuario(**dict(zip(columns, row))) for row in results]
        return []

    def buscar_usuario_por_email(self, email: str) -> Optional[Usuario]:
        """Busca um usuario pelo email."""
        query = "SELECT id, nome, email, funcao, status, role, hashed_password, require_password_change FROM usuarios WHERE email = %s"
        columns, result = self.db.execute_query(query, (email,), fetch_one=True)
        if result:
            return Usuario(**dict(zip(columns, result)))
        return None

    def buscar_usuario_por_id(self, user_id: int) -> Optional[Usuario]:
        """Busca um usuario pelo ID e retorna o objeto Usuario completo."""
        query = "SELECT id, nome, email, funcao, status, role, hashed_password, require_password_change FROM usuarios WHERE id = %s"
        columns, result = self.db.execute_query(query, (user_id,), fetch_one=True)
        if result:
            return Usuario(**dict(zip(columns, result)))
        return None

    # --- METODOS DE DADOS E DELECAO ---

    def verificar_credenciais(self, email: str, password: str) -> Optional[Usuario]:
        """Verifica se as credenciais do usuario sao validas (essencial para o Login)."""
        usuario = self.buscar_usuario_por_email(email)
        if usuario and verify_password(password, usuario.hashed_password):
            return usuario
        return None

    def deletar_usuario(self, usuario_id: int):
        query = "DELETE FROM usuarios WHERE id = %s"
        params = (usuario_id,)
        return self.db.execute_query(query, params, commit=True)

    def alterar_senha(self, email: str, old_password: str, new_password: str) -> bool:
        """Altera a senha se a senha atual confere e limpa o flag de troca obrigatoria."""
        usuario = self.buscar_usuario_por_email(email)
        if not usuario or not verify_password(old_password, usuario.hashed_password):
            return False
        new_hash = hash_password(new_password)
        return self.editar_usuario_seguro(
            user_id=usuario.id,
            role=usuario.role,
            hashed_password=new_hash,
            require_password_change=False,
        )
