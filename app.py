from flask import Flask, render_template, request, redirect, url_for
from PIL import Image
import pytesseract
import cv2
import secrets
import os
import cohere
import config
import speech_recognition as sr
import pyaudio
import wave
import random

co = cohere.Client(config.api_key)


words = ["accept", "meaning", "school", "total", "view", "degree", "who", 'where', 'why', 'interesting']

#image = Image.open('image.png', mode='r')
#print(image_to_string(image))
app = Flask(__name__)


@app.route('/')
def home():
    return render_template("home.html")

@app.route('/upload', methods=['POST', 'GET'])
def upload():

    if request.method == 'POST':
        file = request.files.get('file')
        
        filename, extension = file.filename.split(".")
        generated_filename = secrets.token_hex(10) + f".{extension}"
        

        raw_file_location = os.path.join(os.getcwd(), "static", "saved_img" , generated_filename)
        file.save(raw_file_location)

        # print(file_location)

        # OCR here
        pytesseract.pytesseract.tesseract_cmd = rf'{os.getcwd()}\\Tesseract-OCR\\tesseract.exe'
       
        #img = Image.open(file_location)
        img = cv2.imread(raw_file_location)
    
          
        raw = pytesseract.image_to_string(img)
        converted_text = raw.split()
        img_shape = img.shape
        d = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        print(d.keys())
        for i in range(len(d["conf"])):
            print([d[key][i] for key in d])
        data_size = len(d["text"])
        cur_level = [(0, 0, 0, 0, 0), (0, 0), (0, 0)]
        text_size = 0
        for i in range(data_size):
            if int(d['conf'][i] >= 60):
                text_size += d['height'][i]
                if (d['level'][i] ,d['page_num'][i], d['block_num'][i], d['par_num'][i], d['line_num'][i]) == cur_level[0]:
                    
                    d['top'][i], d['height'][i] = cur_level[1]
                    d['left'][i] = cur_level[2][0] + cur_level[2][1] + 20
                    cur_level[2] = (d['left'][i], d['width'][i])
                else:
                    cur_level[0] = (d['level'][i] ,d['page_num'][i], d['block_num'][i], d['par_num'][i], d['line_num'][i])
                    cur_level[1] = (d['top'][i], d['height'][i])
                    cur_level[2] = (d['left'][i], d['width'][i])    
        
        text_size /= data_size
        for i in range(len(d["conf"])):
            print([d[key][i] for key in d])  
        
        summary = co.summarize(text=raw).summary
        print(summary)
        print(type(summary))
        return render_template('upload.html',img_shape=img_shape, d=d, font_size=text_size, data_size=data_size, converted_text=converted_text, img_url=raw_file_location, filename=generated_filename, summary=summary)
    
    else:
        
        return render_template('upload.html')           


@app.route('/about')                
def about():
    return render_template('about.html')

@app.route('/features')                
def converted():
    return render_template('features.html')

global word
word = random.choice(words)
score = 0

@app.route('/learn',  methods=['POST', 'GET'])
def learn():
    global word
    global score
    
    message=""
    if request.method == 'POST':
        text = request.form['text'] 
        if text == word:
            message = "Well done!"
            old_word = word
            word = random.choice(words)
            score += 1
            return render_template("correct.html", message=message, word=old_word, written=text, score=score)
        else:
            message = "Try again"
            return render_template("learn.html", message=message, word=word, written=text, len_written=len(text), len_word=len(word))
        
    return render_template("learn.html", message=message, word=word)



speechs = ["i love kimberly so much", "kimberly is my girlfriend", "my name is kimberly"]

global speech
speech = random.choice(speechs)





@app.route('/finished', methods=['POST', 'GET'])
def done_learn():
    global score
    user_score = score
    score = 0
    return render_template("finish.html", score=user_score)

@app.route('/audio', methods=['POST', 'GET'])
def audio():
    global speech
    
    speechs.remove(speech)
    
    speech = random.choice(speechs)
    return render_template('recording.html', speech=speech)

global false_words
false_words = []


@app.route('/record', methods=['POST', 'GET'])
def record():
    global speech
    global false_words
    speech_words = speech.replace('.', '').replace(',', '').lower().split()
    print(speech_words)
    print('start')
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        print('Please say something')
        audio = r.listen(source ,timeout=10)
        print('Recognizing...')
        try:
            text = r.recognize_google(audio)
        except: 
            text = "Sorry, We couldn't hear you"
    text_words = text.lower().split()
    correct = 0
    total = len(speech_words)
    incorrect_words = []
    for word in speech_words:
        if word in text_words:
            text_words.remove(word)
            correct+=1
        else:
            incorrect_words.append(word)
    false_words = incorrect_words
    if len(false_words) == 0:
        first_try = "yes"
    else:
        first_try = "no"
    return render_template("recording.html", speech=speech, text=text, score=correct/total, incorrect=incorrect_words,first_try=first_try)



cur_word = ''

@app.route('/speech', methods=['POST', 'GET'])
def read_display():
    global cur_word
    global false_words
    print(false_words)
    cur_word = false_words.pop()
    return render_template("speech.html", word=cur_word)

@app.route('/speech-start', methods=['POST', 'GET'])
def read_start():
    global speech
    global cur_word
    global false_words
    speech_word = cur_word
    
    print('start')
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        print('Please say something')
        audio = r.listen(source ,timeout=10)
        print('Recognizing...')
        
        try:
            text = r.recognize_google(audio)
        except: 
            text = "Sorry, We couldn't hear you"
    text_words = text.lower().split()
    correct = 0
    if speech_word.lower() in text_words:
        correct="true"
    else:
        correct="false"
        false_words.append(speech_word)
    
    if len(false_words) == 0:
        return redirect("/finish-read")
    
    return render_template("speech.html", speech=speech, text=text, correct=correct, single_word="true")


@app.route("/finish-read")  
def finish_read():
    return render_template("finishread.html")