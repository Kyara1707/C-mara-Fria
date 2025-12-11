import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(
    page_title="Monitoramento Câmara Fria ❄️",
    page_icon="❄️",
    layout="centered"
)

# --- ARQUIVOS E CONSTANTES ---
ARQUIVO_USUARIOS = "users.csv"
ARQUIVO_DADOS = "dados_temperatura.csv"
LIE = 2.0  # Limite Inferior
LSE = 7.0  # Limite Superior

# --- ESTILO CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f6f9; color: #0e1117; }
    .stButton>button {
        background-color: #0054a6; color: white; border-radius: 20px;
        border: none; padding: 10px 24px; font-weight: bold; width: 100%;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #003d7a; }
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        border-radius: 15px; border: 1px solid #0054a6;
    }
    .alert-box-red {
        background-color: #ffcccc; color: #990000; padding: 20px;
        border-radius: 15px; border: 2px solid #990000; text-align: center;
        font-size: 20px; font-weight: bold; margin-top: 15px;
    }
    .alert-box-green {
        background-color: #ccffcc; color: #006600; padding: 20px;
        border-radius: 15px; border: 2px solid #006600; text-align: center;
        font-size: 20px; font-weight: bold; margin-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE DADOS (COM PROTEÇÃO) ---

def carregar_usuarios():
    """Lê users.csv. Se não existir, avisa."""
    if not os.path.exists(ARQUIVO_USUARIOS):
        return None

    try:
        # Lê o arquivo existente
        df = pd.read_csv(ARQUIVO_USUARIOS, sep=';', encoding='latin1', dtype=str)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.error(f"O arquivo users.csv existe mas está corrompido: {e}")
        return None

def carregar_historico():
    if not os.path.exists(ARQUIVO_DADOS):
        return pd.DataFrame(columns=["Usuario", "Cargo", "Data", "Horario", "Temperatura", "Status"])
    return pd.read_csv(ARQUIVO_DADOS, sep=";")

def salvar_registro(usuario, cargo, temp, status):
    agora = datetime.now()
    nova_linha = pd.DataFrame([{
        "Usuario": usuario,
        "Cargo": cargo,
        "Data": agora.strftime("%d/%m/%Y"),
        "Horario": agora.strftime("%H:%M:%S"),
        "Temperatura": temp,
        "Status": status
    }])
    try:
        nova_linha.to_csv(ARQUIVO_DADOS, mode='a', header=not os.path.exists(ARQUIVO_DADOS), index=False, sep=";")
    except PermissionError:
        st.error("Erro: Feche o arquivo Excel antes de salvar!")

# --- TELAS ---

def tela_login():
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #0054a6;'>Câmara Fria ❄️</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Controle de Qualidade</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.info("Identifique-se para continuar")
        login_id = st.text_input("ID de Matrícula").strip()
        
        if st.button("ACESSAR"):
            df_users = carregar_usuarios()
            
            if df_users is None or df_users.empty:
                st.error("Erro: users.csv não encontrado na pasta.")
                return 

            if 'id_login' in df_users.columns:
                # Busca exata (remove espaços)
                usuario = df_users[df_users['id_login'].str.strip() == login_id]
                
                if not usuario.empty:
                    st.session_state['usuario_nome'] = usuario.iloc[0]['nome']
                    st.session_state['usuario_cargo'] = usuario.iloc[0]['tipo']
                    st.rerun()
                else:
                    st.error("❌ Matrícula não encontrada.")
            else:
                st.error("Erro: O arquivo CSV não tem a coluna 'id_login'.")

def tela_cadastro():
    st.sidebar.markdown(f"### 👤 {st.session_state['usuario_nome']}")
    st.sidebar.markdown(f"**Cargo:** {st.session_state['usuario_cargo']}")
    
    if st.sidebar.button("Sair / Logout"):
        st.session_state.clear()
        st.rerun()

    st.markdown("## 📝 Registrar Temperatura")
    st.markdown(f"**Faixa Permitida:** <span style='color:blue'>{LIE}ºC</span> a <span style='color:blue'>{LSE}ºC</span>", unsafe_allow_html=True)
    
    with st.container():
        st.write("") 
        temp_input = st.number_input("Temperatura Atual (ºC):", step=0.1, format="%.1f")
        
        if st.button("SALVAR LEITURA"):
            status = ""
            if LIE <= temp_input <= LSE:
                status = "OK"
                salvar_registro(st.session_state['usuario_nome'], st.session_state['usuario_cargo'], temp_input, status)
                st.markdown(f"""<div class="alert-box-green">✅ SUCESSO<br>Temperatura {temp_input}ºC registrada.</div>""", unsafe_allow_html=True)
                st.balloons()
            else:
                status = "ERRO"
                salvar_registro(st.session_state['usuario_nome'], st.session_state['usuario_cargo'], temp_input, status)
                st.markdown(f"""<div class="alert-box-red">🚨 ERRO: FORA DO LIMITE!<br>Temperatura: {temp_input}ºC<hr>⚠️ INFORMAR AO SUPERIOR</div>""", unsafe_allow_html=True)

def tela_grafico():
    st.markdown("## 📊 Controle Semanal")
    df = carregar_historico()
    
    if df.empty:
        st.info("Nenhum dado registrado ainda.")
        return

    # Converte para datetime
    df['Datetime'] = pd.to_datetime(df['Data'] + ' ' + df['Horario'], format='%d/%m/%Y %H:%M:%S')
    
    # Filtra semana
    data_limite = datetime.now() - timedelta(days=7)
    df_semanal = df[df['Datetime'] >= data_limite].sort_values(by='Datetime')

    if df_semanal.empty:
        st.warning("Sem dados nesta semana.")
        return

    # Gráfico
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_semanal['Datetime'], 
        y=df_semanal['Temperatura'], 
        mode='lines+markers', 
        name='Temperatura', 
        line=dict(color='#0054a6', width=4), 
        marker=dict(size=10, color='white', line=dict(width=2, color='#0054a6'))
    ))
    fig.add_hline(y=LSE, line_dash="dash", line_color="red", annotation_text=f"Max {LSE}ºC")
    fig.add_hline(y=LIE, line_dash="dash", line_color="blue", annotation_text=f"Min {LIE}ºC")
    fig.update_layout(title="Variação de Temperatura", xaxis_title="Data/Hora", yaxis_title="ºC", template="plotly_white", height=450)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # --- CORREÇÃO DO ERRO AQUI ---
    with st.expander("Ver Histórico Detalhado"):
        # Ordenamos PRIMEIRO pela data, DEPOIS selecionamos as colunas para exibir
        tabela_exibicao = df_semanal.sort_values(by='Datetime', ascending=False)
        st.dataframe(
            tabela_exibicao[['Data', 'Horario', 'Usuario', 'Temperatura', 'Status']], 
            use_container_width=True
        )

    with open(ARQUIVO_DADOS, "rb") as file:
        st.download_button(label="📥 Baixar Relatório (Excel)", data=file, file_name="relatorio_camara_fria.csv", mime="text/csv")

# --- NAVEGAÇÃO ---
if 'usuario_nome' not in st.session_state:
    tela_login()
else:
    menu = st.radio("Navegação:", ["Cadastro", "Gráfico"], horizontal=True)
    if menu == "Cadastro": tela_cadastro()
    else: tela_grafico()