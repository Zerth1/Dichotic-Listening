import threading
import tempfile
from gtts import gTTS
from pydub import AudioSegment
import inflect
import pyaudio
import openai
import numpy as np
import os
import keyboard
import random
import time
inflect_engine = inflect.engine()
openai.api_key = ""
huge_number_range = list(range(32))
category_pairs = [
    "Prime Number vs. Composite Number",
    "Positive Number vs. Negative Number",
    "Even Number vs. Odd Number",
    "Divisible by 2 vs. Not Divisible by 2",
    "Divisible by 3 vs. Not Divisible by 3",
    "Divisible by 5 vs. Not Divisible by 5",
    "Prime Power vs. Non-Prime Power",
    "Number Less than 0 vs. Number Greater than or Equal to 0",
    "Multiple of 7 vs. Non-multiple of 7",
    "Multiple of 11 vs. Non-multiple of 11",
    "Number that are Powers of 2 vs. Number that are not Powers of 2",
    "Number with an Even Number of Positive Divisors vs. Number with an Odd Number of Positive Divisors",
    "Even Power of 2 vs. Odd Power of 2",
]
def list_audio_devices():
    p = pyaudio.PyAudio()
    device_count = p.get_device_count()
    devices = []
    for i in range(device_count):
        device_info = p.get_device_info_by_index(i)
        devices.append((i, device_info['name']))
    return devices
def text_to_speech_in_memory(text):
    tts = gTTS(text=text, lang='en')
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
        tts.save(temp_file.name)
        sound = AudioSegment.from_mp3(temp_file.name)
    os.remove(temp_file.name)
    return sound
def play_sound_concurrently(sound, output_device_index, left_ear_intensity=1.0, right_ear_intensity=1.0):
    samples = np.array(sound.get_array_of_samples())
    if len(samples) == 0:
        return
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, 
                    channels=2, 
                    rate=sound.frame_rate, 
                    output=True, 
                    output_device_index=output_device_index)
    stereo_samples = np.zeros((len(samples), 2), dtype=np.int16)
    stereo_samples[:, 0] = (samples * left_ear_intensity).astype(np.int16)
    stereo_samples[:, 1] = (samples * right_ear_intensity).astype(np.int16)

    byte_data = stereo_samples.tobytes()
    stream.write(byte_data)
    stream.stop_stream()
    stream.close()
    p.terminate()

def pan_and_play(text, output_device_index, left_ear_intensity, right_ear_intensity):
    sound = text_to_speech_in_memory(text)
    play_sound_concurrently(sound, output_device_index, left_ear_intensity, right_ear_intensity)
def generate_matrix(gamemode, output_device_index):
    a, b = gamemode.split(" vs. ")
    result = random.choice([a, b])
    print(result)
    minimum_range_a = random.choice(huge_number_range)
    minimum_range_b = random.choice(huge_number_range)
    response_correct = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages = [
            {"role": "user", "content": "Generate a 2x2 matrix in the example matrix index format '11,12,21,22' WITHOUT the quotation marks where the determinant of the matrix (Use the determinant formula: (11 * 22) - (12 * 21)) belongs to the category: " + result + ". Ensure that the absolute value of the determinant is above " + str(minimum_range_a) + ". The randomized matrix can only be composed of integers. ONLY PROVIDE THE MATRIX IN THE EXAMPLE FORM WITH NO ESCAPE SEQUENCE CHARACTERS."},
        ],
        temperature=0.0,
        n=8,
    )
    response_incorrect = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages = [
            {"role": "user", "content": "Generate a 2x2 matrix in the example matrix index format '11,12,21,22' WITHOUT the quotation marks where the determinant of the matrix (Use the determinant formula: (11 * 22) - (12 * 21).) DOES NOT belong to the category: " + result + ". Ensure that the absolute value of the determinant is above " + str(minimum_range_b) + ". The randomized matrix can only be composed of integers. ONLY PROVIDE THE MATRIX IN THE EXAMPLE FORM WITH NO ESCAPE SEQUENCE CHARACTERS."},
        ],
        temperature=0.0,
        n=8,
    )
    pan_and_play("The following category is " + result, output_device_index, 1.0 , 1.0)
    return [[inflect_engine.number_to_words(int(x.replace("'", "").replace("`", "").replace(r"  \n0", ""))) for x in random.choice(response_correct.choices).message["content"].strip().split(',')], [inflect_engine.number_to_words(int(x.replace("'", "").replace("`", "").replace(r"  \n0", ""))) for x in random.choice(response_incorrect.choices).message["content"].strip().split(',')]]
devices = list_audio_devices()
selected_device_index = None
for idx, name in devices:
    if name == "Headphones (Realtek(R) Audio)":
        selected_device_index = idx
        break        
while True:
    left_intensity = 1.0
    right_intensity = 1.0
    is_left = random.random() < 0.5
    if is_left:
        right_intensity = 0.1
    else:
        left_intensity = 0.1
    if is_left:
        pan_and_play("Listen with your left ear", selected_device_index, 1.0, 1.0)
    else:
        pan_and_play("Listen with your right ear", selected_device_index, 1.0, 1.0)    
    gamemode = random.choice(category_pairs)    
    responses_data = generate_matrix(gamemode, selected_device_index)
    correct_speech = ' '.join(map(str, responses_data[0]))
    incorrect_speech = ' '.join(map(str, responses_data[1]))
    is_violation = random.random() < 0.5
    if is_violation:
        if is_left:
            thread1 = threading.Thread(target=pan_and_play, args=(incorrect_speech, selected_device_index, left_intensity, 0.0))
            thread2 = threading.Thread(target=pan_and_play, args=(correct_speech, selected_device_index, 0.0, right_intensity))
            thread1.start()
            time.sleep(0.2)
            thread2.start()
            thread1.join()
            thread2.join()
        else:
            thread1 = threading.Thread(target=pan_and_play, args=(correct_speech, selected_device_index, left_intensity, 0.0))
            thread2 = threading.Thread(target=pan_and_play, args=(incorrect_speech, selected_device_index, 0.0, right_intensity))
            thread1.start()
            time.sleep(0.2)
            thread2.start()
            thread1.join()
            thread2.join() 
    else:
        if is_left:
            thread1 = threading.Thread(target=pan_and_play, args=(correct_speech, selected_device_index, left_intensity, 0.0))
            thread2 = threading.Thread(target=pan_and_play, args=(incorrect_speech, selected_device_index, 0.0, right_intensity))
            thread1.start()
            time.sleep(0.2)
            thread2.start()
            thread1.join()
            thread2.join() 
        else:
            thread1 = threading.Thread(target=pan_and_play, args=(incorrect_speech, selected_device_index, left_intensity, 0.0))
            thread2 = threading.Thread(target=pan_and_play, args=(correct_speech, selected_device_index, 0.0, right_intensity))
            thread1.start()
            time.sleep(0.2)
            thread2.start()
            thread1.join()
            thread2.join()
    time.sleep(2)
    pan_and_play("Respond with the A key if the condition is satisfied. If not, then press the L key.", selected_device_index, 1.0, 1.0)
    while True:
        if keyboard.is_pressed("a"):
            if is_violation:
                pan_and_play("False", selected_device_index, 1.0, 1.0)
            else:
                pan_and_play("True", selected_device_index, 1.0, 1.0)
            break    
        if keyboard.is_pressed('l'):
            if is_violation:
                pan_and_play("True", selected_device_index, 1.0, 1.0)
            else:
                pan_and_play("False", selected_device_index, 1.0, 1.0)
            break
