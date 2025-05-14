import re
import pandas as pd
from io import BytesIO
from utils import create_xml, create_txt, process_transactions

def preprocess_text(text):
    """
    Pré-processa o texto do Sicoob para dividir transações, ignorando cabeçalho e rodapé.
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
    pending_value = None
    
    value_pattern = r"^\d{1,3}(?:\.\d{3})*,\d{2}$"
    
    for line in transaction_lines:
        if re.match(value_pattern, line):
            pending_value = line
            continue
        
        if re.match(r"^\d{2}/\d{2}\s", line):
            if in_transaction and current_transaction:
                if pending_value:
                    transactions.append({"raw": "\n".join([pending_value] + current_transaction)})
                    pending_value = None
                else:
                    transactions.append({"raw": "\n".join(current_transaction)})
            current_transaction = [line]
            in_transaction = True
        elif in_transaction:
            current_transaction.append(line)
            if "DOC.:" in line:
                if pending_value:
                    transactions.append({"raw": "\n".join([pending_value] + current_transaction)})
                    pending_value = None
                else:
                    transactions.append({"raw": "\n".join(current_transaction)})
                in_transaction = False
                current_transaction = []
    
    if in_transaction and current_transaction:
        if pending_value:
            transactions.append({"raw": "\n".join([pending_value] + current_transaction)})
        else:
            transactions.append({"raw": "\n".join(current_transaction)})
    
    return transactions, year

def extract_transactions(transactions, year=None):
    """
    Extrai Data, Descrição, Valor e Tipo (C/D) de cada transação do Sicoob.
    Usa o ano fornecido para formatar as datas como DD/MM/YYYY.
    Remove o valor e tipo (ex.: 1.012,29 C) da descrição com pós-processamento robusto.
    Retorna uma lista de dicionários no formato final.
    """
    data = []
    date_pattern = r"^(\d{2}/\d{2})\s"
    value_pattern = r"(\d{1,3}(?:\.\d{3})*,\d{2})"
    doc_pattern = r"DOC\.:"
    # Regex para remover valor e tipo da descrição (ex.: 1.012,29 C ou 3.550,95 D)
    clean_value_type_pattern = r"\d{1,3}(?:\.\d{3})*,\d{2}\s*[CD](?:\s|$)"
    
    for transaction_dict in transactions:
        transaction = transaction_dict["raw"]
        lines = transaction.split("\n")
        
        # Extrair valor
        value = None
        value_match = re.match(value_pattern, lines[0])
        if value_match:
            value = value_match.group(1)
            lines = lines[1:]
        else:
            for line in lines:
                value_match = re.search(value_pattern, line)
                if value_match:
                    value = value_match.group(1)
                    break
        
        if not value:
            continue
        
        if value.endswith(",00"):
            value = value[:-3]
        
        # Extrair data
        date_match = re.search(date_pattern, lines[0])
        if not date_match:
            continue
        date = date_match.group(1)
        if year:
            date = f"{date}/{year}"  # Adiciona o ano do período (ex.: 01/04/2025)
        
        # Extrair tipo (C/D)
        transaction_type = None
        for line in lines:
            if re.search(r"[CD]", line):
                transaction_type = re.search(r"[CD]", line).group()
                break
        
        if not transaction_type:
            continue
        
        # Extrair descrição até o DOC.:
        doc_match = re.search(doc_pattern, transaction)
        if not doc_match:
            continue
        
        doc_start = doc_match.start()
        start_idx = date_match.end()
        description = transaction[start_idx:doc_start].strip()
        
        # Pós-processamento: remover valores e tipos (ex.: 450,22C) da descrição
        description = re.sub(clean_value_type_pattern, "", description).strip()
        
        # Remover quaisquer outros valores monetários remanescentes (ex.: 450,22 sem C/D)
        description = re.sub(r"\d{1,3}(?:\.\d{3})*,\d{2}", "", description).strip()
        
        # Adicionar conteúdo do DOC.: à descrição
        doc_content = transaction[doc_match.end():].strip()
        if doc_content:
            description = f"{description} DOC.: {doc_content}".strip()
        
        # Normalizar espaços em branco
        description = re.sub(r"\s+", " ", description).strip()
        
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