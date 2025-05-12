import pdfplumber
from pathlib import Path

def validate_pdf(file):
    """
    Valida se o arquivo fornecido é um PDF verificando sua extensão.
    Retorna True se válido, False caso contrário.
    """
    if file is None:
        return False
    file_name = file.name if hasattr(file, 'name') else str(file)
    return Path(file_name).suffix.lower() == '.pdf'

def read_pdf(file):
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