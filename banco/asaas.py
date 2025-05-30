import re
import pandas as pd
import pdfplumber
from io import BytesIO
from utils import create_xml, create_txt, process_transactions  # Importar funções do utils

def preprocess_text(text):
    """
    Pré-processa o texto do extrato ASAAS, extraindo e formatando todas as transações.
    Retorna uma lista de dicionários com Data, Descrição, Valor e Tipo.
    Ignora cabeçalhos, rodapés, saldos e linhas mal formatadas.
    """
    def processar_transacao(transacao_unificada):
        """Processa uma transação unificada e retorna um dicionário ou None."""
        partes = transacao_unificada.split()
        if not partes or not date_pattern.match(partes[0]):
            return None
        
        data = partes[0]
        valor_match = value_pattern.search(transacao_unificada)
        if not valor_match:
            return None
        
        valor_str = valor_match.group(0)
        tipo = 'D' if 'R$ -' in valor_str else 'C'
        valor = valor_str.replace('R$', '').replace('-', '').strip()
        if valor.endswith(",00"):
            valor = valor[:-3]
        elif valor.endswith("0"):
            valor = valor[:-1]
        
        transacao_sem_data = ' '.join(partes[1:])
        descricao = transacao_sem_data.replace(valor_str, '').strip()
        
        if not (descricao and valor):
            return None
        
        return {
            "Data": data,
            "Descrição": descricao,
            "Valor": valor,
            "Tipo": tipo
        }

    # Dividir o texto em linhas
    linhas = text.splitlines()
    transactions = []
    transacao_atual = []
    encontrou_marcador_inicio = False
    date_pattern = re.compile(r'^\d{2}/\d{2}/\d{4}')  # DD/MM/YYYY
    value_pattern = re.compile(r'R\$\s*-?\d{1,3}(?:\.\d{3})*,\d{2}')  # R$ ou R$ - seguido de valor
    
    for linha in linhas:
        linha = linha.strip()
        if not linha:
            continue
        
        # Corrigir tabulações nos valores (ex.: 1.055\t00 -> 1.055,00)
        linha = re.sub(r'(\d)\t(\d)', r'\1,\2', linha)
        # Normalizar espaços
        linha = re.sub(r'\s+', ' ', linha).strip()
        
        # Identificar a linha "Data Movimentações Valor"
        if "Data Movimentações Valor" in linha:
            encontrou_marcador_inicio = True
            continue
        
        # Ignorar tudo antes do marcador inicial
        if not encontrou_marcador_inicio:
            continue
        
        # Ignorar cabeçalhos, rodapés, saldos e linhas com "Conta" seguido de número com hífen
        if any(phrase in linha for phrase in [
            "GERAR SAUDE E BEM ESTAR",
            "CNPJ",
            "Período",
            "Extrato gerado em",
            "Saldo inicial",
            "Saldo final",
            "ASAAS Gestão Financeira",
        ]) or re.search(r'Conta\s+\d+-\d', linha):
            continue
        
        # Verificar se a linha começa com uma data
        if date_pattern.match(linha):
            # Processar a transação acumulada, se existir
            if transacao_atual:
                transacao_unificada = ' '.join(transacao_atual)
                transacao = processar_transacao(transacao_unificada)
                if transacao:
                    transactions.append(transacao)
            transacao_atual = [linha]
        else:
            transacao_atual.append(linha)
    
    # Processar a última transação
    if transacao_atual:
        transacao_unificada = ' '.join(transacao_atual)
        transacao = processar_transacao(transacao_unificada)
        if transacao:
            transactions.append(transacao)
    
    return transactions

def extract_transactions(transactions):
    """
    Retorna a lista de transações (mantido para compatibilidade).
    """
    return transactions

def process(text):
    """
    Processa o texto extraído do extrato ASAAS e retorna o DataFrame, XML e TXT.
    """
    return process_transactions(text, preprocess_text, extract_transactions)