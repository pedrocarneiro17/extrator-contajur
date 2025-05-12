import pandas as pd
from io import BytesIO
from xml.etree.ElementTree import parse

def xml_to_csv(xml_data):
    """
    Converte um arquivo XML em CSV e retorna o CSV como BytesIO.
    """
    try:
        tree = parse(xml_data)
        root = tree.getroot()
        
        data = []
        for transaction in root.findall("Transaction"):
            data.append({
                "Data": transaction.find("Data").text,
                "Descrição": transaction.find("Descrição").text,
                "Valor": transaction.find("Valor").text,
                "Tipo": transaction.find("Tipo").text
            })
        
        df = pd.DataFrame(data)
        
        output = BytesIO()
        df.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)
        
        return output
    except Exception as e:
        raise Exception(f"Erro ao converter XML para CSV: {str(e)}")