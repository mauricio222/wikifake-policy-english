import os
import google.generativeai as genai
import markdown
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
import uuid

# Cargar variables de entorno
load_dotenv()

# Configurar API de Gemini
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("No se encontró una clave de API. Por favor, configure la variable de entorno GEMINI_API_KEY en el archivo .env.")

genai.configure(api_key=api_key)

# Intentar obtener modelos disponibles
try:
    available_models = [model.name for model in genai.list_models()]
    print("Modelos disponibles:", available_models)
    
    # Modelos preferidos en orden de preferencia, priorizando los que usan menos recursos
    preferred_models = [
        "models/gemini-1.5-flash",     # Flash models use fewer resources
        "models/gemini-2.0-flash",
        "models/gemini-1.5-flash-latest",
        "models/gemini-1.0-pro-vision-latest",
        "models/gemini-1.5-pro",
        "models/gemini-1.5-pro-latest"
    ]
    
    # Encontrar el primer modelo preferido que esté disponible
    model_name = None
    for preferred in preferred_models:
        if preferred in available_models:
            model_name = preferred
            print(f"Usando modelo preferido: {model_name}")
            break
    
    # Si ninguno de los modelos preferidos está disponible, usar cualquier modelo Gemini sin visión
    if not model_name:
        # Priorizar modelos 'flash' sobre otros cuando sea posible
        flash_models = [model for model in available_models if "gemini" in model.lower() and "flash" in model.lower()]
        if flash_models:
            model_name = flash_models[0]
            print(f"Usando modelo flash disponible: {model_name}")
        else:
            for model in available_models:
                if "gemini" in model.lower() and "vision" not in model.lower():
                    model_name = model
                    print(f"Usando modelo disponible: {model_name}")
                    break
    
    # Si aún no se encuentra ningún modelo, usar uno predeterminado
    if not model_name:
        model_name = "models/gemini-1.5-flash"  # Cambiar el predeterminado al modelo flash
        print(f"No se encontraron modelos adecuados. Recurriendo a: {model_name}")
        
except Exception as e:
    print(f"Error al listar modelos: {e}")
    # Recurrir a un modelo recomendado de menos recursos
    model_name = "models/gemini-1.5-flash"  # Cambiar el predeterminado al modelo flash
    print(f"Recurriendo a: {model_name}")

# Inicializar el modelo
model = genai.GenerativeModel(model_name)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24).hex())  # Necesario para usar session

# Diccionario para almacenar historiales de chat
chat_histories = {}

# Cargar el contenido del archivo de texto
def load_text_file(file_path="politicas_junta_personal.txt"):
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Hacer que la tabla de contenidos sea clickeable
    toc_start = "ÍNDICE DE CONTENIDOS"
    toc_end = "=============================================================================\n1."
    
    toc_section = content.split(toc_start)[1].split(toc_end)[0]
    clickable_toc = toc_section
    
    # Reemplazar las entradas de la tabla de contenidos con enlaces clickeables
    # Secciones principales
    clickable_toc = clickable_toc.replace("1. POLÍTICA DE CÓDIGO DE CONDUCTA", '<a href="#section-1">1. POLÍTICA DE CÓDIGO DE CONDUCTA</a>')
    clickable_toc = clickable_toc.replace("2. CÓDIGO DE CONDUCTA PARA LA JUNTA DE FIDEICOMISARIOS", '<a href="#section-2">2. CÓDIGO DE CONDUCTA PARA LA JUNTA DE FIDEICOMISARIOS</a>')
    clickable_toc = clickable_toc.replace("3. POLÍTICA DE CONFLICTO DE INTERESES", '<a href="#section-3">3. POLÍTICA DE CONFLICTO DE INTERESES</a>')
    clickable_toc = clickable_toc.replace("4. ACUERDO DE CONFIDENCIALIDAD", '<a href="#section-4">4. ACUERDO DE CONFIDENCIALIDAD</a>')
    clickable_toc = clickable_toc.replace("5. POLÍTICAS FINANCIERAS", '<a href="#section-5">5. POLÍTICAS FINANCIERAS</a>')
    clickable_toc = clickable_toc.replace("6. POLÍTICAS OPERATIVAS", '<a href="#section-6">6. POLÍTICAS OPERATIVAS</a>')
    clickable_toc = clickable_toc.replace("7. POLÍTICAS DE CUMPLIMIENTO", '<a href="#section-7">7. POLÍTICAS DE CUMPLIMIENTO</a>')
    clickable_toc = clickable_toc.replace("8. POLÍTICAS DE VIAJE", '<a href="#section-8">8. POLÍTICAS DE VIAJE</a>')
    clickable_toc = clickable_toc.replace("9. PROTECCIÓN DE DENUNCIANTES", '<a href="#section-9">9. PROTECCIÓN DE DENUNCIANTES</a>')
    
    # Subsecciones (asegurando que los espacios y formato exacto coincida)
    clickable_toc = clickable_toc.replace("   5.1 Uso de Tarjetas de Crédito", '   <a href="#section-5-1">5.1 Uso de Tarjetas de Crédito</a>')
    clickable_toc = clickable_toc.replace("   5.2 Delegación de Autoridad", '   <a href="#section-5-2">5.2 Delegación de Autoridad</a>')
    clickable_toc = clickable_toc.replace("   6.1 Directrices para Gastos de Representación", '   <a href="#section-6-1">6.1 Directrices para Gastos de Representación</a>')
    clickable_toc = clickable_toc.replace("   6.2 Política de Regalos", '   <a href="#section-6-2">6.2 Política de Regalos</a>')
    clickable_toc = clickable_toc.replace("   7.1 Política Anticorrupción", '   <a href="#section-7-1">7.1 Política Anticorrupción</a>')
    clickable_toc = clickable_toc.replace("   7.2 Política de No Discriminación", '   <a href="#section-7-2">7.2 Política de No Discriminación</a>')
    clickable_toc = clickable_toc.replace("   8.1 Política General de Viajes", '   <a href="#section-8-1">8.1 Política General de Viajes</a>')
    clickable_toc = clickable_toc.replace("   8.2 Proceso de Aprobación de Viajes", '   <a href="#section-8-2">8.2 Proceso de Aprobación de Viajes</a>')
    
    # Reemplazar la tabla de contenidos original con la clickeable
    formatted_content = content.replace(toc_section, clickable_toc)
    
    return formatted_content

# Variable global para almacenar el contenido del texto
TEXT_CONTENT = load_text_file()

@app.route('/')
def index():
    """Renderizar la página principal con el contenido del archivo de texto."""
    return render_template('index.html', text_content=TEXT_CONTENT)

@app.route('/api/chat', methods=['POST'])
def chat():
    """Manejar solicitudes de chat a la API de Gemini."""
    data = request.json
    user_message = data.get('message', '')
    session_id = data.get('session_id', '')
    
    # Si no hay session_id, crear uno nuevo
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Inicializar historial de chat si es nuevo
    if session_id not in chat_histories:
        chat_histories[session_id] = []
    
    # Añadir mensaje del usuario al historial
    chat_histories[session_id].append({"role": "user", "parts": [user_message]})
    
    # Crear un prompt que incluya el contenido del texto y la pregunta del usuario
    system_prompt = f"""
    Eres un asistente que ayuda a los usuarios a entender el contenido de un archivo de texto.
    El archivo de texto contiene el siguiente contenido:
    
    {TEXT_CONTENT}
    
    Por favor, proporciona respuestas útiles, precisas y concisas basadas únicamente en la información del archivo de texto.
    Si la respuesta no se encuentra en el archivo de texto, indícalo claramente.
    
    IMPORTANTE: Para cada punto en tu respuesta, incluye una cita a la sección específica con su número
    en el archivo de texto donde se encuentra la información. Formatea las citas como [Subsección: X.X NOMBRE DE SECCIÓN - X.X.X NOMBRE DE SUBSECCIÓN] 
    donde X.X es el número de sección y X.X.X es el número de subsección. Siempre incluye los números de sección/subsección 
    y usa los nombres exactos de sección y subsección tal como aparecen en el documento.
    """
    
    try:
        # Iniciar chat con historial
        chat = model.start_chat(history=[])
        
        # Añadir mensaje del sistema como primer mensaje para establecer el contexto
        chat.send_message(system_prompt)
        
        # Enviar los mensajes anteriores para mantener el contexto de la conversación
        # No enviamos el primer mensaje (sistema) al historial visible para el usuario
        for message in chat_histories[session_id][:-1]:  # Todos menos el último que ya añadimos
            response = chat.send_message(message["parts"][0])
        
        # Enviar el mensaje actual del usuario
        response = chat.send_message(user_message)
        
        # Añadir respuesta del modelo al historial
        chat_histories[session_id].append({"role": "model", "parts": [response.text]})
        
        # Limitar el historial a las últimas 10 interacciones (5 del usuario, 5 del modelo)
        if len(chat_histories[session_id]) > 10:
            chat_histories[session_id] = chat_histories[session_id][-10:]
        
        # Convertir markdown a HTML si está presente en la respuesta
        response_text = response.text
        if '```' in response_text or '#' in response_text:
            response_text = markdown.markdown(response_text)
            
        return jsonify({"response": response_text, "session_id": session_id})
    except Exception as e:
        error_message = str(e)
        print(f"Error al generar contenido: {error_message}")
        
        # Si el error está relacionado con el modelo no encontrado, proporcionar información más útil
        if "not found" in error_message.lower() or "not supported" in error_message.lower() or "deprecated" in error_message.lower():
            try:
                available_models = [model.name for model in genai.list_models()]
                error_message += f"\n\nModelos disponibles: {', '.join(available_models)}"
            except Exception as list_error:
                error_message += f"\n\nNo se pudieron listar los modelos disponibles: {str(list_error)}"
        
        return jsonify({"error": error_message, "session_id": session_id}), 500

if __name__ == '__main__':
    app.run(debug=True) 