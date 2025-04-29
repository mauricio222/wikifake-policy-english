# Wikifake Policies - Spanish Chat Assistant

A Flask web application that uses Google's Gemini AI to answer questions about specific policies in Spanish. The application loads content from a text file containing policies and provides a chat interface for users to ask questions.

## Features

- Interactive chat interface for policy questions
- Uses Google's Gemini AI for generating responses
- Automatically references specific policy sections in responses
- Handles conversation history for context-aware answers

## Setup

1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
```

2. Set up a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and add your Gemini API key
```bash
cp .env.example .env
# Edit .env with your text editor and add your API key
```

5. Run the application
```bash
python app.py
```

6. Open your browser and navigate to `http://127.0.0.1:5000`

## Environment Variables

- `GEMINI_API_KEY`: Your Google Gemini API key
- `SECRET_KEY`: Secret key for Flask sessions

## License

This project is licensed under the MIT License - see the LICENSE file for details. 