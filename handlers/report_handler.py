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

(
    ESCOLHER_OPCAO, 
    PROCESSAR_CALENDARIO_DIA, 
    CONFIRMAR_DIA_UNICO,
    PROCESSAR_CALENDARIO_INICIO, 
    PROCESSAR_CALENDARIO_FIM,
    CONFIRMAR_INTERVALO
) = range(16, 22)

async def relatorio_iniciar(update: Update, context: CallbackContext):
    """Ponto de entrada para o fluxo de geração de relatórios."""
    context.user_data.clear()
    keyboard = [
        [InlineKeyboardButton("Relatório de um Dia Específico", callback_data="dia_unico")],
        [InlineKeyboardButton("Relatório por Intervalo de Datas", callback_data="intervalo")],
        [InlineKeyboardButton("Cancelar Operação", callback_data="cancelar_geral")],
    ]
    await update.message.reply_text("Como deseja gerar o relatório?", reply_markup=InlineKeyboardMarkup(keyboard))
    return ESCOLHER_OPCAO

async def escolher_opcao(update: Update, context: CallbackContext):
    """Processa a opção do utilizador (dia único ou intervalo)."""
    query = update.callback_query
    await query.answer()
    
    # Se o utilizador cancelar
    if query.data == 'cancelar_geral':
        return await cancelar(update, context)

    if query.data == "dia_unico":
        calendar, step = DetailedTelegramCalendar().build()
        await query.edit_message_text(f"Selecione o dia para o relatório.\n{LSTEP[step]}", reply_markup=calendar)
        return PROCESSAR_CALENDARIO_DIA
    elif query.data == "intervalo":
        calendar, step = DetailedTelegramCalendar().build()
        await query.edit_message_text(f"Selecione a DATA INICIAL do intervalo.\n{LSTEP[step]}", reply_markup=calendar)
        return PROCESSAR_CALENDARIO_INICIO

async def processar_calendario_dia(update: Update, context: CallbackContext):
    """Processa a seleção de data e pede confirmação."""
    query = update.callback_query
    await query.answer()
    result, key, step = DetailedTelegramCalendar().process(query.data)

    if not result and key:
        await query.edit_message_text(f"Selecione o dia.\n{LSTEP[step]}", reply_markup=key)
        return PROCESSAR_CALENDARIO_DIA
    elif result:
        context.user_data['data_selecionada'] = result
        keyboard = [
            [InlineKeyboardButton("✅ Confirmar e Gerar", callback_data="confirmar")],
            [InlineKeyboardButton("✏️ Escolher Outra Data", callback_data="voltar")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")],
        ]
        await query.edit_message_text(
            f"Você selecionou a data: {result.strftime('%d/%m/%Y')}.\n\nConfirma a geração do relatório?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CONFIRMAR_DIA_UNICO

async def confirmar_dia_unico(update: Update, context: CallbackContext):
    """Gere as ações de confirmação, voltar ou cancelar para dia único."""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'confirmar':
        data = context.user_data['data_selecionada']
        data_str = data.strftime('%Y-%m-%d')
        await query.edit_message_text(f"A gerar relatório para {data.strftime('%d/%m/%Y')}. Aguarde...")
        await gerar_e_enviar_pdf(update, context, data_str, data_str)
        return ConversationHandler.END
    elif query.data == 'voltar':
        calendar, step = DetailedTelegramCalendar().build()
        await query.edit_message_text(f"Seleção anterior cancelada. Escolha o dia novamente.\n{LSTEP[step]}", reply_markup=calendar)
        return PROCESSAR_CALENDARIO_DIA
    else: # Cancelar
        return await cancelar(update, context)

async def processar_calendario_inicio(update: Update, context: CallbackContext):
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
    query = update.callback_query
    await query.answer()
    result, key, step = DetailedTelegramCalendar(min_date=context.user_data['data_inicio']).process(query.data)

    if not result and key:
        await query.edit_message_text(f"Selecione a DATA FINAL.\n{LSTEP[step]}", reply_markup=key)
        return PROCESSAR_CALENDARIO_FIM
    elif result:
        context.user_data['data_fim'] = result
        data_inicio = context.user_data['data_inicio']
        keyboard = [
            [InlineKeyboardButton("✅ Confirmar e Gerar", callback_data="confirmar")],
            [InlineKeyboardButton("✏️ Escolher Outro Período", callback_data="voltar")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")],
        ]
        await query.edit_message_text(
            f"Você selecionou o período de {data_inicio.strftime('%d/%m/%Y')} a {result.strftime('%d/%m/%Y')}.\n\nConfirma a geração do relatório?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CONFIRMAR_INTERVALO

async def confirmar_intervalo(update: Update, context: CallbackContext):
    """Gere as ações de confirmação, voltar ou cancelar para intervalo."""
    query = update.callback_query
    await query.answer()

    if query.data == 'confirmar':
        data_inicio = context.user_data['data_inicio'].strftime('%Y-%m-%d')
        data_fim = context.user_data['data_fim'].strftime('%Y-%m-%d')
        await query.edit_message_text(f"A gerar relatório para o período selecionado. Aguarde...")
        await gerar_e_enviar_pdf(update, context, data_inicio, data_fim)
        return ConversationHandler.END
    elif query.data == 'voltar':
        # Volta para o primeiro passo, de escolher dia único ou intervalo
        return await relatorio_iniciar(query, context)
    else: # Cancelar
        return await cancelar(update, context)


async def gerar_e_enviar_pdf(update: Update, context: CallbackContext, data_inicio: str, data_fim: str):
    """Função auxiliar para buscar dados, gerar e enviar o PDF."""
    chat_id = update.effective_chat.id
    usuario = buscar_usuario_por_id(chat_id)
    ordens = buscar_os_por_periodo(chat_id, data_inicio, data_fim)

    if not usuario or not ordens:
        await context.bot.send_message(chat_id, "Nenhuma Ordem de Serviço foi encontrada para o período selecionado.")
    else:
        periodo_str = f"{datetime.strptime(data_inicio, '%Y-%m-%d').strftime('%d/%m/%Y')} a {datetime.strptime(data_fim, '%Y-%m-%d').strftime('%d/%m/%Y')}"
        filepath = gerar_relatorio_pdf(usuario, ordens, periodo_str)
        if filepath and os.path.exists(filepath):
            await context.bot.send_document(chat_id, document=open(filepath, 'rb'), filename=os.path.basename(filepath))
            os.remove(filepath)
        else:
            await context.bot.send_message(chat_id, "Ocorreu um erro ao gerar o seu relatório em PDF.")
    
    await context.bot.send_message(chat_id, "Selecione uma nova opção:", reply_markup=get_main_keyboard())


async def cancelar(update: Update, context: CallbackContext):
    """Cancela a operação atual."""
    query = update.callback_query
    await query.edit_message_text("Operação cancelada.", reply_markup=None)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Selecione uma opção:",
        reply_markup=get_main_keyboard()
    )
    context.user_data.clear()
    return ConversationHandler.END


def get_report_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("relatorio", relatorio_iniciar),
            MessageHandler(filters.Text([UIBotao.GERAR_RELATORIO]), relatorio_iniciar)
        ],
        states={
            ESCOLHER_OPCAO: [CallbackQueryHandler(escolher_opcao)],
            PROCESSAR_CALENDARIO_DIA: [CallbackQueryHandler(processar_calendario_dia)],
            CONFIRMAR_DIA_UNICO: [CallbackQueryHandler(confirmar_dia_unico)],
            PROCESSAR_CALENDARIO_INICIO: [CallbackQueryHandler(processar_calendario_inicio)],
            PROCESSAR_CALENDARIO_FIM: [CallbackQueryHandler(processar_calendario_fim)],
            CONFIRMAR_INTERVALO: [CallbackQueryHandler(confirmar_intervalo)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
        per_message=False
    )
