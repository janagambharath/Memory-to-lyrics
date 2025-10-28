from flask import Flask, render_template, request, jsonify, session
import os
import requests
import json
from dotenv import load_dotenv
import secrets
import traceback
import time

load_dotenv()

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Configure session
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# Language configurations
LANGUAGES = {
    'english': {
        'name': 'English',
        'code': 'en',
        'flag': '🇬🇧'
    },
    'telugu': {
        'name': 'తెలుగు',
        'code': 'te',
        'flag': '🇮🇳'
    },
    'hindi': {
        'name': 'हिंदी',
        'code': 'hi',
        'flag': '🇮🇳'
    }
}

def call_openrouter_api(messages, max_retries=2):
    """Call OpenRouter API with conversation history"""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not configured. Please check your .env file.")

    for attempt in range(max_retries):
        try:
            print(f"API Call Attempt {attempt + 1}/{max_retries}")
            print(f"Sending {len(messages)} messages to API")
            
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": os.environ.get("APP_URL", "http://localhost:5000"),
                    "X-Title": "Memory Lyrics Generator"
                },
                json={
                    "model": "meta-llama/llama-3.3-70b-instruct:free",
                    "messages": messages,
                    "temperature": 0.8,
                    "max_tokens": 2000
                },
                timeout=90  # Increased timeout to 90 seconds
            )

            print(f"API Response Status: {response.status_code}")

            if response.status_code == 200:
                response_data = response.json()
                content = response_data['choices'][0]['message']['content'].strip()
                print(f"API Response received: {len(content)} characters")
                return content
            
            # Handle specific error codes
            elif response.status_code == 502:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"502 error, retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise Exception("The AI service is temporarily unavailable. Please try again in a moment.")
            
            elif response.status_code == 429:
                raise Exception("Rate limit reached. Please wait a moment and try again.")
            
            elif response.status_code == 401:
                raise Exception("API key is invalid. Please check your configuration.")
            
            else:
                error_msg = f"API Error {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', error_msg)
                except:
                    error_msg = f"API returned status {response.status_code}"
                raise Exception(error_msg)
        
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                print(f"Timeout, retrying...")
                time.sleep(2)
                continue
            else:
                raise Exception("Request timed out. The AI service is taking too long. Please try again.")
        
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                print(f"Connection error, retrying...")
                time.sleep(2)
                continue
            else:
                raise Exception("Cannot connect to AI service. Please check your internet connection.")
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
    
    raise Exception("Failed to get response from AI service after multiple attempts.")

def create_form_prompt(user_inputs):
    """Generate prompt from form data with language support"""
    avoid_cliches = user_inputs.get('avoid_cliches', [])
    if isinstance(avoid_cliches, str):
        avoid_cliches = [avoid_cliches]
    
    language = user_inputs.get('language', 'english')
    language_name = LANGUAGES.get(language, {}).get('name', 'English')
    
    # Language-specific instructions
    language_instructions = ""
    if language == 'telugu':
        language_instructions = """
**IMPORTANT - TELUGU LANGUAGE REQUIREMENTS**:
- Generate lyrics ENTIRELY in Telugu script (తెలుగు)
- Use authentic Telugu poetic expressions and idioms
- Follow Telugu song writing traditions (పద్యాలు, చరణాలు)
- Use proper Telugu grammar and vocabulary
- Maintain natural Telugu rhythm and meter
- Keep section labels in English: [Verse 1], [Chorus], [Bridge], etc.
"""
    elif language == 'hindi':
        language_instructions = """
**IMPORTANT - HINDI LANGUAGE REQUIREMENTS**:
- Generate lyrics ENTIRELY in Hindi script (हिंदी)
- Use authentic Hindi poetic expressions and shayari style
- Follow Hindi/Urdu song writing traditions
- Use proper Hindi grammar and vocabulary (can include Urdu words naturally)
- Maintain natural Hindi rhythm and meter
- Keep section labels in English: [Verse 1], [Chorus], [Bridge], etc.
"""
    
    prompt = f"""You are an expert songwriter and lyricist specializing in {language_name} songs. Generate creative, emotionally resonant song lyrics based on the following details:

**Target Language**: {language_name}
{language_instructions}

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
1. Create authentic, original lyrics in {language_name} that capture the essence of this memory
2. Use vivid imagery and sensory details appropriate to the language
3. Ensure the lyrics match the specified genre, mood, and tone
4. Follow the requested song structure (clearly label: [Verse 1], [Chorus], [Verse 2], [Bridge], etc.)
5. Make the lyrics personal and emotionally resonant
6. Incorporate any requested special phrases naturally
7. Avoid the specified clichés and overused expressions
8. Use varied rhyme schemes appropriate to the genre and language
9. Keep the language authentic to the emotional truth of the memory
10. Use cultural references and expressions native to {language_name} speakers

Generate only the song lyrics with clear section labels in English. Do not include explanations or commentary."""

    return prompt

def create_chat_system_prompt(language='english'):
    """Create system prompt for chat mode with language support"""
    language_name = LANGUAGES.get(language, {}).get('name', 'English')
    
    language_instructions = ""
    if language == 'telugu':
        language_instructions = """
When generating lyrics, write ENTIRELY in Telugu script (తెలుగు). Use authentic Telugu expressions, poetic traditions, and maintain natural Telugu rhythm. Keep section labels like [Verse 1], [Chorus] in English for clarity.
"""
    elif language == 'hindi':
        language_instructions = """
When generating lyrics, write ENTIRELY in Hindi script (हिंदी). Use authentic Hindi/Urdu expressions, shayari style, and maintain natural Hindi rhythm. Keep section labels like [Verse 1], [Chorus] in English for clarity.
"""
    
    return f"""You are a creative and empathetic AI songwriter assistant specializing in {language_name} songs. Your job is to help users transform their memories and stories into beautiful song lyrics in {language_name}.

Guidelines:
1. Have a natural, friendly conversation to understand their memory
2. Ask thoughtful questions about emotions, details, and what makes the memory special
3. Inquire about their music preferences (genre, mood, tempo, perspective)
4. Once you have enough information, generate creative, emotionally resonant lyrics in {language_name}
5. Be warm, encouraging, and make the process feel personal
6. Format lyrics with clear sections like [Verse 1], [Chorus], [Bridge], etc.
7. Use vivid imagery and sensory details
8. Create authentic, original content that captures the essence of their memory

{language_instructions}

Start by warmly greeting the user and asking them about a memory they'd like to turn into a song."""

@app.route('/')
def index():
    """Homepage with mode selection"""
    return render_template('index.html', languages=LANGUAGES)

@app.route('/form')
def form_mode():
    """Form-based lyrics generation"""
    return render_template('form.html', languages=LANGUAGES)

@app.route('/chat')
def chat_mode():
    """Chatbot-based lyrics generation"""
    return render_template('chat.html', languages=LANGUAGES)

@app.route('/generate-form', methods=['POST'])
def generate_form():
    """Handle form submission"""
    try:
        print("=== Form Submission Received ===")
        
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
            'avoid_cliches': request.form.getlist('avoid_cliches'),
            'language': request.form.get('language', 'english')
        }

        print(f"Language: {user_inputs['language']}")
        print(f"Memory length: {len(user_inputs['memory'])} chars")

        # Validate required fields
        if not user_inputs['memory']:
            return jsonify({'error': 'Please describe your memory'}), 400
        
        if not user_inputs['emotion']:
            return jsonify({'error': 'Please select an emotion'}), 400
            
        if not user_inputs['genre']:
            return jsonify({'error': 'Please select a genre'}), 400

        # Create prompt
        prompt = create_form_prompt(user_inputs)
        print(f"Prompt created: {len(prompt)} chars")
        
        # Call API with single message
        print("Calling OpenRouter API...")
        lyrics = call_openrouter_api([
            {"role": "user", "content": prompt}
        ])
        
        print(f"Lyrics generated: {len(lyrics)} chars")

        # Store in session
        session['lyrics'] = lyrics
        session['user_inputs'] = user_inputs
        session.modified = True

        print("Session saved successfully")
        return jsonify({'success': True, 'redirect': '/result'}), 200

    except ValueError as ve:
        print(f"Validation Error: {str(ve)}")
        return jsonify({'error': str(ve)}), 400
    
    except Exception as e:
        print(f"Generation Error: {str(e)}")
        traceback.print_exc()
        error_message = str(e)
        
        # Provide user-friendly error messages
        if "OPENROUTER_API_KEY" in error_message:
            error_message = "API key not configured. Please contact the administrator."
        elif "timed out" in error_message.lower():
            error_message = "Request timed out. Please try again with a shorter memory description."
        elif "temporarily unavailable" in error_message.lower():
            error_message = "AI service is temporarily unavailable. Please try again in a moment."
        
        return jsonify({'error': error_message}), 500

@app.route('/chat-message', methods=['POST'])
def chat_message():
    """Handle chat messages"""
    try:
        print("=== Chat Message Received ===")
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request'}), 400
            
        user_message = data.get('message', '').strip()
        language = data.get('language', 'english')
        
        print(f"Language: {language}")
        print(f"Message length: {len(user_message)} chars")
        
        if not user_message:
            return jsonify({'error': 'Please enter a message'}), 400

        # Initialize conversation history in session if not exists
        if 'conversation' not in session or session.get('chat_language') != language:
            session['conversation'] = [
                {
                    "role": "system",
                    "content": create_chat_system_prompt(language)
                }
            ]
            session['chat_language'] = language
            session.modified = True
            print("New conversation started")

        # Add user message to conversation
        session['conversation'].append({
            "role": "user",
            "content": user_message
        })

        print(f"Conversation history: {len(session['conversation'])} messages")
        print("Calling OpenRouter API...")
        
        # Get AI response
        ai_response = call_openrouter_api(session['conversation'])
        
        print(f"AI response: {len(ai_response)} chars")

        # Add AI response to conversation
        session['conversation'].append({
            "role": "assistant",
            "content": ai_response
        })
        session.modified = True

        return jsonify({
            'success': True,
            'response': ai_response
        }), 200

    except Exception as e:
        print(f"Chat Error: {str(e)}")
        traceback.print_exc()
        error_message = str(e)
        
        # Provide user-friendly error messages
        if "OPENROUTER_API_KEY" in error_message:
            error_message = "API key not configured. Please contact the administrator."
        elif "timed out" in error_message.lower():
            error_message = "Request timed out. Please try with a shorter message."
        elif "temporarily unavailable" in error_message.lower():
            error_message = "AI service is temporarily unavailable. Please try again in a moment."
        
        return jsonify({'error': error_message}), 500

@app.route('/clear', methods=['POST'])
def clear_conversation():
    """Clear conversation history"""
    try:
        session.pop('conversation', None)
        session.pop('chat_language', None)
        session.modified = True
        return jsonify({'success': True, 'message': 'Conversation cleared'}), 200
    except Exception as e:
        print(f"Clear Error: {str(e)}")
        return jsonify({'error': 'Failed to clear conversation'}), 500

@app.route('/result')
def result():
    """Display generated lyrics"""
    lyrics = session.get('lyrics', '')
    user_inputs = session.get('user_inputs', {})
    
    if not lyrics:
        return render_template('index.html', languages=LANGUAGES)
    
    return render_template('result.html', lyrics=lyrics, inputs=user_inputs, languages=LANGUAGES)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Server is running'}), 200

if __name__ == '__main__':
    # Check if API key is configured
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("WARNING: OPENROUTER_API_KEY not found in environment variables!")
        print("Please create a .env file with your API key.")
    else:
        print("API key configured successfully")
    
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)
