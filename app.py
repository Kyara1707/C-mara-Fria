import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(
    page_title="ColdSpec | Qualidade",
    page_icon="🧊",
    layout="centered"
)

# --- ARQUIVOS E CONSTANTES ---
ARQUIVO_USUARIOS = "users.csv"
ARQUIVO_DADOS_TEMP = "dados_temperatura.csv"
ARQUIVO_DADOS_NC = "dados_nao_conformidade.csv"
ARQUIVO_SKU = "sku.csv"

LIE = 2.0  # Limite Inferior Temperatura
LSE = 7.0  # Limite Superior Temperatura

# --- ESTILO CSS (VISUAL) ---
st.markdown("""
    <style>
    /* Forçar fundo claro e texto escuro globalmente */
    .stApp {
        background-color: #131314;
        color: #000000 !important;
    }
    
    /* Forçar cor preta em textos comuns, parágrafos e labels */
    p, label, span, div, li {
        color: #f0f0f0;
    }
    
    /* Forçar cor preta específica nos labels dos inputs */
    .stTextInput > label, .stNumberInput > label, .stSelectbox > label, .stRadio > label, .stTextArea > label {
        color: #f0f0f0 !important;
        font-weight: bold;
    }
    
    /* Forçar cor preta dentro das caixas de texto */
    .stTextInput input, .stNumberInput input, .stTextArea textarea {
        color: #000000 !important;
    }

    /* Títulos em Azul Escuro */
    h1, h2, h3, h4, h5, h6 {
        color: #479bd8 !important;
    }

    /* Botões */
    .stButton>button {
        background-color: #0054a6;
        color: white !important;
        border-radius: 20px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
        width: 100%;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #003d7a;
        color: white !important;
    }
    
    /* Inputs arredondados */
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        border-radius: 15px; 
        border: 1px solid #0054a6;
        background-color: #ffffff;
        color: #000000;
    }

    /* Alertas */
    .alert-box-red {
        background-color: #ffcccc; color: #990000 !important; padding: 20px;
        border-radius: 15px; border: 2px solid #990000; text-align: center;
        font-size: 20px; font-weight: bold; margin-top: 15px;
    }
    .alert-box-green {
        background-color: #ccffcc; color: #006600 !important; padding: 20px;
        border-radius: 15px; border: 2px solid #006600; text-align: center;
        font-size: 20px; font-weight: bold; margin-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE DADOS ---

def carregar_usuarios():
    if not os.path.exists(ARQUIVO_USUARIOS):
        return None
    try:
        df = pd.read_csv(ARQUIVO_USUARIOS, sep=';', encoding='latin1', dtype=str)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except: return None

def carregar_sku():
    if not os.path.exists(ARQUIVO_SKU):
        return pd.DataFrame()
    try:
        df = pd.read_csv(ARQUIVO_SKU, sep=';', encoding='latin1', dtype=str)
        return df
    except: return pd.DataFrame()

def carregar_historico_temp():
    if not os.path.exists(ARQUIVO_DADOS_TEMP):
        return pd.DataFrame(columns=["Usuario", "Cargo", "Data", "Horario", "Temperatura", "Status"])
    return pd.read_csv(ARQUIVO_DADOS_TEMP, sep=";")

def salvar_temp(usuario, cargo, temp, status):
    agora = datetime.now()
    nova_linha = pd.DataFrame([{
        "Usuario": usuario, "Cargo": cargo, "Data": agora.strftime("%d/%m/%Y"),
        "Horario": agora.strftime("%H:%M:%S"), "Temperatura": temp, "Status": status
    }])
    try: nova_linha.to_csv(ARQUIVO_DADOS_TEMP, mode='a', header=not os.path.exists(ARQUIVO_DADOS_TEMP), index=False, sep=";")
    except PermissionError: st.error("Erro: Feche o arquivo Excel!")

def salvar_nc(dados_dict):
    agora = datetime.now()
    dados_dict['Data'] = agora.strftime("%d/%m/%Y")
    dados_dict['Horario'] = agora.strftime("%H:%M:%S")
    
    df_new = pd.DataFrame([dados_dict])
    try:
        df_new.to_csv(ARQUIVO_DADOS_NC, mode='a', header=not os.path.exists(ARQUIVO_DADOS_NC), index=False, sep=";")
        return True
    except PermissionError:
        st.error("Erro: Feche o arquivo de Não Conformidade!")
        return False

# --- TELAS ---

def tela_login():
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>🧊 ColdSpec</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: white;'>Monitoramento & Qualidade</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.info("Acesso Restrito")
        login_id = st.text_input("ID de Matrícula").strip()
        
        if st.button("ACESSAR"):
            df_users = carregar_usuarios()
            if df_users is None or df_users.empty:
                st.error("Erro: users.csv não encontrado.")
                return 

            if 'id_login' in df_users.columns:
                usuario = df_users[df_users['id_login'].str.strip() == login_id]
                if not usuario.empty:
                    st.session_state['usuario_nome'] = usuario.iloc[0]['nome']
                    st.session_state['usuario_cargo'] = usuario.iloc[0]['tipo']
                    st.rerun()
                else: st.error("❌ Matrícula não encontrada.")
            else: st.error("Erro: CSV sem coluna id_login.")

def tela_cadastro_temp():
    st.markdown("## 🌡️ Monitoramento de Temperatura")
    st.markdown(f"**Faixa Permitida:** <span style='color:blue'>{LIE}ºC</span> a <span style='color:blue'>{LSE}ºC</span>", unsafe_allow_html=True)
    
    with st.container():
        st.write("") 
        temp_input = st.number_input("Temperatura Atual (ºC):", step=0.1, format="%.1f")
        
        if st.button("SALVAR LEITURA"):
            status = ""
            if LIE <= temp_input <= LSE:
                status = "OK"
                salvar_temp(st.session_state['usuario_nome'], st.session_state['usuario_cargo'], temp_input, status)
                st.markdown(f"""<div class="alert-box-green">✅ SUCESSO<br>Temperatura {temp_input}ºC registrada.</div>""", unsafe_allow_html=True)
                st.balloons()
            else:
                status = "ERRO"
                salvar_temp(st.session_state['usuario_nome'], st.session_state['usuario_cargo'], temp_input, status)
                st.markdown(f"""<div class="alert-box-red">🚨 ERRO: FORA DO LIMITE!<br>Temperatura: {temp_input}ºC<hr>⚠️ INFORMAR AO SUPERIOR</div>""", unsafe_allow_html=True)

def tela_nao_conformidade():
    st.markdown("## ⚠️ Registro de Não Conformidade")
    
    df_sku = carregar_sku()
    codigo_input = st.text_input("Código do SKU:")
    material_nome = ""
    
    if codigo_input and not df_sku.empty:
        try:
            col_cod = df_sku.columns[0]
            res = df_sku[df_sku[col_cod].astype(str).str.strip() == codigo_input.strip()]
            if not res.empty:
                material_nome = str(res.iloc[0].values[1])
            else:
                material_nome = "SKU não cadastrado no arquivo (mas pode prosseguir)"
        except: pass
    
    st.text_input("Descrição do Material:", value=material_nome, disabled=True)
    st.markdown("---")
    
    with st.form("form_nc"):
        st.markdown("### 📋 Check-list de Avaria")

        st.write("**Armazém da Avaria:**")
        arm_avaria = st.radio("Selecione:", ["Armazém A", "Armazém B", "Armazém C", "Armazém R", "Armazém M"], horizontal=True)

        st.write("**Localização da Avaria:**")
        local_avaria = st.radio("Selecione:", ["Topo", "Meio", "Base"], horizontal=True)
        st.divider()
        
        st.write("**Tipo(s) de Não Conformidade:**")
        c1, c2 = st.columns(2)
        chk_quebra = c1.checkbox("Quebra de Garrafa")
        chk_lata_am = c1.checkbox("Lata Amassada/Rasgada")
        chk_filme = c1.checkbox("Filme Rasgado")
        chk_sku = c1.checkbox("Falta de SKU")
        
        chk_emb = c2.checkbox("Embalagem Avariada")
        chk_pal_q = c2.checkbox("Palete Quebrado")
        chk_pal_d = c2.checkbox("Palete Desalinhado")
        chk_pal_d = c2.checkbox("Vazamento")
        
        st.divider()
        obs = st.text_area("Observações / Detalhes:")
        
        if st.form_submit_button("REGISTRAR NÃO CONFORMIDADE"):
            if codigo_input:
                dados = {
                    "Usuario": st.session_state['usuario_nome'],
                    "Cargo": st.session_state['usuario_cargo'],
                    "SKU": codigo_input,
                    "Descricao_SKU": material_nome,
                    "Local_Avaria": local_avaria,
                    "Quebra_Garrafa": "Sim" if chk_quebra else "Não",
                    "Lata_Amassada": "Sim" if chk_lata_am else "Não",
                    "Filme_Rasgado": "Sim" if chk_filme else "Não",
                    "Falta_SKU": "Sim" if chk_sku else "Não",
                    "Emb_Avariada": "Sim" if chk_emb else "Não",
                    "Palete_Quebrado": "Sim" if chk_pal_q else "Não",
                    "Palete_Desalinhado": "Sim" if chk_pal_d else "Não",
                    "Observacoes": obs
                }
                if salvar_nc(dados):
                    st.success("✅ Não Conformidade registrada com sucesso!")
                    st.balloons()
            else:
                st.warning("⚠️ Favor informar o Código do SKU.")

def tela_grafico_temp():
    st.markdown("## 📊 Controle de Temperatura (Semanal)")
    df = carregar_historico_temp()
    
    if df.empty:
        st.info("Nenhum dado registrado ainda.")
        return

    # Criar coluna Datetime
    df['Datetime'] = pd.to_datetime(df['Data'] + ' ' + df['Horario'], format='%d/%m/%Y %H:%M:%S')
    data_limite = datetime.now() - timedelta(days=7)
    
    # Filtrar últimos 7 dias
    df_semanal = df[df['Datetime'] >= data_limite]

    if df_semanal.empty:
        st.warning("Sem dados nesta semana.")
        return

    # Gráfico
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_semanal['Datetime'], y=df_semanal['Temperatura'], mode='lines+markers', name='Temperatura', line=dict(color='#0054a6', width=4), marker=dict(size=10, color='white', line=dict(width=2, color='#0054a6'))))
    fig.add_hline(y=LSE, line_dash="dash", line_color="red", annotation_text=f"Max {LSE}ºC")
    fig.add_hline(y=LIE, line_dash="dash", line_color="blue", annotation_text=f"Min {LIE}ºC")
    fig.update_layout(
        title="Variação Térmica", xaxis_title="Data/Hora", yaxis_title="ºC",
        template="plotly_white", height=450,
        font=dict(color="black")
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # --- CORREÇÃO DO ERRO AQUI ---
    with st.expander("Ver Histórico de Temperatura"):
        # 1. Primeiro ordena usando a coluna Datetime
        tabela_ordenada = df_semanal.sort_values(by='Datetime', ascending=False)
        
        # 2. Depois seleciona as colunas para exibir (sem Datetime, pois não queremos mostrar ela duplicada)
        st.dataframe(
            tabela_ordenada[['Data', 'Horario', 'Usuario', 'Temperatura', 'Status']], 
            use_container_width=True
        )

    with open(ARQUIVO_DADOS_TEMP, "rb") as file:
        st.download_button(label="📥 Baixar Dados Temp (Excel)", data=file, file_name="relatorio_temperatura.csv", mime="text/csv")

# --- NAVEGAÇÃO ---
if 'usuario_nome' not in st.session_state:
    tela_login()
else:
    st.sidebar.markdown(f"## 👤 {st.session_state['usuario_nome']}")
    st.sidebar.caption(f"{st.session_state['usuario_cargo']}")
    st.sidebar.markdown("---")
    
    menu = st.sidebar.radio("Navegação:", ["🌡️ Temperatura", "⚠️ Não Conformidade", "📊 Gráfico Temp"], index=0)
    
    if st.sidebar.button("Sair"):
        st.session_state.clear()
        st.rerun()

    if menu == "🌡️ Temperatura": tela_cadastro_temp()
    elif menu == "⚠️ Não Conformidade": tela_nao_conformidade()
    else: tela_grafico_temp()








