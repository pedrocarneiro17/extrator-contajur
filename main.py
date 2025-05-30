import streamlit as st
from auxiliares.pdf_reader import validate_pdf
from banco import get_processor
from auxiliares.xml_to_csv import xml_to_csv
from auxiliares.menu import display_menu, display_results

def run_app():
    """
    Orquestra o fluxo principal da aplicação Streamlit.
    """
    bank, uploaded_file, text = display_menu()

    if uploaded_file is not None and bank:
        if not validate_pdf(uploaded_file) or uploaded_file.size == 0:
            st.error("❌ O arquivo PDF está vazio ou inválido. Por favor, envie um arquivo válido.")
            return

        try:
            with st.spinner("Processando arquivo..."):
                # O texto já foi extraído em display_menu, reutilizamos
                processor = get_processor(bank)
                result = processor(text)
                
                xml_data, txt_data = result
                
                if xml_data is None or txt_data is None:
                    st.warning("Nenhuma transação encontrada. Verifique o formato do arquivo.")
                    return
                
                xml_data.seek(0)
                csv_data = xml_to_csv(xml_data)
                
                display_results(csv_data, bank)

        except Exception as e:
            st.error(f"❌ Erro no processamento: {str(e)}")
            st.error("Verifique se o arquivo corresponde ao formato esperado.")

run_app()