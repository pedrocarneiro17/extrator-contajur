import re

def identificar_banco(text):
    """
    Identifica o banco a partir do texto extraído do PDF.
    Retorna o nome do banco ou 'Banco não identificado'.
    """
    if not text:
        return "Erro: Texto vazio ou ilegível"

    linhas = text.splitlines()
    if not linhas:
        return "Erro: Texto vazio ou ilegível"
    palavras = text.split()

    # Stone
    if len(linhas) >= 3 and 'Instituição Stone Instituição' in linhas[2].strip():
        return "Stone"
    
    # Nubank
    if 'ouvidoria@nubank.com.br' in text:
        return "Nubank"

    # Santander
    if '3472' in text or '3222' in text and 'EXTRATOCONSOLIDADOINTELIGENTE' in text:
        return "Santander2"
        
    if '3472' in text or '3222' in text:
        return "Santander1"

    # Bradesco
    if '00632' in text:
        return "Bradesco"
    
    # Banco do Brasil (variações)
    if '473-1' in text:
        return "Banco do Brasil2" if text.strip().split()[0].lower() == 'extrato' else "Banco do Brasil1"
    
    # Sicredi
    if '0179' in text:
        return "Sicredi"
    
    # PagBank
    first_line = linhas[0].strip().lower()
    if 'pagseguro' in first_line:
        return "PagBank"
    
    # Sicoob (variações)
    if palavras and palavras[0].lower().startswith('sicoob'):
        return "Sicoob1"
    if (linhas and "Sicoob | Internet Banking" in linhas[0].strip() and 
        "SISTEMA DE COOPERATIVAS DE CRÉDITO DO BRASIL" in text):
        return "Sicoob2"
    
    # Banco Inter
    if len(linhas) >= 3 and 'Banco Inter' in linhas[2]:
        return "Banco Inter"
    
    # Itaú (variações)
    if '8119' in text or '1472' in text:
        first_line = linhas[0].strip().lower()
        if re.match(r"^\s*extrato\s+mensal", first_line):
            return "Itaú3"
        if 'dados gerais' in first_line:
            for linha in linhas:
                if re.match(r"^\d{2}/\d{2}/\d{4}$", linha.strip()):
                    return "Itaú2"
        return "Itaú"
    
    # Outros bancos específicos
    if 'Extrato da Conta Digital iFood' in text:
        return "iFood"
    
    if 'ASAAS Gestão Financeira Instituição de Pagamento S.A.' in text:
        return "Asaas"
    
    if 'Cora SCFI' in text:
        return "Cora"
    
    if 'Banco Safra S/A' in text:
        return "Safra"
    
    if any(palavra.lower() == 'extrato' for palavra in text.split()):
        return "Caixa"

    return "Banco não identificado"