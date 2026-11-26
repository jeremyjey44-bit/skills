"""Identity similarity (ArcFace cosine) between a reference face and images. >0.6 = same person for the recognizer.
Usage: python -I face_score.py reference.png img1 [img2 ...]"""
import sys, cv2, numpy as np
from insightface.app import FaceAnalysis
app=FaceAnalysis(name="buffalo_l",providers=["CPUExecutionProvider"]); app.prepare(ctx_id=-1,det_size=(640,640))
def emb(p):
    f=app.get(cv2.imread(p)); 
    return None if not f else max(f,key=lambda x:x.bbox[2]-x.bbox[0]).normed_embedding
r=emb(sys.argv[1])
for p in sys.argv[2:]:
    e=emb(p); print(f"{'NOFACE' if e is None else round(float(np.dot(r,e)),3)}\t{p.split('/')[-2]}/{p.split('/')[-1]}")
