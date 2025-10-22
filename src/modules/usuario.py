# src/modules/usuario.py

from typing import Optional
from src.utils.database_manager import DatabaseManager
from src.utils.models import Usuario 

class UsuarioService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        
    def registrar_usuario(self, usuario: Usuario):
        """Registra um usuário ou retorna o ID se já existir."""
        # 1. Tenta buscar o usuário primeiro
        usuario_existente = self.buscar_usuario_por_email(usuario.email)
        if usuario_existente:
            # Encontrado! Retorna o ID do existente para manter a ordem.
            print(f" (Alerta Washu: Usuário '{usuario.nome}' já existe. Usando ID: {usuario_existente.id})")
            return usuario_existente.id

        # 2. Se não existir, insere e retorna o novo ID
        query = "INSERT INTO usuarios (nome, email, funcao, status) VALUES (?, ?, ?, ?)"
        params = (usuario.nome, usuario.email, usuario.funcao, usuario.status)
        
        # Agora execute_query vai retornar o lastrowid!
        return self.db.execute_query(query, params, commit=True)
    
    def buscar_usuarios(self):
        """Busca todos os usuários e os retorna como objetos Usuario."""
        query = "SELECT id, nome, email, funcao, status FROM usuarios"
        columns, results = self.db.execute_query(query, fetch_all=True)
        
        # A MÁGICA DA TRANSMUTAÇÃO: Converte tuplas SQL para objetos Usuario
        if results:
            return [Usuario(**dict(zip(columns, row))) for row in results]
        return []
    
    def buscar_usuario_por_email(self, email: str) -> Optional[Usuario]:
        """Busca um usuário pelo email."""
        query = "SELECT id, nome, email, funcao, status FROM usuarios WHERE email = ?"
        columns, result = self.db.execute_query(query, (email,), fetch_one=True)
        if result:
            return Usuario(**dict(zip(columns, result)))
        return None

    def editar_usuario(self, usuario_id, nome, email, funcao, status):
        # ... (Outros métodos CRUD estão corretos em sua lógica)
        query = "UPDATE usuarios SET nome = ?, email = ?, funcao = ?, status = ? WHERE id = ?"
        params = (nome, email, funcao, status, usuario_id)
        return self.db.execute_query(query, params, commit=True)
    
    def deletar_usuario(self, usuario_id: int):
        # ...
        query = "DELETE FROM usuarios WHERE id = ?"
        params = (usuario_id,)
        return self.db.execute_query(query, params, commit=True)