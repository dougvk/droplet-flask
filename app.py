import os
import re

from anthropic import Anthropic
from flask import Flask, jsonify, request
from flask_cors import CORS
import whisper
import yt_dlp

app = Flask(__name__)
CORS(app)
def sanitize_filename(title):
    sanitized = re.sub(r'[^\w\-_\. ]', '', title)
    return sanitized[:50].strip()
def download_audio(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': {
            'default': '%(title)s.%(ext)s'
        },
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info['title']
        sanitized_title = sanitize_filename(title)
        ydl_opts['outtmpl']['default'] = f'{sanitized_title}.%(ext)s'
        ydl.download([url])
        return f"{sanitized_title}.mp3"
def transcribe_audio(audio_file):
    model = whisper.load_model("tiny")
    result = model.transcribe(audio_file)
    return result["text"]
def save_transcription(text, filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)
def generate_summary(text, custom_prompt):
    anthropic = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    message = anthropic.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=3000,
        messages=[
            {
                "role": "user",
                "content": f"{custom_prompt}\n\n{text}"
            }
        ]
    )
    return message.content[0].text
def save_summary(summary, filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(summary)
@app.route('/api/hello')
def hello():
    return {"message": "Hello from Flask!"}
@app.route('/process', methods=['POST'])
def process():
    data = request.json
    input_type = data['inputType']
    content = data['content']
    custom_prompt = data.get('customPrompt', "Please provide a concise summary of the following transcription:")
    if input_type == 'youtube':
        audio_filename = download_audio(content)
        transcription = transcribe_audio(audio_filename)
        text_filename = os.path.splitext(audio_filename)[0] + ".txt"
        save_transcription(transcription, text_filename)
    elif input_type == 'transcription':
        transcription = content
    else:
        return jsonify({"error": "Invalid input type"}), 400
    summary = generate_summary(transcription, custom_prompt)
    summary_filename = "summary.txt"
    save_summary(summary, summary_filename)
    return jsonify({
        "transcription": transcription,
        "summary": summary
    })
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)