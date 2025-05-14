import streamlit as st

def display_menu():
    """
    Exibe o menu do Streamlit e retorna o banco selecionado e o arquivo carregado.
    """
    st.title("📊 Extrator de Extrato Bancário")
    st.write("Faça upload do extrato em PDF para extrair as movimentações.")

    bank = st.selectbox(
        "Selecione o banco",
        ["Caixa", "Inter", "Itaú","Nubank", "Sicoob"],
        help="Escolha o banco correspondente ao extrato"
    )
    
    uploaded_file = st.file_uploader(
        "Escolha o arquivo PDF",
        type="pdf",
        help="Envie o extrato bancário em formato PDF"
    )
    
    return bank, uploaded_file

def display_results(csv_data, bank):
    """
    Exibe os resultados do processamento e opções de download.
    """
    st.success("✅ Dados extraídos com sucesso!")
    #st.dataframe(df)


    st.download_button(
        "Baixar CSV",
        data=csv_data,
        file_name=f"extrato_{bank.lower()}.csv",
        mime="text/csv",
        help="Download dos dados em formato CSV"
        )