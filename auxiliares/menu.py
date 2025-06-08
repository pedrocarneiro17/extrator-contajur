import streamlit as st
from auxiliares.pdf_reader import read_pdf
from auxiliares.pdf_reader2 import read_pdf2

def display_menu():
    """
    Exibe o menu do Streamlit e retorna listas de bancos identificados, arquivos carregados e textos extraídos.
    """
    st.title("📊 Extrator de Extrato Bancário")
    st.write("Faça upload de um ou mais extratos em PDF para extrair as movimentações.")

    uploaded_files = st.file_uploader(
        "Escolha os arquivos PDF",
        type="pdf",
        accept_multiple_files=True,  # Permite múltiplos arquivos
        help="Envie os extratos bancários em formato PDF"
    )

    banks = []
    texts = []
    if uploaded_files:
        for uploaded_file in uploaded_files:
            try:
                # Resetar o ponteiro do arquivo para o início
                uploaded_file.seek(0)
                # Ler o PDF e identificar o banco (recebemos tupla)
                text, identified_bank = read_pdf(uploaded_file)
                
                if identified_bank.startswith("Erro") or identified_bank == "Banco não identificado":
                    st.error(f"{uploaded_file.name}: {identified_bank}")
                    banks.append(None)
                    texts.append(None)
                else:
                    #st.success(f"{uploaded_file.name}: Banco identificado: **{identified_bank}**")
                    # Se for um dos bancos que precisam de read_pdf2
                    if identified_bank in ['Bradesco', 'Sicoob1', 'Sicoob2', 'Stone', 'Banco do Brasil1', 'Safra', 'Santander2', 'Efi1', 'Efi2']:
                        uploaded_file.seek(0)  # Resetar o ponteiro novamente
                        text = read_pdf2(uploaded_file)  # read_pdf2 retorna apenas o texto
                    banks.append(identified_bank)
                    texts.append(text)
                
            except Exception as e:
                st.error(f"{uploaded_file.name}: Erro ao processar o PDF: {str(e)}")
                banks.append(None)
                texts.append(None)

    return banks, uploaded_files, texts

def display_results(csv_data, file_name):
    """
    Função mantida para compatibilidade, mas não será usada diretamente.
    """
    pass  # Não precisamos mais exibir botões individuais