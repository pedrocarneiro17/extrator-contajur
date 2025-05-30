from pathlib import Path
import pdfplumber
from auxiliares.identificador import identificar_banco

def validate_pdf(file):
    """Valida se o arquivo é um PDF válido."""
    if file is None:
        return False
    file_name = file.name if hasattr(file, 'name') else str(file)
    return Path(file_name).suffix.lower() == '.pdf'

def read_pdf(file):
    """
    Extrai texto de um PDF e identifica o banco.
    Retorna uma tupla com (texto, nome_banco) ou levanta exceção em caso de erro.
    """
    if not validate_pdf(file):
        raise ValueError("Arquivo não é um PDF válido")
    
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    
    if not text.strip():
        raise ValueError("Nenhum texto extraído do PDF")
    
    return text, identificar_banco(text)