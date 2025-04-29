document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    
    // Variable para almacenar el ID de sesión
    let sessionId = localStorage.getItem('chat_session_id') || '';
    
    // Función para ajustar automáticamente el tamaño del área de texto según su contenido
    function autoResizeTextarea() {
        // Restablecer la altura a automático para obtener el scrollHeight correcto
        userInput.style.height = 'auto';
        
        // Establecer la altura para que coincida con el contenido (con una altura máxima aplicada vía CSS)
        userInput.style.height = (userInput.scrollHeight) + 'px';
    }
    
    // Inicializar la altura del área de texto
    autoResizeTextarea();
    
    // Agregar escuchador de eventos para redimensionar mientras el usuario escribe
    userInput.addEventListener('input', autoResizeTextarea);
    
    // Función para añadir un mensaje al chat
    function addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', type);
        
        // Comprobar si el contenido es HTML (de conversión markdown)
        if (content.startsWith('<')) {
            messageDiv.innerHTML = content;
        } else {
            messageDiv.textContent = content;
        }
        
        chatMessages.appendChild(messageDiv);
        
        // Desplazarse hasta el final del chat
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Función para enviar un mensaje a la API
    async function sendMessage(message) {
        // Añadir mensaje del usuario al chat
        addMessage(message, 'user');
        
        // Añadir indicador de carga
        const loadingDiv = document.createElement('div');
        loadingDiv.classList.add('message', 'bot', 'loading');
        loadingDiv.textContent = 'Pensando...';
        chatMessages.appendChild(loadingDiv);
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    message, 
                    session_id: sessionId 
                })
            });
            
            const data = await response.json();
            
            // Almacenar el ID de sesión recibido
            if (data.session_id) {
                sessionId = data.session_id;
                localStorage.setItem('chat_session_id', sessionId);
            }
            
            // Eliminar indicador de carga
            chatMessages.removeChild(loadingDiv);
            
            if (data.error) {
                addMessage(`Error: ${data.error}`, 'system');
            } else {
                addMessage(data.response, 'bot');
            }
        } catch (error) {
            // Eliminar indicador de carga
            chatMessages.removeChild(loadingDiv);
            
            addMessage(`Error: ${error.message}`, 'system');
        }
    }
    
    // Función para manejar el envío del mensaje y restablecer el área de texto
    function handleSendMessage() {
        const message = userInput.value.trim();
        if (message) {
            sendMessage(message);
            userInput.value = '';
            // Restablecer la altura del área de texto después de limpiarlo
            userInput.style.height = 'auto';
            userInput.style.height = userInput.scrollHeight + 'px';
        }
    }
    
    // Escuchador de eventos para el botón de enviar
    sendButton.addEventListener('click', handleSendMessage);
    
    // Escuchador de eventos para la tecla Enter (pero permitir Shift+Enter para nuevas líneas)
    userInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault(); // Prevenir el comportamiento predeterminado para evitar añadir una nueva línea
            handleSendMessage();
        }
    });
    
    // Enfocar el campo de entrada cuando se carga la página
    userInput.focus();
});

// Manejar enlaces de la tabla de contenidos
document.addEventListener('DOMContentLoaded', function() {
    const textContent = document.querySelector('.text-content');
    
    // Añadir escuchador de eventos de clic al área de contenido de texto para delegación
    textContent.addEventListener('click', function(e) {
        // Comprobar si el elemento clicado es un enlace de TOC
        if (e.target.tagName === 'A' && e.target.getAttribute('href').startsWith('#section-')) {
            e.preventDefault();
            
            // Extraer el ID de sección del href
            const sectionId = e.target.getAttribute('href').substring(1);
            
            // Encontrar el texto de sección correspondiente según el ID
            let searchText;
            
            // Mapa de secciones para simplificar la lógica
            const sectionMap = {
                'section-1': "1. POLÍTICA DE CÓDIGO DE CONDUCTA",
                'section-2': "2. CÓDIGO DE CONDUCTA PARA LA JUNTA DE FIDEICOMISARIOS",
                'section-3': "3. POLÍTICA DE CONFLICTO DE INTERESES",
                'section-4': "4. ACUERDO DE CONFIDENCIALIDAD",
                'section-5': "5. POLÍTICAS FINANCIERAS",
                'section-6': "6. POLÍTICAS OPERATIVAS",
                'section-7': "7. POLÍTICAS DE CUMPLIMIENTO",
                'section-8': "8. POLÍTICAS DE VIAJE", 
                'section-9': "9. PROTECCIÓN DE DENUNCIANTES",
                'section-5-1': "5.1 POLÍTICA DE USO DE TARJETAS DE CRÉDITO",
                'section-5-2': "5.2 POLÍTICA DE DELEGACIÓN DE AUTORIDAD",
                'section-6-1': "6.1 POLÍTICA DE DIRECTRICES PARA GASTOS DE REPRESENTACIÓN",
                'section-6-2': "6.2 POLÍTICA DE REGALOS",
                'section-7-1': "7.1 POLÍTICA ANTICORRUPCIÓN",
                'section-7-2': "7.2 POLÍTICA DE NO DISCRIMINACIÓN",
                'section-8-1': "8.1 POLÍTICA GENERAL DE VIAJES",
                'section-8-2': "8.2 PROCESO DE APROBACIÓN DE VIAJES"
            };
            
            // Alternativas para diferentes formatos de texto en el documento
            const sectionAlternatives = {
                'section-5-1': ["5.1 USO DE TARJETAS DE CRÉDITO", "5.1 POLÍTICA DE USO DE TARJETAS DE CRÉDITO (adoptada"],
                'section-5-2': ["5.2 DELEGACIÓN DE AUTORIDAD", "5.2 POLÍTICA DE DELEGACIÓN DE AUTORIDAD"]
            };
            
            // Obtener el texto de búsqueda primario
            searchText = sectionMap[sectionId];
            
            if (searchText) {
                // Obtener el contenido completo del documento
                const preElement = textContent.querySelector('pre');
                const text = preElement.textContent;
                
                // Patrones de búsqueda en orden de preferencia
                const searchPatterns = [
                    // Patrón 1: Línea separadora + título de sección
                    "=============================================================================\n" + searchText,
                    // Patrón 2: Solo el título de sección
                    searchText,
                    // Patrón 3: Para secciones con formato especial (5.1, 5.2, etc.)
                    ...(sectionAlternatives[sectionId] || [])
                ];
                
                // Buscar la sección usando los patrones en orden
                let foundIndex = -1;
                for (const pattern of searchPatterns) {
                    const index = text.indexOf(pattern);
                    if (index !== -1) {
                        foundIndex = index;
                        break;
                    }
                }
                
                // Si encontramos la sección, desplazarse a ella
                if (foundIndex !== -1) {
                    // Calcular posición aproximada
                    const lines = text.substring(0, foundIndex).split('\n');
                    const lineHeight = 22; // Altura de línea aproximada en píxeles
                    const scrollPosition = lines.length * lineHeight;
                    
                    // Desplazarse a la posición con un pequeño offset para contexto
                    textContent.scrollTop = scrollPosition - 50;
                    
                    // Resaltar brevemente la sección encontrada para que sea más fácil de identificar
                    highlightSection(preElement, foundIndex, searchText.length);
                } else {
                    console.error(`No se pudo encontrar la sección: ${searchText}`);
                }
            }
        }
    });
    
    // Función para resaltar temporalmente una sección
    function highlightSection(element, startIndex, length) {
        // Crear un rango para seleccionar el texto
        const range = document.createRange();
        const textNode = element.firstChild;
        
        // Solo intentar seleccionar si existe el nodo de texto
        if (textNode && textNode.nodeType === Node.TEXT_NODE) {
            try {
                // Seleccionar el texto y aplicar un estilo de resaltado
                const tempSpan = document.createElement('span');
                tempSpan.style.backgroundColor = '#ffff99';
                tempSpan.style.transition = 'background-color 2s ease';
                
                // Intentar ubicar la posición exacta si es posible
                // (esto es aproximado y puede necesitar ajustes)
                range.setStart(textNode, startIndex);
                range.setEnd(textNode, startIndex + length);
                
                // Envolver el texto seleccionado
                range.surroundContents(tempSpan);
                
                // Quitar el resaltado después de 2 segundos
                setTimeout(() => {
                    tempSpan.style.backgroundColor = 'transparent';
                    // Después de la transición, restaurar el texto normal
                    setTimeout(() => {
                        const parent = tempSpan.parentNode;
                        while (tempSpan.firstChild) {
                            parent.insertBefore(tempSpan.firstChild, tempSpan);
                        }
                        parent.removeChild(tempSpan);
                    }, 2000);
                }, 1000);
            } catch (e) {
                console.warn("No se pudo resaltar la sección exacta", e);
            }
        }
    }
}); 