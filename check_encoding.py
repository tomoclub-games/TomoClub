with open('styles.css', 'rb') as f:
    rawdata = f.read(100)
    if b'\x00' in rawdata:
        print("Likely UTF-16")
    else:
        print("Likely UTF-8 or ASCII")
    print(rawdata[:20])
