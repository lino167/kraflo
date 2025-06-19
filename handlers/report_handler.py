import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler, CommandHandler, MessageHandler, 
    CallbackQueryHandler, filters, CallbackContext
)
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

from config import logging, UIBotao
from database.models import buscar_usuario_por_id, buscar_os_por_periodo
from utils.pdf_generator import gerar_relatorio_pdf
from .ui import get_main_keyboard

# Estados da conversa
ESCOLHER_OPCAO, PROCESSAR_CALENDARIO_DIA, PROCESSAR_CALENDARIO_INICIO, PROCESSAR_CALENDARIO_FIM = range(16, 20)

async def relatorio_iniciar(update: Update, context: CallbackContext):
    """Ponto de entrada para o fluxo de geração de relatórios."""
    keyboard = [
        [InlineKeyboardButton("Relatório de um Dia Específico", callback_data="dia_unico")],
        [InlineKeyboardButton("Relatório por Intervalo de Datas", callback_data="intervalo")],
    ]
    await update.message.reply_text("Como deseja gerar o relatório?", reply_markup=InlineKeyboardMarkup(keyboard))
    return ESCOLHER_OPCAO

async def escolher_opcao(update: Update, context: CallbackContext):
    """Processa a opção do utilizador (dia único ou intervalo)."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "dia_unico":
        calendar, step = DetailedTelegramCalendar().build()
        await query.edit_message_text(f"Selecione o dia para o relatório.\n{LSTEP[step]}", reply_markup=calendar)
        return PROCESSAR_CALENDARIO_DIA
    elif query.data == "intervalo":
        calendar, step = DetailedTelegramCalendar().build()
        await query.edit_message_text(f"Selecione a DATA INICIAL do intervalo.\n{LSTEP[step]}", reply_markup=calendar)
        return PROCESSAR_CALENDARIO_INICIO

async def processar_calendario_dia(update: Update, context: CallbackContext):
    """Processa a seleção de data para o relatório de dia único."""
    query = update.callback_query
    await query.answer()
    result, key, step = DetailedTelegramCalendar().process(query.data)

    if not result and key:
        await query.edit_message_text(f"Selecione o dia.\n{LSTEP[step]}", reply_markup=key)
        return PROCESSAR_CALENDARIO_DIA
    elif result:
        await query.edit_message_text(f"A gerar relatório para {result.strftime('%d/%m/%Y')}. Aguarde...")
        # Gera o relatório para um único dia (data_inicio = data_fim)
        await gerar_e_enviar_pdf(update, context, result.strftime('%Y-%m-%d'), result.strftime('%Y-%m-%d'))
        return ConversationHandler.END

async def processar_calendario_inicio(update: Update, context: CallbackContext):
    """Processa a seleção da data inicial para o intervalo."""
    query = update.callback_query
    await query.answer()
    result, key, step = DetailedTelegramCalendar().process(query.data)

    if not result and key:
        await query.edit_message_text(f"Selecione a DATA INICIAL.\n{LSTEP[step]}", reply_markup=key)
        return PROCESSAR_CALENDARIO_INICIO
    elif result:
        context.user_data['data_inicio'] = result
        calendar, step = DetailedTelegramCalendar(min_date=result).build()
        await query.edit_message_text(f"Data inicial: {result.strftime('%d/%m/%Y')}.\nAgora, selecione a DATA FINAL.", reply_markup=calendar)
        return PROCESSAR_CALENDARIO_FIM

async def processar_calendario_fim(update: Update, context: CallbackContext):
    """Processa a seleção da data final e gera o relatório do intervalo."""
    query = update.callback_query
    await query.answer()
    result, key, step = DetailedTelegramCalendar(min_date=context.user_data['data_inicio']).process(query.data)

    if not result and key:
        await query.edit_message_text(f"Selecione a DATA FINAL.\n{LSTEP[step]}", reply_markup=key)
        return PROCESSAR_CALENDARIO_FIM
    elif result:
        data_inicio_str = context.user_data['data_inicio'].strftime('%Y-%m-%d')
        data_fim_str = result.strftime('%Y-%m-%d')
        await query.edit_message_text(f"A gerar relatório para o período de {context.user_data['data_inicio'].strftime('%d/%m/%Y')} a {result.strftime('%d/%m/%Y')}. Aguarde...")
        await gerar_e_enviar_pdf(update, context, data_inicio_str, data_fim_str)
        return ConversationHandler.END

async def gerar_e_enviar_pdf(update: Update, context: CallbackContext, data_inicio: str, data_fim: str):
    """Função auxiliar para buscar dados, gerar e enviar o PDF."""
    chat_id = update.effective_chat.id
    usuario = buscar_usuario_por_id(chat_id)
    ordens = buscar_os_por_periodo(chat_id, data_inicio, data_fim)

    if not usuario:
        await context.bot.send_message(chat_id, "Erro: não foi possível encontrar o seu registo de utilizador.")
        return

    if not ordens:
        await context.bot.send_message(chat_id, f"Nenhuma Ordem de Serviço encontrada para o período selecionado.")
        return

    periodo_str = f"{datetime.strptime(data_inicio, '%Y-%m-%d').strftime('%d/%m/%Y')} a {datetime.strptime(data_fim, '%Y-%m-%d').strftime('%d/%m/%Y')}"
    filepath = gerar_relatorio_pdf(usuario, ordens, periodo_str)
    
    if filepath and os.path.exists(filepath):
        await context.bot.send_document(chat_id, document=open(filepath, 'rb'), filename=os.path.basename(filepath))
        os.remove(filepath) # Limpa o ficheiro após o envio
    else:
        await context.bot.send_message(chat_id, "Ocorreu um erro ao gerar o seu relatório em PDF.")
        
    await context.bot.send_message(chat_id, "Selecione uma nova opção:", reply_markup=get_main_keyboard())


def get_report_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("relatorio", relatorio_iniciar),
            MessageHandler(filters.Text([UIBotao.GERAR_RELATORIO]), relatorio_iniciar)
        ],
        states={
            ESCOLHER_OPCAO: [CallbackQueryHandler(escolher_opcao)],
            PROCESSAR_CALENDARIO_DIA: [CallbackQueryHandler(processar_calendario_dia)],
            PROCESSAR_CALENDARIO_INICIO: [CallbackQueryHandler(processar_calendario_inicio)],
            PROCESSAR_CALENDARIO_FIM: [CallbackQueryHandler(processar_calendario_fim)],
        },
        fallbacks=[CommandHandler("cancelar", lambda u,c: (u.message.reply_text("Operação cancelada."), ConversationHandler.END))],
        per_message=False
    )
