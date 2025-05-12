import re
import pandas as pd
from io import BytesIO
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

def preprocess_text(text):
    """
    Pré-processa o texto do Sicoob para dividir transações, ignorando cabeçalho e rodapé.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
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
                    transactions.append("\n".join([pending_value] + current_transaction))
                    pending_value = None
                else:
                    transactions.append("\n".join(current_transaction))
            current_transaction = [line]
            in_transaction = True
        elif in_transaction:
            current_transaction.append(line)
            if "DOC.:" in line:
                if pending_value:
                    transactions.append("\n".join([pending_value] + current_transaction))
                    pending_value = None
                else:
                    transactions.append("\n".join(current_transaction))
                in_transaction = False
                current_transaction = []
    
    if in_transaction and current_transaction:
        if pending_value:
            transactions.append("\n".join([pending_value] + current_transaction))
        else:
            transactions.append("\n".join(current_transaction))
    
    return transactions

def extract_transactions(transactions):
    """
    Extrai Data, Descrição, Valor e Tipo (C/D) de cada transação do Sicoob.
    """
    data = []
    date_pattern = r"^(\d{2}/\d{2})\s"
    value_pattern = r"(\d{1,3}(?:\.\d{3})*,\d{2})"
    doc_pattern = r"DOC\.:"
    
    for transaction in transactions:
        lines = transaction.split("\n")
        
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
        
        date_match = re.search(date_pattern, lines[0])
        if not date_match:
            continue
        date = date_match.group(1)
        
        transaction_type = None
        for line in lines:
            if re.search(r"[CD]", line):
                transaction_type = re.search(r"[CD]", line).group()
                break
        
        if not transaction_type:
            continue
        
        doc_match = re.search(doc_pattern, transaction)
        if not doc_match:
            continue
        
        doc_start = doc_match.start()
        start_idx = date_match.end()
        description = transaction[start_idx:doc_start].strip()
        
        doc_content = transaction[doc_match.end():].strip()
        if doc_content:
            description = f"{description} DOC.: {doc_content}".strip()
        
        description = re.sub(r"\s+", " ", description).strip()
        
        data.append({
            "Data": date,
            "Descrição": description,
            "Valor": value,
            "Tipo": transaction_type
        })
    
    return data

def create_xml(data):
    """
    Cria um arquivo XML a partir dos dados extraídos e retorna o DataFrame e o XML como BytesIO.
    """
    df = pd.DataFrame(data)
    
    root = Element("Transactions")
    
    for transaction in data:
        trans_elem = SubElement(root, "Transaction")
        
        date_elem = SubElement(trans_elem, "Data")
        date_elem.text = transaction["Data"]
        
        desc_elem = SubElement(trans_elem, "Descrição")
        desc_elem.text = transaction["Descrição"]
        
        value_elem = SubElement(trans_elem, "Valor")
        value_elem.text = transaction["Valor"]
        
        type_elem = SubElement(trans_elem, "Tipo")
        type_elem.text = transaction["Tipo"]
    
    rough_string = tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    output = BytesIO()
    output.write(pretty_xml.encode('utf-8'))
    output.seek(0)
    
    return df, output

def create_txt(data):
    """
    Cria um arquivo TXT a partir dos dados extraídos e retorna o TXT como BytesIO.
    """
    txt_content = ""
    for transaction in data:
        txt_content += f"Data: {transaction['Data']}\n"
        txt_content += f"Descrição: {transaction['Descrição']}\n"
        txt_content += f"Valor: {transaction['Valor']}\n"
        txt_content += f"Tipo: {transaction['Tipo']}\n"
        txt_content += "-" * 50 + "\n"
    
    output = BytesIO()
    output.write(txt_content.encode('utf-8'))
    output.seek(0)
    
    return output

def process(text):
    """
    Processa o texto extraído para o Sicoob e retorna o DataFrame, XML e TXT.
    """
    transactions = preprocess_text(text)
    data = extract_transactions(transactions)
    if not data:
        return None, None, None
    df, xml_data = create_xml(data)
    txt_data = create_txt(data)
    return df, xml_data, txt_data