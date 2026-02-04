import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import time
import shutil

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
PASTA_HISTORICO = "historico_uploads"

LIE = 2.0
LSE = 7.0

# --- ESTILO CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #131314; color: #f0f0f0 !important; }
    p, label, span, div, li, h1, h2, h3, h4, h5, h6 { color: #f0f0f0 !important; }
    h1, h2, h3 { color: #479bd8 !important; }
    .stTextInput > label, .stNumberInput > label, .stSelectbox > label, .stRadio > label, .stTextArea > label, .stFileUploader > label {
        color: #f0f0f0 !important; font-weight: bold; font-size: 1.1em;
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
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #1f1f1f; border-radius: 4px; color: #f0f0f0; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #479bd8 !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE ARQUIVO E DADOS ---

def gerenciar_pasta_historico():
    """Cria a pasta se não existir e remove arquivos com mais de 15 dias."""
    if not os.path.exists(PASTA_HISTORICO):
        os.makedirs(PASTA_HISTORICO)
    
    agora = time.time()
    limite_dias = 15 * 86400  # 15 dias em segundos

    for f in os.listdir(PASTA_HISTORICO):
        caminho_arquivo = os.path.join(PASTA_HISTORICO, f)
        if os.path.isfile(caminho_arquivo):
            # Se a data de modificação for mais antiga que o limite, apaga
            if os.stat(caminho_arquivo).st_mtime < (agora - limite_dias):
                os.remove(caminho_arquivo)

def salvar_arquivo_historico(uploaded_file):
    """Salva o arquivo enviado na pasta de histórico."""
    gerenciar_pasta_historico()
    caminho = os.path.join(PASTA_HISTORICO, uploaded_file.name)
    with open(caminho, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return caminho

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

def carregar_historico_nc(caminho_arquivo=None):
    """Carrega o histórico interno ou um arquivo específico se passado o caminho."""
    arquivo_alvo = caminho_arquivo if caminho_arquivo else ARQUIVO_DADOS_NC
    
    if not os.path.exists(arquivo_alvo):
        return pd.DataFrame()
    try:
        # Tenta ler com utf-8 primeiro
        df = pd.read_csv(arquivo_alvo, sep=";", encoding='utf-8')
        return df
    except:
        try:
            # Tenta latin1 se falhar
            return pd.read_csv(arquivo_alvo, sep=";", encoding='latin1', on_bad_lines='skip', engine='python')
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

def salvar_nc(dados_dict):
    agora = datetime.now()
    dados_dict['Data'] = agora.strftime("%d/%m/%Y")
    
    df_novo = pd.DataFrame([dados_dict])
    
    try:
        if os.path.exists(ARQUIVO_DADOS_NC):
            try:
                df_antigo = pd.read_csv(ARQUIVO_DADOS_NC, sep=";")
            except:
                df_antigo = pd.DataFrame()
            
            df_final = pd.concat([df_antigo, df_novo], ignore_index=True)
            df_final.to_csv(ARQUIVO_DADOS_NC, index=False, sep=";")
        else:
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
        st.info("Acesso Restrito 👩🏻‍💻")
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
    
    tab1, tab2 = st.tabs(["📝 Nova Leitura", "📊 Histórico Geral"])

    with tab1:
        st.markdown(f"**Faixa:** <span style='color:#479bd8'>{LIE}ºC</span> a <span style='color:#479bd8'>{LSE}ºC</span>", unsafe_allow_html=True)
        st.write("") 
        temp_input = st.number_input("🌡️ Temperatura Atual (ºC):", step=0.1, format="%.1f", key="temp_input_field")
        
        if st.button("SALVAR LEITURA"):
            status = "OK" if LIE <= temp_input <= LSE else "ERRO"
            salvar_temp(st.session_state['usuario_nome'], st.session_state['usuario_cargo'], temp_input, status)
            if status == "OK":
                st.markdown(f"""<div class="alert-box-green"><p>✅ SUCESSO</p><p>{temp_input}ºC registrada.</p></div>""", unsafe_allow_html=True)
                st.balloons()
                time.sleep(1)
                st.rerun()    
            else:
                st.markdown(f"""<div class="alert-box-red"><p>🚨 FORA DA FAIXA!</p><p>{temp_input}ºC</p></div>""", unsafe_allow_html=True)
                time.sleep(1)
                st.rerun()

    with tab2:
        df = carregar_historico_temp()
        
        if df.empty:
            st.info("Nenhum registro encontrado.")
        else:
            if 'Data' in df.columns and 'Horario' in df.columns:
                try:
                    df['Datetime'] = pd.to_datetime(df['Data'] + ' ' + df['Horario'], dayfirst=True, errors='coerce')
                    df = df.sort_values(by='Datetime', ascending=False).drop(columns=['Datetime'])
                except:
                    pass 

            csv_data = df.to_csv(index=False, sep=";").encode('utf-8')
            st.download_button("📥 Baixar Histórico Completo", data=csv_data, file_name="historico_temperatura.csv", mime="text/csv")
            
            st.markdown("---")
            
            col_met1, col_met2, col_met3 = st.columns(3)
            col_met1.metric("Total de Leituras", len(df))
            
            ultima_temp = df.iloc[0]['Temperatura'] if not df.empty else 0
            delta_temp = None
            if len(df) > 1:
                penultima = pd.to_numeric(df.iloc[1]['Temperatura'], errors='coerce')
                atual = pd.to_numeric(ultima_temp, errors='coerce')
                if not pd.isna(penultima) and not pd.isna(atual):
                    delta_temp = round(atual - penultima, 1)

            col_met2.metric("Última Temp.", f"{ultima_temp}ºC", delta=delta_temp)
            
            erros = df[df['Status'] == 'ERRO'].shape[0]
            col_met3.metric("Desvios (ERRO)", erros, delta_color="inverse")
            
            st.divider()
            st.write("📋 **Registros Recentes:**")
            st.dataframe(df, use_container_width=True, hide_index=True)


def tela_nao_conformidade():
    st.markdown("## 🚚 Gestão de Avarias (NC)")
    
    # Inicializa variáveis de sessão para controle do arquivo visualizado
    if 'nc_arquivo_atual' not in st.session_state:
        st.session_state['nc_arquivo_atual'] = "Dados Atuais (Registros do Dia/Interno)"
    if 'nc_caminho_arquivo' not in st.session_state:
        st.session_state['nc_caminho_arquivo'] = None

    # Lógica de limpar o form (no topo)
    if st.session_state.get('limpar_nc_sucesso'):
        st.session_state['nc_sku'] = ""
        st.session_state['nc_rua'] = ""
        st.session_state['nc_obs'] = ""
        st.session_state['nc_arm'] = "Armazém A"
        st.session_state['nc_loc'] = "Topo"
        for i in range(1, 9):
            st.session_state[f"nc_chk{i}"] = False
        st.session_state['limpar_nc_sucesso'] = False
        st.success("✅ Registro salvo e formulário limpo!")

    tab1, tab2, tab3 = st.tabs(["📦 Registrar NC", "📊 Dashboard", "🗂️ Histórico & Upload"])
    
    # --- ABA 1: CADASTRO ---
    with tab1:
        df_sku = carregar_sku()
        codigo_input = st.text_input("📦 Código do SKU:", key="nc_sku")
        material_nome = ""
        
        if df_sku is not None and not df_sku.empty and codigo_input:
            try:
                col_cod = df_sku.columns[0]
                res = df_sku[df_sku[col_cod].astype(str).str.strip() == codigo_input.strip()]
                if not res.empty:
                    material_nome = str(res.iloc[0].values[1]) if len(res.columns) > 1 else "Encontrado"
                else: material_nome = "Não encontrado"
            except: material_nome = "Erro ao buscar"
        
        st.text_input("Descrição do Item:", value=material_nome, disabled=True)
        st.markdown("---")
        
        with st.form("form_nc"):
            c_loc1, c_loc2 = st.columns(2)
            arm_avaria = c_loc1.selectbox("🚚 Armazém:", ["Armazém A", "Armazém B", "Armazém C", "Armazém R", "Armazém M"], key="nc_arm")
            rua_avaria = c_loc2.text_input("🗺️ Rua / Corredor:", placeholder="Ex: 15B", key="nc_rua")

            st.write("**📍 Posição no Rack:**")
            local_avaria = st.radio("Nível:", ["Topo", "Meio", "Base"], horizontal=True, key="nc_loc")
            
            st.divider()
            st.write("**⚠️ Tipo de Avaria:**")
            c1, c2 = st.columns(2)
            chk_quebra = c1.checkbox("Quebra de Garrafa", key="nc_chk1")
            chk_lata_am = c1.checkbox("Lata Amassada/Rasgada", key="nc_chk2")
            chk_filme = c1.checkbox("Filme Rasgado", key="nc_chk3")
            chk_sku = c1.checkbox("Falta de SKU", key="nc_chk4")
            chk_emb = c2.checkbox("Embalagem Avariada", key="nc_chk5")
            chk_pal_q = c2.checkbox("Palete Quebrado", key="nc_chk6")
            chk_pal_d = c2.checkbox("Palete Desalinhado", key="nc_chk7")
            chk_vazamento = c2.checkbox("Vazamento", key="nc_chk8")
            
            st.divider()
            obs = st.text_area("📝 Observações:", key="nc_obs")
            
            submitted = st.form_submit_button("💾 SALVAR REGISTRO")
            
            if submitted:
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
                        st.session_state['limpar_nc_sucesso'] = True
                        st.rerun()
                else: st.warning("⚠️ Digite o SKU.")

    # --- ABA 2: DASHBOARD ---
    with tab2:
        st.markdown(f"**Visualizando:** `{st.session_state['nc_arquivo_atual']}`")
        if st.button("🔄 Voltar para Dados Atuais (Ao Vivo)", key="btn_reset_dash"):
            st.session_state['nc_arquivo_atual'] = "Dados Atuais"
            st.session_state['nc_caminho_arquivo'] = None
            st.rerun()
        
        st.markdown("---")
        
        # Carrega dados baseados na seleção do histórico
        df_nc = carregar_historico_nc(st.session_state['nc_caminho_arquivo'])

        if df_nc.empty:
            st.info("Sem dados para exibir no arquivo selecionado.")
        else:
            # Opção de baixar o que está sendo visualizado
            csv_data = df_nc.to_csv(index=False, sep=";").encode('utf-8')
            st.download_button("📥 Baixar CSV Visualizado", data=csv_data, file_name="relatorio_nc.csv", mime="text/csv")
            
            st.metric("📦 Total de Ocorrências", len(df_nc))
            
            colunas_avarias = ["Quebra_Garrafa", "Lata_Amassada", "Filme_Rasgado", "Falta_SKU", 
                               "Emb_Avariada", "Palete_Quebrado", "Palete_Desalinhado", "Vazamento"]
            
            contagem_avarias = {}
            for col in colunas_avarias:
                if col in df_nc.columns:
                    # Conta "Sim", ignorando maiúsculas/minúsculas e espaços
                    qtd = df_nc[df_nc[col].astype(str).str.strip().str.lower() == 'sim'].shape[0]
                    if qtd > 0:
                        contagem_avarias[col.replace('_', ' ')] = qtd
            
            if contagem_avarias:
                fig_donut = go.Figure(data=[go.Pie(labels=list(contagem_avarias.keys()), values=list(contagem_avarias.values()), hole=.4)])
                fig_donut.update_layout(title="📊 Tipos de Avaria", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', font=dict(color="#f0f0f0"))
                st.plotly_chart(fig_donut, use_container_width=True)
            else:
                st.warning("Nenhuma avaria marcada como 'Sim' encontrada.")

            c1, c2 = st.columns(2)
            with c1:
                if 'Armazem' in df_nc.columns:
                    counts = df_nc['Armazem'].value_counts()
                    fig = go.Figure(go.Bar(x=counts.values, y=counts.index, orientation='h', marker=dict(color='#479bd8')))
                    fig.update_layout(title="🚚 Por Armazém", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', font=dict(color="#f0f0f0"))
                    st.plotly_chart(fig, use_container_width=True)
            
            with c2:
                if 'Local_Avaria' in df_nc.columns:
                    counts = df_nc['Local_Avaria'].value_counts()
                    fig = go.Figure(go.Bar(x=counts.index, y=counts.values, marker=dict(color=['#ff4444', '#44ff44', '#ffff44'])))
                    fig.update_layout(title="📍 Por Posição", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', font=dict(color="#f0f0f0"))
                    st.plotly_chart(fig, use_container_width=True)

            with st.expander("Ver Dados Brutos"):
                st.dataframe(df_nc, use_container_width=True)

    # --- ABA 3: HISTÓRICO E UPLOAD ---
    with tab3:
        st.markdown("### 📤 Upload de Arquivo CSV")
        st.markdown("Suba um arquivo de avarias (`.csv` separado por ponto-e-vírgula) para analisar no dashboard.")
        
        uploaded_nc = st.file_uploader("Selecionar Arquivo", type=['csv'], key="upload_nc_externo")
        
        if uploaded_nc is not None:
            caminho_salvo = salvar_arquivo_historico(uploaded_nc)
            st.success(f"Arquivo salvo em histórico: {uploaded_nc.name}")
            time.sleep(1)
            st.rerun()

        st.divider()
        st.markdown("### 🗂️ Arquivos Salvos (Últimos 15 dias)")
        
        gerenciar_pasta_historico() # Limpa antigos antes de listar
        arquivos = [f for f in os.listdir(PASTA_HISTORICO) if f.endswith('.csv')]
        
        if arquivos:
            # Ordenar por data de modificação (mais recente primeiro)
            arquivos.sort(key=lambda x: os.path.getmtime(os.path.join(PASTA_HISTORICO, x)), reverse=True)
            
            for arq in arquivos:
                col_f1, col_f2 = st.columns([3, 1])
                col_f1.text(f"📄 {arq}")
                if col_f2.button("VISUALIZAR", key=f"btn_view_{arq}"):
                    st.session_state['nc_arquivo_atual'] = arq
                    st.session_state['nc_caminho_arquivo'] = os.path.join(PASTA_HISTORICO, arq)
                    # Muda para a aba de dashboard (hack visual ou apenas aviso)
                    st.success(f"Carregado! Vá para a aba 'Dashboard' para ver os gráficos de: {arq}")
        else:
            st.info("Nenhum arquivo no histórico recente.")


def tela_grafico_temp():
    st.markdown("## 📊 Análise Gráfica")
    st.markdown("---")

    uploaded_file = st.file_uploader("📂 Carregar CSV externo (Para gerar gráfico)", type=["csv"])
    
    df_final = pd.DataFrame()
    origem_dados = "interno"

    if uploaded_file is not None:
        try:
            try:
                df_upload = pd.read_csv(uploaded_file, sep=";")
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                df_upload = pd.read_csv(uploaded_file, sep=";", encoding="latin1")
            
            col_data_csv = "Hora de conclusão"
            col_temp_csv = "Temperatura da Câmara Fria:"

            if col_data_csv in df_upload.columns and col_temp_csv in df_upload.columns:
                df_upload['Temperatura'] = df_upload[col_temp_csv].astype(str).str.replace(',', '.')
                df_upload['Temperatura'] = pd.to_numeric(df_upload['Temperatura'], errors='coerce')
                df_upload['Datetime'] = pd.to_datetime(df_upload[col_data_csv], dayfirst=True, errors='coerce')
                df_final = df_upload.dropna(subset=['Temperatura', 'Datetime'])
                origem_dados = "upload"
                if df_final.empty:
                    st.warning("Arquivo lido, mas sem dados válidos.")
            else:
                st.error(f"Erro: O CSV precisa ter as colunas: '{col_data_csv}' e '{col_temp_csv}'")
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {e}")

    else:
        df = carregar_historico_temp()
        if not df.empty:
            df['Datetime'] = pd.to_datetime(df['Data'] + ' ' + df['Horario'], dayfirst=True, errors='coerce')
            df_final = df.dropna(subset=['Datetime'])

    if df_final.empty:
        st.info("Aguardando dados para gerar o gráfico.")
        return

    if origem_dados == "interno":
        data_limite = datetime.now() - timedelta(days=7)
        df_plot = df_final[df_final['Datetime'] >= data_limite]
    else:
        df_plot = df_final

    if df_plot.empty:
        st.warning("Sem dados recentes.")
        return

    df_plot = df_plot.sort_values(by='Datetime')

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_plot['Datetime'], y=df_plot['Temperatura'], 
        mode='lines+markers', name='Temperatura', 
        line=dict(color='#479bd8', width=4), 
        marker=dict(size=8, color='white', line=dict(width=2, color='#479bd8'))
    ))
    
    fig.add_hline(y=LSE, line_dash="dash", line_color="#ff4444", annotation_text=f"Max {LSE}ºC")
    fig.add_hline(y=LIE, line_dash="dash", line_color="#44ff44", annotation_text=f"Min {LIE}ºC")
    
    fig.update_layout(
        title=f"Variação Térmica ({'Arquivo Externo' if origem_dados == 'upload' else 'Registros Manuais'})", 
        xaxis_title="Data/Hora", yaxis_title="ºC",
        template="plotly_dark", height=450,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#f0f0f0")
    )
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("Ver Dados Detalhados"):
        if origem_dados == "upload":
            cols_exibir = ['Datetime', 'Temperatura da Câmara Fria:', 'Nome', 'Conferente coletor:']
            cols_finais = [c for c in cols_exibir if c in df_plot.columns]
            st.dataframe(df_plot[cols_finais], use_container_width=True)
        else:
            st.dataframe(df_plot[['Data', 'Horario', 'Usuario', 'Temperatura', 'Status']], use_container_width=True)

    if origem_dados == "interno":
        with open(ARQUIVO_DADOS_TEMP, "rb") as file:
            st.download_button(label="📥 Baixar Histórico (Excel)", data=file, file_name="relatorio_temperatura.csv", mime="text/csv")

# --- NAVEGAÇÃO ---
if 'usuario_nome' not in st.session_state:
    tela_login()
else:
    st.sidebar.title(f"👩🏻‍💻 {st.session_state['usuario_nome']}")
    menu = st.sidebar.radio("Menu", ["🌡️ Temperatura", "🚚 Não Conformidade", "📊 Análise Gráfica"])
    
    if menu == "🌡️ Temperatura": tela_cadastro_temp()
    elif menu == "🚚 Não Conformidade": tela_nao_conformidade()
    else: tela_grafico_temp()
