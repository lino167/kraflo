from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler, CommandHandler, MessageHandler, 
    CallbackQueryHandler, filters, CallbackContext
)
from config import logging, UIBotao
from database.models import buscar_usuario_por_id, criar_ordem_servico, buscar_os_abertas_por_usuario, fechar_ordem_servico
from .ui import get_main_keyboard

# --- Estados da Conversa ---
# Adicionamos um estado genérico para confirmação no início dos fluxos
CONFIRMAR_ACAO = 0

# Estados de Criação de OS
NUMERO_MAQUINA, MODELO_MAQUINA, TIPO_MANUTENCAO, PROBLEMA_APRESENTADO = range(5, 9)

# Estados de Fecho de OS
SELECIONAR_OS, SOLUCAO_APLICADA, PERGUNTAR_PECA, DESCRICAO_PECA, TAG_PECA, SERVICO_CONCLUIDO, PERGUNTAR_OBSERVACAO, OBSERVACOES = range(9, 17)


# --- Funções de Confirmação e Cancelamento ---

async def confirmar_acao(update: Update, context: CallbackContext):
    """Gere a resposta dos botões de confirmação 'Sim'/'Não'."""
    query = update.callback_query
    await query.answer()
    
    acao_pendente = context.user_data.get('acao_pendente')

    if query.data == 'nao':
        await query.edit_message_text("Operação cancelada.")
        return await cancelar(update, context)

    if acao_pendente == 'criar_os':
        await query.edit_message_text("Ok, vamos criar uma nova Ordem de Serviço.")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Qual é o número da máquina? (Apenas números)")
        return NUMERO_MAQUINA
        
    elif acao_pendente == 'fechar_os':
        await query.edit_message_text("Ok, a procurar as suas Ordens de Serviço abertas...")
        return await listar_os_para_fechar(update, context)

async def cancelar(update: Update, context: CallbackContext):
    """Função genérica para cancelar e limpar qualquer conversa."""
    if update.callback_query:
        # Se a origem for um botão, não podemos usar reply_text
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Operação cancelada.",
            reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text("Operação cancelada.", reply_markup=get_main_keyboard())
    
    context.user_data.clear()
    return ConversationHandler.END


# <<< --- FLUXO DE CRIAÇÃO DE OS --- >>>

async def criar_os_iniciar(update: Update, context: CallbackContext):
    """Ponto de entrada para criar OS. Pede confirmação."""
    context.user_data.clear()
    usuario = buscar_usuario_por_id(update.effective_chat.id)
    if not usuario:
        await update.message.reply_text("Você precisa estar registrado para criar uma OS. Use /start para se registrar.")
        return ConversationHandler.END
        
    context.user_data['acao_pendente'] = 'criar_os'
    keyboard = [[InlineKeyboardButton("Sim, criar OS", callback_data="sim")], [InlineKeyboardButton("Não", callback_data="nao")]]
    await update.message.reply_text("Tem a certeza de que deseja criar uma nova Ordem de Serviço?", reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRMAR_ACAO

async def receber_numero_maquina(update: Update, context: CallbackContext):
    """Recebe e VALIDA o número da máquina."""
    numero_maquina_texto = update.message.text
    if not numero_maquina_texto.isdigit():
        await update.message.reply_text("❌ Entrada inválida. Por favor, insira apenas números para a máquina.")
        return NUMERO_MAQUINA 
    
    context.user_data['numero_maquina'] = int(numero_maquina_texto)
    await update.message.reply_text("Ok. E qual é o modelo da máquina?")
    return MODELO_MAQUINA

async def receber_modelo_maquina(update: Update, context: CallbackContext):
    context.user_data['modelo_maquina'] = update.message.text
    keyboard = [[InlineKeyboardButton("Preventiva", callback_data="Preventiva")], [InlineKeyboardButton("Corretiva", callback_data="Corretiva")],[InlineKeyboardButton("Preditiva", callback_data="Preditiva")]]
    await update.message.reply_text("Selecione o tipo de manutenção:", reply_markup=InlineKeyboardMarkup(keyboard))
    return TIPO_MANUTENCAO

async def receber_tipo_manutencao(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    context.user_data['tipo_manutencao'] = query.data
    await query.edit_message_text(f"Tipo: {query.data}.\n\nPor favor, descreva o problema apresentado.")
    return PROBLEMA_APRESENTADO

async def receber_problema_apresentado(update: Update, context: CallbackContext):
    context.user_data['problema_apresentado'] = update.message.text
    sucesso = criar_ordem_servico(chat_id=update.effective_chat.id, **context.user_data)
    if sucesso:
        await update.message.reply_text("✅ OS criada com sucesso!", reply_markup=get_main_keyboard())
    else:
        await update.message.reply_text("❌ Erro ao criar OS.", reply_markup=get_main_keyboard())
    return await cancelar(update, context)


# <<< --- FLUXO DE FECHO DE OS --- >>>

async def fechar_os_iniciar(update: Update, context: CallbackContext):
    """Ponto de entrada para fechar OS. Pede confirmação."""
    context.user_data.clear()
    context.user_data['acao_pendente'] = 'fechar_os'
    keyboard = [[InlineKeyboardButton("Sim, fechar OS", callback_data="sim")], [InlineKeyboardButton("Não", callback_data="nao")]]
    await update.message.reply_text("Tem a certeza de que deseja fechar uma Ordem de Serviço?", reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRMAR_ACAO

async def listar_os_para_fechar(update: Update, context: CallbackContext):
    """Busca e lista as OS abertas para o utilizador selecionar."""
    chat_id = update.effective_chat.id
    ordens_abertas = buscar_os_abertas_por_usuario(chat_id)
    
    if not ordens_abertas:
        await context.bot.send_message(chat_id, "Você não tem nenhuma Ordem de Serviço aberta no momento.", reply_markup=get_main_keyboard())
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(f"ID: {os['id']} - Máquina: {os['numero_maquina']}", callback_data=str(os['id']))] for os in ordens_abertas]
    await context.bot.send_message(chat_id, "Selecione a Ordem de Serviço que deseja fechar:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECIONAR_OS

async def selecionar_os(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    context.user_data['os_id'] = int(query.data)
    await query.edit_message_text("Ótimo. Por favor, descreva a solução que foi aplicada.")
    return SOLUCAO_APLICADA

async def receber_solucao(update: Update, context: CallbackContext):
    context.user_data['solucao_aplicada'] = update.message.text
    keyboard = [[InlineKeyboardButton("Sim", callback_data="sim")], [InlineKeyboardButton("Não", callback_data="nao")]]
    await update.message.reply_text("Houve substituição de peças?", reply_markup=InlineKeyboardMarkup(keyboard))
    return PERGUNTAR_PECA

async def perguntar_peca(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.data == "sim":
        context.user_data['substituir_peca'] = True
        await query.edit_message_text("Por favor, adicione a descrição da peça substituída:")
        return DESCRICAO_PECA
    else:
        context.user_data['substituir_peca'] = False
        context.user_data['descricao_peca'] = None
        context.user_data['tag_peca'] = None
        keyboard = [[InlineKeyboardButton("Sim, concluído", callback_data="sim")], [InlineKeyboardButton("Não, pendente", callback_data="nao")]]
        await query.edit_message_text("O serviço foi concluído com sucesso?", reply_markup=InlineKeyboardMarkup(keyboard))
        return SERVICO_CONCLUIDO

async def receber_descricao_peca(update: Update, context: CallbackContext):
    context.user_data['descricao_peca'] = update.message.text
    await update.message.reply_text("A peça possui alguma TAG ou código?")
    return TAG_PECA

async def receber_tag_peca(update: Update, context: CallbackContext):
    context.user_data['tag_peca'] = update.message.text
    keyboard = [[InlineKeyboardButton("Sim, concluído", callback_data="sim")], [InlineKeyboardButton("Não, pendente", callback_data="nao")]]
    await update.message.reply_text("O serviço foi concluído com sucesso?", reply_markup=InlineKeyboardMarkup(keyboard))
    return SERVICO_CONCLUIDO

async def receber_servico_concluido(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    context.user_data['servico_concluido'] = (query.data == "sim")
    keyboard = [[InlineKeyboardButton("Sim, adicionar", callback_data="sim")], [InlineKeyboardButton("Não, finalizar", callback_data="nao")]]
    await query.edit_message_text("Deseja adicionar alguma observação final?", reply_markup=InlineKeyboardMarkup(keyboard))
    return PERGUNTAR_OBSERVACAO

async def perguntar_observacao(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.data == "sim":
        await query.edit_message_text("Ok, por favor, digite a sua observação.")
        return OBSERVACOES
    else:
        context.user_data['observacao'] = None
        await query.edit_message_text("A finalizar a Ordem de Serviço...")
        return await finalizar_fechamento_os(update, context)

async def receber_observacoes(update: Update, context: CallbackContext):
    context.user_data['observacao'] = update.message.text
    return await finalizar_fechamento_os(update, context)

async def finalizar_fechamento_os(update: Update, context: CallbackContext):
    dados_fechamento = {
        'solucao_aplicada': context.user_data['solucao_aplicada'],
        'substituir_peca': context.user_data['substituir_peca'],
        'descricao_peca': context.user_data.get('descricao_peca'),
        'tag_peca': context.user_data.get('tag_peca'),
        'servico_concluido': context.user_data['servico_concluido'],
        'observacao': context.user_data.get('observacao'),
    }
    sucesso = fechar_ordem_servico(
        os_id=context.user_data['os_id'],
        chat_id=update.effective_chat.id,
        dados_fechamento=dados_fechamento
    )
    if sucesso:
        await context.bot.send_message(update.effective_chat.id, "✅ Ordem de Serviço fechada com sucesso!", reply_markup=get_main_keyboard())
    else:
        await context.bot.send_message(update.effective_chat.id, "❌ Ocorreu um erro ao fechar a OS. Tente novamente.", reply_markup=get_main_keyboard())
    return await cancelar(update, context)


# --- FUNÇÕES QUE RETORNAM OS HANDLERS ---

def get_criar_os_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("criar_os", criar_os_iniciar), MessageHandler(filters.Text([UIBotao.CRIAR_OS]), criar_os_iniciar)],
        states={
            CONFIRMAR_ACAO: [CallbackQueryHandler(confirmar_acao)],
            NUMERO_MAQUINA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_numero_maquina)],
            MODELO_MAQUINA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_modelo_maquina)],
            TIPO_MANUTENCAO: [CallbackQueryHandler(receber_tipo_manutencao)],
            PROBLEMA_APRESENTADO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_problema_apresentado)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)], per_message=False
    )

def get_fechar_os_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("fechar_os", fechar_os_iniciar), MessageHandler(filters.Text([UIBotao.FECHAR_OS]), fechar_os_iniciar)],
        states={
            CONFIRMAR_ACAO: [CallbackQueryHandler(confirmar_acao)],
            SELECIONAR_OS: [CallbackQueryHandler(selecionar_os)],
            SOLUCAO_APLICADA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_solucao)],
            PERGUNTAR_PECA: [CallbackQueryHandler(perguntar_peca)],
            DESCRICAO_PECA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_descricao_peca)],
            TAG_PECA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_tag_peca)],
            SERVICO_CONCLUIDO: [CallbackQueryHandler(receber_servico_concluido)],
            PERGUNTAR_OBSERVACAO: [CallbackQueryHandler(perguntar_observacao)],
            OBSERVACOES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_observacoes)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)], per_message=False
    )

