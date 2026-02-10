import streamlit as st
import pandas as pd
import plotly.express as px
import os
import datetime

# --- 1. CONFIGURACIÓN DEL SITIO ---
st.set_page_config(
    page_title="Antorcha 2026",
    layout="wide",
    page_icon="🔥",
    initial_sidebar_state="expanded"
)

# --- 2. ESTILOS CSS (CORREGIDO: TABLA SIN DESCUADRE) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        font-size: 14px;
    }

    /* Fondo */
    .stApp { background-color: #f3f4f6; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e5e7eb; }

    /* Espacios del contenedor principal */
    div.block-container {
        padding-top: 2rem !important;
        padding-bottom: 1rem !important;
        margin-top: 0rem !important;
    }
    
    /* Ocultar elementos innecesarios */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Flechita del menú visible y azul */
    [data-testid="stSidebarCollapsedControl"] {
        color: #2563eb !important;
        background-color: white;
        border-radius: 50%;
        border: 1px solid #e5e7eb;
    }

    /* Encabezado */
    h1 {
        color: #111827;
        font-weight: 700;
        font-size: 1.6rem !important;
        margin-bottom: 0.2rem;
        text-transform: uppercase;
        margin-top: 0px !important;
    }
    .subtitle {
        color: #6b7280;
        font-size: 0.9rem !important;
        margin-bottom: 1rem;
    }

    /* KPI Cards */
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 10px 15px;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        border-left: 4px solid #3b82f6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* CORRECCIÓN: Quitamos el padding extra a la tabla para que no se descuadre */
    .stDataFrame {
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        /* padding: 10px;  <-- ELIMINADO */
    }
    
    /* Gráficos con fondo blanco */
    .stPlotlyChart {
        background-color: white;
        border-radius: 8px;
        padding: 10px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. GESTIÓN DE DATOS ---
ARCHIVO_EXCEL = "PAGO DE ANTORCHA 2026.xlsx"

@st.cache_data
def load_data(filepath):
    try:
        # Intenta leer asumiendo el nombre exacto
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)
        
        df.columns = df.columns.str.strip()
        if 'Fecha de pago' in df.columns:
            df['Fecha de pago'] = pd.to_datetime(df['Fecha de pago'], errors='coerce').dt.date
        return df
    except Exception as e:
        return None

# --- 4. LÓGICA PRINCIPAL ---

if not os.path.exists(ARCHIVO_EXCEL):
    st.error(f"🚫 No encuentro el archivo: {ARCHIVO_EXCEL}. Asegúrate de subirlo a GitHub con ese nombre exacto.")
    st.stop()

df = load_data(ARCHIVO_EXCEL)

if df is not None:
    # --- SIDEBAR ---
    st.sidebar.markdown("### 🛠️ Panel de Control")
    
    min_d = df['Fecha de pago'].min() if 'Fecha de pago' in df.columns else datetime.date.today()
    max_d = df['Fecha de pago'].max() if 'Fecha de pago' in df.columns else datetime.date.today()
    
    date_range = st.sidebar.date_input("📅 Periodo:", (min_d, max_d))
    st.sidebar.markdown("---")
    
    lideres = ["Todos"] + sorted(df['Líder directo:'].astype(str).unique().tolist())
    tipos = ["Todos"] + sorted(df['Entrada'].astype(str).unique().tolist())
    
    f_lider = st.sidebar.selectbox("👤 Líder:", lideres)
    f_entrada = st.sidebar.selectbox("🎫 Entrada:", tipos)
    
    if st.sidebar.button("🔄 Actualizar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    # --- FILTROS ---
    df_v = df.copy()
    if isinstance(date_range, tuple) and len(date_range) == 2:
        df_v = df_v[(df_v['Fecha de pago'] >= date_range[0]) & (df_v['Fecha de pago'] <= date_range[1])]
    if f_lider != "Todos":
        df_v = df_v[df_v['Líder directo:'] == f_lider]
    if f_entrada != "Todos":
        df_v = df_v[df_v['Entrada'] == f_entrada]

    # --- DASHBOARD ---
    st.markdown('<h1>MINISTERIO DE MATRIMONIOS JÓVENES - <span style="color:#3b82f6">ANTORCHA 2026</span></h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Monitor ejecutivo de control de entradas.</p>', unsafe_allow_html=True)
    
    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Inscritos", len(df_v))
    c2.metric("Líderes", df_v['Líder directo:'].nunique())
    c3.metric("Top Entrada", df_v['Entrada'].mode()[0] if not df_v.empty else "-")
    pct = (len(df_v)/len(df)*100) if len(df) > 0 else 0
    c4.metric("Avance", f"{pct:.1f}%")

    st.markdown("---")

    # --- 1. TABLA (MEJORADA) ---
    st.subheader("📋 Detalle de Operaciones")
    
    # Mapeo de columnas
    cols_map = {'Nombres':'Nombre', 'Apellidos':'Apellido', 'Líder directo:':'Líder', 
                'Teléfono':'Celular', 'Entrada':'Tipo', 'Fecha de pago':'Fecha'}
    cols_ok = [c for c in cols_map.keys() if c in df_v.columns]
    
    if not df_v.empty:
        # Preparamos el dataframe
        df_display = df_v[cols_ok].rename(columns=cols_map)
        
        # Mostramos la tabla con configuración de columnas para evitar cortes
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            height=300,
            column_config={
                "Líder": st.column_config.TextColumn("Líder", width="medium"),
                "Tipo": st.column_config.TextColumn("Tipo", width="medium"),
                "Celular": st.column_config.TextColumn("Celular", width="small")
            }
        )
    else:
        st.warning("Sin datos para mostrar.")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 2. GRÁFICO ---
    if f_lider == "Todos" and not df_v.empty:
        st.subheader("📊 Ranking")
        conteo = df_v.groupby(['Líder directo:', 'Entrada']).size().reset_index(name='Total')
        total_lider = conteo.groupby('Líder directo:')['Total'].sum().sort_values(ascending=True)
        
        fig = px.bar(
            conteo, y='Líder directo:', x='Total', color='Entrada', text='Total', orientation='h', height=500,
            color_discrete_sequence=px.colors.qualitative.Prism,
            category_orders={'Líder directo:': total_lider.index}
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            xaxis_title="Inscritos", yaxis_title=None,
            font=dict(family="Inter", size=11, color="#374151"),
            margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig.update_traces(textfont_size=11, textposition='inside')
        st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Error cargando archivo.")
