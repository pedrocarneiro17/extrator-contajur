import streamlit as st
from pdf_reader import read_pdf, identificar_banco

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
            text = read_pdf(uploaded_file)
            bank = identificar_banco(text)
            
            if bank.startswith("Erro") or bank == "Banco não identificado":
                st.error(bank)
                bank = None
            else:
                st.success(f"Banco identificado: **{bank}**")
        except Exception as e:
            st.error(f"Erro ao processar o PDF: {str(e)}")
            bank = None

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