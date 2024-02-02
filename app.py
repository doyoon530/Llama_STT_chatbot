from flask import Flask, render_template, request, jsonify
from google.cloud import speech
import os

app = Flask(__name__)

# Google Cloud Speech 클라이언트 초기화
client = speech.SpeechClient()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    if not os.path.exists('uploads'):
        os.makedirs('uploads')

    if 'audio' in request.files:
        audio_file = request.files['audio']
        file_path = os.path.join('uploads', audio_file.filename)
        audio_file.save(file_path)

        with open(file_path, "rb") as audio:
            content = audio.read()
        audio = speech.RecognitionAudio(content=content)
        
        # 인코딩과 샘플 레이트를 생략하여 API가 자동으로 감지하도록 합니다.
        config = speech.RecognitionConfig(
            language_code="ko-KR",
            enable_automatic_punctuation=True
        )

        try:
            response = client.recognize(config=config, audio=audio)
            results = [result.alternatives[0].transcript for result in response.results]
            user_input = " ".join(results)
        except Exception as e:
            print(f"음성 인식 실패: {e}")
            return jsonify({'error': '음성 인식 중 문제가 발생했습니다.'}), 500
    else:
        user_input = request.json.get('message', '')

    return jsonify({'response': user_input})

if __name__ == '__main__':
    app.run(debug=True)
