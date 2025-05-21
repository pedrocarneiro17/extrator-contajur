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
    Diferencia entre Itaú3 (inicia com 'extrato mensal'), Itaú2 (primeira linha contém 'dados gerais' e formato DD/MM/YYYY),
    Itaú (contém '8119' e não se encaixa nos outros casos do Itaú), Santander (contém '3472' ou '3222'),
    e outros bancos com base em palavras-chave específicas.
    """
    if not text:
        return "Erro: Texto vazio ou ilegível"

    # Quebra o texto em linhas
    linhas = text.splitlines()
    if not linhas:
        return "Erro: Texto vazio ou ilegível"

    # Verificar se é Santander (pelos códigos de agência '3472' ou '3222')
    if '3472' in text or '3222' in text:
        return "Santander"

    # Verificar se é Itaú (pelo código '8119')
    if '8119' in text or '1472' in text:
        # Verificar se a primeira linha começa com 'extrato mensal' (Itaú3)
        first_line = linhas[0].strip().lower()
        if re.match(r"^\s*extrato\s+mensal", first_line):
            return "Itaú3"

        # Verificar se a primeira linha contém 'dados gerais' (Itaú2)
        if 'dados gerais' in first_line:
            # Procurar por formato de data DD/MM/YYYY (ex.: 05/03/2025)
            for linha in linhas:
                if re.match(r"^\d{2}/\d{2}/\d{4}$", linha.strip()):
                    return "Itaú2"

        # Caso não se encaixe em Itaú3 ou Itaú2, mas tenha '8119', é Itaú
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