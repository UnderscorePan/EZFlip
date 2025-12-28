import threading
import tempfile
import time
import queue

import cv2
import ffmpeg
import pygame
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox


pygame.mixer.init()

audio_path = ''
playing_video = False
stopping_video = False
current_video_path = ""
audio_thread = None
video_thread = None
video_canvas = None
video_lock = threading.Lock()


def init_media_canvas(canvas):
    global video_canvas
    video_canvas = canvas


def extract_audio(video_path):
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio_file:
            extracted_audio_path = temp_audio_file.name
        ffmpeg.input(video_path).output(extracted_audio_path, loglevel="quiet").run(overwrite_output=True)
    except FileNotFoundError:
        messagebox.showerror("Error", "FFmpeg not found. Please install FFmpeg and ensure it is in the PATH.")
        raise
    except PermissionError as exc:
        messagebox.showerror("Error", f"Permission denied: {exc}")
        raise
    except Exception as exc:  # pylint: disable=broad-except
        messagebox.showerror("Error", f"Failed to extract audio: {exc}")
        raise
    return extracted_audio_path


def play_audio(video_path):
    global audio_path
    try:
        audio_path = extract_audio(video_path)
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except PermissionError as exc:
        messagebox.showerror("Error", f"Permission denied: {exc}")
        raise
    except Exception as exc:  # pylint: disable=broad-except
        messagebox.showerror("Error", f"Failed to play audio: {exc}")
        raise


def stop_audio():
    global audio_path
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()


def play_video(video_path):
    global playing_video, audio_thread, stopping_video

    def video_thread_worker(frame_buffer):
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_time = 1 / fps

        audio_thread = threading.Thread(target=play_audio, args=(video_path,))
        audio_thread.start()
        start_time = time.time()

        while cap.isOpened() and playing_video:
            ret, frame = cap.read()
            if not ret:
                break

            current_time = time.time()
            elapsed_time = current_time - start_time
            expected_frame_number = int(elapsed_time * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, expected_frame_number)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (400, 300))

            if not frame_buffer.full():
                frame_buffer.put(frame)

        cap.release()
        stop_audio()

    def display_thread(frame_buffer, frame_time):
        while playing_video:
            if not frame_buffer.empty():
                frame = frame_buffer.get()
                img = ImageTk.PhotoImage(Image.fromarray(frame))
                video_canvas.create_image(0, 0, anchor=tk.NW, image=img)
                video_canvas.image = img
                video_canvas.update()
            time.sleep(frame_time)

    frame_buffer = queue.Queue(maxsize=10)
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_time = 1 / fps
    cap.release()

    video_play_thread = threading.Thread(target=video_thread_worker, args=(frame_buffer,))
    video_display_thread = threading.Thread(target=display_thread, args=(frame_buffer, frame_time))

    video_play_thread.daemon = True
    video_display_thread.daemon = True

    video_play_thread.start()
    video_display_thread.start()


def stop_video():
    global playing_video, video_thread, stopping_video
    playing_video = False
    if video_thread:
        video_thread.join()
    stop_audio()


def start_video(video_path):
    global playing_video, current_video_path
    playing_video = True
    current_video_path = video_path
    threading.Thread(target=play_video, args=(video_path,)).start()


def display_image(image_path):
    try:
        image = Image.open(image_path)
        image = image.resize((400, 300), Image.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        video_canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        video_canvas.image = photo
        video_canvas.update()
    except Exception:  # pylint: disable=broad-except
        video_canvas.delete("all")
        video_canvas.create_text(200, 150, text='Error loading image', fill='red', font=('TkDefaultFont', 24))
