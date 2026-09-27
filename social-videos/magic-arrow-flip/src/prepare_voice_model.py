"""Fetch the Kokoro-82M voice model (Apache-2.0) used for the narration.

The quantized model and voice styles are taken from the `expo-kokoro` npm
package (registry.npmjs.org), then the per-voice style files are packed into
the voices.bin archive that kokoro-onnx expects.

  python prepare_voice_model.py      -> kokoro-quantized.onnx + voices.bin
"""
import io
import os
import tarfile
import urllib.request

import numpy as np

URL = "https://registry.npmjs.org/expo-kokoro/-/expo-kokoro-1.1.9.tgz"
HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    data = urllib.request.urlopen(URL).read()
    voices = {}
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        for m in tar.getmembers():
            name = m.name
            if name.endswith("kokoro-quantized.onnx"):
                with open(os.path.join(HERE, "kokoro-quantized.onnx"), "wb") as f:
                    f.write(tar.extractfile(m).read())
            elif "/voices/" in name and name.endswith(".bin"):
                arr = np.frombuffer(tar.extractfile(m).read(), dtype=np.float32).reshape(-1, 1, 256)
                voices[os.path.basename(name)[:-4]] = arr
    with open(os.path.join(HERE, "voices.bin"), "wb") as f:
        np.savez(f, **voices)
    print(f"kokoro-quantized.onnx + voices.bin ({len(voices)} voices) ready")


if __name__ == "__main__":
    main()
