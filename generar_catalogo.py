import truststore
truststore.inject_into_ssl()
import os
import pandas as pd

# Datos extraídos del documento oficial y las promociones calculadas
datos = {
    "Categoría": [
        # Aguas y Bebidas
        "Aguas y Bebidas", "Aguas y Bebidas", "Aguas y Bebidas", "Aguas y Bebidas", "Aguas y Bebidas",
        # Helados Artesanales
        "Helados Artesanales", "Helados Artesanales", "Helados Artesanales", "Helados Artesanales", "Helados Artesanales",
        # Snacks y Dulces
        "Snacks y Dulces", "Snacks y Dulces", "Snacks y Dulces", "Snacks y Dulces", "Snacks y Dulces",
        # Aceites y Extras
        "Aceites y Extras", "Aceites y Extras",
        # Promociones
        "Promociones", "Promociones", "Promociones", "Promociones", "Promociones"
    ],
    "Producto": [
        "Agua de Coco (250 ml)", "Agua de Coco (500 ml)", "Refresco Coco y Leche", "Jugo con Stevia", "Leche de Coco Vidrio",
        "Medio Litro Coco y Cremoso", "Vasito Chocolate", "Paleta Leche Coco", "Paleta Mucho Coco", "Paleta Coco Menta",
        "Alfajor Grande", "Alfajor Choco Blanco", "Volcán de Coco", "Cocada con Manjar", "Galleta Crocante (x3)",
        "Aceite de Coco (200 ml)", "Aceite de Coco (400 ml)",
        "Promo Noviembre de Oro (200ml)", "Promo Noviembre de Oro (400ml)", "Combo Dúo Crocante", "Combo Quincena Refrescante", "Combo Truco o Coco"
    ],
    "Descripción": [
        "Agua de coco natural, sin preservantes ni saborizantes añadidos.",
        "Agua de coco natural, formato ideal para llevar. Sin preservantes.",
        "Jugo natural de coco mezclado con deliciosa leche entera (370 ml).",
        "Jugo de coco natural endulzado con stevia, libre de lácteos (250 ml).",
        "Crema de coco mezclada con agua de coco en envase premium (1 L).",
        "Helado cremoso de leche con auténtico coco en presentación de 500 ml.",
        "Helado tradicional de leche con coco y un toque de chocolate (120 ml).",
        "Paleta clásica y cremosa de helado de leche con trozos de coco (95 ml).",
        "Paleta vegana, sin lácteos ni productos de origen animal (120 ml).",
        "Paleta con base de agua, refrescante combinación de coco y menta (85 ml).",
        "Exquisito alfajor con abundante relleno de dulce de leche y borde de coco rallado.",
        "Alfajor recubierto de chocolate blanco, relleno de manjar y decorado con coco.",
        "Postre tradicional horneado en forma de volcán, hecho puramente con coco rallado.",
        "Dulce tradicional de coco horneado y generosamente relleno con suave manjar.",
        "Paquete de tres galletas artesanales y deliciosamente crocantes a base de coco.",
        "Aceite de coco extra virgen, secado al vacío y prensado en frío.",
        "Aceite de coco extra virgen, formato familiar. Ideal para cocina y cuidado personal.",
        "15% de descuento en aceite de coco de 200ml. Válido todo noviembre.",
        "15% de descuento en aceite de coco de 400ml. Válido todo noviembre.",
        "Por la compra de 2 Helados Vasito Chocolate, llévate GRATIS una Galleta Crocante.",
        "Por la compra de 3 Refrescos Coco y Leche, llévate 1 Agua de 250ml GRATIS. Válido del 1 al 15 de Octubre.",
        "Especial Halloween: Compra 2 Volcanes de Coco y llévate una Paleta Coco Menta GRATIS."
    ],
    "Precio": [
        "$1.50", "$2.50", "$2.30", "$2.00", "$10.00",
        "$5.70", "$1.55", "$1.25", "$1.50", "$1.30",
        "$1.55", "$1.30", "$1.00", "$0.80", "$0.95",
        "$9.00", "$16.50",
        "$7.65", "$14.03", "$3.10", "$6.90", "$2.00"
    ],
    "Stock": [
        20, 30, 25, 20, 15,
        15, 40, 35, 30, 20,
        20, 25, 15, 40, 25,
        10, 10,
        0, 0, 0, 0, 0
    ],
    "Ruta_Imagen": [
        "img/agua_250.jpg", "img/agua_500.jpg", "img/refresco_370.jpg", "img/jugo_stevia.jpg", "img/leche_vidrio.jpg",
        "img/medio_litro.jpg", "img/vasito_choco.jpg", "img/paleta_leche.jpg", "img/paleta_mucho.jpg", "img/paleta_menta.jpg",
        "img/alfajor.jpg", "img/alfajor_blanco.jpg", "img/volcan.jpg", "img/cocada.jpg", "img/galleta.jpg",
        "img/aceite_200.jpg", "img/aceite_400.jpg",
        "img/promo_aceite.jpg", "img/promo_aceite.jpg", "img/promo_duo.jpg", "img/promo_quincena.jpg", "img/promo_halloween.jpg"
    ]
}

# Receta de cada promoción: {producto: cantidad necesaria por promoción}
# Los nombres deben ser IGUALES a los de la lista "Producto".
COMPONENTES_PROMOS = {
    "Promo Noviembre de Oro (200ml)": {"Aceite de Coco (200 ml)": 1},
    "Promo Noviembre de Oro (400ml)": {"Aceite de Coco (400 ml)": 1},
    "Combo Dúo Crocante": {"Vasito Chocolate": 2, "Galleta Crocante (x3)": 1},
    "Combo Quincena Refrescante": {"Refresco Coco y Leche": 3, "Agua de Coco (250 ml)": 1},
    "Combo Truco o Coco": {"Volcán de Coco": 2, "Paleta Coco Menta": 1},
}

# Crear el DataFrame
for nombre, lista in datos.items():
    print(f"{nombre}: {len(lista)} elementos")
df = pd.DataFrame(datos)

# Stock de los productos normales
stock_productos = {
    fila["Producto"]: int(fila["Stock"])
    for _, fila in df.iterrows()
    if fila["Categoría"] != "Promociones"
}

# Calcular el stock de cada promoción según sus ingredientes
for i, fila in df.iterrows():
    if fila["Categoría"] != "Promociones":
        continue
    receta = COMPONENTES_PROMOS[fila["Producto"]]
    promos_posibles = min(stock_productos[prod] // cant for prod, cant in receta.items())
    df.at[i, "Stock"] = promos_posibles
    print(f"{fila['Producto']}: alcanza para {promos_posibles}")

# Exportar a Excel
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ruta_archivo = os.path.join(BASE_DIR, "data", "catalogo_coco_express_completo.xlsx")
df.to_excel(ruta_archivo, index=False)
print(f"¡Catálogo generado exitosamente en: {ruta_archivo}!")