import fitz  # PyMuPDF
import re
from auxiliares.utils import process_transactions

def preprocess_text(text):
    """
    Pré-processa o texto do extrato do Banco Safra para dividir transações, ignorando cabeçalho e rodapé.
    Combina todas as linhas entre data e valor em uma única coluna Descrição.
    Mantém valores no formato brasileiro (ex.: 1.012,29).
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    # Extrair o ano do período
    ano = None
    periodo_pattern = re.compile(r'Período de \d{2}/\d{2}/(\d{4}) a \d{2}/\d{2}/\d{4}')
    for line in lines:
        match = periodo_pattern.search(line)
        if match:
            ano = match.group(1)
            break
    
    # Identificar início das transações (após "Valor (R$)")
    start_index = 0
    for i, line in enumerate(lines):
        if "Valor (R$)" in line:
            start_index = i + 1
            break
    
    # Ignorar "Banco Safra S/A" e as 24 linhas seguintes
    transaction_lines = []
    i = start_index
    while i < len(lines):
        if "Banco Safra S/A" in lines[i]:
            i += 25  # Pula a linha atual + 24 linhas
        else:
            transaction_lines.append(lines[i])
            i += 1
    
    date_pattern = r"^\d{2}/\d{2}$"
    value_pattern = r"[-]?\d{1,3}(?:\.\d{3})*,\d{1,2}"
    
    transactions = []
    transacao_atual = []
    
    for line in transaction_lines:
        # Verifica se a linha é uma data (início de nova transação)
        date_match = re.match(date_pattern, line)
        if date_match:
            if transacao_atual:
                # Processa a transação acumulada se tiver um valor monetário
                value_match = re.search(value_pattern, transacao_atual[-1])
                if value_match:
                    data = f"{transacao_atual[0]}/{ano}" if ano else transacao_atual[0]
                    valor = value_match.group(0)
                    tipo = 'D' if '-' in valor else 'C'
                    # Remove o sinal de menos e formata o valor
                    valor_formatado = valor.replace('-', '')
                    if valor_formatado.endswith(',00'):
                        valor_formatado = valor_formatado[:-3]
                    else:
                        try:
                            num = float(valor_formatado.replace(',', '.'))
                            partes = f"{num:.2f}".split('.')
                            inteiro = partes[0]
                            decimal = partes[1]
                            inteiro_formatado = ""
                            for j, digito in enumerate(reversed(inteiro)):
                                if j > 0 and j % 3 == 0:
                                    inteiro_formatado = '.' + inteiro_formatado
                                inteiro_formatado = digito + inteiro_formatado
                            valor_formatado = f"{inteiro_formatado},{decimal}"
                        except ValueError:
                            pass  # Mantém valor_formatado como está
                    # Descrição é tudo entre data e valor
                    descricao = ' '.join(transacao_atual[1:-1]) if len(transacao_atual) > 2 else (transacao_atual[1] if len(transacao_atual) == 2 else '')
                    transactions.append({
                        "Data": data,
                        "Descrição": descricao,
                        "Valor": valor_formatado,
                        "Tipo": tipo
                    })
            transacao_atual = [line]  # Inicia nova transação
            continue
        
        # Verifica se a linha contém um valor monetário
        value_match = re.search(value_pattern, line)
        if value_match and transacao_atual:
            transacao_atual.append(line)
            # Processa a transação
            data = f"{transacao_atual[0]}/{ano}" if ano else transacao_atual[0]
            valor = value_match.group(0)
            tipo = 'D' if '-' in valor else 'C'
            # Remove o sinal de menos e formata o valor
            valor_formatado = valor.replace('-', '')
            if valor_formatado.endswith(',00'):
                valor_formatado = valor_formatado[:-3]
            else:
                try:
                    num = float(valor_formatado.replace(',', '.'))
                    partes = f"{num:.2f}".split('.')
                    inteiro = partes[0]
                    decimal = partes[1]
                    inteiro_formatado = ""
                    for j, digito in enumerate(reversed(inteiro)):
                        if j > 0 and j % 3 == 0:
                            inteiro_formatado = '.' + inteiro_formatado
                        inteiro_formatado = digito + inteiro_formatado
                    valor_formatado = f"{inteiro_formatado},{decimal}"
                except ValueError:
                    pass  # Mantém valor_formatado como está
            # Descrição é tudo entre data e valor
            descricao = ' '.join(transacao_atual[1:-1]) if len(transacao_atual) > 2 else (transacao_atual[1] if len(transacao_atual) == 2 else '')
            transactions.append({
                "Data": data,
                "Descrição": descricao,
                "Valor": valor_formatado,
                "Tipo": tipo
            })
            transacao_atual = []
            continue
        
        # Adiciona a linha à transação atual
        transacao_atual.append(line)
    
    return transactions

def extract_transactions(transactions):
    # Extrai os dados das transações (usado para compatibilidade com a estrutura).
    return transactions

def process(text):
    # Processa o texto extraído do extrato do Banco Safra e retorna o DataFrame, XML e TXT.
    return process_transactions(text, preprocess_text, extract_transactions)