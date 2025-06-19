import os
from dotenv import load_dotenv
import logging

# Carrega as variáveis de ambiente do ficheiro .env
# Isto permite-nos manter as chaves secretas fora do código fonte.
load_dotenv()

# --- Configuração do Logging ---
# Configura um sistema de logging básico para nos ajudar a depurar a aplicação.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

# --- Configurações do Telegram ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_TOKEN:
    logging.error("O token do Telegram (TELEGRAM_BOT_TOKEN) não foi encontrado nas variáveis de ambiente.")
    raise ValueError("Token do Telegram não configurado.")

# --- Configurações do Supabase ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logging.error("As credenciais do Supabase (URL e KEY) não foram encontradas.")
    raise ValueError("Credenciais do Supabase não configuradas.")

# --- Configurações Gerais da Aplicação ---
# Define o diretório onde os relatórios em PDF serão salvos temporariamente.
PDF_SAVE_PATH = "temp_pdfs/"

# Define textos de botões para serem usados em toda a aplicação.
# Centralizar isto aqui facilita a manutenção.
class UIBotao:
    CRIAR_OS = "➕ Criar Nova OS"
    FECHAR_OS = "✔️ Fechar OS"
    GERAR_RELATORIO = "📊 Gerar Relatório"