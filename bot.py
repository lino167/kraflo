from telegram.ext import Application
from config import TELEGRAM_TOKEN, logging
from handlers.start import get_start_handler
from handlers.os_handler import get_criar_os_handler, get_fechar_os_handler 

def main() -> None:
    """
    Ponto de entrada principal do bot.
    Configura a aplicação e inicia o polling para receber mensagens.
    """
    logging.info("A iniciar a aplicação do bot Kraflo...")

    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Adiciona os handlers (gestores de comandos/conversas) à aplicação
    application.add_handler(get_start_handler())
    application.add_handler(get_criar_os_handler())
    application.add_handler(get_fechar_os_handler())
    # ... aqui iremos adicionar o handler de relatório no futuro

    logging.info("Bot iniciado. A aguardar mensagens...")
    
    # Inicia o bot. Ele ficará a escutar por novas mensagens até que o processo seja interrompido.
    application.run_polling()

if __name__ == "__main__":
    main()