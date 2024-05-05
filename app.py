import aiohttp
from flask import Flask, request, jsonify
from pyarabic import araby
from pyarabic.araby import strip_tashkeel
import difflib
from pyarabic.araby import strip_lastharaka

API_URL = "https://api-inference.huggingface.co/models/tarteel-ai/whisper-base-ar-quran"
HEADERS = {"Authorization": "Bearer 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"}


app = Flask(__name__)


def get_different_characters(quran, user):
    word1 = strip_tashkeel(quran)
    word2 = strip_tashkeel(user)


    differ = difflib.ndiff(word1, word2)
    different_chars = [char[2] for char in differ if char[0] != ' ']
    count = len(different_chars)
   
    return count, different_chars

from pyarabic import araby

def find_different_tashkeel(word1, word2):
   
    different_tashkeel = []
    # يقارن كل حرف في الكلمتين مع حركته
    letters1, marks1 = araby.separate(word1)
    letters2, marks2 = araby.separate(word2)
    for letter1, mark1, letter2, mark2 in zip(letters1, marks1, letters2, marks2):
        
        if letter1 != letter2 or mark1 != mark2 :
            different_tashkeel.append(letter1 + mark1)
    
    return different_tashkeel

def compare_quran_texts(quranText, userText):
    different_words = []
    different_wordsintashkeel = []
    different_wordsinONeCharacter = []
   
    q=strip_lastharaka(quranText)
    quranTexttokenize = araby.tokenize(quranText)
    userTexttokenize = araby.tokenize(userText)


    for quran, user in zip(quranTexttokenize, userTexttokenize):

        
        if not araby.vocalizedlike(quran, user):
            quranwithoutTashkeel = strip_tashkeel(quran)
            userwithoutTashkeel = strip_tashkeel(user)

            if araby.vocalizedlike(quranwithoutTashkeel, userwithoutTashkeel):
                if quran == quranTexttokenize[-1] and user == userTexttokenize[-1]:
                  different_tashkeel= find_different_tashkeel(strip_lastharaka(quran),strip_lastharaka(user))
                else:
                 different_tashkeel= find_different_tashkeel(quran,user) 
                different_wordsintashkeel.append((quran, user,different_tashkeel))
            else:
                difference_count, different_chars = get_different_characters(quran, user)
                if difference_count < 3:
                    different_wordsinONeCharacter.append((quran, user,different_chars))
                else:
                    different_words.append((quran, user))
           
    different_words_result = []
    different_wordsintashkeel_result = []
    different_wordsinONeCharacter_result = []
   
    for word_pair in different_words:
        different_words_result.append({
            'quran_word': word_pair[0],
            'user_word': word_pair[1]
        })


    for word_pair in different_wordsintashkeel:
        different_wordsintashkeel_result.append({
            'quran_word': word_pair[0],
            'user_word': word_pair[1],
            'different_wordsintashkeel': word_pair[2]
        })


    for word_pair in different_wordsinONeCharacter:
        different_wordsinONeCharacter_result.append({
            'quran_word': word_pair[0],
            'user_word': word_pair[1],
            'different_chars': word_pair[2]
        })


    return {
        'quranText': quranText,
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
       
        comparison_result = compare_quran_texts(quran_text, result)
   
        return jsonify({'text': comparison_result})


    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)