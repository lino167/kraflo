from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler, CommandHandler, MessageHandler, 
    CallbackQueryHandler, filters, CallbackContext
)
from config import logging
from database.models import buscar_usuario_por_id, registrar_usuario, verificar_matricula_existente
from .ui import get_main_keyboard

# Definimos os "estados" da nossa conversa de registo.
# São como passos num formulário.
NOME, FUNCAO, NIVEL, SETOR, CADASTRO_EMPRESA = range(5)

async def start(update: Update, context: CallbackContext):
    """Função chamada quando o utilizador envia /start."""
    chat_id = update.effective_chat.id
    logging.info(f"Comando /start recebido do chat_id: {chat_id}")
    
    usuario = buscar_usuario_por_id(chat_id)
    
    if usuario:
        await update.message.reply_text(
            f"Bem-vindo(a) de volta, {usuario['nome']}! Selecione uma opção abaixo:",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "Olá! Parece que é a sua primeira vez no Kraflo.\n"
            "Vamos começar o seu registo. Por favor, diga-me o seu nome completo."
        )
        return NOME

async def receber_nome(update: Update, context: CallbackContext):
    """Recebe o nome e pergunta a função."""
    context.user_data['nome'] = update.message.text
    keyboard = [
        [InlineKeyboardButton("Mecânico", callback_data="Mecânico")],
        [InlineKeyboardButton("Eletricista", callback_data="Eletricista")],
        [InlineKeyboardButton("Outro", callback_data="Outro")]
    ]
    await update.message.reply_text("Ótimo! Agora, qual é a sua função?", reply_markup=InlineKeyboardMarkup(keyboard))
    return FUNCAO

async def receber_funcao(update: Update, context: CallbackContext):
    """Recebe a função e pergunta o nível."""
    query = update.callback_query
    await query.answer()
    context.user_data['funcao'] = query.data
    await query.edit_message_text(f"Função definida: {query.data}.\n\nQual é o seu nível? (Ex: Júnior, Pleno, Sénior)")
    return NIVEL

async def receber_nivel(update: Update, context: CallbackContext):
    """Recebe o nível e pergunta o setor."""
    context.user_data['nivel'] = update.message.text
    await update.message.reply_text("Entendido. E qual é o seu setor de trabalho?")
    return SETOR

async def receber_setor(update: Update, context: CallbackContext):
    """Recebe o setor e pede a matrícula."""
    context.user_data['setor'] = update.message.text
    await update.message.reply_text("Para finalizar, informe o seu número de matrícula (ou um código de registo único).")
    return CADASTRO_EMPRESA

async def receber_cadastro_empresa(update: Update, context: CallbackContext):
    """Recebe a matrícula, valida, e finaliza o registo."""
    matricula = update.message.text
    
    if verificar_matricula_existente(matricula):
        await update.message.reply_text(
            "⚠️ Este número de matrícula já está em uso. Por favor, insira uma matrícula válida ou contacte o suporte."
        )
        return CADASTRO_EMPRESA # Permanece no mesmo estado, a pedir a matrícula novamente.

    sucesso = registrar_usuario(
        chat_id=update.effective_chat.id,
        nome=context.user_data['nome'],
        funcao=context.user_data['funcao'],
        nivel=context.user_data['nivel'],
        setor=context.user_data['setor'],
        cadastro_empresa=matricula
    )
    
    if sucesso:
        await update.message.reply_text(
            "✅ Registo realizado com sucesso! Bem-vindo(a) ao Kraflo!\n\n"
            "Selecione uma opção abaixo para começar:",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "❌ Ocorreu um erro inesperado ao salvar o seu registo. Por favor, tente iniciar o processo novamente com /start."
        )
        return ConversationHandler.END

async def cancelar(update: Update, context: CallbackContext):
    """Cancela a operação atual."""
    await update.message.reply_text("Operação cancelada.")
    return ConversationHandler.END

def get_start_handler() -> ConversationHandler:
    """Cria e retorna o ConversationHandler para o fluxo de registo."""
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_nome)],
            FUNCAO: [CallbackQueryHandler(receber_funcao)],
            NIVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_nivel)],
            SETOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_setor)],
            CADASTRO_EMPRESA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_cadastro_empresa)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
        per_message=False # Garante que a conversa seja por utilizador, não por mensagem
    )
