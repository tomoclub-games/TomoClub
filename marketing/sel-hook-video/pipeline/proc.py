"""Privacy pass: blur student faces + student names in a source segment.
usage: python3 proc.py clips.json NAME
Writes proc/NAME.mp4 (1920x1080, 25fps, with audio) and proc/NAME.json (detections)."""
import cv2, numpy as np, json, sys, subprocess, re, difflib, os
from faces import detect, embed, sim
from rapidocr_onnxruntime import RapidOCR
REFS=np.load('models/vk_refs.npy')
STUDENTS=['reyansh','krishay','vishnu','paavani','gupta','vedant','sudeep','nyskool','rayansh','pavani','vedan']
def is_name(txt):
    for w in re.findall(r'[a-z]+', txt.lower()):
        if len(w)<3: continue
        for n in STUDENTS:
            if w in n or n in w or difflib.SequenceMatcher(None,w,n).ratio()>=0.7: return True
    return False
cfg=json.load(open(sys.argv[1]))[sys.argv[2]]
name=sys.argv[2]; src=cfg['src']; t0=cfg['t0']; t1=cfg['t1']
OCR_EVERY=cfg.get('ocr_every',3 if cfg.get('step',1)==1 else 1); FACE_HOLD=cfg.get('face_hold',10); OCR_HOLD=cfg.get('ocr_hold', OCR_EVERY*2+2 if cfg.get('step',1)==1 else 0)
cap=cv2.VideoCapture(src); cap.set(cv2.CAP_PROP_POS_MSEC,t0*1000)
fps=25; STEP=cfg.get('step',1); n=int(round((t1-t0)*fps/STEP))
frames=[]; dets=[]
ocr=RapidOCR() if cfg.get('ocr',True) else None
for i in range(n):
    for _ in range(STEP-1): cap.grab()
    ok,fr=cap.read()
    if not ok: break
    frames.append(cv2.resize(fr,(1920,1080),interpolation=cv2.INTER_AREA))
    faces=[]
    fl=detect(fr,0.5)
    if cfg.get('thumbs'):  # full-res pass on the Zoom thumbnail strip (top-right)
        for f in detect(np.ascontiguousarray(fr[:540,2200:]),1.0):
            f=f.copy(); f[0]+=2200; f[4:14:2]+=2200; fl.append(f)
    for f in fl:
        try: s=max(sim(embed(fr,f),r) for r in REFS)
        except Exception: s=0
        faces.append([float(f[0]),float(f[1]),float(f[2]),float(f[3]),float(s)])
    txt=[]
    if ocr and i%OCR_EVERY==0:
        res,_=ocr(cv2.resize(fr,(1920,1080),interpolation=cv2.INTER_AREA))
        for box,t,sc in (res or []):
            if is_name(t):
                b=np.array(box)*(2560/1920); x0,y0=b.min(0); x1,y1=b.max(0)
                txt.append([float(x0),float(y0),float(x1-x0),float(y1-y0),t])
    dets.append({'faces':faces,'txt':txt})
json.dump(dets,open(f'proc/{name}.json','w'))
S=1920/2560
def blur_region(img, x,y,w,h, oval=False, k=None):
    H,W=img.shape[:2]; x0=max(0,int(x)); y0=max(0,int(y)); x1=min(W,int(x+w)); y1=min(H,int(y+h))
    if x1<=x0 or y1<=y0: return
    roi=img[y0:y1,x0:x1]
    sm=cv2.resize(roi,(max(1,(x1-x0)//14),max(1,(y1-y0)//14)),interpolation=cv2.INTER_AREA)
    bl=cv2.GaussianBlur(cv2.resize(sm,(x1-x0,y1-y0),interpolation=cv2.INTER_LINEAR),(0,0),max(3,(x1-x0)/18))
    if oval:
        m=np.zeros((y1-y0,x1-x0),np.float32)
        cv2.ellipse(m,((x1-x0)//2,(y1-y0)//2),((x1-x0)//2,(y1-y0)//2),0,0,360,1,-1)
        m=cv2.GaussianBlur(m,(0,0),max(2,(x1-x0)/25))[...,None]
        img[y0:y1,x0:x1]=(bl*m+roi*(1-m)).astype(np.uint8)
    else: img[y0:y1,x0:x1]=bl
VK_T=cfg.get('vk_thresh',0.38)
aud=['-ss',str(t0),'-t',str(len(frames)/fps),'-i',src,'-map','0:v','-map','1:a','-c:a','aac','-b:a','192k'] if STEP==1 else []
proc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s','1920x1080','-r','25','-i','-']+aud+
  ['-c:v','libx264','-crf','14','-preset','fast','-pix_fmt','yuv420p',f'proc/{name}.mp4'],stdin=subprocess.PIPE)
for i,fr in enumerate(frames):
    boxes=[]
    for j in range(max(0,i-FACE_HOLD),min(len(frames),i+FACE_HOLD+1)):
        for x,y,w,h,s in dets[j]['faces']:
            if s>=VK_T and not cfg.get('blur_vk'): continue
            boxes.append((x,y,w,h))
    for x,y,w,h in boxes:
        cx,cy=x+w/2,y+h/2; W2=w*1.9; H2=h*2.1
        blur_region(fr,(cx-W2/2)*S,(cy-H2*0.55)*S,W2*S,H2*S,oval=True)
    for j in range(max(0,i-OCR_HOLD),min(len(frames),i+OCR_HOLD+1)):
        for x,y,w,h,t in dets[j]['txt']:
            p=max(10,h*0.5); blur_region(fr,(x-p)*S,(y-p)*S,(w+2*p)*S,(h+2*p)*S)
    for x,y,w,h in cfg.get('static',[]):
        blur_region(fr,x*S,y*S,w*S,h*S)
    proc.stdin.write(fr.tobytes())
proc.stdin.close(); proc.wait()
print('done',name,len(frames))
