from flask import Flask, render_template, request, jsonify, session
import os
import requests
import json
from dotenv import load_dotenv
import secrets

load_dotenv()

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

def call_openrouter_api(messages):
    """Call OpenRouter API with conversation history"""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not configured")

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": os.environ.get("APP_URL", "http://localhost:5000"),
            "X-Title": "Memory Lyrics Chatbot"
        },
        data=json.dumps({
            "model": "meta-llama/llama-3.3-70b-instruct:free",
            "messages": messages,
            "temperature": 0.8,
            "max_tokens": 2000
        }),
        timeout=60
    )

    if response.status_code != 200:
        error_msg = f"API Error: {response.status_code}"
        try:
            error_data = response.json()
            error_msg = error_data.get('error', {}).get('message', error_msg)
        except:
            pass
        raise Exception(error_msg)

    response_data = response.json()
    return response_data['choices'][0]['message']['content'].strip()

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Please enter a message'}), 400

        # Initialize conversation history in session if not exists
        if 'conversation' not in session:
            session['conversation'] = [
                {
                    "role": "system",
                    "content": """You are a creative and empathetic AI songwriter assistant. Your job is to help users transform their memories and stories into beautiful song lyrics.

Guidelines:
1. Have a natural, friendly conversation to understand their memory
2. Ask thoughtful questions about emotions, details, and what makes the memory special
3. Inquire about their music preferences (genre, mood, tempo, perspective)
4. Once you have enough information, generate creative, emotionally resonant lyrics
5. Be warm, encouraging, and make the process feel personal
6. Format lyrics with clear sections like [Verse 1], [Chorus], [Bridge], etc.
7. Use vivid imagery and sensory details
8. Create authentic, original content that captures the essence of their memory

Start by warmly greeting the user and asking them about a memory they'd like to turn into a song."""
                }
            ]
            session.modified = True

        # Add user message to conversation
        session['conversation'].append({
            "role": "user",
            "content": user_message
        })

        # Get AI response
        ai_response = call_openrouter_api(session['conversation'])

        # Add AI response to conversation
        session['conversation'].append({
            "role": "assistant",
            "content": ai_response
        })
        session.modified = True

        return jsonify({
            'success': True,
            'response': ai_response
        })

    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request timed out. Please try again.'}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/clear', methods=['POST'])
def clear_conversation():
    """Clear conversation history"""
    session.pop('conversation', None)
    return jsonify({'success': True, 'message': 'Conversation cleared'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
