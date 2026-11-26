"""Same-face generation: RealVisXL V5 Lightning + IP-Adapter Plus Face (SDXL), local CPU.
Usage: python -I identity_sdxl.py face_crop.png prompts.json outdir [--scale 0.7] [--seed 7]
prompts.json = {"name": "prompt"}. Writes outdir/<name>.png and outdir/board.jpg."""
import sys, json, time, argparse, torch
from PIL import Image, ImageDraw, ImageFont
from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler
from transformers import CLIPVisionModelWithProjection
NEG=("cartoon, 3d render, cgi, plastic skin, airbrushed, doll, deformed face, extra fingers, bad hands, "
     "blurry, lowres, watermark, text, nude, nsfw, heavy makeup, old")
a=argparse.ArgumentParser(); a.add_argument("face"); a.add_argument("prompts"); a.add_argument("out")
a.add_argument("--scale",type=float,default=0.7); a.add_argument("--seed",type=int,default=7)
x=a.parse_args()
enc=CLIPVisionModelWithProjection.from_pretrained("h94/IP-Adapter",subfolder="models/image_encoder",torch_dtype=torch.bfloat16)
pipe=StableDiffusionXLPipeline.from_single_file(
  "https://huggingface.co/SG161222/RealVisXL_V5.0_Lightning/blob/main/RealVisXL_V5.0_Lightning_fp16.safetensors",
  image_encoder=enc, torch_dtype=torch.bfloat16)
pipe.scheduler=DPMSolverMultistepScheduler.from_config(pipe.scheduler.config,algorithm_type="sde-dpmsolver++",use_karras_sigmas=True)
pipe.load_ip_adapter("h94/IP-Adapter",subfolder="sdxl_models",weight_name="ip-adapter-plus-face_sdxl_vit-h.safetensors")
pipe.set_ip_adapter_scale(x.scale); pipe.set_progress_bar_config(disable=True)
face=Image.open(x.face).convert("RGB")
imgs=[]
for name,p in json.load(open(x.prompts)).items():
    t=time.time()
    im=pipe(p,negative_prompt=NEG,ip_adapter_image=face,width=832,height=1216,num_inference_steps=6,
            guidance_scale=1.5,generator=torch.Generator().manual_seed(x.seed)).images[0]
    im.save(f"{x.out}/{name}.png"); imgs.append((name,im)); print("OK",name,f"{time.time()-t:.0f}s",flush=True)
cols=min(4,len(imgs)); w,h=416,608; rows=(len(imgs)+cols-1)//cols
board=Image.new("RGB",(cols*w,rows*(h+40)),"white"); d=ImageDraw.Draw(board)
try: f=ImageFont.truetype("DejaVuSans-Bold.ttf",26)
except Exception: f=ImageFont.load_default()
for i,(n,im) in enumerate(imgs):
    X,Y=(i%cols)*w,(i//cols)*(h+40); board.paste(im.resize((w,h)),(X,Y+40)); d.text((X+10,Y+6),n,fill="black",font=f)
board.save(f"{x.out}/board.jpg",quality=88); print("BOARD done",flush=True)
