import cv2, numpy as np
DET=cv2.FaceDetectorYN.create('models/face_detection_yunet_2023mar.onnx','',(320,320),0.55,0.3,5000)
REC=cv2.FaceRecognizerSF.create('models/face_recognition_sface_2021dec.onnx','')
def detect(img, s=0.5):
    h,w=img.shape[:2]; small=cv2.resize(img,(int(w*s),int(h*s)),interpolation=cv2.INTER_AREA)
    DET.setInputSize((small.shape[1],small.shape[0]))
    _,f=DET.detect(small)
    if f is None: return []
    f=f.copy(); f[:,:14]/=s
    return list(f)
def embed(img,face):
    al=REC.alignCrop(img,face); return REC.feature(al)
def sim(a,b): return REC.match(a,b,cv2.FaceRecognizerSF_FR_COSINE)
