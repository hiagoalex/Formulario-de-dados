import streamlit as st
import pandas as pd
import plotly.express as px
from data_processing import read_data_file, clean_and_prepare_data_dynamic 
from io import StringIO 
from datetime import date, timedelta


ANALISTA_PASSWORD = "smvdados"


st.set_page_config(
    page_title="Painel de Recebimento do Analista",
    layout="wide",
    initial_sidebar_state="expanded"
)


def reset_analise():
    """Limpa o estado da análise e permite nova solicitação."""
    st.session_state.formulario_enviado = False
    st.session_state.solicitacao_data = {}
    if 'df_bruto' in st.session_state:
        del st.session_state.df_bruto
    st.cache_data.clear()
    st.rerun()


@st.cache_data
def get_raw_data(file_uploader, type_):
    return read_data_file(file_uploader, type_)

@st.cache_data
def get_processed_data(df_bruto, mapping_key_data, mapping_key_valor, mapping_key_categoria):
    mapping = {
        mapping_key_data: 'Data',
        mapping_key_valor: 'Valor',
        mapping_key_categoria: 'Categoria'
    }
    valid_mapping = {k: v for k, v in mapping.items() if k is not None and k != ''}
    return clean_and_prepare_data_dynamic(df_bruto, valid_mapping)

def format_currency(value):
    if pd.isna(value):
        return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

@st.cache_data
def convert_df_to_csv(dataframe):
    return dataframe.to_csv(index=False, sep=';', decimal=',')



def main():
    
   
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("🔒 Acesso Restrito ao Painel de Análise")
        
        with st.form("login_form"):
            password_input = st.text_input("Insira sua senha de Analista:", type="password")
            login_button = st.form_submit_button("Acessar Painel", type="primary")
            
            if login_button:
                if password_input == ANALISTA_PASSWORD:
                    st.session_state.logged_in = True
                    st.success("Acesso concedido!")
                    st.rerun()
                else:
                    st.error("Senha incorreta. Acesso negado.")
            
        st.stop() 

  

    st.title("👩‍💻 Painel de Recebimento de Solicitações")
    st.markdown("---")
    
    st.sidebar.button("Sair (Logout)", on_click=lambda: st.session_state.__setitem__('logged_in', False))

    if 'formulario_enviado' not in st.session_state or not st.session_state.formulario_enviado:
        st.info("⚠️ Nenhuma solicitação foi enviada pela equipe. Aguardando envio via Formulário.")
        st.stop()
    
    
    request_data = st.session_state.solicitacao_data
    uploaded_file = request_data.get('file')
    link_planilha = request_data.get('link')
    
 

    st.header("📢 Última Solicitação Recebida")
    st.caption(f"Recebida em: {request_data['timestamp']}")

    col_det_1, col_det_2, col_det_3 = st.columns(3)
    
    with col_det_1:
        st.metric("Prazo Solicitado", request_data.get('prazo', 'N/A'))
    with col_det_2:
        st.info(f"**Pessoas/Setores:** {request_data.get('setores', 'N/A')}")
    with col_det_3:
        st.warning(f"**Fonte:** {'Arquivo Anexado' if uploaded_file else ('Link Externo' if link_planilha else 'Não especificada')}")

    st.markdown("---")
    
    st.subheader("📋 Requisitos da Análise")
    st.markdown(f"**Objetivo:** {request_data.get('objetivo', 'N/A')}")
    st.markdown(f"**Indicadores Chave:** {request_data.get('indicadores', 'N/A')}")
    st.markdown("---")
    

    if link_planilha:
        
        st.subheader("🔗 Link de Fonte de Dados")
        st.code(link_planilha)
        st.markdown(f"**[Abrir Link da Planilha]({link_planilha})**", unsafe_allow_html=True)
        st.info("Para analisar, abra o link, baixe o arquivo e inicie um novo recebimento com o arquivo local.")

    elif uploaded_file:
        
        st.subheader(f"📂 Arquivo Anexado: {uploaded_file.name}")
        st.caption(f"Tamanho: {round(uploaded_file.size / (1024 * 1024), 2)} MB")
        
        
        st.download_button(
            label="Baixar Arquivo Bruto",
            data=uploaded_file.getvalue(),
            file_name=uploaded_file.name,
            mime=uploaded_file.type,
            type="secondary"
        )
        
        st.markdown("---")
        
       
        
        st.header("⚙️ Processar para Análise Rápida")
        st.info("Clique no botão abaixo para carregar o arquivo e iniciar o mapeamento dinâmico de colunas.")
        
        
        if 'df_bruto' not in st.session_state:
             if st.button("Carregar Arquivo e Iniciar Mapeamento", type="primary"):
                 file_type = 'xlsx' if uploaded_file.name.endswith('.xlsx') else 'csv'
                 st.session_state.df_bruto = get_raw_data(uploaded_file, file_type)
                 st.rerun() 

        if 'df_bruto' in st.session_state and not st.session_state.df_bruto.empty:
            df_bruto = st.session_state.df_bruto
            
            with st.expander("Mapeamento e Análise Rápida", expanded=True):
                
                
                st.subheader("Configuração Dinâmica de Colunas")
                col_names = df_bruto.columns.tolist()
                col_options = ['NÃO USAR'] + col_names

                col_map_1, col_map_2, col_map_3 = st.columns(3)
                
                with col_map_1: col_data = st.selectbox("Coluna de **DATA**:", options=col_names, index=0)
                with col_map_2: col_valor = st.selectbox("Coluna de **VALOR**:", options=col_names, index=1 if len(col_names) > 1 else 0)
                with col_map_3: col_categoria = st.selectbox("Coluna de **CATEGORIA**:", options=col_options, index=0)
                
                if col_categoria == 'NÃO USAR': col_categoria = None

                
                if st.button("Limpar e Gerar Painel Rápido", key='process_btn', type="secondary"):
                    df = get_processed_data(df_bruto, col_data, col_valor, col_categoria)

                    if df.empty:
                        st.warning("⚠️ **Alerta:** A base de dados resultante está vazia. Verifique as colunas selecionadas ou o arquivo fonte.")
                    else:
                        st.success("✅ **Dados Mapeados e Limpos com Sucesso!**")
                        
                       
                        st.session_state.df_processed = df 
                        st.rerun() 

                
                if 'df_processed' in st.session_state and not st.session_state.df_processed.empty:
                    df = st.session_state.df_processed
                    
                    st.markdown("---")
                    st.subheader("📥 Base Tratada para Download")
                    csv_export = convert_df_to_csv(df)
                    st.download_button(
                        label="Baixar Base Tratada (CSV para Power BI)",
                        data=csv_export,
                        file_name=f'Base_Tratada_Solicitacao_{request_data["timestamp"].split(" ")[0]}.csv',
                        mime='text/csv',
                        type="primary"
                    )
                    
                  
                    st.header("Análise Rápida de Consistência")

                    df_filtered = df.copy() 

                    if 'Valor' in df_filtered.columns and 'Data' in df_filtered.columns:
                       
                        total_valor = df_filtered['Valor'].sum()
                        df_agrupado_data = df_filtered.groupby(df_filtered['Data'].dt.date)['Valor'].sum()
                        media_diaria = df_agrupado_data.mean() if not df_agrupado_data.empty else 0
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1: st.metric(label="💰 **Valor Total**", value=format_currency(total_valor))
                        with col2: st.metric(label="📊 **Transações**", value=len(df_filtered))
                        with col3: st.metric(label="📅 **Média Diária**", value=format_currency(media_diaria))

                    st.markdown("---")
                    
                  
                    col_vis_1, col_vis_2 = st.columns(2)

                    if 'Valor' in df_filtered.columns and 'Data' in df_filtered.columns:
                        
                        with col_vis_1:
                            st.subheader("Evolução do Valor")
                            df_daily = df_filtered.groupby(df_filtered['Data'].dt.to_period('D'))['Valor'].sum().reset_index()
                            df_daily['Data'] = df_daily['Data'].dt.to_timestamp()
                            fig = px.line(df_daily, x='Data', y='Valor', title='Soma Diária', template='plotly_white')
                            st.plotly_chart(fig, use_container_width=True)

                    if 'Categoria' in df.columns and 'Valor' in df.columns and col_categoria is not None: 
                        
                        with col_vis_2:
                            st.subheader("Proporção por Categoria")
                            df_category = df_filtered.groupby('Categoria')['Valor'].sum().reset_index()
                            fig_pie = px.pie(df_category, values='Valor', names='Categoria', title='Percentual', template='plotly_white')
                            st.plotly_chart(fig_pie, use_container_width=True)
                    elif 'Valor' in df.columns:
                        with col_vis_2:
                            st.info("Gráfico de Categoria indisponível.")

                    st.markdown("---")
                    st.caption("Tabela de Dados (Tratada)")
                    if st.checkbox('Mostrar Tabela Completa', key='show_table_processed'):
                        st.dataframe(df_filtered, use_container_width=True)

        elif 'df_bruto' in st.session_state and st.session_state.df_bruto.empty:
            st.error("⚠️ Erro de Leitura do Arquivo. Verifique o formato (.xlsx ou .csv).")

    else:
        st.warning("Nenhum arquivo ou link foi enviado na última solicitação. Verifique o Formulário de Envio.")

    st.sidebar.markdown("---")
    st.sidebar.button("Limpar e Receber Novo Envio", on_click=reset_analise)


if __name__ == '__main__':
    main()