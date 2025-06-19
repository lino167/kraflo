from . import get_db
from config import logging
from datetime import datetime
from typing import Dict, Any, List

# --- Funções de Gestão de Usuários ---

def buscar_usuario_por_id(chat_id: int) -> Dict[str, Any] | None:
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
    except Exception:
        return False

def registrar_usuario(chat_id: int, nome: str, funcao: str, nivel: str, setor: str, cadastro_empresa: str) -> bool:
    """
    Registra um novo usuário na tabela 'usuarios'.

    Returns:
        True se o registro for bem-sucedido, False caso contrário.
    """
    try:
        db = get_db()
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

# --- Funções de Gestão de Ordens de Serviço ---

def criar_ordem_servico(chat_id: int, numero_maquina: str, modelo_maquina: str, tipo_manutencao: str, problema_apresentado: str) -> bool:
    """
    Cria uma nova ordem de serviço na tabela 'ordens_servico'.

    Returns:
        True se a OS for criada com sucesso, False caso contrário.
    """
    try:
        db = get_db()
        db.table('ordens_servico').insert({
            'chat_id': chat_id,
            'numero_maquina': numero_maquina,
            'modelo_maquina': modelo_maquina,
            'tipo_manutencao': tipo_manutencao,
            'problema_apresentado': problema_apresentado,
            'data_abertura': datetime.now().isoformat()
        }).execute()
        logging.info(f"Nova OS criada para o chat_id {chat_id} na máquina {numero_maquina}.")
        return True
    except Exception as e:
        logging.error(f"Falha ao criar OS para o chat_id {chat_id}: {e}")
        return False