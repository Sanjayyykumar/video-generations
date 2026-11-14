"""Demo cast for voice/speak_cast.py: each line has its own voice.
LINES = [(key, voice, speed, text), ...]  ->  OUT_DIR/<key>.wav"""
NARRATOR, MAYA, LEO = 'af_heart', 'bf_emma', 'am_michael'
LINES = [
    ('01', NARRATOR, 1.00, "It was two minutes to launch ... and the demo still had no voiceover."),
    ('02', MAYA,     1.05, "Leo, / we need narration, captions and music. / In ten minutes."),
    ('03', LEO,      1.00, "Ten minutes? // I only need one command."),
    ('04', NARRATOR, 0.96, "And that is how the video got made."),
]
