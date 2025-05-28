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

import re

def identificar_banco(text):
    """
    Identifica o banco a partir do texto extraído da primeira página do PDF.
    Diferencia entre Stone (terceira linha contém 'Instituição Stone Instituição de Pagamento S.A.'),
    Itaú3 (inicia com 'extrato mensal'), Itaú2 (primeira linha contém 'dados gerais' e formato DD/MM/YYYY),
    Itaú (contém '8119' e não se encaixa nos outros casos do Itaú), Santander (contém '3472' ou '3222'),
    Nubank (contém 'Agência 0001' e 'ouvidoria@nubank.com.br' no rodapé), Sicoob1 (inicia com 'sicoob'),
    Sicoob2 (inicia com data e contém 'Sicoob | Internet Banking' e 'SISTEMA'), e outros bancos.
    """
    if not text:
        return "Erro: Texto vazio ou ilegível"

    # Quebra o texto em linhas e palavras
    linhas = text.splitlines()
    if not linhas:
        return "Erro: Texto vazio ou ilegível"
    palavras = text.split()

    # Verificar se é Stone: terceira linha contém 'Instituição Stone Instituição de Pagamento S.A.'
    if len(linhas) >= 3 and 'Instituição Stone Instituição' in linhas[2].strip():
        return "Stone"

    # Verificar se é Nubank: 'Agência 0001' no texto e 'ouvidoria@nubank.com.br' no rodapé
    if 'Agência 0001' in text:
        paginas = re.split(r'Extrato gerado dia \d{2} de \w+ de \d{4} às \d{2}:\d{2} \d de \d', text)
        for pagina in paginas:
            linhas_pagina = [linha.strip() for linha in pagina.splitlines() if linha.strip()]
            ultimas_linhas = linhas_pagina[-10:] if len(linhas_pagina) >= 10 else linhas_pagina
            if any('ouvidoria@nubank.com.br' in linha.lower() for linha in ultimas_linhas):
                return "Nubank"

    # Verificar se é Santander (pelos códigos de agência '3472' ou '3222')
    if '3472' in text or '3222' in text:
        return "Santander"

    # Verificar se é Itaú (pelo código '8119' ou '1472')
    if '8119' in text or '1472' in text:
        first_line = linhas[0].strip().lower()
        if re.match(r"^\s*extrato\s+mensal", first_line):
            return "Itaú3"
        if 'dados gerais' in first_line:
            for linha in linhas:
                if re.match(r"^\d{2}/\d{2}/\d{4}$", linha.strip()):
                    return "Itaú2"
        return "Itaú"

    # Outras regras de identificação
    if '00632' in text:
        return "Bradesco"
    if '0179' in text:
        return "Sicredi"
    
    first_line = linhas[0].strip().lower()
    if 'pagseguro' in first_line:
        return "PagBank"
    
    # Verificar Sicoob1: começa com 'sicoob'
    if palavras and palavras[0].lower().startswith('sicoob'):
        return "Sicoob1"

    # Verificar Sicoob2: primeira linha contém 'Sicoob | Internet Banking' e texto contém 'SISTEMA'
    if (linhas and "Sicoob | Internet Banking" in linhas[0].strip() and 
        "SISTEMA DE COOPERATIVAS DE CRÉDITO DO BRASIL" in text):
        return "Sicoob2"
    
    if len(linhas) >= 3 and 'Banco Inter' in linhas[2]:
        return "Banco Inter"
    
    if any(palavra.lower() == 'extrato' for palavra in text.split()):
        return "Caixa"

    return "Banco não identificado"

