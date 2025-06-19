from telegram import ReplyKeyboardMarkup, KeyboardButton
from config import UIBotao

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Cria e retorna o teclado principal com os botões de comando.
    """
    keyboard = [
        [KeyboardButton(UIBotao.CRIAR_OS)],
        [KeyboardButton(UIBotao.FECHAR_OS), KeyboardButton(UIBotao.GERAR_RELATORIO)],
    ]
    
    # resize_keyboard=True faz o teclado se ajustar ao tamanho da tela.
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)