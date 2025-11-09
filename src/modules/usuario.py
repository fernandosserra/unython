# src/modules/usuario.py (VERSÃO FINAL SANADA)

from typing import Optional, List
from src.utils.database_manager import DatabaseManager
from src.utils.models import Usuario 
from src.utils.security import hash_password, verify_password # Adicionado verify_password

class UsuarioService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    # --- MÉTODOS DE SEGURANÇA E REGISTRO ---
    
    def editar_usuario_seguro(self, user_id: int, role: str, hashed_password: str) -> bool:
        """Atualiza role e hashed_password para um usuário existente."""
        query = "UPDATE usuarios SET role = %s, hashed_password = %s WHERE id = %s"
        params = (role, hashed_password, user_id)
        return self.db.execute_query(query, params, commit=True)
        
    
    def registrar_usuario(self, usuario: Usuario, password: str):
        """Registra um novo usuário com a senha criptografada (com UPSERT)."""
        
        usuario_existente = self.buscar_usuario_por_email(usuario.email)
        hashed_pwd = hash_password(password)
        
        if usuario_existente:
            # PROTOCOLO UPSERT: ATUALIZA a senha e o role no DB
            self.editar_usuario_seguro(usuario_existente.id, usuario.role, hashed_pwd)
            print(f" (Alerta Washu: Usuário '{usuario.nome}' atualizado. Usando ID: {usuario_existente.id})")
            return usuario_existente.id
        
        # Se não existe, insere (código original)
        query = "INSERT INTO usuarios (nome, email, funcao, status, role, hashed_password) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id"
        params = (usuario.nome, usuario.email, usuario.funcao, usuario.status, usuario.role, hashed_pwd)
        
        return self.db.execute_query(query, params, commit=True)

    # --- MÉTODOS DE BUSCA ---
    
    def buscar_usuarios(self) -> List[Usuario]:
        """Busca todos os usuários e os retorna como objetos Usuario."""
        # CRÍTICO: Incluir 'hashed_password' e 'role' no SELECT
        query = "SELECT id, nome, email, funcao, status, role, hashed_password FROM usuarios" 
        columns, results = self.db.execute_query(query, fetch_all=True)
        
        if results:
            return [Usuario(**dict(zip(columns, row))) for row in results]
        return []
    
    def buscar_usuario_por_email(self, email: str) -> Optional[Usuario]:
        """Busca um usuário pelo email."""
        # CRÍTICO: Incluir 'hashed_password' e 'role' no SELECT
        query = "SELECT id, nome, email, funcao, status, role, hashed_password FROM usuarios WHERE email = %s" 
        columns, result = self.db.execute_query(query, (email,), fetch_one=True)
        if result:
            return Usuario(**dict(zip(columns, result)))
        return None
    
    def buscar_usuario_por_id(self, user_id: int) -> Optional[Usuario]:
        """Busca um usuário pelo ID e retorna o objeto Usuario completo."""
        
        # A query deve ser a mesma da busca por email, mas o WHERE é pelo ID
        query = "SELECT id, nome, email, funcao, status, role, hashed_password FROM usuarios WHERE id = %s" 
        
        columns, result = self.db.execute_query(query, (user_id,), fetch_one=True)
        
        if result:
            # Transmutação de Dados (SQL -> Usuario Model)
            return Usuario(**dict(zip(columns, result)))
        return None
        
    # --- MÉTODOS DE DADOS E DELEÇÃO (Removido o editar_usuario que estava quebrado) ---
    
    def verificar_credenciais(self, email: str, password: str) -> Optional[Usuario]:
        """Verifica se as credenciais do usuário são válidas (essencial para o Login)."""
        usuario = self.buscar_usuario_por_email(email)
        if usuario and verify_password(password, usuario.hashed_password):
            return usuario
        return None

    def deletar_usuario(self, usuario_id: int):
        query = "DELETE FROM usuarios WHERE id = %s"
        params = (usuario_id,)
        return self.db.execute_query(query, params, commit=True)