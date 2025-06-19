from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler, CommandHandler, MessageHandler, 
    CallbackQueryHandler, filters, CallbackContext
)
from config import logging, UIBotao
# Importa as novas funções da base de dados
from database.models import buscar_usuario_por_id, criar_ordem_servico, buscar_os_abertas_por_usuario, fechar_ordem_servico
from .ui import get_main_keyboard

# --- Estados da Conversa de Criação de OS ---
NUMERO_MAQUINA, MODELO_MAQUINA, TIPO_MANUTENCAO, PROBLEMA_APRESENTADO = range(5, 9)

# --- Estados da Conversa de Fecho de OS ---
SELECIONAR_OS, SOLUCAO_APLICADA, PERGUNTAR_PECA, DESCRICAO_PECA, TAG_PECA, SERVICO_CONCLUIDO, OBSERVACOES = range(9, 16)


# <<< --- FLUXO DE CRIAÇÃO DE OS --- >>>
async def criar_os_iniciar(update: Update, context: CallbackContext):
    """Ponto de entrada para iniciar a criação de uma OS."""
    usuario = buscar_usuario_por_id(update.effective_chat.id)
    if not usuario:
        await update.message.reply_text("Você precisa estar registrado para criar uma OS. Use /start para se registrar.")
        return ConversationHandler.END
    await update.message.reply_text("Vamos criar uma nova Ordem de Serviço. Qual é o número da máquina?")
    return NUMERO_MAQUINA

async def receber_numero_maquina(update: Update, context: CallbackContext):
    context.user_data['numero_maquina'] = update.message.text
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
        await update.message.reply_text("✅ Ordem de Serviço criada com sucesso!", reply_markup=get_main_keyboard())
    else:
        await update.message.reply_text("❌ Ocorreu um erro ao criar a OS.", reply_markup=get_main_keyboard())
    return ConversationHandler.END


# <<< --- NOVO FLUXO DE FECHO DE OS --- >>>

async def fechar_os_iniciar(update: Update, context: CallbackContext):
    """Ponto de entrada para o fecho de uma OS. Mostra as OS abertas."""
    chat_id = update.effective_chat.id
    
    ordens_abertas = buscar_os_abertas_por_usuario(chat_id)
    
    if not ordens_abertas:
        await update.message.reply_text("Você não tem nenhuma Ordem de Serviço aberta no momento.", reply_markup=get_main_keyboard())
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton(f"ID: {os['id']} - Máquina: {os['numero_maquina']}", callback_data=str(os['id']))]
        for os in ordens_abertas
    ]
    await update.message.reply_text(
        "Selecione a Ordem de Serviço que deseja fechar:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECIONAR_OS

async def selecionar_os(update: Update, context: CallbackContext):
    """Recebe o ID da OS selecionada e pede a solução."""
    query = update.callback_query
    await query.answer()
    context.user_data['os_id'] = int(query.data)
    await query.edit_message_text("Ótimo. Por favor, descreva a solução que foi aplicada.")
    return SOLUCAO_APLICADA

async def receber_solucao(update: Update, context: CallbackContext):
    """Recebe a solução e pergunta se houve troca de peças."""
    context.user_data['solucao_aplicada'] = update.message.text
    keyboard = [[InlineKeyboardButton("Sim", callback_data="sim")], [InlineKeyboardButton("Não", callback_data="nao")]]
    await update.message.reply_text("Houve substituição de peças?", reply_markup=InlineKeyboardMarkup(keyboard))
    return PERGUNTAR_PECA

async def perguntar_peca(update: Update, context: CallbackContext):
    """Processa a resposta sobre a troca de peças."""
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
    """Recebe a descrição da peça e pergunta a tag."""
    context.user_data['descricao_peca'] = update.message.text
    await update.message.reply_text("A peça possui alguma TAG ou código?")
    return TAG_PECA

async def receber_tag_peca(update: Update, context: CallbackContext):
    """Recebe a tag da peça e pergunta sobre a conclusão do serviço."""
    context.user_data['tag_peca'] = update.message.text
    keyboard = [[InlineKeyboardButton("Sim, concluído", callback_data="sim")], [InlineKeyboardButton("Não, pendente", callback_data="nao")]]
    await update.message.reply_text("O serviço foi concluído com sucesso?", reply_markup=InlineKeyboardMarkup(keyboard))
    return SERVICO_CONCLUIDO

async def receber_servico_concluido(update: Update, context: CallbackContext):
    """Recebe o status da conclusão e pergunta por observações."""
    query = update.callback_query
    await query.answer()
    context.user_data['servico_concluido'] = (query.data == "sim")
    await query.edit_message_text("Excelente. Deseja adicionar alguma observação final? (Se não, digite 'não')")
    return OBSERVACOES

async def receber_observacoes(update: Update, context: CallbackContext):
    """Recebe as observações, fecha a OS no banco e finaliza a conversa."""
    context.user_data['observacao'] = update.message.text

    dados_fechamento = {
        'solucao_aplicada': context.user_data['solucao_aplicada'],
        'substituir_peca': context.user_data['substituir_peca'],
        'descricao_peca': context.user_data.get('descricao_peca'),
        'tag_peca': context.user_data.get('tag_peca'),
        'servico_concluido': context.user_data['servico_concluido'],
        'observacao': context.user_data['observacao'],
    }
    
    sucesso = fechar_ordem_servico(
        os_id=context.user_data['os_id'],
        chat_id=update.effective_chat.id,
        dados_fechamento=dados_fechamento
    )

    if sucesso:
        await update.message.reply_text("✅ Ordem de Serviço fechada com sucesso!", reply_markup=get_main_keyboard())
    else:
        await update.message.reply_text("❌ Ocorreu um erro ao fechar a OS. Tente novamente.", reply_markup=get_main_keyboard())
        
    return ConversationHandler.END

async def cancelar(update: Update, context: CallbackContext):
    """Função genérica para cancelar qualquer conversa."""
    await update.message.reply_text("Operação cancelada.", reply_markup=get_main_keyboard())
    return ConversationHandler.END


# --- FUNÇÕES QUE RETORNAM OS HANDLERS ---

def get_criar_os_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("criar_os", criar_os_iniciar), MessageHandler(filters.Text([UIBotao.CRIAR_OS]), criar_os_iniciar)],
        states={
            NUMERO_MAQUINA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_numero_maquina)],
            MODELO_MAQUINA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_modelo_maquina)],
            TIPO_MANUTENCAO: [CallbackQueryHandler(receber_tipo_manutencao)],
            PROBLEMA_APRESENTADO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_problema_apresentado)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)], per_message=False
    )

def get_fechar_os_handler() -> ConversationHandler:
    """Cria e retorna o ConversationHandler para o fluxo de fecho de OS."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("fechar_os", fechar_os_iniciar),
            MessageHandler(filters.Text([UIBotao.FECHAR_OS]), fechar_os_iniciar)
        ],
        states={
            SELECIONAR_OS: [CallbackQueryHandler(selecionar_os)],
            SOLUCAO_APLICADA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_solucao)],
            PERGUNTAR_PECA: [CallbackQueryHandler(perguntar_peca)],
            DESCRICAO_PECA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_descricao_peca)],
            TAG_PECA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_tag_peca)],
            SERVICO_CONCLUIDO: [CallbackQueryHandler(receber_servico_concluido)],
            OBSERVACOES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_observacoes)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)], per_message=False
    )
