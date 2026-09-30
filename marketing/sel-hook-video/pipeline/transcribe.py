import sys, json
from faster_whisper import WhisperModel
v=sys.argv[1]
m=WhisperModel('small', device='cpu', compute_type='int8', cpu_threads=2)
segs,info=m.transcribe(f'audio/{v}.wav', language='en', vad_filter=True, word_timestamps=True, beam_size=1)
out=[]
with open(f'audio/{v}.txt','w') as f:
    for s in segs:
        out.append({'start':s.start,'end':s.end,'text':s.text,'words':[(w.start,w.end,w.word) for w in (s.words or [])]})
        f.write(f"[{int(s.start//60):02d}:{s.start%60:05.2f} - {int(s.end//60):02d}:{s.end%60:05.2f}] {s.text.strip()}\n"); f.flush()
json.dump(out, open(f'audio/{v}.json','w'))
print('done',v)
