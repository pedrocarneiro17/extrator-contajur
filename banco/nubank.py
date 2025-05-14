import re
import pandas as pd
from io import BytesIO
from utils import create_xml, create_txt, process_transactions  # Importar funções utilitárias

def preprocess_text(text):
    """
    Pré-processa o texto do extrato do Nubank para extrair transações, ignorando cabeçalho e rodapé.
    Combina o tipo de transação e o identificador em uma única coluna Descrição.
    Mantém valores no formato brasileiro (ex.: 1.012,29).
    Identifica Tipo (C para crédito, D para débito) com base no texto da transação.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    # Mapa de meses para conversão de data
    month_map = {
        'jan': '01', 'janeiro': '01',
        'fev': '02', 'fevereiro': '02',
        'mar': '03', 'março': '03', 'marco': '03',
        'abr': '04', 'abril': '04',
        'mai': '05', 'maio': '05',
        'jun': '06', 'junho': '06',
        'jul': '07', 'julho': '07',
        'ago': '08', 'agosto': '08',
        'set': '09', 'setembro': '09',
        'out': '10', 'outubro': '10',
        'nov': '11', 'novembro': '11',
        'dez': '12', 'dezembro': '12'
    }
    
    # Padrão para identificar datas (ex.: "02 ABR 2025")
    date_pattern = r"^(\d{1,2})\s+([A-Z]+)\s+(\d{4})"
    # Padrão para identificar valores (ex.: "315,00" ou "1.012,29")
    value_pattern = r"(\d{1,3}(?:\.\d{3})*,\d{2})$"
    # Padrões de transações de débito
    debit_patterns = [
        r"Pagamento de boleto",
        r"Compra no débito",
        r"Transferência enviada",
        r"PAGAMENTOS\s*-\s*IP"
    ]
    
    transactions = []
    current_date = None
    start_processing = False
    
    for line in lines:
        # Identificar o início das movimentações
        if "MOVIMENTAÇÕES" in line.upper() or "MOVIMENTACOES" in line.upper():
            start_processing = True
            continue
        
        if not start_processing:
            continue
        
        # Ignorar linhas de rodapé ou irrelevantes
        if any(keyword in line.upper() for keyword in [
            "OUVIDORIA", "EXTRATO GERADO", "CNPJ", "SALDO LÍQUIDO",
            "NÃO NOS RESPONSABILIZAMOS", "ASSEGURAMOS A AUTENTICIDADE",
            "ATENDIMENTO", "CPF", "AGÊNCIA", "CONTA", "VALORES EM R",
            "FINANCEIRA S.A.", "PAGAMENTOS S.A.", "0800", "4020"
        ]):
            continue
        
        # Ignorar linhas de "Pagamento de fatura"
        if "PAGAMENTO DE FATURA" in line.upper() or "SALDO DO DIA" in line.upper() or "TOTAL DE SAÍDAS" in line.upper():
            continue

        
        # Verificar se a linha é uma data
        date_match = re.match(date_pattern, line, re.IGNORECASE)
        if date_match:
            day = date_match.group(1).zfill(2)  # Garantir dois dígitos
            month_name = date_match.group(2).upper()
            month = month_map.get(month_name, "01")  # Default para 01 se mês inválido
            year = date_match.group(3)
            current_date = f"{day}/{month}/{year}"
            continue
        
        # Processar linhas de transação
        value_match = re.search(value_pattern, line)
        if value_match and current_date:
            valor = value_match.group(1)  # Ex.: "315,00" ou "1.012,29"
            
            # Determinar tipo (C ou D) com base no texto da transação
            tipo = "D" if any(re.search(pattern, line, re.IGNORECASE) for pattern in debit_patterns) else "C"
            
            # Extrair descrição (tudo antes do valor)
            desc_end = value_match.start()
            description = line[:desc_end].strip()
            
            # Ajustar valor: remover ",00" se for um número inteiro
            if valor.endswith(",00"):
                valor = valor[:-3]
            
            transactions.append({
                "Data": current_date,
                "Descrição": description,
                "Valor": valor,
                "Tipo": tipo
            })
    
    return transactions

def extract_transactions(transactions):
    """
    Extrai os dados das transações (usado para compatibilidade com a estrutura).
    Como preprocess_text já retorna os dados no formato correto, apenas retorna a lista.
    """
    return transactions

def process(text):
    """
    Processa o texto extraído do extrato do Nubank e retorna o DataFrame, XML e TXT.
    """
    return process_transactions(text, preprocess_text, extract_transactions)