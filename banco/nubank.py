import re
import pandas as pd
from io import BytesIO
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

def preprocess_text(text):
    """
    Pré-processa o texto do extrato do Nubank para extrair transações, ignorando cabeçalho, rodapé e totais.
    Usa a descrição completa da transação como coluna Descrição.
    Mantém valores no formato brasileiro (ex.: 1.012,29).
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    # Mapa de meses para conversão de data
    month_map = {
        "jan": "01", "fev": "02", "mar": "03", "abr": "04", "mai": "05", "jun": "06",
        "jul": "07", "ago": "08", "set": "09", "out": "10", "nov": "11", "dez": "12"
    }
    
    date_pattern = r"^\d{1,2}\s+(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)\s+\d{4}"
    value_pattern = r"([-]?\s*\d{1,3}(?:\.\d{3})*,\d{2})\b"
    
    transactions = []
    current_date = None
    current_description = []
    last_value_line = None
    
    for i, line in enumerate(lines):
        # Ignorar linhas de cabeçalho, rodapé e totais
        if any(keyword in line.upper() for keyword in [
            "PEDRO AUGUSTO", "CPF", "AGÊNCIA", "CONTA", "VALORES EM R$", "SALDO FINAL",
            "SALDO INICIAL", "RENDIMENTO", "TOTAL DE ENTRADAS", "TOTAL DE SAÍDAS",
            "TEM ALGUMA DÚVIDA", "OUVIDORIA", "EXTRATO GERADO", "NU FINANCEIRA",
            "NU PAGAMENTOS", "SALDO LÍQUIDO", "MOVIMENTAÇÕES"
        ]):
            continue
        
        # Verificar se a linha é uma data
        date_match = re.match(date_pattern, line, re.IGNORECASE)
        if date_match:
            day = date_match.group(1).zfill(2)
            month = month_map.get(date_match.group(2).lower(), "01")
            year = date_match.group(3)
            current_date = f"{day}/{month}/{year}"
            current_description = []
            last_value_line = None
            continue
        
        # Processar linhas de transação
        value_match = re.search(value_pattern, line)
        if value_match and current_date:
            value = value_match.group(1).replace(" ", "").strip()
            tipo = "D" if value.startswith("-") else "C"
            valor = value.replace("-", "").strip()
            
            # Remover ",00" se for um número inteiro
            if valor.endswith(",00"):
                valor = valor[:-3]
            
            # Usar linhas acumuladas como descrição
            description_parts = current_description[:]
            
            # Adicionar texto antes do valor na linha atual, se houver
            desc_start = 0
            desc_end = value_match.start()
            line_description = line[desc_start:desc_end].strip()
            if line_description:
                description_parts.append(line_description)
            
            description = " ".join(part for part in description_parts if part).strip()
            
            # Evitar descrições vazias
            if description:
                transactions.append({
                    "Data": current_date,
                    "Descrição": description,
                    "Valor": valor,
                    "Tipo": tipo
                })
            
            # Resetar descrição, mas manter a linha atual como possível início de nova descrição
            current_description = [line[value_match.end():].strip()] if line[value_match.end():].strip() else []
            last_value_line = i
        else:
            # Acumular linha como parte da descrição, exceto se for imediatamente após um valor
            if last_value_line is None or i > last_value_line + 1 or not current_description:
                current_description.append(line)
    
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
    Processa o texto extraído do extrato do Nubank e retorna o DataFrame, XML e TXT.
    """
    transactions = preprocess_text(text)
    data = extract_transactions(transactions)
    if not data:
        return None, None, None
    df, xml_data = create_xml(data)
    txt_data = create_txt(data)
    return df, xml_data, txt_data