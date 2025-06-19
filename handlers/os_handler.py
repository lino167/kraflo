from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler, CommandHandler, MessageHandler, 
    CallbackQueryHandler, filters, CallbackContext
)
from config import logging, UIBotao
from database.models import buscar_usuario_por_id, criar_ordem_servico
from .ui import get_main_keyboard

# Estados da conversa para criar OS
NUMERO_MAQUINA, MODELO_MAQUINA, TIPO_MANUTENCAO, PROBLEMA_APRESENTADO = range(5, 9)

async def criar_os_iniciar(update: Update, context: CallbackContext):
    """Ponto de entrada para iniciar a criação de uma OS."""
    chat_id = update.effective_chat.id
    
    # Verifica se o usuário está registrado antes de permitir a criação de OS
    usuario = buscar_usuario_por_id(chat_id)
    if not usuario:
        await update.message.reply_text(
            "Você precisa estar registrado para criar uma Ordem de Serviço. "
            "Por favor, use o comando /start para se registrar."
        )
        return ConversationHandler.END

    await update.message.reply_text("Vamos criar uma nova Ordem de Serviço. Qual é o número da máquina?")
    return NUMERO_MAQUINA

async def receber_numero_maquina(update: Update, context: CallbackContext):
    """Recebe o número da máquina e pergunta o modelo."""
    context.user_data['numero_maquina'] = update.message.text
    await update.message.reply_text("Ok. E qual é o modelo da máquina?")
    return MODELO_MAQUINA

async def receber_modelo_maquina(update: Update, context: CallbackContext):
    """Recebe o modelo e pergunta o tipo de manutenção."""
    context.user_data['modelo_maquina'] = update.message.text
    keyboard = [
        [InlineKeyboardButton("Preventiva", callback_data="Preventiva")],
        [InlineKeyboardButton("Corretiva", callback_data="Corretiva")],
        [InlineKeyboardButton("Preditiva", callback_data="Preditiva")]
    ]
    await update.message.reply_text(
        "Entendido. Agora, selecione o tipo de manutenção:", 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TIPO_MANUTENCAO

async def receber_tipo_manutencao(update: Update, context: CallbackContext):
    """Recebe o tipo de manutenção e pergunta a descrição do problema."""
    query = update.callback_query
    await query.answer()
    context.user_data['tipo_manutencao'] = query.data
    await query.edit_message_text(f"Tipo de manutenção: {query.data}.\n\nPor favor, descreva o problema apresentado.")
    return PROBLEMA_APRESENTADO

async def receber_problema_apresentado(update: Update, context: CallbackContext):
    """Recebe a descrição, salva a OS no banco e finaliza a conversa."""
    context.user_data['problema_apresentado'] = update.message.text

    sucesso = criar_ordem_servico(
        chat_id=update.effective_chat.id,
        numero_maquina=context.user_data['numero_maquina'],
        modelo_maquina=context.user_data['modelo_maquina'],
        tipo_manutencao=context.user_data['tipo_manutencao'],
        problema_apresentado=context.user_data['problema_apresentado']
    )

    if sucesso:
        await update.message.reply_text(
            "✅ Ordem de Serviço criada com sucesso!", 
            reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ Ocorreu um erro ao salvar a Ordem de Serviço. Tente novamente mais tarde.",
            reply_markup=get_main_keyboard()
        )
    
    return ConversationHandler.END

async def cancelar(update: Update, context: CallbackContext):
    """Cancela a operação atual de criação de OS."""
    await update.message.reply_text("Criação de OS cancelada.", reply_markup=get_main_keyboard())
    return ConversationHandler.END

def get_criar_os_handler() -> ConversationHandler:
    """Cria e retorna o ConversationHandler para o fluxo de criação de OS."""
    return ConversationHandler(
        # O entry_points define como a conversa pode ser iniciada.
        # Aqui, ela pode ser iniciada tanto pelo comando /criar_os quanto pelo texto do botão.
        entry_points=[
            CommandHandler("criar_os", criar_os_iniciar),
            MessageHandler(filters.Text([UIBotao.CRIAR_OS]), criar_os_iniciar)
        ],
        states={
            NUMERO_MAQUINA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_numero_maquina)],
            MODELO_MAQUINA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_modelo_maquina)],
            TIPO_MANUTENCAO: [CallbackQueryHandler(receber_tipo_manutencao)],
            PROBLEMA_APRESENTADO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_problema_apresentado)],
        },
        # O fallbacks define o que fazer se o utilizador enviar um comando inesperado.
        fallbacks=[CommandHandler("cancelar", cancelar)],
        per_message=False
    )
