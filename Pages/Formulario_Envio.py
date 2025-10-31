import streamlit as st
import pandas as pd
from datetime import date, timedelta


st.set_page_config(
    page_title="Formulário de Solicitação de Relatório",
    layout="centered"
)


if 'solicitacao_data' not in st.session_state:
    st.session_state.solicitacao_data = {}
if 'formulario_enviado' not in st.session_state:
    st.session_state.formulario_enviado = False



st.title("📄 Formulário de Solicitação de Relatório")
st.markdown("---")

st.markdown(
    """
    Olá! Neste formulário você responderá algumas perguntas sobre o que deseja investigar: 
    o objetivo da análise, quais indicadores e métricas você considera essenciais e indispensáveis, 
    qual(ais) setor(es) envolvido(s), o prazo em que você espera receber esse reporte e o mais essencial: a fonte de dados.
    
    Cada informação é importante, então não deixe nada de fora!
    """
)

if st.session_state.formulario_enviado:
    st.success("✅ **Solicitação Enviada com Sucesso!**")
    st.info("O Analista de Dados foi notificado e pode acessar o Painel Restrito (Home).")
    
    if st.button("Enviar Nova Solicitação"):
        st.session_state.formulario_enviado = False
        st.rerun()

else:
    
    with st.form("solicitacao_relatorio_form", clear_on_submit=True):
        
        st.header("Detalhes da Análise")

        
        objetivo_analise = st.text_area(
            "1. Qual o **Objetivo da Análise**? (O que deseja investigar?) *",
            height=100,
            placeholder="Ex: Identificar a causa da queda de vendas na região Sudeste no último trimestre."
        )

        
        indicadores = st.text_area(
            "2. Quais **Indicadores e Métricas** você considera essenciais e indispensáveis? *",
            height=70,
            placeholder="Ex: Volume de Vendas, Margem de Lucro, Taxa de Conversão, Ticket Médio."
        )
        
        
        st.markdown("**Quais as pessoas e/ou setores envolvidos?***")
        setores_envolvidos = st.text_area(
            "Incluir quem precisa ter acesso ao link do relatório, quem pode esclarecer dúvidas sobre a base ou projeto...",
            height=70,
            placeholder="Ex: João, Maria, Diretoria de Vendas..."
        )

        st.markdown("---")
        st.header("Prazo e Fonte de Dados")
        
        
        st.markdown("**Prazo esperado de entrega do relatório***")
        st.caption("Tenha em mente um prazo realista e com o mínimo de 2 dias.")
        prazo_esperado = st.date_input(
            "Selecione a data de vencimento",
            min_value=date.today() + timedelta(days=2),
            value=date.today() + timedelta(days=5) 
        )

        
        st.subheader("Fonte de Dados *")
        st.caption("Você pode anexar o arquivo OU fornecer um link.")

        col_file, col_link = st.columns(2)

        with col_file:
            arquivo_upload = st.file_uploader(
                "Precisa anexar arquivos? Solte seu arquivo (Excel/CSV) aqui.",
                type=['xlsx', 'csv'],
                accept_multiple_files=False
            )
        
        with col_link:
            link_planilha = st.text_input(
                "OU cole o link da planilha/base (Google Sheets, OneDrive, etc.)",
                placeholder="https://docs.google.com/spreadsheets/d/..."
            )


        st.markdown("---")
        
        
        submitted = st.form_submit_button("Enviar Solicitação", type="primary")

        if submitted:
            
            if not objetivo_analise:
                st.error("⚠️ **Erro:** O campo 'Objetivo da Análise' é obrigatório.")
            elif not indicadores:
                st.error("⚠️ **Erro:** O campo 'Indicadores e Métricas' é obrigatório.")
            elif not setores_envolvidos:
                st.error("⚠️ **Erro:** O campo 'Pessoas e/ou setores envolvidos' é obrigatório.")
            elif not arquivo_upload and not link_planilha:
                st.error("⚠️ **Erro:** A Fonte de Dados (arquivo OU link) é obrigatória.")
            else:
                
                st.session_state.solicitacao_data = {
                    'objetivo': objetivo_analise,
                    'indicadores': indicadores,
                    'setores': setores_envolvidos,
                    'prazo': prazo_esperado.strftime("%d/%m/%Y"),
                    'file': arquivo_upload,
                    'link': link_planilha,
                    'timestamp': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.formulario_enviado = True
                st.rerun()