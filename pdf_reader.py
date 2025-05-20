import re
import pandas as pd
from io import BytesIO
from pathlib import Path
import pdfplumber
from utils import create_xml, create_txt, process_transactions  # Importar funções do utils

def validate_pdf(file):
    """
    Valida se o arquivo fornecido é um PDF verificando sua extensão.
    Retorna True se válido, False caso contrário.
    """
    if file is None:
        return False
    file_name = file.name if hasattr(file, 'name') else str(file)
    return Path(file_name).suffix.lower() == '.pdf'

def read_pdf(file, bank=None):
    """
    Lê um arquivo PDF e extrai o texto de todas as páginas como um fluxo contínuo.
    Retorna o texto extraído ou levanta uma exceção se o arquivo for inválido.
    """
    if not validate_pdf(file):
        raise ValueError("O arquivo fornecido não é um PDF válido.")
    
    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        if not text.strip():
            raise ValueError("Nenhum texto foi extraído do PDF.")
        return text
    except Exception as e:
        raise Exception(f"Erro ao ler o PDF: {str(e)}")

def identificar_banco(text):
    """
    Identifica o banco a partir do texto extraído da primeira página do PDF.
    Diferencia entre Itaú3 (inicia com 'extrato mensal'), Itaú (formato DD / abr), 
    e Itaú2 (formato DD/MM/YYYY), todos com código '8119'.
    """
    if not text:
        return "Erro: Texto vazio ou ilegível"

    # Quebra o texto em linhas
    linhas = text.splitlines()
    if not linhas:
        return "Erro: Texto vazio ou ilegível"

    # Verificar se é Itaú (pelo código '8119')
    if '8119' in text:
        # Verificar se a primeira linha começa com 'extrato mensal' (Itaú3)
        first_line = linhas[0].strip().lower()
        if re.match(r"^\s*extrato\s+mensal", first_line):
            return "Itaú3"

        # Procurar por formatos de data
        for linha in linhas:
            # Itaú2: Formato DD/MM/YYYY (ex.: 05/03/2025)
            if re.match(r"^\d{2}/\d{2}/\d{4}$", linha):
                return "Itaú2"
            # Itaú: Formato DD / abr (ex.: 05 / mar)
            if re.match(r"^\d{2}\s*/\s*[a-z]{3}$", linha, re.IGNORECASE):
                return "Itaú"

    # Outras regras de identificação
    if '00632' in text:
        return "Bradesco"
    if any(palavra.lower().startswith('sicoob') for palavra in text.split()):
        return "Sicoob"
    if len(linhas) >= 3 and 'Banco Inter' in linhas[2]:
        return "Banco Inter"
    if any(palavra.lower() == 'extrato' for palavra in text.split()):
        return "Caixa"
    if 'ouvidoria@nubank.com.br' in text.lower():
        return "Nubank"
    return "Banco não identificado"