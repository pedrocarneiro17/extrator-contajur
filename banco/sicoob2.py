import re
import pandas as pd
from io import BytesIO
from utils import create_xml, create_txt, process_transactions

def preprocess_text(text):
    """
    Pré-processa o texto do Sicoob no novo formato, agrupando transações por data.
    Extrai o ano da primeira palavra do texto (data de retirada do extrato).
    Separa linhas de saldo (SALDO DO DIA, SALDO ANTERIOR, SALDO BLOQUEADO) em blocos distintos.
    Ignora linhas que contêm 'https://www.sicoob.com.br/sicoobnet/ib/#/home-extrato' e as duas linhas acima.
    Retorna uma lista de dicionários com os blocos de transações e o ano extraído.
    """
    # Dividir o texto em linhas e remover linhas vazias
    all_lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    # Identificar índices das linhas que contêm o link
    link_indices = [i for i, line in enumerate(all_lines) 
                   if "https://www.sicoob.com.br/sicoobnet/ib/#/home-extrato" in line]
    
    # Criar conjunto de índices para remover (link + 2 linhas acima)
    indices_to_remove = set()
    for idx in link_indices:
        indices_to_remove.add(idx)  # linha do link
        if idx > 0:
            indices_to_remove.add(idx-1)  # linha acima
        if idx > 1:
            indices_to_remove.add(idx-2)  # duas linhas acima
    
    # Filtrar linhas mantendo apenas as que não estão nos índices a remover
    lines = [line for i, line in enumerate(all_lines) if i not in indices_to_remove]
    
    # Extrair o ano da primeira palavra do texto (data de retirada do extrato)
    year = None
    if lines:
        palavras = lines[0].split()
        if palavras:
            first_word = palavras[0]
            date_pattern = r"(\d{2}/\d{2}/\d{4})"
            match = re.match(date_pattern, first_word)
            if match:
                year = match.group(1).split('/')[2]
            else:
                for line in lines:
                    match = re.search(r"\d{2}/\d{2}/\d{4}", line)
                    if match:
                        year = match.group(0).split('/')[2]
                        break
    
    if not year:
        raise ValueError("Não foi possível extrair o ano do texto.")
    
    # Identificar blocos de transações por data
    transactions = []
    current_transaction = []
    date_pattern = r"^\d{2}/\d{2}$"
    saldo_keywords = ["SALDO DO DIA", "SALDO ANTERIOR", "SALDO BLOQUEADO"]
    
    for line in lines:
        if re.match(date_pattern, line):
            if current_transaction:
                transactions.append({"raw": "\n".join(current_transaction)})
            current_transaction = [line]
        elif any(keyword in line for keyword in saldo_keywords):
            if current_transaction:
                if len(current_transaction) > 1:
                    transactions.append({"raw": "\n".join(current_transaction)})
            current_transaction = [line]
        elif current_transaction:
            current_transaction.append(line)
    
    if current_transaction:
        transactions.append({"raw": "\n".join(current_transaction)})
    
    return transactions, year

def extract_transactions(transactions, year=None):
    """
    Extrai Data, Descrição, Valor e Tipo (C/D) de cada transação no novo formato.
    Descarta blocos que contêm apenas SALDO DO DIA, SALDO ANTERIOR ou SALDO BLOQUEADO.
    Usa o ano fornecido para formatar as datas como DD/MM/YYYY.
    Retorna uma lista de dicionários no formato final.
    """
    data = []
    value_pattern = r"R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})([CD])"
    
    for transaction_dict in transactions:
        transaction = transaction_dict["raw"]
        lines = transaction.split("\n")
        
        # Ignorar blocos que são apenas de saldo
        if any(s in transaction for s in ["SALDO DO DIA", "SALDO ANTERIOR", "SALDO BLOQUEADO"]):
            continue
        
        # Extrair data
        date = lines[0]
        if year:
            date = f"{date}/{year}"  # Formata como DD/MM/YYYY
        
        # Processar o bloco de transação
        description = []
        value = None
        transaction_type = None
        
        for line in lines[1:]:
            value_match = re.search(value_pattern, line)
            if value_match:
                value = value_match.group(1)
                transaction_type = value_match.group(2)
                if value.endswith(",00"):
                    value = value[:-3]
            elif line and not line.startswith("Data") and not line.startswith("Periodo:") and not line.startswith("Sicoob"):
                description.append(line.strip())
        
        if value and transaction_type:
            description_text = " ".join(description).strip()
            data.append({
                "Data": date,
                "Descrição": description_text,
                "Valor": value,
                "Tipo": transaction_type
            })
    
    return data

def process(text):
    """
    Processa o texto extraído do Sicoob e retorna o DataFrame, XML e TXT.
    Garante que o DataFrame tenha as datas no formato DD/MM/YYYY.
    """
    transactions, year = preprocess_text(text)
    data = extract_transactions(transactions, year)
    if not data:
        return None, None, None
    
    # Gerar XML e TXT (usando as funções fornecidas)
    xml_data = create_xml(data)
    txt_data = create_txt(data)
    
    return xml_data, txt_data