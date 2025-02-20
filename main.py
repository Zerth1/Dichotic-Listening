import threading
import tempfile
from gtts import gTTS
from pydub import AudioSegment
import inflect
import pyaudio
import numpy as np
import os
import keyboard
import random
import time
inflect_engine = inflect.engine()
huge_number_range = list(range(25))
category_enumeration = ["Positive Numbers", "Negative Numbers", "Even Numbers", "Odd Numbers"]
category_pairs = {
    "Positive Numbers": list(range(1, 50)),
    "Negative Numbers": list(range(-1, -50, -1)),
    "Even Numbers": list(range(-50, 51, 2)),
    "Odd Numbers": list(range(-51, 51, 2)),
}
MATRIX_SIZE = 2
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
    result_a = category_pairs[category_enumeration[gamemode]]
    response_correct = []
    while True:
        random_compressed_matrix = list(range(-25, 25))
        random.shuffle(random_compressed_matrix)
        random_compressed_matrix = random_compressed_matrix[:int(MATRIX_SIZE ** 2)]
        random_matrix = []
        for i in range(int(MATRIX_SIZE ** 2)):
            if i % MATRIX_SIZE == 0:
                random_matrix.append([])
            random_matrix[-1].append(random_compressed_matrix[i])
        determinant_a = np.linalg.det(np.array(random_matrix))
        if int(determinant_a) in result_a:
            response_correct = list(map(inflect_engine.number_to_words, random_compressed_matrix))
            break
    response_incorrect = []
    while True:
        random_compressed_matrix = list(range(-20, 20))
        random.shuffle(random_compressed_matrix)
        random_compressed_matrix = random_compressed_matrix[:int(MATRIX_SIZE ** 2)]
        random_matrix = []
        for i in range(int(MATRIX_SIZE ** 2)):
            if i % MATRIX_SIZE == 0:
                random_matrix.append([])
            random_matrix[-1].append(random_compressed_matrix[i])
        determinant_b = np.linalg.det(np.array(random_matrix))
        if int(determinant_b) not in result_a:
            response_incorrect = list(map(inflect_engine.number_to_words, random_compressed_matrix))
            break
    pan_and_play("The following category is " + category_enumeration[gamemode], output_device_index, 1.0, 1.0)
    return [", ".join(response_correct), ", ".join(response_incorrect)]
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
        right_intensity = 0.25
    else:
        left_intensity = 0.25
    if is_left:
        pan_and_play("Listen with your left ear", selected_device_index, 1.0, 1.0)
    else:
        pan_and_play("Listen with your right ear", selected_device_index, 1.0, 1.0)    
    gamemode = random.choice(list(range(0, len(category_enumeration) - 1, 2)))
    responses_data = generate_matrix(gamemode, selected_device_index)
    correct_speech = responses_data[0]
    incorrect_speech = responses_data[1]
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
