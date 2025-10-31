import pandas as pd
from io import StringIO, BytesIO

def read_data_file(uploaded_file, file_type: str) -> pd.DataFrame:
    """
    Lê o arquivo carregado e retorna o DataFrame BRUTO.
    """
    if uploaded_file is None:
        return pd.DataFrame()

    try:
        if file_type == 'xlsx':
            
            df = pd.read_excel(BytesIO(uploaded_file.getvalue()))
        elif file_type == 'csv':
            
            df = pd.read_csv(StringIO(uploaded_file.getvalue().decode('utf-8')))
        else:
            print("Tipo de arquivo não suportado.")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"Erro ao ler o arquivo {uploaded_file.name}: {e}")
        return pd.DataFrame()

    return df


def clean_and_prepare_data_dynamic(df_bruto: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """
    Realiza a limpeza e padronização usando o mapeamento fornecido pelo usuário.
    """
    if df_bruto.empty:
        return pd.DataFrame()
        
    df = df_bruto.copy()
    
   
    valid_mapping = {k: v for k, v in mapping.items() if k is not None and k != ''}
    
    
    df.rename(columns=valid_mapping, inplace=True)
    
    
    if 'Data' in df.columns:
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')

    if 'Valor' in df.columns:
        
        df['Valor'] = df['Valor'].astype(str).str.replace(r'[^\d,\.-]', '', regex=True).str.replace(',', '.', regex=False)
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce')
    
  
    try:
        df.dropna(subset=['Data', 'Valor'], inplace=True)
    except KeyError as e:
        print(f"Erro grave: Coluna crítica ausente após mapeamento: {e}")
        return pd.DataFrame()

    if 'Categoria' not in df.columns:
        df['Categoria'] = 'Geral' 
    else:
        df['Categoria'] = df['Categoria'].fillna('N/A').astype(str)
    
    df.reset_index(drop=True, inplace=True)
    return df