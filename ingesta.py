import truststore
truststore.inject_into_ssl()
import os
import pandas as pd
from langchain_core.documents import Document
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_qdrant import QdrantVectorStore

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_DB = os.path.join(BASE_DIR, "qdrant_db_gratis")
RUTA_EXCEL = os.path.join(BASE_DIR, "data", "catalogo_coco_express_completo.xlsx")

# Receta de cada promoción: {producto: cantidad necesaria por promoción}
# Los nombres deben ser IGUALES a los de la columna "Producto" del Excel.
COMPONENTES_PROMOS = {
    "Promo Noviembre de Oro (200ml)": {"Aceite de Coco (200 ml)": 1},
    "Promo Noviembre de Oro (400ml)": {"Aceite de Coco (400 ml)": 1},
    "Combo Dúo Crocante": {"Vasito Chocolate": 2, "Galleta Crocante (x3)": 1},
    "Combo Quincena Refrescante": {"Refresco Coco y Leche": 3, "Agua de Coco (250 ml)": 1},
    "Combo Truco o Coco": {"Volcán de Coco": 2, "Paleta Coco Menta": 1},
}


def calcular_stock_promo(nombre_promo, stock_productos):
    """Devuelve (promos_disponibles, lista_de_faltantes)."""
    receta = COMPONENTES_PROMOS.get(nombre_promo)
    if not receta:
        return 0, ["receta no definida"]

    disponibles = []
    faltantes = []
    for producto, cantidad in receta.items():
        stock = stock_productos.get(producto, 0)
        posibles = stock // cantidad
        disponibles.append(posibles)
        if posibles == 0:
            faltantes.append(producto)

    return min(disponibles), faltantes


def realizar_ingesta():
    print("1. Leyendo el catálogo de Excel...")
    df = pd.read_excel(RUTA_EXCEL)
    df = df.dropna(subset=["Producto", "Descripción"])

    # Stock de todos los productos, para calcular las promociones
    stock_productos = {fila["Producto"]: int(fila["Stock"]) for _, fila in df.iterrows()}

    documentos = []
    for _, fila in df.iterrows():
        nombre = fila["Producto"]
        es_promo = fila["Categoría"] == "Promociones"

        if es_promo:
            stock, faltantes = calcular_stock_promo(nombre, stock_productos)
            if stock > 0:
                disponibilidad = (
                    f"DISPONIBLE hasta agotar stock "
                    f"(alcanza para {stock} promociones)"
                )
            else:
                disponibilidad = (
                    "AGOTADO (no hay stock suficiente de: "
                    + ", ".join(faltantes) + ")"
                )
        else:
            stock = int(fila["Stock"])
            if stock > 0:
                disponibilidad = f"DISPONIBLE ({stock} unidades en stock)"
            else:
                disponibilidad = "AGOTADO (0 unidades en stock)"

        texto = (
            f"Producto: {nombre}\n"
            f"Categoría: {fila['Categoría']}\n"
            f"Descripción: {fila['Descripción']}\n"
            f"Precio: {fila['Precio']}\n"
            f"Disponibilidad: {disponibilidad}"
        )
        documentos.append(
            Document(
                page_content=texto,
                metadata={
                    "producto": str(nombre),
                    "categoria": str(fila["Categoría"]),
                    "stock": stock,
                    "ruta_imagen": str(fila["Ruta_Imagen"]),
                },
            )
        )
        print(f"   - {nombre}: {disponibilidad}")

    print(f"   {len(documentos)} productos preparados.")

    print("2. Cargando el modelo de embeddings...")
    embeddings = FastEmbedEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    print("3. Creando la base de datos vectorial local (Qdrant)...")
    QdrantVectorStore.from_documents(
        documentos,
        embeddings,
        path=RUTA_DB,
        collection_name="catalogo_coco_gratis",
    )

    print("¡Ingesta completada con éxito!")


if __name__ == "__main__":
    realizar_ingesta()