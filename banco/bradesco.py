import re
from utils import process_transactions

def preprocess_text(text):
    """
    Pré-processa o texto bruto do extrato do Bradesco para extrair transações.
    Implementa a lógica de extrair_texto_limpo_pdf (identificação de tabela,
    junção de descrições quebradas, propagação de datas) e extrai transações
    no formato {Data, Descrição, Valor, Tipo}.
    """
    # Log do texto bruto recebido
    print("Texto bruto recebido (primeiras 500 caracteres):")
    print(text[:500] + "..." if len(text) > 500 else text)
    
    # Normaliza o texto e divide em linhas
    text = re.sub(r"\s+", " ", text.strip())
    linhas = [linha.strip() for linha in text.splitlines() if linha.strip()]
    
    if not linhas:
        print("Nenhuma linha válida encontrada no texto bruto.")
        raise ValueError("Nenhuma linha válida encontrada no texto bruto.")
    
    print(f"Total de linhas após normalização: {len(linhas)}")
    
    # Identifica início da tabela
    inicio_idx = None
    for i, linha in enumerate(linhas):
        if re.search(r"\bData\b.*\bLançamento\b", linha, re.IGNORECASE):
            inicio_idx = i + 1
            break
    
    # Identifica fim da tabela
    fim_idx = None
    for i, linha in enumerate(linhas):
        if re.search(r"\bTotal\b", linha, re.IGNORECASE):
            fim_idx = i
            break
    
    if inicio_idx is None or fim_idx is None:
        print("Cabeçalho da tabela não encontrado. Linhas processadas:")
        for i, linha in enumerate(linhas[:10]):
            print(f"Linha {i}: {linha}")
        raise ValueError("Tabela de lançamentos não encontrada no PDF.")
    
    # Fatia linhas e remove linhas com "SALDO ANTERIOR"
    linhas_tabela = [
        linha.strip()
        for linha in linhas[inicio_idx:fim_idx]
        if linha.strip() and "SALDO ANTERIOR" not in linha.upper()
    ]
    print("Linhas da tabela extraídas:")
    for i, linha in enumerate(linhas_tabela):
        print(f"Linha {i}: {linha}")
    
    if not linhas_tabela:
        print("Nenhuma linha de transação encontrada na tabela.")
        raise ValueError("Nenhuma linha de transação encontrada na tabela.")
    
    # Junta descrições quebradas
    linhas_corrigidas = []
    buffer = ""
    for linha in linhas_tabela:
        if re.search(r"-?\d{1,3}(?:\.\d{3})*,\d{2}\b", linha):
            if buffer:
                linha = buffer.strip() + ' ' + linha.strip()
                buffer = ""
            linha = re.sub(r"\s+", " ", linha.strip())
            linhas_corrigidas.append(linha)
        else:
            buffer += "  " + linha.strip()
    print("Linhas após junção de descrições:")
    for i, linha in enumerate(linhas_corrigidas):
        print(f"Linha {i}: {linha}")
    
    # Propaga datas
    linhas_final = []
    data_atual = ""
    for linha in linhas_corrigidas:
        match_data = re.match(r"^(\d{2}/\d{2}/\d{4})\s+(.*)", linha)
        if match_data:
            data_atual = match_data.group(1)
            restante = match_data.group(2)
        else:
            restante = linha
        linha_formatada = f"{data_atual} {restante}".strip()
        linha_formatada = re.sub(r"\s+", " ", linha_formatada)
        linhas_final.append(linha_formatada)
    print("Linhas após propagação de datas:")
    for i, linha in enumerate(linhas_final):
        print(f"Linha {i}: {linha}")
    
    # Extrai transações
    transactions = []
    value_pattern = r"-?\d{1,3}(?:\.\d{3})*,\d{2}\b"
    
    for linha in linhas_final:
        # Extrai data
        match_data = re.match(r"^(\d{2}/\d{2}/\d{4})\s+(.*)", linha)
        if not match_data:
            print(f"Linha ignorada (sem data válida): {linha}")
            continue
        
        data = match_data.group(1)
        restante = match_data.group(2)
        
        # Encontra o primeiro valor monetário
        value_match = re.search(value_pattern, restante)
        if not value_match:
            print(f"Linha ignorada (sem valor monetário): {linha}")
            continue
        
        # O primeiro valor é o valor da transação
        valor = value_match.group(0).replace("-", "").strip()
        tipo = "C" if not value_match.group(0).startswith("-") else "D"
        
        # Captura a descrição como tudo antes do primeiro valor monetário
        desc_end = value_match.start()
        descricao = restante[:desc_end].strip()
        descricao = re.sub(r"\s+", " ", descricao)
        
        # Remove ",00" para números inteiros
        if valor.endswith(",00"):
            valor = valor[:-3]
        
        transacao = {
            "Data": data,
            "Descrição": descricao,
            "Valor": valor,
            "Tipo": tipo
        }
        transactions.append(transacao)
        print(f"Transação extraída: {transacao}")
    
    if not transactions:
        print("Nenhuma transação extraída. Linhas processadas:")
        for i, linha in enumerate(linhas_final):
            print(f"Linha {i}: {linha}")
        raise ValueError("Nenhuma transação válida encontrada no extrato.")
    
    return transactions

def extract_transactions(transactions):
    """
    Extrai os dados das transações (usado para compatibilidade com a estrutura).
    """
    return transactions

def process(text):
    """
    Processa o texto extraído do extrato do Bradesco e retorna xml_data e txt_data.
    """
    return process_transactions(text, preprocess_text, extract_transactions)