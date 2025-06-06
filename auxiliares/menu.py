import streamlit as st
from auxiliares.pdf_reader import read_pdf
from auxiliares.pdf_reader2 import read_pdf2

def display_menu():
    """
    Exibe o menu do Streamlit e retorna o banco identificado e o arquivo carregado.
    """
    st.title("📊 Extrator de Extrato Bancário")
    st.write("Faça upload do extrato em PDF para extrair as movimentações.")

    uploaded_file = st.file_uploader(
        "Escolha o arquivo PDF",
        type="pdf",
        help="Envie o extrato bancário em formato PDF"
    )

    bank = None
    text = None
    if uploaded_file is not None:
        try:
            # Resetar o ponteiro do arquivo para o início
            uploaded_file.seek(0)
            # Ler o PDF e identificar o banco (recebemos tupla)
            text, identified_bank = read_pdf(uploaded_file)
            bank = identified_bank  # Usamos o banco já identificado pela função
            
            if bank.startswith("Erro") or bank == "Banco não identificado":
                st.error(bank)
                bank = None
                text = None
            else:
                st.success(f"Banco identificado: **{bank}**")
                # Se for um dos bancos que precisam de read_pdf2
                if bank in ['Bradesco', 'Sicoob1', 'Sicoob2', 'Stone', 'Banco do Brasil1', 'Safra', 'Santander2', 'Efi1', 'Efi2']:
                    uploaded_file.seek(0)  # Resetar o ponteiro novamente
                    text = read_pdf2(uploaded_file)  # Note que read_pdf2 deve retornar apenas o texto
                
        except Exception as e:
            st.error(f"Erro ao processar o PDF: {str(e)}")
            bank = None
            text = None

    return bank, uploaded_file, text

def display_results(csv_data, bank):
    """
    Exibe os resultados do processamento e opções de download.
    """
    st.success("✅ Dados extraídos com sucesso!")
    # st.dataframe(df)  # Descomente se quiser exibir o dataframe

    st.download_button(
        label="Baixar CSV",
        data=csv_data,
        file_name=f"extrato_{bank.lower()}.csv",
        mime="text/csv",
        help="Download dos dados em formato CSV"
    )