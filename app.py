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
            "X-Title": "Memory Lyrics Generator"
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

def create_form_prompt(user_inputs):
    """Generate prompt from form data"""
    avoid_cliches = user_inputs.get('avoid_cliches', [])
    if isinstance(avoid_cliches, str):
        avoid_cliches = [avoid_cliches]
    
    prompt = f"""You are an expert songwriter and lyricist. Generate creative, emotionally resonant song lyrics based on the following details:

**Memory/Story**: {user_inputs['memory']}
**Main Emotion**: {user_inputs['emotion']}
**Genre**: {user_inputs['genre']}
**Tempo**: {user_inputs['tempo']}
**Perspective**: {user_inputs['perspective']}
**Mood**: {user_inputs['mood']}
**Structure**: {user_inputs['structure']}
**Length**: {user_inputs['length']}
**Special Phrases to Include**: {user_inputs.get('special_phrases', 'None')}
**Song is for/about**: {user_inputs['song_for']}
**Tone**: {user_inputs['tone']}
**Avoid Clichés**: {', '.join(avoid_cliches) if avoid_cliches else 'No specific restrictions'}

**Instructions**:
1. Create authentic, original lyrics that capture the essence of this memory
2. Use vivid imagery and sensory details
3. Ensure the lyrics match the specified genre, mood, and tone
4. Follow the requested song structure (clearly label: [Verse 1], [Chorus], [Verse 2], [Bridge], etc.)
5. Make the lyrics personal and emotionally resonant
6. Incorporate any requested special phrases naturally
7. Avoid the specified clichés and overused expressions
8. Use varied rhyme schemes appropriate to the genre
9. Keep the language authentic to the emotional truth of the memory

Generate only the song lyrics with clear section labels. Do not include explanations or commentary."""

    return prompt

@app.route('/')
def index():
    """Homepage with mode selection"""
    return render_template('index.html')

@app.route('/form')
def form_mode():
    """Form-based lyrics generation"""
    return render_template('form.html')

@app.route('/chat')
def chat_mode():
    """Chatbot-based lyrics generation"""
    return render_template('chat.html')

@app.route('/generate-form', methods=['POST'])
def generate_form():
    """Handle form submission"""
    try:
        user_inputs = {
            'memory': request.form.get('memory', '').strip(),
            'emotion': request.form.get('emotion', ''),
            'genre': request.form.get('genre', ''),
            'tempo': request.form.get('tempo', ''),
            'perspective': request.form.get('perspective', ''),
            'mood': request.form.get('mood', ''),
            'structure': request.form.get('structure', ''),
            'length': request.form.get('length', ''),
            'special_phrases': request.form.get('special_phrases', '').strip(),
            'song_for': request.form.get('song_for', ''),
            'tone': request.form.get('tone', ''),
            'avoid_cliches': request.form.getlist('avoid_cliches')
        }

        if not user_inputs['memory']:
            return jsonify({'error': 'Please describe your memory'}), 400

        prompt = create_form_prompt(user_inputs)
        
        # Call API with single message
        lyrics = call_openrouter_api([
            {"role": "user", "content": prompt}
        ])

        session['lyrics'] = lyrics
        session['user_inputs'] = user_inputs

        return jsonify({'success': True, 'redirect': '/result'})

    except Exception as e:
        return jsonify({'error': f'Generation failed: {str(e)}'}), 500

@app.route('/chat-message', methods=['POST'])
def chat_message():
    """Handle chat messages"""
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

    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/clear', methods=['POST'])
def clear_conversation():
    """Clear conversation history"""
    session.pop('conversation', None)
    return jsonify({'success': True, 'message': 'Conversation cleared'})

@app.route('/result')
def result():
    """Display generated lyrics"""
    lyrics = session.get('lyrics', '')
    user_inputs = session.get('user_inputs', {})
    
    if not lyrics:
        return render_template('index.html')
    
    return render_template('result.html', lyrics=lyrics, inputs=user_inputs)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
