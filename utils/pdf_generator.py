import os
from datetime import datetime
from fpdf import FPDF
from config import logging, PDF_SAVE_PATH
from typing import List, Dict, Any

class PDF(FPDF):
    """Classe personalizada para ter cabeçalho e rodapé no PDF."""
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Relatório de Atividades - Kraflo', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def formatar_data(data_str: str | None) -> str:
    """Formata uma data ISO para o formato DD/MM/YYYY às HH:MM."""
    if not data_str:
        return "Não preenchido"
    try:
        data_obj = datetime.fromisoformat(data_str)
        return data_obj.strftime('%d/%m/%Y às %H:%M')
    except (ValueError, TypeError):
        return str(data_str)

def gerar_relatorio_pdf(usuario: Dict[str, Any], ordens: List[Dict[str, Any]], periodo: str) -> str | None:
    try:
        pdf = PDF('P', 'mm', 'A4')
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # --- Para cada Ordem de Serviço, criamos uma nova página ---
        for i, ordem in enumerate(ordens):
            pdf.add_page()
            
            # --- Cabeçalho da Página com Detalhes do Profissional ---
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, '1. Detalhes do Profissional', ln=True, border='B')
            pdf.ln(4)
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 6, f"Nome: {usuario.get('nome', 'N/A')}", ln=True)
            pdf.cell(0, 6, f"Função: {usuario.get('funcao', 'N/A')}", ln=True)
            pdf.cell(0, 6, f"Período do Relatório: {periodo}", ln=True)
            pdf.ln(8)
            
            # --- Detalhes da Ordem de Serviço ---
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, f"2. Detalhes da OS ID: {ordem.get('id')}", ln=True, border='B')
            pdf.ln(4)
            
            # Formato Label -> Valor
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 7, "Máquina", ln=True)
            pdf.set_font('Arial', '', 11)
            pdf.cell(0, 7, f"  {ordem.get('numero_maquina', 'N/A')} - {ordem.get('modelo_maquina', 'N/A')}", ln=True)

            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 7, "Tipo de Manutenção", ln=True)
            pdf.set_font('Arial', '', 11)
            pdf.cell(0, 7, f"  {ordem.get('tipo_manutencao', 'N/A')}", ln=True)

            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 7, "Problema Apresentado", ln=True)
            pdf.set_font('Arial', '', 11)
            pdf.multi_cell(0, 7, f"  {ordem.get('problema_apresentado', 'Não preenchido')}")
            pdf.ln(1) # CORREÇÃO: Força o cursor para a próxima linha

            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 7, "Solução Aplicada", ln=True)
            pdf.set_font('Arial', '', 11)
            pdf.multi_cell(0, 7, f"  {ordem.get('solucao_aplicada', 'Não preenchido')}")
            pdf.ln(1) # CORREÇÃO: Força o cursor para a próxima linha
            
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 7, "Datas", ln=True)
            pdf.set_font('Arial', '', 11)
            pdf.cell(0, 7, f"  Abertura: {formatar_data(ordem.get('data_abertura'))}", ln=True)
            pdf.cell(0, 7, f"  Fecho: {formatar_data(ordem.get('data_fechamento'))}", ln=True)
            
            if ordem.get('substituir_peca'):
                pdf.set_font('Arial', 'B', 11)
                pdf.cell(0, 7, "Peças Utilizadas", ln=True)
                pdf.set_font('Arial', '', 11)
                pdf.cell(0, 7, f"  Descrição: {ordem.get('descricao_peca', 'N/A')}", ln=True)
                pdf.cell(0, 7, f"  TAG/Código: {ordem.get('tag_peca', 'N/A')}", ln=True)

            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 7, "Serviço Concluído", ln=True)
            pdf.set_font('Arial', '', 11)
            pdf.cell(0, 7, f"  {'Sim' if ordem.get('servico_concluido') else 'Não'}", ln=True)

            if ordem.get('observacao'):
                pdf.set_font('Arial', 'B', 11)
                pdf.cell(0, 7, "Observações", ln=True)
                pdf.set_font('Arial', '', 11)
                pdf.multi_cell(0, 7, f"  {ordem.get('observacao')}")

        # --- Salvar o ficheiro ---
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
