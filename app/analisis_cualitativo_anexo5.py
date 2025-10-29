# =============================================
# analisis_cualitativo_anexo5.py  —  Versión optimizada 2025
# =============================================
import pandas as pd
import re
import plotly.express as px
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from pysentimiento import create_analyzer
from pathlib import Path

# =============================================
# ⚙️ CONFIGURACIÓN DE RUTAS
# =============================================
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "processed" / "anexo5" / "anexo5_consolidado.xlsx"
OUTPUT_DIR = BASE_DIR / "data" / "analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =============================================
# 🔠 STOPWORDS EN ESPAÑOL PERSONALIZADAS
# =============================================
STOPWORDS_ES = """
de la que el en y a los se del las por un para con no una su al lo como más pero sus le ya o este
sí porque esta entre cuando muy sin sobre también me hasta hay donde quien desde todo nos durante todos
uno les ni contra otros ese eso ante ellos e esto mí antes algunos qué unos yo otro otras otra él tanto
esa estos mucho quienes nada muchos cual poco ella estar estas algunas algo nosotros mi mis tú te ti tu tus ellas
nosotros vosotros vosotras ellos ellas usted ustedes ser es soy eres somos sois están estado estaba estábamos estaban
tener tengo tiene tenemos tienen tuve tuvo tenido teniendo hacer hago hace hacemos hacen hice hizo hecho decir digo dice dicen dicho ver veo ve vemos ven vio visto dar doy da damos dan dado saber sé sabe sabemos saben sabido querer quiero quiere queremos quieren querido llegar llego llega llegamos llegan llegando pasar paso pasa pasamos pasan pasado deber debo debe debemos deben debiendo poner pongo pone ponemos ponen puesto parecer parezco parece parecemos parecen pareciendo quedar quedo queda quedamos quedan quedado creer creo cree creemos creen creído hablar hablo habla hablamos hablan hablado llevar llevo lleva llevamos llevan llevado dejar dejo deja dejamos dejan dejado seguir sigo sigue seguimos siguen seguido encontrar encuentro encuentra encontramos encuentran encontrado llamar llamo llama llamamos llaman llamado
""".split()

vectorizer = TfidfVectorizer(max_features=500, stop_words=STOPWORDS_ES)


# =============================================
# 🧩 FUNCIONES AUXILIARES
# =============================================
def limpiar_texto(texto):
    """Limpia texto eliminando símbolos y deja solo palabras útiles."""
    if pd.isna(texto):
        return ""
    texto = texto.lower()
    texto = re.sub(r"[^a-záéíóúñü0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()

def generar_nube_palabras(texto_total, titulo, filename):
    """Genera una nube de palabras a partir de un texto largo."""
    wc = WordCloud(width=1000, height=500, background_color="white",
                   colormap="viridis", collocations=False).generate(texto_total)
    plt.figure(figsize=(10, 5))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.title(titulo, fontsize=16)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename)
    plt.close()

# =============================================
# 📥 CARGA Y LIMPIEZA DE DATOS
# =============================================
print(f"📂 Cargando datos desde {DATA_PATH}")
df = pd.read_excel(DATA_PATH)

if len(df) == 0:
    raise ValueError("❌ El archivo de Anexo 5 no contiene registros.")

df["texto_hallazgo"] = df["PUNTOS_CRITICOS"].apply(limpiar_texto)
df["texto_acuerdo"] = df["ACUERDOS_MEJORA"].apply(limpiar_texto)
df["texto_total"] = df["texto_hallazgo"] + " " + df["texto_acuerdo"]

print(f"✅ {len(df)} registros cargados y limpiados correctamente")

# =============================================
# 🔍 ANÁLISIS DE TEMAS (TF-IDF + KMeans)
# =============================================
if len(df) >= 3:
    vectorizer = TfidfVectorizer(max_features=500, stop_words=STOPWORDS_ES)
    X = vectorizer.fit_transform(df["texto_total"])

    # Ajuste dinámico del número de clusters según tamaño del dataset
    num_clusters = min(6, max(2, len(df) // 2))
    kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
    df["cluster"] = kmeans.fit_predict(X)

    # Palabras clave por cluster
    order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
    terms = vectorizer.get_feature_names_out()

    temas = {}
    for i in range(num_clusters):
        top_terms = [terms[ind] for ind in order_centroids[i, :10]]
        temas[i] = ", ".join(top_terms)

    df["tema_label"] = df["cluster"].map(temas)

    print("🧭 Temas detectados:")
    for i, palabras in temas.items():
        print(f"Tema {i+1}: {palabras}")

else:
    df["cluster"] = 0
    df["tema_label"] = "Tema General"
    print("⚠️ Muy pocos registros, se omitió clustering. Se asignó 'Tema General' a todos.")

# =============================================
# 💬 ANÁLISIS DE SENTIMIENTO
# =============================================
print("🔎 Analizando sentimiento en español...")
analyzer = create_analyzer(task="sentiment", lang="es")

df["sentimiento"] = df["texto_hallazgo"].apply(
    lambda x: analyzer.predict(x).output if x.strip() else "neutro"
)

sentimiento_resumen = df["sentimiento"].value_counts(normalize=True) * 100
print("\n📊 Distribución de sentimientos:")
print(sentimiento_resumen.round(1).to_dict())

# =============================================
# 🌈 NUBE DE PALABRAS Y VISUALIZACIONES
# =============================================
texto_total = " ".join(df["texto_total"].tolist())
generar_nube_palabras(texto_total, "Nube de Palabras - Hallazgos y Acuerdos", "nube_palabras_anexo5.png")

fig_sent = px.pie(df, names="sentimiento", title="Distribución de Sentimientos")
fig_sent.write_html(str(OUTPUT_DIR / "sentimientos_anexo5.html"))

fig_temas = px.bar(df.groupby("tema_label").size().reset_index(name="Frecuencia"),
                   x="tema_label", y="Frecuencia",
                   title="Temas Recurrentes en Hallazgos y Acuerdos")
fig_temas.write_html(str(OUTPUT_DIR / "temas_anexo5.html"))

# =============================================
# 💾 EXPORTAR RESULTADOS
# =============================================
output_excel = OUTPUT_DIR / "anexo5_analisis_cualitativo.xlsx"
df.to_excel(output_excel, index=False)

print(f"\n✅ Análisis completado y exportado a {output_excel}")
print(f"🖼️ Nube de palabras: {OUTPUT_DIR / 'nube_palabras_anexo5.png'}")
print(f"📈 Gráficos: {OUTPUT_DIR / 'sentimientos_anexo5.html'}, {OUTPUT_DIR / 'temas_anexo5.html'}")