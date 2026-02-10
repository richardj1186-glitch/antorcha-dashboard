import streamlit as st
import pandas as pd
import plotly.express as px
import os
import datetime

# --- 1. CONFIGURACIÓN DEL SITIO ---
st.set_page_config(
    page_title="Monitor Antorcha",
    layout="wide",
    page_icon="🔥",
    initial_sidebar_state="expanded"
)

# --- 2. ESTILOS CSS (Limpios y Ordenados) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        color: #1f2937;
    }
    .stApp { background-color: #f8fafc; }
    
    /* Ajuste de espacios */
    div.block-container { padding-top: 2rem !important; padding-bottom: 3rem !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Flecha menú */
    [data-testid="stSidebarCollapsedControl"] {
        color: #2563eb !important;
        background-color: white;
        border: 1px solid #e2e8f0;
        border-radius: 50%;
    }

    /* Títulos */
    h1 { color: #1e3a8a; font-weight: 800; font-size: 1.8rem !important; text-transform: uppercase; margin-bottom: 0.5rem; }
    .subtitle { color: #64748b; font-size: 1rem !important; margin-bottom: 1.5rem; }

    /* KPI Cards */
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 15px 20px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    div[data-testid="stMetricLabel"] { font-size: 0.85rem !important; color: #64748b; font-weight: 600; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #1e3a8a; font-weight: 700; }

    /* Tablas y Gráficos */
    .stDataFrame, .stPlotlyChart {
        background-color: white;
        border-radius: 12px;
        padding: 15px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CARGA DE DATOS ---
ARCHIVO_EXCEL = "PAGO DE ANTORCHA 2026.xlsx"

@st.cache_data
def load_data(filepath):
    try:
        # Soporte para CSV o Excel
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)
        
        df.columns = df.columns.str.strip()
        # Convertir fecha
        if 'Fecha de pago' in df.columns:
            df['Fecha de pago'] = pd.to_datetime(df['Fecha de pago'], errors='coerce').dt.date
        
        # --- LIMPIEZA DE DATOS AUTOMÁTICA ---
        # Creamos una columna "Categoria" que limpia el texto largo
        # Ejemplo: "General (Precio Oferta...)" -> "General"
        if 'Entrada' in df.columns:
            df['Categoria'] = df['Entrada'].apply(lambda x: str(x).split('(')[0].strip())
            
        return df
    except Exception as e:
        return None

# --- 4. LÓGICA DE NEGOCIO ---

if not os.path.exists(ARCHIVO_EXCEL):
    st.error(f"🚫 Archivo no encontrado: {ARCHIVO_EXCEL}")
    st.stop()

df = load_data(ARCHIVO_EXCEL)

if df is not None:
    # --- SIDEBAR ---
    st.sidebar.markdown("### 🎯 Filtros")
    
    min_d = df['Fecha de pago'].min() if 'Fecha de pago' in df.columns else datetime.date.today()
    max_d = df['Fecha de pago'].max() if 'Fecha de pago' in df.columns else datetime.date.today()
    
    date_range = st.sidebar.date_input("📅 Fechas:", (min_d, max_d))
    st.sidebar.divider()
    
    lideres = ["Todos"] + sorted(df['Líder directo:'].astype(str).unique().tolist())
    # Usamos la categoría limpia para el filtro también, es más amigable
    tipos = ["Todos"] + sorted(df['Categoria'].astype(str).unique().tolist())
    
    f_lider = st.sidebar.selectbox("👤 Líder:", lideres)
    f_entrada = st.sidebar.selectbox("🎫 Tipo Entrada:", tipos)
    
    if st.sidebar.button("🔄 Refrescar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    # --- FILTRADO ---
    df_v = df.copy()
    if isinstance(date_range, tuple) and len(date_range) == 2:
        df_v = df_v[(df_v['Fecha de pago'] >= date_range[0]) & (df_v['Fecha de pago'] <= date_range[1])]
    if f_lider != "Todos":
        df_v = df_v[df_v['Líder directo:'] == f_lider]
    if f_entrada != "Todos":
        df_v = df_v[df_v['Categoria'] == f_entrada] # Filtramos por la categoría limpia

    # --- HEADER ---
    st.markdown('<h1>Monitor <span style="color:#2563eb">Antorcha 2026</span></h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="subtitle">Actualizado al: {datetime.datetime.now().strftime("%d/%m %H:%M")}</p>', unsafe_allow_html=True)

    # --- KPIS ---
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Inscritos", len(df_v), delta="Personas")
    k2.metric("Líderes Activos", df_v['Líder directo:'].nunique())
    
    # Lógica KPI Mejorada: Usa la columna limpia 'Categoria'
    if not df_v.empty:
        top_cat = df_v['Categoria'].mode()[0]
        cant_top = len(df_v[df_v['Categoria'] == top_cat])
        k3.metric("Entrada Top", top_cat, delta=f"{cant_top} vendidas")
    else:
        k3.metric("Entrada Top", "-")
    
    pct = (len(df_v)/len(df)*100) if len(df) > 0 else 0
    k4.metric("Meta Global", f"{pct:.1f}%")

    st.divider()

    # --- GRÁFICO ORDENADO ---
    if not df_v.empty:
        st.subheader("📊 Rendimiento por Líder")
        
        if f_lider == "Todos":
            # Agrupamos por Líder y Categoria (el nombre corto)
            conteo = df_v.groupby(['Líder directo:', 'Categoria']).size().reset_index(name='Total')
            
            # Acortar nombres de líderes (eje Y)
            conteo['Líder Corto'] = conteo['Líder directo:'].apply(lambda x: x[:25] + '...' if len(str(x)) > 25 else x)
            
            # Ordenar ranking
            ranking = conteo.groupby('Líder Corto')['Total'].sum().sort_values(ascending=True)
            
            fig = px.bar(
                conteo, 
                y='Líder Corto', 
                x='Total', 
                color='Categoria', # <--- AQUÍ ESTÁ EL TRUCO: Usamos la categoría limpia
                text='Total', 
                orientation='h',
                height=500,
                # Tooltip muestra el nombre real completo
                hover_data={'Líder directo:': True, 'Líder Corto': False},
                category_orders={'Líder Corto': ranking.index},
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', 
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis_title=None, 
                yaxis_title=None,
                font=dict(family="Inter", size=12, color="#374151"),
                margin=dict(l=10, r=10, t=30, b=0),
                # Leyenda limpia arriba
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=None),
                bargap=0.25
            )
            fig.update_traces(textposition='auto', textfont_size=12)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"Mostrando detalle para: {f_lider}")

        st.markdown("<br>", unsafe_allow_html=True)

        # --- TABLA DETALLADA ---
        st.subheader("📋 Base de Datos")
        
        # Columnas a mostrar
        cols_map = {'Nombres':'Nombre', 'Apellidos':'Apellido', 'Líder directo:':'Líder', 
                    'Teléfono':'Celular', 'Entrada':'Detalle Entrada', 'Fecha de pago':'Fecha'}
        cols_ok = [c for c in cols_map.keys() if c in df_v.columns]
        
        df_display = df_v[cols_ok].rename(columns=cols_map)
        
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            height=400,
            column_config={
                "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
                "Celular": st.column_config.TextColumn("WhatsApp"),
            }
        )
else:
    st.warning("Cargando datos...")

