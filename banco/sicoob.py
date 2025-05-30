import re

from auxiliares.utils import create_xml, create_txt, process_transactions

def preprocess_text(text):
    """
    Pré-processa o texto do Sicoob no formato estruturado do PyMuPDF.
    Agrupa transações a partir de uma data até DOC.: ou SALDO DO DIA.
    Retorna uma tupla com lista de dicionários de transações e o ano extraído do período.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    # Extrair o ano do período (ex.: PERÍODO: 01/04/2025 - 30/04/2025)
    year = None
    period_pattern = r"PERÍODO:\s*\d{2}/\d{2}/(\d{4})\s*-\s*\d{2}/\d{2}/\d{4}"
    for line in lines:
        match = re.search(period_pattern, line)
        if match:
            year = match.group(1)
            break
    
    # Identificar início e fim das transações
    start_index = 0
    for i, line in enumerate(lines):
        if "DATA  HISTÓRICO  VALOR" in line:
            start_index = i + 1
            break
    
    end_index = len(lines)
    for i, line in enumerate(lines[start_index:], start=start_index):
        if "RESUMO" in line or "SALDO EM C.CORRENTE" in line:
            end_index = i
            break
    
    transaction_lines = lines[start_index:end_index]
    
    transactions = []
    current_transaction = []
    in_transaction = False
    date_pattern = r"^\d{2}/\d{2}\s*$"
    
    for line in transaction_lines:
        if re.match(date_pattern, line):
            if in_transaction and current_transaction:
                transactions.append({"raw": "\n".join(current_transaction)})
            current_transaction = [line]
            in_transaction = True
        elif in_transaction:
            current_transaction.append(line)
            if "DOC.:" in line or "SALDO DO DIA" in line or "SALDO ANTERIOR" in line or "SALDO BLOQ" in line:
                transactions.append({"raw": "\n".join(current_transaction)})
                in_transaction = False
                current_transaction = []
    
    if in_transaction and current_transaction:
        transactions.append({"raw": "\n".join(current_transaction)})
    
    return transactions, year

def extract_transactions(transactions, year=None):
    """
    Extrai Data, Descrição, Valor e Tipo (C/D) de cada transação do Sicoob.
    Remove apenas as linhas de valor e tipo, preservando a descrição original.
    Descarta transações de SALDO DO DIA, SALDO ANTERIOR ou SALDO BLOQ.
    Usa o ano fornecido para formatar as datas como DD/MM/YYYY.
    Retorna uma lista de dicionários no formato final.
    """
    data = []
    date_pattern = r"^(\d{2}/\d{2})\s*$"
    value_pattern = r"(\d{1,3}(?:\.\d{3})*,\d{2})([CD])?"
    type_pattern = r"^[CD]$"
    doc_pattern = r"DOC\.:"
    
    for transaction_dict in transactions:
        transaction = transaction_dict["raw"]
        lines = transaction.split("\n")
        
        # Ignorar transações de saldo
        if any(s in transaction for s in ["SALDO DO DIA", "SALDO ANTERIOR", "SALDO BLOQ"]):
            continue
        
        # Extrair data
        date_match = re.match(date_pattern, lines[0])
        if not date_match:
            continue
        date = date_match.group(1)
        if year:
            date = f"{date}/{year}"
        
        # Extrair valor e tipo
        value = None
        transaction_type = None
        value_line_index = None
        type_line_index = None
        for i, line in enumerate(lines[1:], start=1):
            value_match = re.match(value_pattern, line.strip())
            if value_match:
                value = value_match.group(1)
                value_line_index = i
                transaction_type = value_match.group(2)
                if not transaction_type and i + 1 < len(lines) and re.match(type_pattern, lines[i + 1].strip()):
                    transaction_type = lines[i + 1].strip()
                    type_line_index = i + 1
                break
        
        if not value or not transaction_type:
            continue
        
        if value.endswith(",00"):
            value = value[:-3]
        
        # Extrair descrição até o DOC.:
        doc_match = re.search(doc_pattern, transaction)
        if not doc_match:
            continue
        
        # Construir descrição, excluindo linhas de valor e tipo
        description_lines = []
        for i, line in enumerate(lines[1:], start=1):
            if i == value_line_index or i == type_line_index:
                continue
            if "DOC.:" in line:
                description_lines.append(line)
                break
            description_lines.append(line)
        
        description = " ".join(description_lines).strip()
        
        data.append({
            "Data": date,
            "Descrição": description,
            "Valor": value,
            "Tipo": transaction_type
        })
    
    return data

def process(text):
    """
    Processa o texto extraído do Sicoob e retorna o DataFrame, XML e TXT.
    """
    transactions, year = preprocess_text(text)
    data = extract_transactions(transactions, year)
    if not data:
        return None, None, None
    xml_data = create_xml(data)
    txt_data = create_txt(data)
    return xml_data, txt_data