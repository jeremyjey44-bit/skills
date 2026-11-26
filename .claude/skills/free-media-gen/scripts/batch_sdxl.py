"""Batch local generation: one model load, many prompts. Usage: python -I batch_sdxl.py prompts.json outdir
prompts.json = {"name": "prompt", ...}. Also writes outdir/board.jpg (labelled contact sheet)."""
import sys, json, time, torch
from PIL import Image, ImageDraw, ImageFont
from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler
NEG=("cartoon, 3d render, cgi, plastic skin, airbrushed, doll, deformed face, extra fingers, bad hands, "
     "blurry, lowres, watermark, text, nude, nsfw, heavy makeup, old, wrinkles")
prompts=json.load(open(sys.argv[1])); out=sys.argv[2]; seed=int(sys.argv[3]) if len(sys.argv)>3 else 7
if len(sys.argv)>4: NEG=sys.argv[4]
pipe=StableDiffusionXLPipeline.from_single_file(
  "https://huggingface.co/SG161222/RealVisXL_V5.0_Lightning/blob/main/RealVisXL_V5.0_Lightning_fp16.safetensors",
  torch_dtype=torch.bfloat16)
pipe.scheduler=DPMSolverMultistepScheduler.from_config(pipe.scheduler.config,algorithm_type="sde-dpmsolver++",use_karras_sigmas=True)
pipe.set_progress_bar_config(disable=True)
imgs=[]
for name,p in prompts.items():
    t=time.time()
    im=pipe(p,negative_prompt=NEG,width=832,height=1216,num_inference_steps=6,guidance_scale=1.5,
            generator=torch.Generator().manual_seed(seed)).images[0]
    im.save(f"{out}/{name}.png"); imgs.append((name,im)); print("OK",name,f"{time.time()-t:.0f}s",flush=True)
cols=4; w,h=416,608; rows=(len(imgs)+cols-1)//cols
board=Image.new("RGB",(cols*w,rows*(h+40)),"white"); d=ImageDraw.Draw(board)
try: f=ImageFont.truetype("DejaVuSans-Bold.ttf",28)
except Exception: f=ImageFont.load_default()
for i,(n,im) in enumerate(imgs):
    x,y=(i%cols)*w,(i//cols)*(h+40); board.paste(im.resize((w,h)),(x,y+40)); d.text((x+10,y+5),n,fill="black",font=f)
board.save(f"{out}/board.jpg",quality=88); print("BOARD done",flush=True)
