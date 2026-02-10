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

# --- 2. ESTILOS CSS PROFESIONALES ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        color: #1f2937;
    }

    /* Fondo general */
    .stApp { background-color: #f8fafc; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { 
        background-color: #ffffff; 
        border-right: 1px solid #e2e8f0; 
    }

    /* Espaciado superior */
    div.block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* Ocultar elementos default */
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
    h1 {
        color: #1e3a8a; /* Azul oscuro */
        font-weight: 800;
        font-size: 1.8rem !important;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        color: #64748b;
        font-size: 1rem !important;
        margin-bottom: 1.5rem;
    }

    /* Tarjetas KPI */
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 15px 20px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    div[data-testid="stMetricLabel"] { 
        font-size: 0.85rem !important; 
        color: #64748b;
        font-weight: 600;
    }
    div[data-testid="stMetricValue"] { 
        font-size: 1.8rem !important; 
        color: #1e3a8a;
        font-weight: 700;
    }

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

# --- 4. LÓGICA DE NEGOCIO ---

if not os.path.exists(ARCHIVO_EXCEL):
    st.error(f"🚫 No se encuentra el archivo: {ARCHIVO_EXCEL}")
    st.stop()

df = load_data(ARCHIVO_EXCEL)

if df is not None:
    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.markdown("### 🎯 Filtros de Control")
    
    min_d = df['Fecha de pago'].min() if 'Fecha de pago' in df.columns else datetime.date.today()
    max_d = df['Fecha de pago'].max() if 'Fecha de pago' in df.columns else datetime.date.today()
    
    date_range = st.sidebar.date_input("📅 Rango de Fechas:", (min_d, max_d))
    st.sidebar.divider()
    
    lideres = ["Todos"] + sorted(df['Líder directo:'].astype(str).unique().tolist())
    tipos = ["Todos"] + sorted(df['Entrada'].astype(str).unique().tolist())
    
    f_lider = st.sidebar.selectbox("👤 Filtrar por Líder:", lideres)
    f_entrada = st.sidebar.selectbox("🎫 Filtrar por Entrada:", tipos)
    
    if st.sidebar.button("🔄 Refrescar Datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    # --- FILTRADO ---
    df_v = df.copy()
    if isinstance(date_range, tuple) and len(date_range) == 2:
        df_v = df_v[(df_v['Fecha de pago'] >= date_range[0]) & (df_v['Fecha de pago'] <= date_range[1])]
    if f_lider != "Todos":
        df_v = df_v[df_v['Líder directo:'] == f_lider]
    if f_entrada != "Todos":
        df_v = df_v[df_v['Entrada'] == f_entrada]

    # --- HEADER ---
    st.markdown('<h1>Monitor <span style="color:#2563eb">Antorcha 2026</span></h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="subtitle">Última actualización: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M")}</p>', unsafe_allow_html=True)

    # --- KPIS ---
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Inscritos", len(df_v), delta="Personas")
    k2.metric("Líderes Activos", df_v['Líder directo:'].nunique())
    
    top_entrada = df_v['Entrada'].mode()[0] if not df_v.empty else "-"
    # Acortamos el nombre de la entrada si es muy largo para el KPI
    k3.metric("Entrada Más Vendida", top_entrada[:15] + "..." if len(top_entrada) > 15 else top_entrada)
    
    pct = (len(df_v)/len(df)*100) if len(df) > 0 else 0
    k4.metric("Porcentaje del Total", f"{pct:.1f}%")

    st.divider()

    # --- SECCIÓN 1: GRÁFICO MEJORADO ---
    if not df_v.empty:
        c_chart, c_table = st.columns([1, 1]) # Dividimos pantalla si quieres, o uno abajo de otro. Aquí lo dejo uno abajo de otro mejor.

        st.subheader("📊 Rendimiento por Líder")
        
        if f_lider == "Todos":
            # 1. Agrupar datos
            conteo = df_v.groupby(['Líder directo:', 'Entrada']).size().reset_index(name='Total')
            
            # 2. Crear columna de Nombres Cortos para el eje Y (Truco para que no se vea feo)
            conteo['Líder Corto'] = conteo['Líder directo:'].apply(lambda x: x[:25] + '...' if len(str(x)) > 25 else x)
            
            # 3. Ordenar para que el mejor salga arriba
            total_por_lider = conteo.groupby('Líder Corto')['Total'].sum().sort_values(ascending=True)
            
            # 4. Gráfico con paleta profesional
            fig = px.bar(
                conteo, 
                y='Líder Corto', 
                x='Total', 
                color='Entrada', 
                text='Total', 
                orientation='h',
                height=500,
                # Usamos los nombres reales en el tooltip al pasar el mouse
                hover_data={'Líder directo:': True, 'Líder Corto': False},
                category_orders={'Líder Corto': total_por_lider.index},
                color_discrete_sequence=px.colors.qualitative.Pastel # Colores más suaves y profesionales
            )
            
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', 
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis_title="Cantidad de Inscritos", 
                yaxis_title=None,
                font=dict(family="Inter", size=12, color="#374151"),
                margin=dict(l=10, r=10, t=30, b=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=None),
                bargap=0.3 # Barras un poco más delgadas y elegantes
            )
            fig.update_traces(textposition='auto', textfont_size=12)
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"Viendo datos específicos de: {f_lider}")

        st.markdown("<br>", unsafe_allow_html=True)

        # --- SECCIÓN 2: TABLA DETALLADA ---
        st.subheader("📋 Base de Datos Filtrada")
        
        cols_map = {'Nombres':'Nombre', 'Apellidos':'Apellido', 'Líder directo:':'Líder', 
                    'Teléfono':'Celular', 'Entrada':'Tipo', 'Fecha de pago':'Fecha'}
        cols_ok = [c for c in cols_map.keys() if c in df_v.columns]
        
        df_display = df_v[cols_ok].rename(columns=cols_map)
        
        # Tabla interactiva
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
    st.warning("Esperando datos...")
