import aiohttp
from flask import Flask, request, jsonify
from pyarabic import araby
from pyarabic.araby import strip_tashkeel
import difflib
from pyarabic.araby import strip_lastharaka

API_URL = "https://api-inference.huggingface.co/models/tarteel-ai/whisper-base-ar-quran"
HEADERS = {"Authorization": "Bearer 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"}

app = Flask(__name__)

def find_different_tashkeel(word1, word2):
    different_tashkeel = []
    letters1, marks1 = araby.separate(word1)
    letters2, marks2 = araby.separate(word2)
    for letter1, mark1, letter2, mark2 in zip(letters1, marks1, letters2, marks2):
        if letter1 != letter2 or mark1 != mark2:
            different_tashkeel.append(letter1 + mark1)
    
    return different_tashkeel

def get_different_characters(quran, user):
    word1 = strip_tashkeel(quran)
    word2 = strip_tashkeel(user)

    differ = difflib.ndiff(word1, word2)
    different_chars = [char[2] for char in differ if char[0] != ' ']
    count = len(different_chars)
    return count, different_chars

def compare_texts(quran_text, user_text):
    quran_words = quran_text.split()
    user_words = user_text.split()
    result = []
    different_words_result = []
    different_wordsintashkeel_result = []
    different_wordsinONeCharacter_result= []
    flag=False
    for q_word in quran_words:
        flag=False
        for u_word in user_words:
            difference_count, different_chars = get_different_characters(q_word, u_word)
            if difference_count < 3:
                if q_word == quran_words[-1] and u_word == user_words[-1]:
                    tashkeel= find_different_tashkeel(strip_lastharaka(q_word),strip_lastharaka(u_word))
                else:
                     tashkeel=find_different_tashkeel(q_word, u_word)
                if different_chars:
                   different_wordsinONeCharacter_result.append((q_word,different_chars)) 
                if tashkeel:       
                    different_wordsintashkeel_result.append((q_word,tashkeel))
                flag=True
                break
        if(flag==False):
            different_words_result.append(q_word)        
    return {
        'quranText': quran_text,
        'different_words': different_words_result,
        'different_wordsintashkeel': different_wordsintashkeel_result,
        'different_wordsinONeCharacter': different_wordsinONeCharacter_result
    }

async def query(filename):
    async with aiohttp.ClientSession() as session:
        data = filename.read()
        async with session.post(API_URL, headers=HEADERS, data=data) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Failed to query API, status code: {response.status}")


async def convert_speech_to_text(filename):
    response = await query(filename)
    if response and "text" in response:
        return response["text"]
    else:
        raise Exception("Text not found in API response")


@app.route('/process-audio', methods=['POST'])
async def process_audio():
    try:
        if 'audioFile' not in request.files:
            return jsonify({'error': 'No audio file uploaded'}), 400


        audio_file = request.files['audioFile']
        result = await convert_speech_to_text(audio_file)
       
        if 'quranText' not in request.form:
            return jsonify({'error': 'No Quran text provided in the request'}), 400
       
        quran_text = request.form['quranText']
       
        comparison_result = compare_texts(quran_text, result)
   
        return jsonify({'text': comparison_result})


    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)

