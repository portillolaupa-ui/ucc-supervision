# ==============================================================
# MONITOREO A LAS ACCIONES DE ACOMPAÑAMIENTO AL HOGAR
# CON GESTIÓN TERRITORIAL – ANEXO 2 (versión final optimizada)
# ==============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import yaml
from utils.loaders import cargar_datos
from utils.style import aplicar_estilos

# ==============================================================
# CONFIGURACIÓN DE PÁGINA
# ==============================================================

st.set_page_config(
    page_title="Anexo 2 – Acompañamiento al Hogar",
    page_icon="📋",
    layout="wide"
)
aplicar_estilos()

# ==============================================================
# CABECERA
# ==============================================================

st.title("Acompañamiento al Hogar con Gestión Territorial")
st.markdown("<br>", unsafe_allow_html=True)

# ==============================================================
# CARGA DE DATOS
# ==============================================================

data = cargar_datos()
df = data.get("a2")

if df is None:
    st.warning("⚠️ No se encontró el archivo `anexo2_consolidado.xlsx` en `/data/processed/`.")
    st.stop()

# ==============================================================
# CARGAR YAML DE NOMBRES DE ÍTEMS
# ==============================================================

BASE_DIR = Path(__file__).resolve().parents[2]
YAML_PATH = BASE_DIR / "config" / "settings_anexo2.yaml"

try:
    with open(YAML_PATH, "r", encoding="utf-8") as f:
        config_a2 = yaml.safe_load(f)
        mapa_items = config_a2.get("items_nombres", {})
except Exception as e:
    st.error(f"❌ Error al leer {YAML_PATH.name}: {e}")
    mapa_items = {}

# ==============================================================
# FILTROS
# ==============================================================

col1, col2, col3 = st.columns(3)
with col1:
    ut_sel = st.multiselect("Unidad Territorial:", sorted(df["UNIDAD_TERRITORIAL"].dropna().unique()))
with col2:
    mes_sel = st.multiselect("Mes:", sorted(df["MES"].dropna().unique()))
with col3:
    sup_sel = st.multiselect("Supervisor:", sorted(df["SUPERVISOR"].dropna().unique()))

df_filtrado = df.copy()
if ut_sel:
    df_filtrado = df_filtrado[df_filtrado["UNIDAD_TERRITORIAL"].isin(ut_sel)]
if mes_sel:
    df_filtrado = df_filtrado[df_filtrado["MES"].isin(mes_sel)]
if sup_sel:
    df_filtrado = df_filtrado[df_filtrado["SUPERVISOR"].isin(sup_sel)]

if df_filtrado.empty:
    st.warning("⚠️ No hay registros que coincidan con los filtros seleccionados.")
    st.stop()

# ==============================================================
# 🔹 NUEVA SECCIÓN: TARJETAS DE ÍTEMS 'NO CUMPLE' (valor 0)
# ==============================================================

st.markdown("### 🔴 Actividades que requieren fortalecimiento")
cols_items = [f"ITEM_{i}" for i in range(1, 21)]

# Calcular frecuencia y porcentaje de 'no cumple'
freq_0 = (df_filtrado[cols_items] == 0).sum()
pct_0 = (freq_0 / df_filtrado[cols_items].notna().sum() * 100).round(1)
no_cumple = pct_0[pct_0 > 0].sort_values(ascending=False)

if no_cumple.empty:
    st.info("✅ No se registran ítems con valor 'No cumple' en la selección actual.")
else:
    n = len(no_cumple)
    cols_per_row = 3
    items = list(no_cumple.index)

    for i in range(0, n, cols_per_row):
        row = st.columns(cols_per_row)
        for j, item in enumerate(items[i:i+cols_per_row]):
            nombre = mapa_items.get(item, item)
            porcentaje = no_cumple[item]

            # Determinar grupo según número de ítem
            item_num = int(item.split("_")[1])
            if 1 <= item_num <= 5:
                grupo_texto = "Al CTZ:"
            else:
                grupo_texto = "Al Gestor Local:"

            # Color según nivel de riesgo
            if porcentaje >= 40:
                color_borde = "#B71C1C"   # rojo oscuro
            elif porcentaje >= 20:
                color_borde = "#F57C00"   # naranja
            else:
                color_borde = "#FBC02D"   # amarillo

            with row[j]:
                st.markdown(
                    f"""
                    <div style="
                        background-color:#FFFFFF;
                        border-radius:14px;
                        border-left:6px solid {color_borde};
                        box-shadow:0 2px 8px rgba(0,0,0,0.07);
                        padding:14px 16px;
                        margin-bottom:10px;">
                        <div style="font-size:13px;color:#004C97;font-weight:600;margin-bottom:4px;">
                            {grupo_texto}
                        </div>
                        <div style="font-weight:600;color:#003A70;margin-bottom:6px;font-size:15px;">
                            {nombre}
                        </div>
                        <div style="font-size:13px;color:{color_borde};">
                            <b>{porcentaje}%</b> de fichas marcaron “No cumple”
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

if df_filtrado.empty:
    st.warning("⚠️ No hay registros que coincidan con los filtros seleccionados.")
    st.stop()

# ==============================================================
# 📈 LÍNEAS: Avance mensual del % "No cumple" por ítem (para MES numérico)
# ==============================================================

import plotly.graph_objects as go

if not no_cumple.empty:
    # Mapeo de número de mes a nombre
    mapa_meses = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }

    # Asegurar que MES sea numérico
    df_filtrado["MES"] = pd.to_numeric(df_filtrado["MES"], errors="coerce")
    meses_disponibles = sorted(df_filtrado["MES"].dropna().unique())
    if not meses_disponibles:
        st.info("⚠️ No hay datos de meses numéricos para graficar.")
    else:
        # Convertir a nombres para eje X
        x_vals = [mapa_meses.get(int(m), str(m)) for m in meses_disponibles]

        items_con_0 = list(no_cumple.index)
        item_top = items_con_0[0]

        def nombre_item_corto(item_key: str) -> str:
            n = int(item_key.split("_")[1])
            return f"Item {n}"

        def truncar(texto: str, maxlen: int = 42) -> str:
            texto = (texto or "").strip()
            return (texto[:maxlen-1] + "…") if len(texto) > maxlen else texto

        fig_line = go.Figure()

        for it in items_con_0:
            serie = []
            for mes in meses_disponibles:
                df_mes = df_filtrado[df_filtrado["MES"] == mes]
                total_validos = df_mes[it].notna().sum()
                if total_validos == 0:
                    serie.append(None)
                else:
                    pct0 = ((df_mes[it] == 0).sum() / total_validos) * 100
                    serie.append(round(pct0, 1))

            item_num = int(it.split("_")[1])
            nombre_largo = mapa_items.get(it, it)
            trace_name = nombre_item_corto(it)
            legend_name = f"{trace_name}: {truncar(nombre_largo)}"

            fig_line.add_trace(go.Scatter(
                x=x_vals,
                y=serie,
                mode="lines+markers",
                name=legend_name,
                visible=True if it == item_top else "legendonly",
                hovertemplate="<b>%{x}</b><br>" +
                              trace_name + ": %{y:.1f}%<br>" +
                              f"<span style='color:#666;'>{nombre_largo}</span><extra></extra>"
            ))

        fig_line.update_layout(
            title="Evolución mensual del % de 'No cumple' por ítem (mostrar/ocultar desde la leyenda)",
            xaxis=dict(title="Mes", showgrid=True, gridcolor="#ECEFF1"),
            yaxis=dict(title="% 'No cumple'", range=[0, 100], showgrid=True, gridcolor="#ECEFF1"),
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            font=dict(size=12, color="#003A70"),
            title_font=dict(size=16, color="#003A70"),
            legend_title_text="Ítems (nombre truncado)",
            margin=dict(t=60, b=40, l=70, r=40),
            height=480
        )

        st.plotly_chart(fig_line, use_container_width=True)

# ==============================================================
# 📊 PARETO: Ítems con "No cumple" (conteo y % acumulado)
# ==============================================================

from plotly.subplots import make_subplots

if not no_cumple.empty:
    # Conteo total de 0 por ítem (en la selección actual)
    conteos_0 = (df_filtrado[cols_items] == 0).sum()
    df_p = conteos_0[conteos_0 > 0].rename("conteo").to_frame().reset_index()
    df_p["item_num"] = df_p["index"].str.extract(r"(\d+)").astype(int)
    df_p["item_etiqueta"] = df_p["item_num"].apply(lambda n: f"Item {n}")
    df_p["nombre_largo"] = df_p["index"].apply(lambda k: mapa_items.get(k, k))

    # Orden descendente por conteo
    df_p = df_p.sort_values(by="conteo", ascending=False).reset_index(drop=True)
    total_0 = df_p["conteo"].sum()
    df_p["pct"] = (df_p["conteo"] / total_0 * 100).round(1)
    df_p["pct_acum"] = (df_p["pct"].cumsum()).round(1)

    # Truncado para la leyenda/hover
    def truncar(texto: str, maxlen: int = 42) -> str:
        texto = (texto or "").strip()
        return (texto[:maxlen-1] + "…") if len(texto) > maxlen else texto

    # Eje X como "Item N"
    x_vals = df_p["item_etiqueta"].tolist()

    # Subplot con eje secundario: barras (conteo) + línea (% acumulado)
    fig_pareto = make_subplots(specs=[[{"secondary_y": True}]])
    # Barras
    fig_pareto.add_trace(
        go.Bar(
            x=x_vals,
            y=df_p["conteo"],
            name="Conteo de 'No cumple'",
            marker=dict(color="#D32F2F"),
            hovertext=[truncar(n) for n in df_p["nombre_largo"]],
            hovertemplate="<b>%{x}</b><br>Conteo: %{y}<br><span style='color:#666;'>%{hovertext}</span><extra></extra>"
        ),
        secondary_y=False
    )
    # Línea % acumulado
    fig_pareto.add_trace(
        go.Scatter(
            x=x_vals,
            y=df_p["pct_acum"],
            name="% acumulado",
            mode="lines+markers",
            marker=dict(size=7),
            hovertemplate="<b>%{x}</b><br>% acumulado: %{y:.1f}%<extra></extra>"
        ),
        secondary_y=True
    )

    fig_pareto.update_yaxes(title_text="Conteo", secondary_y=False)
    fig_pareto.update_yaxes(title_text="% acumulado", range=[0, 100], secondary_y=True)

    fig_pareto.update_layout(
        title="Pareto de ítems con 'No cumple' (solo ítems con al menos un 0)",
        xaxis=dict(title="", showgrid=False),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(size=12, color="#003A70"),
        title_font=dict(size=16, color="#003A70"),
        legend_title_text="",
        margin=dict(t=60, b=40, l=70, r=40),
        height=480,
        bargap=0.25
    )

    st.plotly_chart(fig_pareto, use_container_width=True)

# ==============================================================
# 🔹 RESUMEN AUTOMÁTICO ASISTIDO POR IA (versión limpia y automática)
# ==============================================================

from utils.llm import generate_anexo2_summary

# 1) Preparamos agregados (mismo cálculo que antes)
cols_items = [f"ITEM_{i}" for i in range(1, 21)]
df_items = df_filtrado[cols_items].copy()

valores = df_items.values.flatten()
valores = valores[~pd.isna(valores)]
total_validos = int(len(valores))
total_0 = int((valores == 0).sum())
total_1 = int((valores == 1).sum())
total_2 = int((valores == 2).sum())

pct_0 = round((total_0 / total_validos) * 100, 1) if total_validos else 0.0
pct_1 = round((total_1 / total_validos) * 100, 1) if total_validos else 0.0
pct_2 = round((total_2 / total_validos) * 100, 1) if total_validos else 0.0

grupos = {
    "Al CTZ": [f"ITEM_{i}" for i in range(1, 6)],
    "Al Gestor Local": [f"ITEM_{i}" for i in range(6, 9)],
    "Al Hogar": [f"ITEM_{i}" for i in range(9, 12)],
    "Durante el Acompañamiento": [f"ITEM_{i}" for i in range(12, 21)]
}

def totales_por_valor(df, items, valor):
    if not items:
        return 0
    subset = df[items]
    return int((subset == valor).sum().sum())

# ==============================================================
# Ajuste semántico: nombres humanizados de categorías
# ==============================================================

nombres_humanos = {
    "Al CTZ": "las actividades sobre CTZ",
    "Al Gestor Local": "las actividades sobre el Gestor Local",
    "Al Hogar": "las actividades en el Hogar",
    "Durante el Acompañamiento": "las actividades Durante la Visita"
}

resumen_grupos = []
for nombre, items in grupos.items():
    resumen_grupos.append({
        # 🔹 Nuevo nombre de campo: categoria_actividades (en vez de grupo)
        "categoria_actividades": nombres_humanos.get(nombre, nombre),
        "total_0": totales_por_valor(df_filtrado, items, 0),
        "total_1": totales_por_valor(df_filtrado, items, 1),
        "total_validos_en_categoria": int(df_filtrado[items].notna().sum().sum())
    })

def ranking_items(df, items, valor, etiqueta_map):
    s = df[items].apply(lambda col: (col == valor).sum())
    s = s[s > 0].sort_values(ascending=False)
    return [
        {"item": k, "nombre": etiqueta_map.get(k, k), "freq": int(v)}
        for k, v in s.items()
    ]

rank_0 = ranking_items(df_filtrado, cols_items, 0, mapa_items)
rank_1 = ranking_items(df_filtrado, cols_items, 1, mapa_items)

contexto_llm = {
    "filtros_aplicados": {
        "unidad_territorial": ut_sel or "todas",
        "mes": mes_sel or "todos",
        "supervisor": sup_sel or "todos",
    },
    "global": {
        "total_registros": int(len(df_filtrado)),
        "total_respuestas_validas": total_validos,
        "porcentajes": {"no_cumple_0": pct_0, "en_desarrollo_1": pct_1, "cumple_2": pct_2}
    },
    "categorias_de_actividades": resumen_grupos,
    "ranking_no_cumple": rank_0,
    "ranking_en_desarrollo": rank_1
}

# 2) Generar resumen automáticamente
try:
    with st.spinner("Generando resumen ejecutivo..."):
        texto = generate_anexo2_summary(contexto_llm)
        # Limpiar etiquetas tipo <s> [B_NATURAL] etc.
        import re
        texto_limpio = re.sub(r"<[^>]+>", "", texto)
        texto_limpio = re.sub(r"\[[^\]]+\]", "", texto_limpio)
        texto_limpio = texto_limpio.strip()

    # Mostrar texto limpio sin título visible (solo si se desea)
    st.markdown(
        f"""
        <div style="font-size:16px; line-height:1.6; color:#222; background-color:#f9fafb; padding:15px; border-radius:8px; border-left:5px solid #004C97;">
            {texto_limpio}
        </div>
        """,
        unsafe_allow_html=True
    )
except Exception as e:
    st.warning("No fue posible generar el resumen automático.")
    st.text(str(e))
    
# ==============================================================
# INDICADORES EJECUTIVOS (KPI)
# ==============================================================

st.markdown("---")
# Solo columnas de ítems
cols_items = [f"ITEM_{i}" for i in range(1, 21)]
df_items = df_filtrado[cols_items].copy()

# Aplanar y eliminar NaN
valores = df_items.values.flatten()
valores = valores[~pd.isna(valores)]

if len(valores) == 0:
    st.info("No hay datos válidos para calcular indicadores.")
else:
    total_validos = len(valores)
    total_0 = (valores == 0).sum()
    total_1 = (valores == 1).sum()
    total_2 = (valores == 2).sum()

    pct_0 = round((total_0 / total_validos) * 100, 1)
    pct_1 = round((total_1 / total_validos) * 100, 1)
    pct_2 = round((total_2 / total_validos) * 100, 1)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="✅ % de Ítems Cumplidos",
            value=f"{pct_2}%",
            delta=None
        )
    with col2:
        st.metric(
            label="⚠️ % de Ítems en Desarrollo",
            value=f"{pct_1}%",
            delta=None
        )
    with col3:
        st.metric(
            label="❌ % de Ítems No Cumplidos",
            value=f"{pct_0}%",
            delta=None
        )
    with col4:
        st.metric(
            label="Total de registros analizados",
            value=len(df_filtrado),
            delta=None
        )

st.markdown("---")

# ==============================================================
# DEFINICIÓN DE GRUPOS
# ==============================================================

grupos = {
    "Al CTZ": [f"ITEM_{i}" for i in range(1, 6)],
    "Al Gestor Local": [f"ITEM_{i}" for i in range(6, 9)],
    "Al Hogar": [f"ITEM_{i}" for i in range(9, 12)],
    "Durante el Acompañamiento": [f"ITEM_{i}" for i in range(12, 21)]
}

orden_items = [f"ITEM_{i}" for i in range(1, 21)]

# ==============================================================
# PROCESAMIENTO DE PORCENTAJES
# ==============================================================

def preparar_porcentajes(df):
    registros = []
    for grupo, items in grupos.items():
        for item in items:
            if item in df.columns:
                total = df[item].notna().sum()
                if total == 0:
                    continue
                counts = df[item].value_counts().reindex([0, 1, 2], fill_value=0)
                for valor, freq in counts.items():
                    registros.append({
                        "Ítem": item,
                        "Grupo": grupo,
                        "Descripción": mapa_items.get(item, item),
                        "Valor": valor,
                        "Frecuencia": freq,
                        "Porcentaje": round((freq / total) * 100, 1)
                    })
    if not registros:
        return None
    return pd.DataFrame(registros)

df_porcentajes = preparar_porcentajes(df_filtrado)
if df_porcentajes is None:
    st.info("No existen datos válidos para graficar.")
    st.stop()

# ==============================================================
# TRANSFORMACIÓN FINAL Y ORDEN
# ==============================================================

pivot_df = df_porcentajes.pivot_table(
    index=["Grupo", "Ítem", "Descripción"],
    columns="Valor",
    values="Porcentaje",
    fill_value=0
).reset_index()

pivot_df.columns.name = None
pivot_df = pivot_df.rename(columns={0: "❌ No cumple", 1: "⚠️ En desarrollo", 2: "✅ Cumple"})

pivot_df["Ítem_nro"] = pivot_df["Ítem"].str.extract(r"(\d+)").astype(int)
pivot_df = pivot_df.sort_values("Ítem_nro")

# ==============================================================
# GRAFICADO – UN SOLO GRÁFICO CON DIVISIONES VISUALES
# ==============================================================

color_map = {
    "❌ No cumple": "#D32F2F",
    "⚠️ En desarrollo": "#FBC02D",
    "✅ Cumple": "#388E3C"
}

fig = go.Figure()

# Añadir barras apiladas con tooltip minimalista (corregido)
for col in ["❌ No cumple", "⚠️ En desarrollo", "✅ Cumple"]:
    fig.add_trace(go.Bar(
        y=pivot_df["Descripción"],
        x=pivot_df[col],
        name=col,
        orientation="h",
        marker=dict(color=color_map[col]),
        # Tooltip minimalista y limpio
        hovertemplate=f"<b>{col}:</b> %{{x:.1f}}%<extra></extra>"
    ))
    
# Añadir líneas divisorias entre grupos
y_positions = []
for grupo, items in grupos.items():
    ultimo_item = int(items[-1].split("_")[1])
    if ultimo_item < 20:
        desc = mapa_items.get(f"ITEM_{ultimo_item}", "")
        try:
            y_val = pivot_df[pivot_df["Descripción"] == desc].index[-1]
            y_positions.append(y_val + 0.5)
        except:
            pass

for y in y_positions:
    fig.add_shape(
        type="line",
        x0=0, x1=100,
        y0=y, y1=y,
        line=dict(color="#B0BEC5", width=1.5, dash="dot")
    )

# Etiquetas de grupo al margen derecho
for grupo, items in grupos.items():
    desc_ref = mapa_items.get(items[0], "")
    try:
        idx_inicio = pivot_df[pivot_df["Descripción"] == desc_ref].index[0]
        idx_fin = pivot_df[pivot_df["Ítem"] == items[-1]].index[0]
        fig.add_annotation(
            x=102, y=(idx_inicio + idx_fin) / 2,
            text=f"<b>{grupo}</b>",
            showarrow=False,
            font=dict(size=13, color="#003A70"),
            xanchor="left"
        )
    except:
        pass

# ==============================================================
# FORMATO FINAL
# ==============================================================

fig.update_layout(
    title="Distribución porcentual del cumplimiento de ítems evaluados",
    barmode="stack",
    xaxis=dict(title="Porcentaje (%)", range=[0, 100], showgrid=True, gridcolor="#ECEFF1"),
    yaxis=dict(title="", showgrid=False, autorange="reversed"),
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    font=dict(size=12, color="#003A70"),
    title_font=dict(size=16, color="#003A70"),
    legend_title_text="Estado del ítem",
    bargap=0.15,
    bargroupgap=0.05,
    margin=dict(t=60, b=30, l=280, r=120),
    height=900,
    hoverlabel=dict(
        bgcolor="white",
        font_size=12,
        font_color="black",
        bordercolor="#B0BEC5"
    )
)

st.plotly_chart(fig, use_container_width=True)