import re
import pandas as pd
from io import BytesIO
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

def convert_date_format(date_str):
    """
    Converte datas no formato DD/mes para DD/MM.
    Ex.: 01/abr -> 01/04, 31/mar -> 31/03
    """
    month_map = {
        "jan": "01", "fev": "02", "mar": "03", "abr": "04", "mai": "05", "jun": "06",
        "jul": "07", "ago": "08", "set": "09", "out": "10", "nov": "11", "dez": "12"
    }
    match = re.match(r"(\d{2})/(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)", date_str, re.IGNORECASE)
    if match:
        day = match.group(1)
        month = month_map[match.group(2).lower()]
        return f"{day}/{month}"
    return date_str

def preprocess_text(text):
    """
    Pré-processa o texto do Itaú para dividir transações, ignorando cabeçalho e rodapé.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    start_index = 0
    for i, line in enumerate(lines):
        if "SALDO ANTERIOR" in line:
            start_index = i + 1
            break
    
    end_index = len(lines)
    for i, line in enumerate(lines[start_index:], start=start_index):
        if "saldo da conta corrente" in line.lower():
            end_index = i
            break
    
    transaction_lines = lines[start_index:end_index]
    
    date_pattern = r"^\d{2}\s*/\s*(?:jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)\s"
    value_pattern = r"-?\d{1,3}(?:\.\d{3})*,\d{2}"
    
    transactions = []
    
    for line in transaction_lines:
        if "SALDO TOTAL DISPON" in line:
            continue
            
        if re.match(date_pattern, line, re.IGNORECASE):
            date_match = re.match(r"(\d{2}\s*/\s*(?:jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez))", line, re.IGNORECASE)
            value_matches = list(re.finditer(value_pattern, line))
            
            if date_match and value_matches:
                date = date_match.group(1).replace(" ", "")
                date = convert_date_format(date)
                value = value_matches[0].group()
                desc_start = date_match.end()
                desc_end = value_matches[0].start()
                description = line[desc_start:desc_end].strip()
                
                tipo = "D" if value.startswith("-") else "C"
                valor = value.replace("-", "")
                
                # Ajustar valor: remover ",00" se for um número inteiro
                if valor.endswith(",00"):
                    valor = valor[:-3]
                
                transactions.append({
                    "Data": date,
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
    Processa o texto extraído para o Itaú e retorna o DataFrame, XML e TXT.
    """
    transactions = preprocess_text(text)
    data = extract_transactions(transactions)
    if not data:
        return None, None, None
    df, xml_data = create_xml(data)
    txt_data = create_txt(data)
    return df, xml_data, txt_data