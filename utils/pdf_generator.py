import os
from datetime import datetime
from fpdf import FPDF
from config import logging, PDF_SAVE_PATH
from typing import List, Dict, Any

class PDF(FPDF):
    """Classe personalizada para ter cabeçalho e rodapé no PDF."""
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Relatório de Ordens de Serviço - Kraflo', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def formatar_data(data_str: str | None) -> str:
    """Formata uma data ISO para o formato DD/MM/YYYY HH:MM."""
    if not data_str:
        return "N/A"
    try:
        # A data vem no formato ISO 8601 com fuso horário
        data_obj = datetime.fromisoformat(data_str)
        return data_obj.strftime('%d/%m/%Y %H:%M')
    except (ValueError, TypeError):
        return data_str

def gerar_relatorio_pdf(usuario: Dict[str, Any], ordens: List[Dict[str, Any]], periodo: str) -> str | None:
    """
    Gera o ficheiro PDF com os dados fornecidos.

    Returns:
        O caminho do ficheiro PDF gerado, ou None em caso de erro.
    """
    try:
        pdf = PDF('P', 'mm', 'A4')
        pdf.add_page()
        
        # --- Cabeçalho do Relatório ---
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Detalhes do Profissional', ln=True)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, f"Nome: {usuario.get('nome', 'N/A')}", ln=True)
        pdf.cell(0, 6, f"Função: {usuario.get('funcao', 'N/A')}", ln=True)
        pdf.cell(0, 6, f"Matrícula: {usuario.get('cadastro_empresa', 'N/A')}", ln=True)
        pdf.cell(0, 6, f"Período do Relatório: {periodo}", ln=True)
        pdf.ln(10)

        # --- Detalhes das Ordens de Serviço ---
        for os in ordens:
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, f"OS ID: {os.get('id')} - Máquina: {os.get('numero_maquina', 'N/A')}", ln=True, border='B')
            pdf.ln(4)

            pdf.set_font('Arial', '', 10)
            pdf.multi_cell(0, 5, f"Problema Apresentado: {os.get('problema_apresentado', 'N/A')}")
            pdf.multi_cell(0, 5, f"Solução Aplicada: {os.get('solucao_aplicada', 'N/A')}")
            pdf.ln(2)
            pdf.cell(0, 5, f"Abertura: {formatar_data(os.get('data_abertura'))} | Fecho: {formatar_data(os.get('data_fechamento'))}", ln=True)
            pdf.cell(0, 5, f"Serviço Concluído: {'Sim' if os.get('servico_concluido') else 'Não'}", ln=True)
            pdf.ln(8)
            
        # --- Salvar o ficheiro ---
        # Garante que o diretório de PDFs temporários exista
        if not os.path.exists(PDF_SAVE_PATH):
            os.makedirs(PDF_SAVE_PATH)
            
        filename = f"relatorio_kraflo_{usuario['chat_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        filepath = os.path.join(PDF_SAVE_PATH, filename)
        
        pdf.output(filepath)
        logging.info(f"Relatório PDF gerado com sucesso em: {filepath}")
        return filepath

    except Exception as e:
        logging.error(f"Falha ao gerar o ficheiro PDF: {e}")
        return None
