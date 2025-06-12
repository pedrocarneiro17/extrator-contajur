import streamlit as st
from auxiliares.pdf_reader import validate_pdf
from banco import get_processor
from auxiliares.xml_to_csv import xml_to_csv
from auxiliares.menu import display_menu, display_results
import concurrent.futures
import io
import zipfile

def process_single_pdf(uploaded_file, bank, text):
    """
    Processa um único PDF e retorna o nome do arquivo, CSV gerado e mensagem de erro (se houver).
    """
    try:
        if not validate_pdf(uploaded_file) or uploaded_file.size == 0:
            return uploaded_file.name, None, "❌ O arquivo PDF está vazio ou inválido."

        with st.spinner(f"Processando {uploaded_file.name}..."):
            processor = get_processor(bank)
            result = processor(text)
            
            xml_data, txt_data = result
            
            if xml_data is None or txt_data is None:
                return uploaded_file.name, None, "Nenhuma transação encontrada no arquivo."
            
            xml_data.seek(0)
            csv_data = xml_to_csv(xml_data)
            return uploaded_file.name, csv_data, None

    except Exception as e:
        return uploaded_file.name, None, f"❌ Erro no processamento: {str(e)}"

def create_zip_from_csvs(results):
    """
    Cria um arquivo ZIP contendo todos os CSVs gerário.
    """
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_name, csv_data, _ in results:
            if csv_data:
                # Gera o nome do arquivo CSV baseado no nome do PDF
                csv_file_name = f"extrato_{file_name.rsplit('.', 1)[0]}.csv"
                # Converte csv_data para bytes
                if isinstance(csv_data, io.StringIO):
                    data = csv_data.getvalue().encode('utf-8')  # Converte string para bytes
                elif isinstance(csv_data, io.BytesIO):
                    data = csv_data.getvalue()  # Obtém bytes diretamente
                else:
                    data = csv_data  # Assume que já é bytes ou string
                    if isinstance(data, str):
                        data = data.encode('utf-8')
                # Adiciona o CSV ao ZIP
                zip_file.writestr(csv_file_name, data)
    zip_buffer.seek(0)
    return zip_buffer

def run_app():
    """
    Orquestra o fluxo principal da aplicação Streamlit para múltiplos PDFs com download único.
    """
    banks, uploaded_files, texts = display_menu()

    if uploaded_files and banks and texts:
        results = []
        with st.spinner("Processando arquivos..."):
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Cria tarefas para processar cada PDF em paralelo
                future_to_file = {
                    executor.submit(process_single_pdf, uploaded_file, bank, text): uploaded_file
                    for uploaded_file, bank, text in zip(uploaded_files, banks, texts)
                }
                
                for future in concurrent.futures.as_completed(future_to_file):
                    uploaded_file = future_to_file[future]
                    try:
                        file_name, csv_data, error = future.result()
                        results.append((file_name, csv_data, error))
                    except Exception as e:
                        results.append((uploaded_file.name, None, f"❌ Erro inesperado: {str(e)}"))

        # Exibe os resultados e erros
        has_success = False
        for file_name, csv_data, error in results:
            if error:
                st.error(f"{file_name}: {error}")
            else:
                #st.success(f"{file_name}: ✅ Dados extraídos com sucesso!")
                has_success = True

        # Se houver pelo menos um CSV gerado, oferece o download do ZIP
        if has_success:
            zip_buffer = create_zip_from_csvs(results)
            st.download_button(
                label="Baixar todos os CSVs (ZIP)",
                data=zip_buffer,
                file_name="extratos.zip",
                mime="application/zip",
                help="Download de todos os CSVs gerados em um arquivo ZIP"
            )

run_app()