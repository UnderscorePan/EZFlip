# EZFlip Flashcard Application

EZFlip is a flashcard application designed to help users create, manage, and learn from custom flashcards. It supports text, images, and videos, and includes gesture control for hands-free operation.

## Features

- Create and manage flashcard sets
- Add flashcards with text, images, and videos
- Learn mode with gesture control for flipping cards and navigating
- Simple and intuitive user interface

## Requirements

- Python 3.x
- SQLite3
- Tkinter
- Ttkbootstrap
- PIL (Pillow)
- OpenCV
- FFMPEG
- Pygame
- Mediapipe

## Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/ezflip.git
    cd ezflip
    ```

2. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Install FFMPEG:**
    - Download FFMPEG from the official site: https://ffmpeg.org/download.html
    - Add FFMPEG to your system's PATH.

4. **Run the application:**
    ```bash
    python ezflip.py
    ```

## Usage

### Creating a New Flashcard Set

1. Open the application and navigate to the `Create Set` tab.
2. Enter the name of the flashcard set.
3. Add words, definitions, images, and video paths.
4. Click `Add Word` to add the flashcard to the set.
5. Click `Save Set` to save the flashcard set.

### Learning Mode

1. Navigate to the `Select Set` tab.
2. Choose a flashcard set from the dropdown and click `Select Set`.
3. Navigate to the `Learning Mode` tab to start reviewing the flashcards.
4. Use the `Previous` and `Next` buttons to navigate through the flashcards.
5. Click `Flip` to view the definition of the current flashcard.
6. Use hand gestures to control the flashcards:
    - 1 finger: Previous card
    - 2 fingers: Next card
    - 3 fingers: Flip card

## Gesture Control

The application uses Mediapipe for gesture recognition. To use gesture control:

1. Ensure your webcam is enabled.
2. The application will automatically detect hand gestures and perform actions based on the number of fingers shown.

## Contributing

If you would like to contribute to EZFlip, please fork the repository and submit a pull request. Contributions are welcome!

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgments

- Tkinter and Ttkbootstrap for the GUI
- Mediapipe for gesture recognition
- OpenCV for video processing
- FFMPEG for audio extraction
