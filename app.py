import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import time

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
ARQUIVO_SKU = "sku (1).csv"

LIE = 2.0
LSE = 7.0

# --- ESTILO CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #131314; color: #f0f0f0 !important; }
    p, label, span, div, li, h1, h2, h3, h4, h5, h6 { color: #f0f0f0 !important; }
    h1, h2, h3 { color: #479bd8 !important; }
    .stTextInput > label, .stNumberInput > label, .stSelectbox > label, .stRadio > label, .stTextArea > label, .stFileUploader > label {
        color: #f0f0f0 !important; font-weight: bold;
    }
    .stTextInput input, .stNumberInput input, .stTextArea textarea {
        background-color: #ffffff !important; color: #000000 !important;
        border-radius: 10px; border: 1px solid #479bd8;
    }
    .stButton>button {
        background-color: #0054a6; color: white !important;
        border-radius: 20px; border: none; padding: 10px 24px;
        font-weight: bold; width: 100%; transition: 0.3s;
    }
    .stButton>button:hover { background-color: #479bd8; }
    .alert-box-red {
        background-color: #ffcccc; border: 2px solid #990000;
        border-radius: 15px; padding: 20px; text-align: center; margin-top: 15px;
    }
    .alert-box-red p, .alert-box-red div { color: #990000 !important; font-weight: bold; }
    .alert-box-green {
        background-color: #ccffcc; border: 2px solid #006600;
        border-radius: 15px; padding: 20px; text-align: center; margin-top: 15px;
    }
    .alert-box-green p, .alert-box-green div { color: #006600 !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE DADOS ---

def carregar_usuarios():
    if not os.path.exists(ARQUIVO_USUARIOS): return None
    try:
        df = pd.read_csv(ARQUIVO_USUARIOS, sep=';', encoding='latin1', dtype=str)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except: return None

def carregar_sku():
    if not os.path.exists(ARQUIVO_SKU): return None
    try:
        df = pd.read_csv(ARQUIVO_SKU, sep=';', encoding='latin1', dtype=str)
        # Tenta separador vírgula se ponto e vírgula falhar na estrutura
        if df.shape[1] < 2:
            df = pd.read_csv(ARQUIVO_SKU, sep=',', encoding='latin1', dtype=str)
        return df
    except: return pd.DataFrame()

def carregar_historico_temp():
    if not os.path.exists(ARQUIVO_DADOS_TEMP):
        return pd.DataFrame(columns=["Usuario", "Cargo", "Data", "Horario", "Temperatura", "Status"])
    try:
        return pd.read_csv(ARQUIVO_DADOS_TEMP, sep=";")
    except:
        return pd.read_csv(ARQUIVO_DADOS_TEMP, sep=";", on_bad_lines='skip', engine='python')

def carregar_historico_nc():
    if not os.path.exists(ARQUIVO_DADOS_NC):
        return pd.DataFrame()
    try:
        df = pd.read_csv(ARQUIVO_DADOS_NC, sep=";")
        return df
    except:
        # Fallback para arquivos corrompidos
        try:
            return pd.read_csv(ARQUIVO_DADOS_NC, sep=";", on_bad_lines='skip', engine='python')
        except:
            return pd.DataFrame()

def salvar_temp(usuario, cargo, temp, status):
    agora = datetime.now()
    nova_linha = pd.DataFrame([{
        "Usuario": usuario, "Cargo": cargo, "Data": agora.strftime("%d/%m/%Y"),
        "Horario": agora.strftime("%H:%M:%S"), "Temperatura": temp, "Status": status
    }])
    try: 
        nova_linha.to_csv(ARQUIVO_DADOS_TEMP, mode='a', header=not os.path.exists(ARQUIVO_DADOS_TEMP), index=False, sep=";")
    except PermissionError: st.error("Erro: Feche o arquivo Excel!")

# --- FUNÇÃO DE SALVAR CORRIGIDA (INTELIGENTE) ---
def salvar_nc(dados_dict):
    agora = datetime.now()
    dados_dict['Data'] = agora.strftime("%d/%m/%Y")
    dados_dict['Horario'] = agora.strftime("%H:%M:%S")
    
    # Transforma o novo dado em DataFrame
    df_novo = pd.DataFrame([dados_dict])
    
    try:
        if os.path.exists(ARQUIVO_DADOS_NC):
            # 1. Tenta ler o arquivo existente
            try:
                df_antigo = pd.read_csv(ARQUIVO_DADOS_NC, sep=";")
            except:
                df_antigo = pd.DataFrame() # Se der erro, considera vazio
            
            # 2. Concatena (Isso alinha as colunas automaticamente!)
            # Se 'Rua' não existia no antigo, o Pandas cria e preenche com NaN nas linhas velhas
            df_final = pd.concat([df_antigo, df_novo], ignore_index=True)
            
            # 3. Salva o arquivo completo por cima (overwrite)
            df_final.to_csv(ARQUIVO_DADOS_NC, index=False, sep=";")
        else:
            # Se não existe, cria novo
            df_novo.to_csv(ARQUIVO_DADOS_NC, index=False, sep=";")
            
        return True
    except PermissionError:
        st.error("Erro: Feche o arquivo de Não Conformidade (Excel)!")
        return False
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

# --- TELAS ---

def tela_login():
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>🧊 ColdSpec</h1>", unsafe_allow_html=True)
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
    st.markdown(f"**Faixa:** <span style='color:#479bd8'>{LIE}ºC</span> a <span style='color:#479bd8'>{LSE}ºC</span>", unsafe_allow_html=True)
    with st.container():
        st.write("") 
        temp_input = st.number_input("Temperatura Atual (ºC):", step=0.1, format="%.1f")
        if st.button("SALVAR LEITURA"):
            status = "OK" if LIE <= temp_input <= LSE else "ERRO"
            salvar_temp(st.session_state['usuario_nome'], st.session_state['usuario_cargo'], temp_input, status)
            if status == "OK":
                st.markdown(f"""<div class="alert-box-green"><p>✅ SUCESSO</p><p>{temp_input}ºC registrada.</p></div>""", unsafe_allow_html=True)
                st.balloons()
            else:
                st.markdown(f"""<div class="alert-box-red"><p>🚨 ERRO!</p><p>{temp_input}ºC</p></div>""", unsafe_allow_html=True)

def tela_nao_conformidade():
    st.markdown("## ⚠️ Gestão de Não Conformidade")
    
    tab1, tab2 = st.tabs(["📝 Cadastrar NC", "📊 Dashboard"])
    
    # --- ABA 1: CADASTRO ---
    with tab1:
        df_sku = carregar_sku()
        codigo_input = st.text_input("Código do SKU:")
        material_nome = ""
        
        if df_sku is not None and not df_sku.empty and codigo_input:
            try:
                col_cod = df_sku.columns[0]
                res = df_sku[df_sku[col_cod].astype(str).str.strip() == codigo_input.strip()]
                if not res.empty:
                    material_nome = str(res.iloc[0].values[1]) if len(res.columns) > 1 else "Encontrado"
                else: material_nome = "Não encontrado"
            except: material_nome = "Erro ao buscar"
        
        st.text_input("Descrição:", value=material_nome, disabled=True)
        st.markdown("---")
        
        with st.form("form_nc"):
            c_loc1, c_loc2 = st.columns(2)
            arm_avaria = c_loc1.selectbox("Armazém:", ["Armazém A", "Armazém B", "Armazém C", "Armazém R", "Armazém M"])
            rua_avaria = c_loc2.text_input("Rua / Corredor:", placeholder="Ex: 15B")

            st.write("**Posição:**")
            local_avaria = st.radio("Selecione:", ["Topo", "Meio", "Base"], horizontal=True)
            
            st.divider()
            st.write("**Avarias:**")
            c1, c2 = st.columns(2)
            chk_quebra = c1.checkbox("Quebra de Garrafa")
            chk_lata_am = c1.checkbox("Lata Amassada/Rasgada")
            chk_filme = c1.checkbox("Filme Rasgado")
            chk_sku = c1.checkbox("Falta de SKU")
            chk_emb = c2.checkbox("Embalagem Avariada")
            chk_pal_q = c2.checkbox("Palete Quebrado")
            chk_pal_d = c2.checkbox("Palete Desalinhado")
            chk_vazamento = c2.checkbox("Vazamento")
            
            st.divider()
            obs = st.text_area("Observações:")
            
            if st.form_submit_button("SALVAR REGISTRO"):
                if codigo_input:
                    dados = {
                        "Usuario": st.session_state['usuario_nome'], "Cargo": st.session_state['usuario_cargo'],
                        "SKU": codigo_input, "Descricao_SKU": material_nome, 
                        "Armazem": arm_avaria, "Rua": rua_avaria,
                        "Local_Avaria": local_avaria, "Observacoes": obs,
                        "Quebra_Garrafa": "Sim" if chk_quebra else "Não",
                        "Lata_Amassada": "Sim" if chk_lata_am else "Não",
                        "Filme_Rasgado": "Sim" if chk_filme else "Não",
                        "Falta_SKU": "Sim" if chk_sku else "Não",
                        "Emb_Avariada": "Sim" if chk_emb else "Não",
                        "Palete_Quebrado": "Sim" if chk_pal_q else "Não",
                        "Palete_Desalinhado": "Sim" if chk_pal_d else "Não",
                        "Vazamento": "Sim" if chk_vazamento else "Não"
                    }
                    if salvar_nc(dados):
                        st.success("✅ Salvo com sucesso!")
                        time.sleep(1)
                        st.rerun()
                else: st.warning("⚠️ Digite o SKU.")

    # --- ABA 2: DASHBOARD ---
    with tab2:
        df_nc = carregar_historico_nc()
        
        if df_nc.empty:
            st.info("Sem dados registrados.")
        else:
            # Botão Download
            csv_data = df_nc.to_csv(index=False, sep=";").encode('utf-8')
            st.download_button("📥 Baixar CSV", data=csv_data, file_name="avarias.csv", mime="text/csv")
            
            st.markdown("---")
            st.metric("Total de Ocorrências", len(df_nc))
            
            # --- LÓGICA DE GRÁFICOS (Com tratamento de string) ---
            colunas_avarias = ["Quebra_Garrafa", "Lata_Amassada", "Filme_Rasgado", "Falta_SKU", 
                               "Emb_Avariada", "Palete_Quebrado", "Palete_Desalinhado", "Vazamento"]
            
            contagem_avarias = {}
            for col in colunas_avarias:
                if col in df_nc.columns:
                    # TRATAMENTO DE STRING: Garante que espaços ou 'Sim ' não quebrem a conta
                    qtd = df_nc[df_nc[col].astype(str).str.strip() == 'Sim'].shape[0]
                    if qtd > 0:
                        contagem_avarias[col.replace('_', ' ')] = qtd
            
            if contagem_avarias:
                fig_donut = go.Figure(data=[go.Pie(labels=list(contagem_avarias.keys()), values=list(contagem_avarias.values()), hole=.4)])
                fig_donut.update_layout(title="Tipos de Avaria", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', font=dict(color="#f0f0f0"))
                st.plotly_chart(fig_donut, use_container_width=True)
            else:
                st.warning("Nenhuma avaria marcada como 'Sim' encontrada.")

            c1, c2 = st.columns(2)
            with c1:
                if 'Armazem' in df_nc.columns:
                    counts = df_nc['Armazem'].value_counts()
                    fig = go.Figure(go.Bar(x=counts.values, y=counts.index, orientation='h'))
                    fig.update_layout(title="Por Armazém", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', font=dict(color="#f0f0f0"))
                    st.plotly_chart(fig, use_container_width=True)
            
            with c2:
                if 'Local_Avaria' in df_nc.columns:
                    counts = df_nc['Local_Avaria'].value_counts()
                    fig = go.Figure(go.Bar(x=counts.index, y=counts.values))
                    fig.update_layout(title="Por Posição", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', font=dict(color="#f0f0f0"))
                    st.plotly_chart(fig, use_container_width=True)

def tela_grafico_temp():
    st.markdown("## 📊 Controle de Temperatura")
    st.info("Funcionalidade de gráfico de temperatura aqui.")
    # (Código do gráfico simplificado para focar na solução do problema principal)
    df = carregar_historico_temp()
    if not df.empty:
        df['Datetime'] = pd.to_datetime(df['Data'] + ' ' + df['Horario'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['Datetime'])
        if not df.empty:
            df = df.sort_values('Datetime')
            fig = go.Figure(go.Scatter(x=df['Datetime'], y=df['Temperatura'], mode='lines+markers'))
            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', font=dict(color="#f0f0f0"), title="Histórico")
            st.plotly_chart(fig, use_container_width=True)

# --- NAVEGAÇÃO ---
if 'usuario_nome' not in st.session_state:
    tela_login()
else:
    st.sidebar.title(st.session_state['usuario_nome'])
    menu = st.sidebar.radio("Menu", ["🌡️ Temperatura", "⚠️ Não Conformidade", "📊 Gráfico Temp"])
    if menu == "🌡️ Temperatura": tela_cadastro_temp()
    elif menu == "⚠️ Não Conformidade": tela_nao_conformidade()
    else: tela_grafico_temp()
