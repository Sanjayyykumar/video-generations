"""Demo narration for voice/speak.py and voice/mix_narration.py.
LINES = [(start_second, speed, text), ...]
Markers:  /  short breath (0.25 s)   //  dramatic pause (0.55 s)   ...  held beat (0.8 s)"""
VOICE = 'af_heart'          # or a blend: 'af_heart:0.6,bf_emma:0.4'
LINES = [
    (0.5, 0.95, "Every great video starts with a voice ... and a story worth telling."),
    (5.0, 1.00, "This studio writes the voice, times every scene to it, / adds captions, / and mixes the music."),
    (11.0, 1.00, "No GPU. No subscription. Just one command, on your own machine."),
    (16.5, 0.96, "Now it's your turn. // Make something people remember."),
]
