"""Narration and scene plan for "Think Like a Musician: 5 AI Literacy Moves".

Each scene is a list of timeline items:
  ("vo", id, text, gap_after)  - narration line (text is what the TTS speaks)
  ("pause", seconds)           - silence / hold
  ("clip", name)               - a segment from the TomoClub session recording

`caption` overrides are used when the spoken text is spelled for the TTS engine
("Tomo Club") but should read normally in captions ("TomoClub").
"""

CAPTION_FIXES = {"Tomo Club": "TomoClub", "thirteen and up": "13 and up", "thirty seconds": "30 seconds"}

# Segments of the Chrome Music Lab session (source seconds). Chosen so that
# no student names are spoken or shown; student tiles get an extra blur pass.
CLIPS = {
    "clipA": [(28.4, 41.4)],
    "clipB": [(48.25, 59.4), (86.3, 99.6)],
}

# Facilitator speech inside the clips (source seconds) for the caption file.
CLIP_CAPTIONS = [
    (35.0, 36.0, "Nice."),
    (36.0, 38.0, "I like the gap in between where it plays"),
    (38.0, 40.8, "and gives something to anticipate as well."),
    (40.8, 41.3, "Well done."),
    (48.7, 50.0, "Wow, wow. I love this."),
    (50.0, 54.0, "Yeah, that's how you experiment."),
    (54.0, 56.5, "That's how you experiment. Yes, I love it."),
    (56.5, 58.0, "Let's see how it would sound."),
    (86.5, 89.0, "I love the pattern in which you have colored,"),
    (89.0, 91.0, "shows that you have gone for some pattern."),
    (91.0, 94.8, "This is like pressing all the keys on the keyboard together, so that's nice."),
    (94.8, 96.9, "Yeah, lovely."),
    (97.0, 98.4, "Like the experimentation."),
    (98.7, 99.6, "Wonderful team."),
]

SCENES = [
    {"id": "hook", "lead": 4.2, "tail": 0.4, "items": [
        ("vo", "h1", "Quick question. What note comes next?", 1.6),
        ("vo", "h2", "Your brain just made a guess. And that's exactly what AI does, all day long, with words, images, and sounds.", 0.5),
        ("vo", "h3", "AI doesn't know things the way you do. It predicts patterns.", 0.5),
        ("vo", "h4", "So today, we're borrowing five moves from musicians, to help you use AI like a pro, not a passenger.", 0.3),
    ]},
    {"id": "title", "lead": 0.0, "tail": 0.0, "items": [
        ("pause", 3.6),
    ]},
    {"id": "soundcheck", "lead": 0.5, "tail": 0.6, "items": [
        ("vo", "s1", "First, a quick sound check.", 0.3),
        ("vo", "s2", "This video is for students thirteen and up. Only use AI tools your school, or a parent or guardian, has approved, and follow each tool's age rules.", 0.4),
        ("vo", "s3", "Then, try the billboard test. If you wouldn't put it on a billboard outside your school, don't type it into an AI. No full names, addresses, passwords, or photos of friends.", 0.3),
    ]},
    {"id": "m1_intro", "lead": 0.5, "tail": 0.5, "items": [
        ("vo", "m1a", "Move one. Guess the next note.", 0.4),
        ("vo", "m1b", "Here's a real Tomo Club session, where students built their own songs in Chrome Music Lab's Song Maker. Listen to what the facilitator notices.", 0.2),
    ]},
    {"id": "clipA", "lead": 0.0, "tail": 0.0, "items": [
        ("clip", "clipA"),
    ]},
    {"id": "m1_body", "lead": 0.4, "tail": 0.6, "items": [
        ("vo", "m1c", "Something to anticipate. That's the key idea. AI writes one small piece at a time, always predicting what's most likely to come next.", 0.4),
        ("vo", "m1d", "Try it yourself. Build three bars in Song Maker, then ask a friend to guess the fourth. Notice how often they pick the safe, expected note.", 0.4),
        ("vo", "m1e", "AI plays it safe too. So when you want something original, that's your cue to choose the surprising note yourself.", 0.3),
    ]},
    {"id": "m2", "lead": 0.5, "tail": 0.6, "items": [
        ("vo", "m2a", "Move two. Play it twice.", 0.4),
        ("vo", "m2b", "Musicians replay a tricky part to see if it holds up. Do the same with AI. Open a brand-new chat, and ask the exact same question again.", 0.4),
        ("vo", "m2c", "If the answers match, that's a good sign. If a name, number, or date changes, the AI was guessing. Treat that part as a rumor until you check it.", 0.3),
    ]},
    {"id": "m3", "lead": 0.5, "tail": 0.6, "items": [
        ("vo", "m3a", "Move three. Flip the key.", 0.4),
        ("vo", "m3b", "Switch a song from a major key to a minor key, and the whole mood changes. Questions work the same way.", 0.4),
        ("vo", "m3c", "Ask: why is studying in the morning better? Then, in a new chat, ask: why is studying at night better?", 0.4),
        ("vo", "m3d", "If the AI happily agrees both times, it's following your lead, not the evidence. So ask neutral questions instead, like: what are the pros and cons of each?", 0.3),
    ]},
    {"id": "m4", "lead": 0.5, "tail": 0.6, "items": [
        ("vo", "m4a", "Move four. Find the sheet music.", 0.4),
        ("vo", "m4b", "Before you repeat a fact from an AI, find the receipt. Open a real source yourself, like a textbook or a trusted website, and find the exact line that backs it up.", 0.4),
        ("vo", "m4c", "A link from an AI doesn't count until you've clicked it and seen that line with your own eyes. No receipt? Don't repeat it.", 0.3),
    ]},
    {"id": "m5", "lead": 0.5, "tail": 0.6, "items": [
        ("vo", "m5a", "Move five. Play it by ear.", 0.4),
        ("vo", "m5b", "A musician who can only play while reading the sheet hasn't really learned the song yet.", 0.4),
        ("vo", "m5c", "So after AI helps you with something, close the tab, and explain it out loud in thirty seconds, to a friend, a family member, or even your dog.", 0.4),
        ("vo", "m5d", "Wherever you get stuck, that's the part you still need to learn. AI should train your brain, not replace it.", 0.3),
    ]},
    {"id": "exp_intro", "lead": 0.4, "tail": 0.3, "items": [
        ("vo", "e1", "The students in this session didn't aim for perfect. They experimented.", 0.2),
    ]},
    {"id": "clipB", "lead": 0.0, "tail": 0.0, "items": [
        ("clip", "clipB"),
    ]},
    {"id": "exp_outro", "lead": 0.4, "tail": 0.6, "items": [
        ("vo", "e2", "That's the mindset. Treat AI like an instrument you're learning. Test it, question it, and listen for its patterns.", 0.3),
    ]},
    {"id": "challenge", "lead": 0.6, "tail": 1.2, "items": [
        ("vo", "c1", "Now it's your turn. Here's today's challenge: can you make an AI flip?", 0.4),
        ("vo", "c2", "Pick a this or that question, like cats or dogs, summer or winter, or morning or night study.", 0.4),
        ("vo", "c3", "In one chat with an approved AI tool, ask why the first one is better. Then open a brand-new chat, and ask why the second one is better.", 0.4),
        ("vo", "c4", "Did your AI flip to agree with you both times, or did it hold its ground? Comment flipped, or held, plus the pair you tested.", 0.4),
        ("vo", "c5", "And keep it anonymous. No names, schools, or personal details in the comments.", 0.3),
    ]},
    {"id": "recap", "lead": 0.4, "tail": 0.9, "items": [
        ("vo", "r0", "Quick recap.", 0.25),
        ("vo", "r1", "Guess the next note.", 0.2),
        ("vo", "r2", "Play it twice.", 0.2),
        ("vo", "r3", "Flip the key.", 0.2),
        ("vo", "r4", "Find the sheet music.", 0.2),
        ("vo", "r5", "And play it by ear.", 0.3),
    ]},
    {"id": "outro", "lead": 0.5, "tail": 7.0, "items": [
        ("vo", "o1", "Oh, and one more thing. The voice you've been hearing was generated by AI. Now you know how to question it.", 0.4),
        ("vo", "o2", "Stay curious, and we'll see you in the comments.", 0.0),
    ]},
]


def caption_text(text):
    for k, v in CAPTION_FIXES.items():
        text = text.replace(k, v)
    return text
