from flask import Flask, render_template, request, jsonify, session
import os
from openai import OpenAI
from dotenv import load_dotenv
import secrets

load_dotenv()

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

def get_openai_client():
    """Initialize OpenAI client with OpenRouter configuration"""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable not set")
    
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={
            "HTTP-Referer": os.environ.get("APP_URL", "http://localhost:5000"),
            "X-Title": "Memory Lyrics Generator"
        }
    )

def create_lyrics_prompt(user_inputs):
    """Generate comprehensive prompt for lyrics generation"""
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
10. Think step by step about the narrative arc of the song

Generate only the song lyrics with clear section labels. Do not include explanations or commentary."""

    return prompt

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
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

        prompt = create_lyrics_prompt(user_inputs)

        # Initialize client when needed
        client = get_openai_client()
        
        response = client.chat.completions.create(
            model="meta-llama/llama-3.1-8b-instruct:free",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=1500
        )

        lyrics = response.choices[0].message.content.strip()

        session['lyrics'] = lyrics
        session['user_inputs'] = user_inputs

        return jsonify({'success': True, 'redirect': '/result'})

    except Exception as e:
        return jsonify({'error': f'Generation failed: {str(e)}'}), 500

@app.route('/result')
def result():
    lyrics = session.get('lyrics', '')
    user_inputs = session.get('user_inputs', {})
    
    if not lyrics:
        return render_template('index.html')
    
    return render_template('result.html', lyrics=lyrics, inputs=user_inputs)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
