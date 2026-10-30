import truststore
truststore.inject_into_ssl()

import time
from groq import BadRequestError
import os
import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_classic.chains import create_retrieval_chain, create_history_aware_retriever
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

# Ruta absoluta a la base de datos (misma que usa ingesta.py)
RUTA_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qdrant_db_gratis")

# 1. Cargar llave
load_dotenv()

# 2. Diseño visual
st.set_page_config(page_title="Coco Express Bot", page_icon="🥥")
st.title("🥥 Asistente Virtual Coco Express")
st.write("¡Hola! Bienvenido a Coco Express (Machala). ¿Qué producto o promoción quieres consultar?")


# 3. Sistema RAG (con caché para no recargar la BD en cada mensaje)
@st.cache_resource
def iniciar_sistema_rag():
    # A. El cerebro
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0.1, reasoning_effort="medium")

    # B. La base de datos
    embeddings = FastEmbedEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    client = QdrantClient(path=RUTA_DB)
    vector_store = QdrantVectorStore(
        client=client,
        collection_name="catalogo_coco_gratis",
        embedding=embeddings,
    )
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})

    # C. Reescribir la pregunta usando el historial (para entender "las", "eso", etc.)
    prompt_reescritura = ChatPromptTemplate.from_messages([
        ("system",
         "Dado el historial de chat y la última pregunta del usuario, reescribe la "
         "pregunta para que se entienda sola, sin necesitar el historial. "
         "NO la respondas. Si ya se entiende sola, devuélvela igual."),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    retriever_con_historial = create_history_aware_retriever(llm, retriever, prompt_reescritura)

    # D. Reglas del bot (solo informativo)
    instrucciones = (
        "Eres el asistente virtual informativo de 'Coco Express', si te preguntan ubiación diras: Nos encontramos ubicados en el Paseo Shopping-Machala"
        "Tu ÚNICA función es dar información sobre los productos y promociones del catálogo. "
        "NO tomas pedidos, NO reservas ni separas productos, NO ofreces entregas ni "
        "gestionas compras.\n"
        "Reglas:\n"
        "1. Usa SOLO la información del catálogo. Nunca inventes precios, promociones ni productos.\n"
        "2. Responde únicamente sobre lo que el cliente pregunta. NO menciones promociones "
        "ni otros productos si no los pidió, salvo que pregunte por promociones.\n"
        "3. Si el producto está DISPONIBLE, indica que hay disponibilidad y su precio. "
        "Si está AGOTADO, díselo amablemente y, si hay una alternativa parecida disponible "
        "en el catálogo, menciónala.\n"
        "4. Si el cliente pide comprar, apartar, reservar o separar algo, aclara amablemente "
        "que solo brindas información y que debe acercarse al local para realizar su compra.\n"
        "5. Si el producto NO aparece en el catálogo, responde: "
        "'Por favor, consulta directamente en nuestro local físico para más detalles'.\n"
        "6. El stock es referencial y puede cambiar durante el día.\n"
        "7. Responde de forma breve y amable.\n\n"
        "Catálogo (Contexto):\n{context}"
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", instrucciones),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    # E. Unir todo
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever_con_historial, question_answer_chain)


rag_chain = iniciar_sistema_rag()

# 4. Memoria visual del chat
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["rol"]):
        st.markdown(mensaje["contenido"])


def construir_historial(max_mensajes=6):
    """Convierte los últimos mensajes en el formato que entiende LangChain."""
    historial = []
    for m in st.session_state.mensajes[-max_mensajes:]:
        if m["rol"] == "user":
            historial.append(HumanMessage(content=m["contenido"]))
        else:
            historial.append(AIMessage(content=m["contenido"]))
    return historial

def consultar_bot(pregunta, historial, intentos=3):
    """Consulta al bot y reintenta si el modelo devuelve una salida inválida."""
    for intento in range(intentos):
        try:
            respuesta = rag_chain.invoke({
                "input": pregunta,
                "chat_history": historial,
            })
            texto = respuesta["answer"].strip()
            if texto:
                return texto
        except BadRequestError as e:
            # Solo reintentamos el error de salida no parseable
            if "output_parse_failed" not in str(e):
                raise
            print(f"Intento {intento + 1}/{intentos} falló (salida vacía del modelo).")
        time.sleep(1)

    return "Tuve un problema técnico para responderte. ¿Puedes repetir tu pregunta, por favor?"

# 5. Caja de texto
pregunta_usuario = st.chat_input("Pregunta por un producto o promoción...")

if pregunta_usuario:
    with st.chat_message("user"):
        st.markdown(pregunta_usuario)

    # El historial se arma ANTES de guardar la pregunta actual
    historial = construir_historial()
    st.session_state.mensajes.append({"rol": "user", "contenido": pregunta_usuario})

    with st.chat_message("assistant"):
        with st.spinner("Buscando en el catálogo..."):
            texto_respuesta = consultar_bot(pregunta_usuario, historial)
            st.markdown(texto_respuesta)

    st.session_state.mensajes.append({"rol": "assistant", "contenido": texto_respuesta})