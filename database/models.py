from . import get_db
from config import logging
from datetime import datetime

# --- Funções de Gestão de Usuários ---

def buscar_usuario_por_id(chat_id: int) -> dict | None:
    """
    Busca um usuário na tabela 'usuarios' pelo seu ID do Telegram.

    Args:
        chat_id: O ID do chat do usuário.

    Returns:
        Um dicionário com os dados do usuário se encontrado, caso contrário None.
    """
    try:
        db = get_db()
        response = db.table('usuarios').select('*').eq('chat_id', chat_id).single().execute()
        return response.data
    except Exception as e:
        logging.error(f"Erro ao buscar usuário por ID {chat_id}: {e}")
        return None

def verificar_matricula_existente(cadastro_empresa: str) -> bool:
    """Verifica se um cadastro de empresa (matrícula) já existe no banco."""
    try:
        db = get_db()
        response = db.table('usuarios').select('cadastro_empresa').eq('cadastro_empresa', cadastro_empresa).single().execute()
        return response.data is not None
    except Exception as e:
        # Um erro aqui geralmente significa que não encontrou, o que é o esperado.
        logging.info(f"Verificação de matrícula não encontrou registro (esperado): {e}")
        return False

def registrar_usuario(chat_id: int, nome: str, funcao: str, nivel: str, setor: str, cadastro_empresa: str) -> bool:
    """
    Registra um novo usuário na tabela 'usuarios'.

    Returns:
        True se o registro for bem-sucedido, False caso contrário.
    """
    try:
        db = get_db()
        # A API do Supabase levantará um erro em caso de violação de constraint (ex: chat_id duplicado)
        db.table('usuarios').insert({
            'chat_id': chat_id,
            'nome': nome,
            'funcao': funcao,
            'nivel': nivel,
            'setor': setor,
            'cadastro_empresa': cadastro_empresa
        }).execute()
        logging.info(f"Usuário {nome} (chat_id: {chat_id}) registrado com sucesso.")
        return True
    except Exception as e:
        logging.error(f"Falha ao registrar usuário {chat_id} no banco: {e}")
        return False