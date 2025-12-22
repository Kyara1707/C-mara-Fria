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

LIE = 2.0  # Limite Inferior Temperatura
LSE = 7.0  # Limite Superior Temperatura

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
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #1f1f1f; border-radius: 4px; color: #f0f0f0; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #479bd8 !important; color: white !important; }
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
        return pd.read_csv(ARQUIVO_DADOS_NC, sep=";")
    except:
        # Se der erro, tenta ler ignorando linhas ruins
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
        # Modo 'a' (append) funciona bem aqui pois a estrutura é fixa
        nova_linha.to_csv(ARQUIVO_DADOS_TEMP, mode='a', header=not os.path.exists(ARQUIVO_DADOS_TEMP), index=False, sep=";")
    except PermissionError: st.error("Erro: Feche o arquivo Excel!")

def salvar_nc(dados_dict):
    agora = datetime.now()
    dados_dict['Data'] = agora.strftime("%d/%m/%Y")
    dados_dict['Horario'] = agora.strftime("%H:%M:%S")
    
    df_novo = pd.DataFrame([dados_dict])
    
    # --- CORREÇÃO DE SALVAMENTO PARA EVITAR ERRO DE COLUNAS ---
    try:
        if os.path.exists(ARQUIVO_DADOS_NC):
            # Lê o arquivo antigo
            try:
                df_antigo = pd.read_csv(ARQUIVO_DADOS_NC, sep=";")
            except:
                df_antigo = pd.DataFrame() # Se estiver corrompido, cria novo
            
            # Junta o antigo com o novo (o Pandas ajusta as colunas automaticamente)
            df_final = pd.concat([df_antigo, df_novo], ignore_index=True)
            df_final.to_csv(ARQUIVO_DADOS_NC, index=False, sep=";")
        else:
            # Se não existe, cria novo
            df_novo.to_csv(ARQUIVO_DADOS_NC, index=False, sep=";")
            
        return True
    except PermissionError:
        st.error("Erro: Feche o arquivo de Não Conformidade!")
        return False
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

# --- TELAS ---

def tela_login():
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>🧊 ColdSpec</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Monitoramento & Qualidade</p>", unsafe_allow_html=True)
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
    st.markdown(f"**Faixa Permitida:** <span style='color:#479bd8'>{LIE}ºC</span> a <span style='color:#479bd8'>{LSE}ºC</span>", unsafe_allow_html=True)
    with st.container():
        st.write("") 
        temp_input = st.number_input("Temperatura Atual (ºC):", step=0.1, format="%.1f")
        if st.button("SALVAR LEITURA"):
            status = "OK" if LIE <= temp_input <= LSE else "ERRO"
            salvar_temp(st.session_state['usuario_nome'], st.session_state['usuario_cargo'], temp_input, status)
            if status == "OK":
                st.markdown(f"""<div class="alert-box-green"><p>✅ SUCESSO</p><p>Temperatura {temp_input}ºC registrada.</p></div>""", unsafe_allow_html=True)
                st.balloons()
            else:
                st.markdown(f"""<div class="alert-box-red"><p>🚨 ERRO: FORA DO LIMITE!</p><p>Temperatura: {temp_input}ºC</p><hr><p>⚠️ INFORMAR AO SUPERIOR</p></div>""", unsafe_allow_html=True)

def tela_nao_conformidade():
    st.markdown("## ⚠️ Gestão de Não Conformidade")
    
    tab1, tab2 = st.tabs(["📝 Cadastrar NC", "📊 Dashboard & Relatórios"])
    
    # --- ABA 1: CADASTRO ---
    with tab1:
        df_sku = carregar_sku()
        codigo_input = st.text_input("Código do SKU:")
        material_nome = ""
        aviso_sku = ""
        
        if df_sku is None: aviso_sku = "⚠️ Arquivo 'sku.csv' não encontrado."
        elif df_sku.empty: aviso_sku = "⚠️ Arquivo 'sku.csv' vazio."
        elif codigo_input:
            try:
                col_cod = df_sku.columns[0]
                res = df_sku[df_sku[col_cod].astype(str).str.strip() == codigo_input.strip()]
                if not res.empty:
                    material_nome = str(res.iloc[0].values[1]) if len(res.columns) > 1 else "Descrição não encontrada"
                else: material_nome = "SKU não cadastrado"
            except Exception as e: aviso_sku = f"Erro ao ler SKU: {e}"
        
        st.text_input("Descrição do Material:", value=material_nome, disabled=True)
        if aviso_sku: st.caption(aviso_sku)
        st.markdown("---")
        
        with st.form("form_nc"):
            st.markdown("### 📋 Localização & Detalhes")
            
            col_loc1, col_loc2 = st.columns(2)
            with col_loc1:
                arm_avaria = st.selectbox("Armazém:", ["Armazém A", "Armazém B", "Armazém C", "Armazém R", "Armazém M"])
            with col_loc2:
                rua_avaria = st.text_input("Rua / Corredor:", placeholder="Ex: 15B")

            st.write("**Posição no Rack:**")
            local_avaria = st.radio("Selecione:", ["Topo", "Meio", "Base"], horizontal=True)
            
            st.divider()
            st.write("**Tipo(s) de Avaria:**")
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
            obs = st.text_area("Observações / Detalhes:")
            
            if st.form_submit_button("REGISTRAR NÃO CONFORMIDADE"):
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
                        st.success("✅ Registrado com sucesso!")
                        time.sleep(1) # Aguarda 1s para o usuário ver a mensagem
                        st.rerun() # FORÇA A ATUALIZAÇÃO DA PÁGINA
                else: st.warning("⚠️ Informe o Código do SKU.")

    # --- ABA 2: DASHBOARD ---
    with tab2:
        df_nc = carregar_historico_nc()
        
        if df_nc.empty:
            st.info("Nenhuma Não Conformidade registrada ainda.")
        else:
            with open(ARQUIVO_DADOS_NC, "rb") as file:
                st.download_button(
                    label="📥 Baixar CSV de Avarias",
                    data=file,
                    file_name="relatorio_avarias.csv",
                    mime="text/csv"
                )
            
            st.markdown("---")
            total_avarias = len(df_nc)
            st.metric("Total de Ocorrências", total_avarias)
            
            colunas_avarias = ["Quebra_Garrafa", "Lata_Amassada", "Filme_Rasgado", "Falta_SKU", 
                               "Emb_Avariada", "Palete_Quebrado", "Palete_Desalinhado", "Vazamento"]
            
            cols_existentes = [c for c in colunas_avarias if c in df_nc.columns]
            
            contagem_avarias = {}
            for col in cols_existentes:
                # Converte para string e limpa espaços para garantir contagem correta
                qtd = df_nc[df_nc[col].astype(str).str.strip() == 'Sim'].shape[0]
                if qtd > 0:
                    contagem_avarias[col.replace('_', ' ')] = qtd
            
            if contagem_avarias:
                labels = list(contagem_avarias.keys())
                values = list(contagem_avarias.values())

                fig_donut = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4)])
                fig_donut.update_layout(
                    title="Distribuição por Tipo de Avaria",
                    template="plotly_dark",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="#f0f0f0")
                )
                st.plotly_chart(fig_donut, use_container_width=True)
            else:
                st.warning("Não há avarias do tipo marcado 'Sim' nos registros.")

            c_graf1, c_graf2 = st.columns(2)
            
            with c_graf1:
                if 'Armazem' in df_nc.columns:
                    counts_arm = df_nc['Armazem'].value_counts()
                    fig_bar = go.Figure(go.Bar(
                        x=counts_arm.values, y=counts_arm.index, orientation='h',
                        marker=dict(color='#479bd8')
                    ))
                    fig_bar.update_layout(
                        title="Ocorrências por Armazém", template="plotly_dark",
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color="#f0f0f0")
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)

            with c_graf2:
                if 'Local_Avaria' in df_nc.columns:
                    counts_loc = df_nc['Local_Avaria'].value_counts()
                    fig_loc = go.Figure(go.Bar(
                        x=counts_loc.index, y=counts_loc.values,
                        marker=dict(color=['#ff4444', '#44ff44', '#ffff44'])
                    ))
                    fig_loc.update_layout(
                        title="Ocorrências por Posição", template="plotly_dark",
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color="#f0f0f0")
                    )
                    st.plotly_chart(fig_loc, use_container_width=True)

def tela_grafico_temp():
    st.markdown("## 📊 Controle de Temperatura")
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
                    st.warning("Arquivo lido, mas sem dados válidos (verifique formatos).")
            else:
                st.error(f"Erro: O CSV precisa ter as colunas: '{col_data_csv}' e '{col_temp_csv}'")
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {e}")

    else:
        df = carregar_historico_temp()
        if not df.empty:
            df['Datetime'] = pd.to_datetime(df['Data'] + ' ' + df['Horario'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
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

