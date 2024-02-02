from flask import Flask, render_template, request, jsonify
from google.cloud import speech
import os
import requests
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms import LlamaCpp

callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are a helpful assistant designed to provide concise answers directly without any prefixes such as 'Assistant:'. 
            Your responses should be brief, aiming for 1 to 3 sentences whenever possible. 
            Focus on delivering the most direct answer to the question provided, starting immediately with the answer.
            """
        ),
        ("human", "Question: {question}"),
    ]
)

llm_model_path = "models/llama-2-7b-chat.Q2_K.gguf"
absolute_model_path = os.path.abspath(llm_model_path)
# 절대 경로 출력
print(f"Absolute Model Path: {absolute_model_path}")
llm = LlamaCpp(
    model_path=llm_model_path,
    temperature=0.7,  # 다양성을 증가시킵니다.
    top_p=1,  # 가능한 경우 모든 토큰을 고려합니다. 필요에 따라 조정하세요.
    max_tokens=256,  # 대부분의 대화 응답에 적합한 값을 사용합니다.
    verbose=True,
    n_ctx=4096  # 모델의 최대 컨텍스트 길이에 맞게 설정하세요.
)

app = Flask(__name__)

# Google Cloud Speech 클라이언트 초기화
client = speech.SpeechClient()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    response_text = ''
    
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    
    if 'audio' in request.files:
        audio_file = request.files['audio']
        file_path = os.path.join('uploads', audio_file.filename)
        audio_file.save(file_path)
        
        with open(file_path, "rb") as audio:
            content = audio.read()
        audio = speech.RecognitionAudio(content=content)
        
        config = speech.RecognitionConfig(
            language_code="ko-KR",
            enable_automatic_punctuation=True
        )
        
        try:
            response = client.recognize(config=config, audio=audio)
            results = [result.alternatives[0].transcript for result in response.results]
            user_input = " ".join(results)
            print(f'\nQ. {user_input}')
            # 사용자 입력에 대해 응답을 생성
            response_text = get_response_from_llama(user_input)
            print(f'\nA. {response_text}')
        except Exception as e:
            print(f"음성 인식 실패: {e}")
            return jsonify({'error': '음성 인식 중 문제가 발생했습니다.'}), 500
    else:
        user_input = request.json.get('message', '죄송합니다 다시 말해주세요.') if request.json else ''
        if user_input:  # 사용자 입력이 있는 경우에만 처리
            response_text = get_response_from_llama(user_input)
    
    return jsonify({'user_speech': user_input, 'sys_response': response_text})

def get_response_from_llama(question):
    # Create an LLMChain instance with your LlamaCpp model
    llm_chain = LLMChain(prompt=prompt, llm=llm)

    # Generate a response from the LlamaCpp model
    response = llm_chain.invoke({"question": question})  # Adjust based on the actual method signature
    response_message=response.get('text', 'No text response')
    return response_message

if __name__ == '__main__':
    app.run(port=5000,debug=False)
