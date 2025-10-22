# src/utils/config.py
# O Módulo de Customização Universal da Washu

# --- CONFIGURAÇÃO PADRÃO DA APLICAÇÃO ---
DB_NAME = "unython.db"

# --- DEFINIÇÃO DOS ALIASES UNIVERSAIS (Onde a mágica acontece!) ---
# Padrões usados no código e DB à esquerda, Aliases Customizados à direita.

CUSTOM_LABELS = {
    # Alias para o Facilitador (Quem atende)
    "FACILITADOR": "Sacerdote",  # Ex: 'Pastor', 'Profissional', 'Obreiro'
    
    # Alias para a Pessoa (Quem é atendido)
    "PESSOA": "Consulente",     # Ex: 'Fiel', 'Assistido(a)', 'Cliente'
    
    # Alias para a função do Facilitador dentro do sistema
    "FUNCAO_FACILITADOR": "Médium", # Ex: 'Diácono', 'Assistente Social', 'Psicólogo'

    # Alias para o tipo de Agendamento
    "TIPO_SERVICO": "Passe e Aconselhamento" # Ex: 'Eucaristia', 'Reunião', 'Entrevista'
}

def get_alias(key: str) -> str:
    """Função de Genialidade: Retorna o Alias customizado, se existir."""
    return CUSTOM_LABELS.get(key, key)