import os
import google.generativeai as genai
import markdown
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("API key not found. Please set the GEMINI_API_KEY environment variable in the .env file.")

genai.configure(api_key=api_key)

# Try to get available models
try:
    available_models = [model.name for model in genai.list_models()]
    print("Available models:", available_models)
    
    # Preferred models in order of preference
    preferred_models = [
        "models/gemini-2.0-flash",
        "models/gemini-1.5-flash",
        "models/gemini-1.5-pro",
        "models/gemini-1.5-flash-latest",
        "models/gemini-1.5-pro-latest"
    ]
    
    # Find the first preferred model that is available
    model_name = None
    for preferred in preferred_models:
        if preferred in available_models:
            model_name = preferred
            print(f"Using preferred model: {model_name}")
            break
    
    # If none of the preferred models is available, use any Gemini model without vision
    if not model_name:
        for model in available_models:
            if "gemini" in model.lower() and "vision" not in model.lower():
                model_name = model
                print(f"Using available model: {model_name}")
                break
    
    # If still no model found, use a default one
    if not model_name:
        model_name = "models/gemini-2.0-flash"
        print(f"No suitable models found. Falling back to: {model_name}")
        
except Exception as e:
    print(f"Error listing models: {e}")
    # Fall back to a recommended model
    model_name = "models/gemini-2.0-flash"
    print(f"Falling back to: {model_name}")

# Initialize the model
model = genai.GenerativeModel(model_name)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24).hex())  # Required for using session

# Dictionary to store chat histories
chat_histories = {}

# Load the content of the text file
def load_text_file(file_path="board_staff_policies.txt"):
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Make the table of contents clickable
    toc_start = "TABLE OF CONTENTS"
    toc_end = "=============================================================================\n1."
    
    toc_section = content.split(toc_start)[1].split(toc_end)[0]
    clickable_toc = toc_section
    
    # Replace table of contents entries with clickable links
    # Main sections
    clickable_toc = clickable_toc.replace("1. CODE OF CONDUCT POLICY", '<a href="#section-1">1. CODE OF CONDUCT POLICY</a>')
    clickable_toc = clickable_toc.replace("2. BOARD OF TRUSTEES CODE OF CONDUCT", '<a href="#section-2">2. BOARD OF TRUSTEES CODE OF CONDUCT</a>')
    clickable_toc = clickable_toc.replace("3. CONFLICT OF INTEREST POLICY", '<a href="#section-3">3. CONFLICT OF INTEREST POLICY</a>')
    clickable_toc = clickable_toc.replace("4. CONFIDENTIALITY AGREEMENT", '<a href="#section-4">4. CONFIDENTIALITY AGREEMENT</a>')
    clickable_toc = clickable_toc.replace("5. FINANCIAL POLICIES", '<a href="#section-5">5. FINANCIAL POLICIES</a>')
    clickable_toc = clickable_toc.replace("6. OPERATIONAL POLICIES", '<a href="#section-6">6. OPERATIONAL POLICIES</a>')
    clickable_toc = clickable_toc.replace("7. COMPLIANCE POLICIES", '<a href="#section-7">7. COMPLIANCE POLICIES</a>')
    clickable_toc = clickable_toc.replace("8. TRAVEL POLICIES", '<a href="#section-8">8. TRAVEL POLICIES</a>')
    clickable_toc = clickable_toc.replace("9. WHISTLEBLOWER PROTECTION", '<a href="#section-9">9. WHISTLEBLOWER PROTECTION</a>')
    
    # Subsections (ensuring that the exact spacing and format matches)
    clickable_toc = clickable_toc.replace("   5.1 Credit Card Usage", '   <a href="#section-5-1">5.1 Credit Card Usage</a>')
    clickable_toc = clickable_toc.replace("   5.2 Delegation of Authority", '   <a href="#section-5-2">5.2 Delegation of Authority</a>')
    clickable_toc = clickable_toc.replace("   6.1 Duty Entertainment Guidelines", '   <a href="#section-6-1">6.1 Duty Entertainment Guidelines</a>')
    clickable_toc = clickable_toc.replace("   6.2 Gift Policy", '   <a href="#section-6-2">6.2 Gift Policy</a>')
    clickable_toc = clickable_toc.replace("   7.1 Anti-Corruption Policy", '   <a href="#section-7-1">7.1 Anti-Corruption Policy</a>')
    clickable_toc = clickable_toc.replace("   7.2 Non-discrimination Policy", '   <a href="#section-7-2">7.2 Non-discrimination Policy</a>')
    clickable_toc = clickable_toc.replace("   8.1 General Travel Policy", '   <a href="#section-8-1">8.1 General Travel Policy</a>')
    clickable_toc = clickable_toc.replace("   8.2 Travel Approval Process", '   <a href="#section-8-2">8.2 Travel Approval Process</a>')
    
    # Replace the original table of contents with the clickable one
    formatted_content = content.replace(toc_section, clickable_toc)
    
    return formatted_content

# Global variable to store the text content
TEXT_CONTENT = load_text_file()

@app.route('/')
def index():
    """Render the main page with the content of the text file."""
    return render_template('index.html', text_content=TEXT_CONTENT)

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat requests to the Gemini API."""
    data = request.json
    user_message = data.get('message', '')
    session_id = data.get('session_id', '')
    
    # If there's no session_id, create a new one
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Initialize chat history if new
    if session_id not in chat_histories:
        chat_histories[session_id] = []
    
    # Add user message to history
    chat_histories[session_id].append({"role": "user", "parts": [user_message]})
    
    # Create a prompt that includes the text content and the user's question
    system_prompt = f"""
    You are an assistant that helps users understand the content of a text file.
    The text file contains the following content:
    
    {TEXT_CONTENT}
    
    Please provide helpful, accurate, and concise responses based solely on the information in the text file.
    If the answer is not found in the text file, clearly indicate this.
    
    IMPORTANT: For each point in your response, include a citation to the specific section with its number
    in the text file where the information is found. Format citations as [Subsection: X.X SECTION NAME - X.X.X SUBSECTION NAME] 
    where X.X is the section number and X.X.X is the subsection number. Always include section/subsection numbers 
    and use the exact section and subsection names as they appear in the document.
    """
    
    try:
        # Start chat with history
        chat = model.start_chat(history=[])
        
        # Add system message as first message to establish context
        chat.send_message(system_prompt)
        
        # Send previous messages to maintain conversation context
        # We don't send the first message (system) to the visible history for the user
        for message in chat_histories[session_id][:-1]:  # All except the last one we already added
            response = chat.send_message(message["parts"][0])
        
        # Send current user message
        response = chat.send_message(user_message)
        
        # Add model response to history
        chat_histories[session_id].append({"role": "model", "parts": [response.text]})
        
        # Limit history to last 10 interactions (5 from user, 5 from model)
        if len(chat_histories[session_id]) > 10:
            chat_histories[session_id] = chat_histories[session_id][-10:]
        
        # Convert markdown to HTML if present in the response
        response_text = response.text
        if '```' in response_text or '#' in response_text:
            response_text = markdown.markdown(response_text)
            
        return jsonify({"response": response_text, "session_id": session_id})
    except Exception as e:
        error_message = str(e)
        print(f"Error generating content: {error_message}")
        
        # If the error is related to model not found, provide more helpful information
        if "not found" in error_message.lower() or "not supported" in error_message.lower() or "deprecated" in error_message.lower():
            try:
                available_models = [model.name for model in genai.list_models()]
                error_message += f"\n\nAvailable models: {', '.join(available_models)}"
            except Exception as list_error:
                error_message += f"\n\nCould not list available models: {str(list_error)}"
        
        return jsonify({"error": error_message, "session_id": session_id}), 500

if __name__ == '__main__':
    app.run(debug=True) 
