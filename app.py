from flask import Flask, request, jsonify
from pyarabic import araby
from pyarabic.araby import strip_tashkeel
import difflib
from pyarabic.araby import strip_lastharaka
from pyarabic.araby import  strip_shadda
import aiohttp


API_URL ="https://api-inference.huggingface.co/models/raghadOmar/whisper-base-quran"
HEADERS = {"Authorization": "Bearer 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"}


app = Flask(__name__)
# def find_different_tashkeel(word11, word22):
#     word1= strip_shadda(word11)
#     word2= strip_shadda(word22)
   
   


#     different_tashkeel = []
#     letters1, marks1 = araby.separate(word1)
#     letters2, marks2 = araby.separate(word2)
#     count=0
#     for letter1, mark1, letter2, mark2 in zip(letters1, marks1, letters2, marks2):
   
#         if letter1 != letter2 or mark1 != mark2:
#             different_tashkeel.append(letter1 )
#             different_tashkeel.append(count)
#         count=count+1    
#     return different_tashkeel


def find_different_tashkeel(word1, word2):
    # word1= strip_shadda(word11)
    # word2= strip_shadda(word22)
    differences = []
    min_length = min(len(word1), len(word2))
   
    for i in range(min_length):
        if word1[i] != word2[i]:
            differences.append((i, word1[i], word2[i]))
   
    if len(word1) > len(word2):
        for i in range(min_length, len(word1)):
            differences.append((i, word1[i], ''))
    elif len(word2) > len(word1):
        for i in range(min_length, len(word2)):
            differences.append((i, '', word2[i]))


    return differences
   
def get_different_characters(quran, user):
    word1 = strip_tashkeel(quran)
    word2 = strip_tashkeel(user)


    differ = list(difflib.ndiff(word1, word2))
   
    different_charsAll = []
    different_chars = []
    quran_index = 0
    user_index = 0
    for char in differ:
       
        if char[0] == ' ':  # إذا كان الحرف هو نفسه في النصين
            quran_index += 1
            user_index += 1
        elif char[0] == '-':  # إذا كان الحرف في النص القرآني فقط
            different_chars.append((quran_index, char[2]))
            different_charsAll.append((quran_index, char[2]))
            quran_index += 1
        elif char[0] == '+':  # إذا كان الحرف في النص المستخدم فقط
            different_charsAll.append((user_index, char[2]))
            user_index += 1
   
    difference_count = len(different_charsAll)
    return difference_count, different_chars,different_charsAll




def compare_texts(quran_text, user_text):
    different_words = []
    different_wordsintashkeel = []
    different_wordsinONeCharacter = []
    extraWords= []


    quran_words = quran_text.split()
    user_words = user_text.split()
   
    different_words_result = []
    different_wordsintashkeel_result = []
    different_wordsinONeCharacter_result= []


    flag=False
    user_words_copy = user_words.copy()
    print(user_words_copy)
    index=-1
    for q_word in quran_words:
        index+=1
        flag = False
        for u_word in user_words_copy:
             
         if q_word == u_word:
              flag=True
              user_words_copy.remove(u_word) 
              break
         if strip_tashkeel(q_word) == strip_tashkeel(u_word):
                 if q_word == quran_words[-1] and u_word == user_words_copy[-1]:
                    different_tashkeel = find_different_tashkeel(strip_lastharaka(q_word), strip_lastharaka(u_word))
                    flag = True
                    user_words_copy.remove(u_word)  
                    break
                 else:
                    different_tashkeel = find_different_tashkeel(q_word, u_word)
                 different_wordsintashkeel.append((q_word, different_tashkeel,u_word,index))
                 print(q_word,different_tashkeel,u_word)
                 flag = True
                 user_words_copy.remove(u_word)  
                 break

         else:
            difference_count, different_chars ,different_charsAll= get_different_characters(q_word, u_word)  
            print(difference_count, different_chars, q_word, u_word)
            if difference_count < 3 and ( abs(len(strip_tashkeel(q_word)) - len(strip_tashkeel(u_word)))<=2 ) :
                print('ok')
                
                if different_charsAll or different_chars:
                    different_wordsinONeCharacter.append((q_word, different_chars,u_word,index))
                   
                     
                flag = True
                user_words_copy.remove(u_word)  
                break
           
        if not flag:
            different_words.append((q_word,index))
 
    for word_pair in different_words:
        different_words_result.append({
            'quran_word': word_pair[0],
            'quran_index':word_pair[1]
        })




    for word_pair in different_wordsintashkeel:
        different_wordsintashkeel_result.append({
            'quran_word': word_pair[0],
            'different_charintashkeel': word_pair[1],
            'user_word':word_pair[2],
             'quran_index':word_pair[3]
        })




    for word_pair in different_wordsinONeCharacter:
        different_wordsinONeCharacter_result.append({
            'quran_word': word_pair[0],
            'different_chars': word_pair[1],
            'user_word':word_pair[2],
             'quran_index':word_pair[3]


        })
       
    extraWords = [{'user_word': word} for word in user_words_copy]
             
    return {
        'quranText': quran_text,
        'userText':user_text,
        'different_words': different_words_result,
        'different_wordsintashkeel': different_wordsintashkeel_result,
        'different_wordsinONeCharacter': different_wordsinONeCharacter_result,
        'extraWord': extraWords
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