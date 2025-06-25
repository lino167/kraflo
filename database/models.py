from . import get_db
from config import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

# --- Funções de Gestão de Usuários ---

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

def criar_ordem_servico(chat_id: int, dados_os: Dict[str, Any]) -> bool:
    """
    Cria uma nova ordem de serviço na tabela 'ordens_servico'.
    Agora espera um dicionário com os dados da OS.
    """
    try:
        db = get_db()
        # Adiciona o chat_id e a data ao dicionário antes de inserir
        dados_os['chat_id'] = chat_id
        dados_os['data_abertura'] = datetime.now().isoformat()
        
        db.table('ordens_servico').insert(dados_os).execute()
        logging.info(f"Nova OS criada para o chat_id {chat_id}.")
        return True
    except Exception as e:
        logging.error(f"Falha ao criar OS para o chat_id {chat_id}: {e}")
        return False

def buscar_os_abertas_por_usuario(chat_id: int) -> List[Dict[str, Any]]:
    """
    Busca todas as OS abertas (sem data_fechamento) para um usuário específico.
    """
    try:
        db = get_db()
        response = db.table('ordens_servico').select('id, numero_maquina').eq('chat_id', chat_id).is_('data_fechamento', None).execute()
        return response.data if response.data else []
    except Exception as e:
        logging.error(f"Erro ao buscar OS abertas para o chat_id {chat_id}: {e}")
        return []

def fechar_ordem_servico(os_id: int, chat_id: int, dados_fechamento: Dict[str, Any]) -> bool:
    """
    Atualiza uma OS com as informações de fecho.
    """
    try:
        db = get_db()
        dados_fechamento['data_fechamento'] = datetime.now().isoformat()
        db.table('ordens_servico').update(dados_fechamento).eq('id', os_id).eq('chat_id', chat_id).execute()
        logging.info(f"OS ID {os_id} fechada com sucesso pelo chat_id {chat_id}.")
        return True
    except Exception as e:
        logging.error(f"Falha ao fechar a OS ID {os_id}: {e}")
        return False

def buscar_os_por_periodo(chat_id: int, data_inicio: str, data_fim: str) -> List[Dict[str, Any]]:
    """
    Busca todas as ordens de serviço de um usuário dentro de um intervalo de datas.
    """
    try:
        db = get_db()
        start_date_obj = datetime.strptime(data_inicio, '%Y-%m-%d')
        end_date_obj = datetime.strptime(data_fim, '%Y-%m-%d')
        
        next_day_obj = end_date_obj + timedelta(days=1)
        
        start_date_iso = start_date_obj.isoformat()
        next_day_iso = next_day_obj.isoformat()

        response = (
            db.table('ordens_servico')
            .select('*')
            .eq('chat_id', chat_id)
            .gte('data_abertura', start_date_iso)
            .lt('data_abertura', next_day_iso)
            .order('data_abertura', desc=False)
            .execute()
        )
        return response.data if response.data else []
    except Exception as e:
        logging.error(f"Erro ao buscar OS por período para o chat_id {chat_id}: {e}")
        return []
