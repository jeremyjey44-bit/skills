"""Swap the reference face onto generated images (InsightFace inswapper_128, CPU).
Usage: python -I faceswap.py reference.png out_dir img1.png [img2.png ...]  -> out_dir/<name>.png (+ board.jpg)"""
import sys, os, cv2, urllib.request, zipfile
import insightface
from insightface.app import FaceAnalysis
from PIL import Image, ImageDraw, ImageFont
home=os.path.expanduser("~/.insightface/models"); os.makedirs(home,exist_ok=True)
sw=os.path.join(home,"inswapper_128.onnx")
if not os.path.exists(sw):
    urllib.request.urlretrieve("https://huggingface.co/ezioruan/inswapper_128.onnx/resolve/main/inswapper_128.onnx",sw)
app=FaceAnalysis(name="buffalo_l",providers=["CPUExecutionProvider"]); app.prepare(ctx_id=-1,det_size=(640,640))
swapper=insightface.model_zoo.get_model(sw,providers=["CPUExecutionProvider"])
ref,out,imgs=sys.argv[1],sys.argv[2],sys.argv[3:]
src=max(app.get(cv2.imread(ref)),key=lambda f:f.bbox[2]-f.bbox[0])
done=[]
for p in imgs:
    im=cv2.imread(p); faces=app.get(im)
    if not faces: print("NOFACE",p); continue
    tgt=max(faces,key=lambda f:f.bbox[2]-f.bbox[0])
    res=swapper.get(im,tgt,src,paste_back=True)
    dst=os.path.join(out,os.path.basename(p)); cv2.imwrite(dst,res); done.append(dst); print("OK",dst,flush=True)
if done:
    cols=min(4,len(done)); w,h=416,608; rows=(len(done)+cols-1)//cols
    b=Image.new("RGB",(cols*w,rows*(h+40)),"white"); d=ImageDraw.Draw(b)
    try: f=ImageFont.truetype("DejaVuSans-Bold.ttf",26)
    except Exception: f=ImageFont.load_default()
    for i,p in enumerate(done):
        X,Y=(i%cols)*w,(i//cols)*(h+40); b.paste(Image.open(p).resize((w,h)),(X,Y+40)); d.text((X+10,Y+6),os.path.basename(p)[:-4],fill="black",font=f)
    b.save(os.path.join(out,"board.jpg"),quality=88)
