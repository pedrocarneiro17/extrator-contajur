import streamlit as st
from pdf_reader import validate_pdf, read_pdf
from banco import get_processor
from xml_to_csv import xml_to_csv
from menu import display_menu, display_results

def main():
    bank, uploaded_file = display_menu()

    if uploaded_file is not None and bank:
        if not validate_pdf(uploaded_file) or uploaded_file.size == 0:
            st.error("❌ O arquivo PDF está vazio ou inválido. Por favor, envie um arquivo válido.")
            return

        try:
            with st.spinner("Processando arquivo..."):
                text = read_pdf(uploaded_file)
                
                processor = get_processor(bank)
                df, xml_data, txt_data = processor(text)
                
                if df is None or xml_data is None or txt_data is None:
                    st.warning("Nenhuma transação encontrada. Verifique o formato do arquivo.")
                    with st.expander("Texto bruto extraído (para depuração)"):
                        st.text_area("Texto extraído", text, height=200)
                    return
                
                xml_data.seek(0)
                csv_data = xml_to_csv(xml_data)
                
                display_results(df, xml_data, txt_data, csv_data, text, bank)

        except Exception as e:
            st.error(f"❌ Erro no processamento: {str(e)}")
            st.error("Verifique se o arquivo corresponde ao banco selecionado")
            with st.expander("Texto bruto extraído (para depuração)"):
                st.text_area("Texto extraído", text, height=200)

if __name__ == "__main__":
    main()