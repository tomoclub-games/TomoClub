# TAICY 2026: what to let AI control, and what not to

*Our AI Innovation Challenge for Youth is a wrap. A smart dustbin, a live team round with no rulebook, and what both taught us about kids and AI.*

![Cover: TAICY 2026, the wrap-up](images/00-cover.jpg)

A tablet hangs on a wall. Someone holds a tomato up to its camera. The screen turns green: **DROP IN WET**. Below it, a paper arrow on a tiny motor swings toward the bin marked WET.

That was one student's Round 1 entry to TAICY 2026, the TomoClub AI Innovation Challenge for Youth. The most impressive part wasn't the AI. It was this:

> "One of the things that I had to identify while making the app was what to let AI control and to not control."

The student who said that is in Grade 8.

![The smart dustbin's tablet turns green: drop in wet](images/01-drop-in-wet.jpg)

## What TAICY asked of students

TAICY was free to enter and open to students aged 8 to 15, anywhere in the world. It ran in two rounds.

**Round 1, Create (solo, online).** Spot a real problem: at home, at school, in your neighbourhood or online. Propose a solution with a clear "how". Use any AI tool to build a prototype. Then explain it in a short video, like you're telling a friend.

Judges scored the thinking, not the production quality:

- Problem identification: 25%
- Proposed solution: 25%
- Working prototype and AI use: 30%
- Pitch and explanation: 20%

Every entry also came with an **AI Use Log**, three short answers:

1. What did you ask?
2. What did you change?
3. What did AI get wrong?

The rule underneath it all: *AI can help build the idea. The thinking must be yours.*

**Round 2, Lead (live, as a team).** Top-scoring students from Round 1 were invited to a live round on Zoom, where they played multiplayer strategy games together, with no rulebook.

![How Round 1 was judged, and the AI Use Log](images/02-judging.jpg)

## Round 1 spotlight: a dustbin that knows where things go

The problem came from something every household does several times a day:

> "Usually, when we hold an object to throw in the trash, it is not always obvious which trash bin to throw it into."

Put it in the wrong bin, and separating it later becomes much harder. So the student built **EcoSense**, a smart dustbin:

- A tablet's camera checks whether something has been placed in front of it.
- The app sends a photo to Gemini, which sorts it into wet, dry or electronic waste.
- The app passes the answer over Bluetooth to an ESP32 microcontroller.
- A small servo motor turns a paper arrow toward the right bin.

In the demo, a tomato goes to wet, a sheet of paper to dry, and a computer mouse to electronic waste.

![The arrow points to the right bin](images/03-arrow-and-bins.jpg)

What impressed us most was the judgment around the AI. The AI does exactly one job: recognising the waste. Talking to the microcontroller and moving the arrow, in the student's words, "does not involve AI whatsoever." When an AI tool proposed a more complicated auto-sorting machine, the student chose the simpler design that worked.

The entry was honest about what didn't work, too. The hardest part was getting the app to tell reliably whether an object was really in front of the camera. Sometimes it saw objects that weren't there, and sometimes it missed ones that were. The fix: the app first photographs the empty background, and only takes a picture once something different has been held still for two seconds. It even runs smoothly on a tablet from 2016.

That's the AI Use Log in action. What did you ask? What did you change? What did AI get wrong?

Other entrants took on very different problems, including a study platform with separate spaces for students and teachers. Different problems, same bar: a problem you actually noticed, a solution with a clear "how", and real back-and-forth with AI.

## Round 2: no rulebook, one team

Round 2 was live, coached by VK. The first thing the students heard was:

> "We don't give you any rules. You have to talk to each other and figure it out."

That's the design. In one maze, a player has to hold down a button so a teammate can get through a door. Nobody can win alone. The students split the roles, called out their moves, and got faster with every attempt.

When VK asked one team, "How are you doing it so fast?", the answer was pure strategy:

> "Because we remember where all the circuit pieces are, and exactly what we should do at which time."

Then the lights went off. Same map, but the players could no longer see it. They cleared it in 45 seconds.

![Round 2, live: the coach and the team on Zoom (students blurred for privacy)](images/04-round-2-live.jpg)

Afterwards, one student summed up the difference better than we could:

> "Usually in other games you're competing against someone, but here you're actually working together for a certain goal."

Another put it in three words: *"Communication is key."*

## What we're taking away

1. **Judgment is the new literacy.** Using AI is easy. Deciding what AI should and shouldn't do is the skill.
2. **Real problems beat assignments.** Students build harder, better things when the problem is one they've actually noticed.
3. **Collaboration has to be practised, live.** You can't lecture a child into teamwork. A game with no rulebook makes them talk.
4. **Honesty about failure is a strength.** The strongest entries told us what went wrong and how they fixed it.

## Congratulations

To our winners, and to every young innovator who took on TAICY 2026: congratulations. You spotted real problems, built real things and showed us your thinking. Thank you to the parents who encouraged them, and to everyone who shared the challenge.

## Want your child to experience this?

TomoClub runs live, coach-led sessions where kids aged 8 to 15 build with AI, learn to question it, and play strategy games that only work with real teamwork. Your child's first session is free.

**[Join a free live session →](https://tally.so/r/gDgLeN)**

*Educators and schools:* want TAICY or game-based AI literacy for your students? Write to [info@tomoclub.org](mailto:info@tomoclub.org).

*Enjoyed this? Subscribe to The Learning Shift for more stories on better ways to teach, learn and play.*
