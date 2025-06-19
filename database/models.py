from . import get_db
from config import logging
from datetime import datetime
from typing import Dict, Any, List

# --- Funções de Gestão de Usuários (sem alterações) ---

def buscar_usuario_por_id(chat_id: int) -> Dict[str, Any] | None:
    try:
        db = get_db()
        response = db.table('usuarios').select('*').eq('chat_id', chat_id).single().execute()
        return response.data
    except Exception as e:
        logging.error(f"Erro ao buscar usuário por ID {chat_id}: {e}")
        return None

def verificar_matricula_existente(cadastro_empresa: str) -> bool:
    try:
        db = get_db()
        response = db.table('usuarios').select('cadastro_empresa').eq('cadastro_empresa', cadastro_empresa).single().execute()
        return response.data is not None
    except Exception:
        return False

def registrar_usuario(chat_id: int, nome: str, funcao: str, nivel: str, setor: str, cadastro_empresa: str) -> bool:
    try:
        db = get_db()
        db.table('usuarios').insert({
            'chat_id': chat_id, 'nome': nome, 'funcao': funcao, 
            'nivel': nivel, 'setor': setor, 'cadastro_empresa': cadastro_empresa
        }).execute()
        logging.info(f"Usuário {nome} (chat_id: {chat_id}) registrado com sucesso.")
        return True
    except Exception as e:
        logging.error(f"Falha ao registrar usuário {chat_id} no banco: {e}")
        return False

# --- Funções de Gestão de Ordens de Serviço ---

def criar_ordem_servico(chat_id: int, numero_maquina: str, modelo_maquina: str, tipo_manutencao: str, problema_apresentado: str) -> bool:
    try:
        db = get_db()
        db.table('ordens_servico').insert({
            'chat_id': chat_id, 'numero_maquina': numero_maquina, 'modelo_maquina': modelo_maquina,
            'tipo_manutencao': tipo_manutencao, 'problema_apresentado': problema_apresentado,
            'data_abertura': datetime.now().isoformat()
        }).execute()
        logging.info(f"Nova OS criada para o chat_id {chat_id} na máquina {numero_maquina}.")
        return True
    except Exception as e:
        logging.error(f"Falha ao criar OS para o chat_id {chat_id}: {e}")
        return False

# --- NOVAS FUNÇÕES ADICIONADAS NESTA ETAPA ---

def buscar_os_abertas_por_usuario(chat_id: int) -> List[Dict[str, Any]]:
    """Busca todas as OS abertas (sem data_fechamento) para um usuário específico."""
    try:
        db = get_db()
        # Selecionamos apenas os campos necessários para a listagem inicial
        response = db.table('ordens_servico').select('id, numero_maquina').eq('chat_id', chat_id).is_('data_fechamento', None).execute()
        return response.data if response.data else []
    except Exception as e:
        logging.error(f"Erro ao buscar OS abertas para o chat_id {chat_id}: {e}")
        return []

def fechar_ordem_servico(os_id: int, chat_id: int, dados_fechamento: Dict[str, Any]) -> bool:
    """
    Atualiza uma OS com as informações de fecho.

    Args:
        os_id: O ID da Ordem de Serviço a ser fechada.
        chat_id: O ID do chat do usuário para garantir a posse da OS.
        dados_fechamento: Um dicionário contendo todas as informações de fecho.

    Returns:
        True se a atualização for bem-sucedida, False caso contrário.
    """
    try:
        db = get_db()
        # Adiciona a data de fecho ao dicionário
        dados_fechamento['data_fechamento'] = datetime.now().isoformat()
        
        # O .eq('chat_id', chat_id) é uma camada extra de segurança para garantir
        # que um utilizador só pode fechar as suas próprias OS.
        db.table('ordens_servico').update(dados_fechamento).eq('id', os_id).eq('chat_id', chat_id).execute()
        logging.info(f"OS ID {os_id} fechada com sucesso pelo chat_id {chat_id}.")
        return True
    except Exception as e:
        logging.error(f"Falha ao fechar a OS ID {os_id}: {e}")
        return False
