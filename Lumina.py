# the following program is provided by DevMiser - https://github.com/DevMiser

#!/usr/bin/env python3

from PIL import Image
import base64
import requests
import datetime
import io
import openai
import os
import pyaudio
import pvcobra
import pvleopard
import pvporcupine
import schedule
import struct
import sys
import textwrap
import threading
import time
import tkinter as tk
import urllib.request

from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageEnhance,ImageTk
from pvleopard import *
from pvrecorder import PvRecorder
from time import sleep
from threading import Thread

pv_access_key= "PICO_VOICE_API_TOKEN_GOES_HERE"

#Local LLM for generating random image descriptions
api_url = "http://10.0.3.9:3000/api/chat/completions"
api_token = "LOCAL_STABLE_DIFFUSION_API_TOKEN_GOES_HERE"

audio_stream = None
cobra = None
pa = None
porcupine = None
recorder = None
global text_var
global screen_width, screen_height

count = 0

CloseProgram_list = ["Close program",
    "End program",
    "Exit program",
    "Stop program"
    "Close the program",
    "End the program",
    "Exit the program",
    "Stop the program",
    "Exit",
    "Stop",
    "End",
    "Close"
    ]

DisplayOn_list = ["Turn on",
    "Wake up"
    ]

DisplayOff_list = ["Turn off",
    "Sleep"
    ]

root = tk.Tk()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root['bg'] = 'black'
root.geometry(f"{screen_width}x{screen_height}+0+0")
root.overrideredirect(True)
root.attributes("-fullscreen", True)
root.update()

def stable_diffusion(prompt):

# no API Token needed for image generation
    url = "http://10.0.3.9:7860/sdapi/v1/txt2img"  # Update with your Stable Diffusion API URL
    headers = {"Content-Type": "application/json"}
    data = {
        "prompt": prompt,
#       "negative_prompt": "people, faces, man, woman, kid, children, human",
#        "width": screen_width // 2,
#        "height": screen_height // 2,
        "width": screen_width,
        "height": screen_height,
        "steps": 60,
        "seed": -1,
#
#	"sampler_name": "UniPC"
#	"sampler_name": "DPM++ 2M"
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()  # Raise an exception for non-2xx responses
        result = response.json()
        # Assuming the API returns a base64-encoded image in the "images" field
        base64_image = result.get("images", [None])[0]

        if not base64_image:
            print("Error: No image data returned.")
            return None

        # Decode the base64 string into image data
        image_data = base64.b64decode(base64_image)
        return image_data
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with the Stable Diffusion API: {e}")
        return None


def close_image_window():

    windows = root.winfo_children()
    for window in windows:
        if isinstance(window, tk.Toplevel):
            if window.attributes("-fullscreen"):
                print("closing image window")
                window.destroy()

def close_program():

    recorder = Recorder()
    recorder.stop()
    o.delete
    recorder = None
    sys.exit ("Program terminated")

def current_time():

    time_now = datetime.datetime.now()
    formatted_time = time_now.strftime("%m-%d-%Y %I:%M %p\n")
    print("The current date and time is:", formatted_time)

def detect_silence():

    cobra = pvcobra.create(access_key=pv_access_key)

    silence_pa = pyaudio.PyAudio()

    cobra_audio_stream = silence_pa.open(
                    rate=cobra.sample_rate,
                    channels=1,
                    format=pyaudio.paInt16,
                    input=True,
                    frames_per_buffer=cobra.frame_length)

    last_voice_time = time.time()

    while True:

        cobra_pcm = cobra_audio_stream.read(cobra.frame_length)
        cobra_pcm = struct.unpack_from("h" * cobra.frame_length, cobra_pcm)
        if cobra.process(cobra_pcm) > 0.2:
            last_voice_time = time.time()
        else:
            silence_duration = time.time() - last_voice_time
            if silence_duration > 0.8:
                print("End of query detected\n")
                cobra_audio_stream.stop_stream
                cobra_audio_stream.close()
                cobra.delete()
                last_voice_time=None
                break

def display_on(transcript):

    for word in DisplayOn_list:
        if word in transcript:
            print("\'"f"{word}\' detected")
            current_time
            os.system("xset dpms force on")
            print("\nTurning on display.")
            sleep(1)

def display_off(transcript):

    for word in DisplayOff_list:
        if word in transcript:
            print("\'"f"{word}\' detected")
            current_time
            print("\nTurning off display.")
            os.system("xset dpms force off")
            sleep(1)

#updated from requesting image URL to using base64 image data sent from the AI API
def draw_request(transcript):
    global text_var

    prompt = transcript
    print("You requested the following image: " + prompt)
    print("\nCreating image...\n")

    wrapped_prompt = textwrap.fill(prompt, width=35)
    text_var.set("Generating new image...\n\n" + wrapped_prompt)
    text_window.update()

    image_url = stable_diffusion(transcript)  # Use the local Stable Diffusion API

    if image_url:
        print("Displaying generated image.")
        update_image(image_url)
    else:
        print("Failed to generate image or image URL is None.")

#draws random image generated from AI
def draw_random(category):
    global text_var

    wrapped_prompt = textwrap.fill(category, width=35)
    text_var.set("!! Random category: " + category +" !!\n\n" + wrapped_prompt)
    text_window.update()


    random = get_image_description(api_url, api_token, category)
    print("Generating random image: " + random)
    print("\nCreating random image...\n")

    wrapped_prompt = textwrap.fill(random, width=35)
    text_var.set("Generating random new image...\n\n" + wrapped_prompt)
    text_window.update()

    image_url = stable_diffusion(random)  # Use the local Stable Diffusion API

    if image_url:
        print("Displaying random generated image.")
        update_image(image_url)
    else:
        print("Failed to random generate image or image URL is None.")

def get_image_description(api_url, api_token, category):
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3.1:latest",
        "messages": [
            {
                "role": "user",
                "content": f"Reply with only a 250 character-long realistic {category} description"
            }
        ]
    }
    response = requests.post(api_url, headers=headers, json=data)

    if response.status_code == 200:
        response_data = response.json()
        message_content = response_data['choices'][0]['message']['content']
        return message_content
    else:
        print(f"API request failed with status code: {response.status_code}")
        print(response.text)
        return None


def listen():
    global image_window
    global text_window
    global text_var
    cobra = pvcobra.create(access_key=pv_access_key)

    close_image_window()

    listen_pa = pyaudio.PyAudio()

    listen_audio_stream = listen_pa.open(
                rate=cobra.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=cobra.frame_length)
    Statement = "Listening"
    text_var.set("Listening")
    text_window.update()

    print("Listening...")

    while True:
        listen_pcm = listen_audio_stream.read(cobra.frame_length)
        listen_pcm = struct.unpack_from("h" * cobra.frame_length, listen_pcm)

        if cobra.process(listen_pcm) > 0.3:
            print("Voice detected")
            listen_audio_stream.stop_stream
            listen_audio_stream.close()
            cobra.delete()
            break

def display_logo():
    global image_window
    global screen_width, screen_height
    image_window = tk.Toplevel(root)
    image_window.title("Image Window")
    image_window.geometry(f"{screen_width}x{screen_height}+0+0")
    image_window.attributes("-fullscreen", True)
    image_window.overrideredirect(True)
    image_window.configure (bg='black')
    image = Image.open("/home/hacksoarizer/Lumina/Lumina Logo.png")
    # Calculate the scaling factor based on the original image size and the screen size
    original_width, original_height = image.size
    scale = max(screen_width / original_width, screen_height / original_height)
    # Resize the image with the scaled dimensions
    scaled_width = int(original_width * scale)
    scaled_height = int(original_height * scale)
    image = image.resize((scaled_width, scaled_height))
    image_photo = ImageTk.PhotoImage(image)
    image_canvas = tk.Canvas(image_window, bg='#000000', width=screen_width, height=screen_height)
    # Center the image on the screen
    x = (screen_width - scaled_width) // 2
    y = (screen_height - scaled_height) // 2
    image_canvas.create_image(x, y, image=image_photo, anchor=tk.NW)
    image_canvas.pack()
    image_window.update()


def on_message(transcript, DisplayOn_list, DisplayOff_list, CloseProgram_list):
    # Check for "CloseProgram" commands
    if any(word in transcript for word in CloseProgram_list):
        close_program()
        return
    # Check for "DisplayOn" commands
    if any(word in transcript for word in DisplayOn_list):
        display_on(transcript)
        return
    # Check for "DisplayOff" commands
    if any(word in transcript for word in DisplayOff_list):
        display_off(transcript)
        return
    # Check for "Random" commands
    if "Random" in transcript:
        words = transcript.split()
        random_index = words.index("Random")
        category = " ".join(words[random_index + 1:]).strip()  # Extract category after "Random"
        if category:  # If a category exists after "Random"
            draw_random(category)
        else:  # If only "Random" is provided
            draw_random("random")  # Default category
        return
    # Default behavior: handle transcript as a direct draw request
    draw_request(transcript)

def text_window_func():
    global text_var
    global text_window
    global screen_width, screen_height
    text_window = tk.Toplevel(root)
    text_window.geometry(f"{screen_width}x{screen_height}+0+0")
    text_window.overrideredirect(True)
    text_window.focus_set()
    text_window.configure (bg='black')
    text_var = tk.StringVar()
    label = tk.Label(text_window, textvariable=text_var, bg='#000000',fg='#ADD8E6', font=("Arial Black", 22))
    label.pack(side=tk.TOP, anchor=tk.CENTER, pady=screen_height//4)
    print("text window open")
    text_window.update()

#new image converted and displayed instead of the OpenAi way
def update_image(image_data):
    if image_data is None:
        print("Error: No image data to display.")
        return

    global image_window
    global screen_width, screen_height
    image_window = tk.Toplevel(root)
    image_window.title("Image Window")
    image_window.geometry(f"{screen_width}x{screen_height}+0+0")
    image_window.attributes("-fullscreen", True)
    image_window.overrideredirect(True)
    image_window.configure (bg='black')

    try:
        # Convert the base64 image data into an Image object
        image = Image.open(io.BytesIO(image_data))
        original_width, original_height = image.size
        scale = max(screen_width / original_width, screen_height / original_height)
        scaled_width = int(original_width * scale)
        scaled_height = int(original_height * scale)
        image = image.resize((scaled_width, scaled_height))
        image_photo = ImageTk.PhotoImage(image)
        image_canvas = tk.Canvas(image_window, bg='#000000', width=screen_width, height=screen_height)
        x = (screen_width - scaled_width) // 2
        y = (screen_height - scaled_height) // 2
        image_canvas.create_image(x, y, image=image_photo, anchor=tk.NW)
        image_canvas.pack()
        image_window.update()
    except Exception as e:
        print(f"Error loading image: {e}")


def wake_word():

    porcupine = pvporcupine.create(keywords=["Lumina",],
                            access_key=pv_access_key,
                            sensitivities=[0.1], #from 0 to 1.0 - a higher number reduces the miss rate at the cost of increased false alarms
                                   )
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(2)
    sys.stderr.flush()
    os.dup2(devnull, 2)
    os.close(devnull)
    wake_pa = pyaudio.PyAudio()

    porcupine_audio_stream = wake_pa.open(
                    rate=porcupine.sample_rate,
                    channels=1,
                    format=pyaudio.paInt16,
                    input=True,
                    frames_per_buffer=porcupine.frame_length)

    Detect = True

    while Detect:
        porcupine_pcm = porcupine_audio_stream.read(porcupine.frame_length)
        porcupine_pcm = struct.unpack_from("h" * porcupine.frame_length, porcupine_pcm)

        porcupine_keyword_index = porcupine.process(porcupine_pcm)

        if porcupine_keyword_index >= 0:

            print("\nWake word detected\n")
            current_time()
            porcupine_audio_stream.stop_stream
            porcupine_audio_stream.close()
            porcupine.delete()
            os.dup2(old_stderr, 2)
            os.close(old_stderr)
            Detect = False

class Recorder(Thread):
    def __init__(self):
        super().__init__()
        self._pcm = list()
        self._is_recording = False
        self._stop = False

    def is_recording(self):
        return self._is_recording

    def run(self):
        self._is_recording = True

        recorder = PvRecorder(device_index=-1, frame_length=512)
        recorder.start()

        while not self._stop:
            self._pcm.extend(recorder.read())
        recorder.stop()

        self._is_recording = False

    def stop(self):
        self._stop = True
        while self._is_recording:
            pass

        return self._pcm

try:
    # Initialize the Recorder
    o = create(access_key=pv_access_key)

    count = 0

    while True:
        try:
            # Display logo once at the beginning
            if count == 0:
                display_logo()
            count = 1

            # Initialize and start the recorder
            recorder = Recorder()
            wake_word()  # Wait for wake word
            text_window_func()  # Set up the text window

            recorder.start()
            listen()  # Listen for commands
            detect_silence()  # Detect silence between commands

            # Process the recorded audio and get transcript
            transcript, words = o.process(recorder.stop())
            recorder.stop()

            print("You said: " + transcript)

            # Handle the command based on the transcript
            on_message(transcript, DisplayOn_list, DisplayOff_list, CloseProgram_list)
            recorder = None

        except Exception as e:
            # If an error occurs, log it and stop the recorder
            print(f"Error occurred: {e}")
            recorder.stop()
            o.delete()
            recorder = None
            sleep(1)

except KeyboardInterrupt:
    sys.exit("\nExiting Lumina")
