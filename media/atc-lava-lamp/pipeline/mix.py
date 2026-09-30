import numpy as np, wave
from scipy import signal
import timeline as TL
SR = 44100


def rd(p):
    w = wave.open(p); ch = w.getnchannels()
    a = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(np.float64) / 32768
    return a.reshape(-1, ch)


music = rd('music.wav'); sfx = rd('sfx.wav'); voice = rd('voice_raw.wav')[:, 0]
N = int(TL.END * SR)
music = music[:N]; sfx = sfx[:N]

# voice chain: HPF, presence lift, light compression, fades
voice = signal.sosfilt(signal.butter(2, 90, 'high', fs=SR, output='sos'), voice)
b, a = signal.iirpeak(3000 / (SR / 2), 1.2)
voice = voice + 0.35 * signal.lfilter(b, a, voice)
env = np.sqrt(signal.sosfilt(signal.butter(1, 12, fs=SR, output='sos'), voice ** 2) + 1e-9)
thr = 10 ** (-24 / 20)
gain = np.where(env > thr, (env / thr) ** (1 / 3 - 1), 1.0)
voice = voice * gain
voice /= np.max(np.abs(voice)) + 1e-9
fl = int(0.03 * SR)
voice[:fl] *= np.linspace(0, 1, fl); voice[-fl:] *= np.linspace(1, 0, fl)

vt = TL.VOICE['t']
vi = int(vt * SR)
vbuf = np.zeros(N); vbuf[vi:vi + len(voice)] = voice[:N - vi]

# duck the music under the voice
duck = np.ones(N)
d0, d1 = vi - int(0.08 * SR), vi + len(voice) + int(0.02 * SR)
ramp = int(0.08 * SR)
duck[d0:d1] = 10 ** (-8 / 20)
duck[d0 - ramp:d0] = np.linspace(1, 10 ** (-8 / 20), ramp)
duck[d1:d1 + ramp] = np.linspace(10 ** (-8 / 20), 1, ramp)

out = music * duck[:, None] + sfx * 0.9 + (vbuf * 0.85)[:, None]
fo = int(0.4 * SR)
out[-fo:] *= np.linspace(1, 0, fo)[:, None]
out *= 0.95 / np.max(np.abs(out))
w = wave.open('mix.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(out, -1, 1) * 32767).astype('<i2').tobytes()); w.close()
print('mix ok', len(out) / SR)
