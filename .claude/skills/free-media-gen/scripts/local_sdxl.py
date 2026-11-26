"""Local, unlimited, free image generation on CPU with RealVisXL V5 Lightning (SDXL).
Usage: python -I local_sdxl.py --prompt "..." --out out.png [--seed 1] [--w 832 --h 1216] [--steps 6]
SDXL reads ~75 tokens per prompt: put the most important features first."""
import argparse, time, torch
from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler
NEG = ("cartoon, 3d render, cgi, plastic skin, airbrushed, doll, deformed, extra fingers, bad hands, "
       "blurry, lowres, watermark, text, nude, nsfw, heavy makeup")
a = argparse.ArgumentParser()
a.add_argument("--prompt", required=True); a.add_argument("--out", required=True)
a.add_argument("--negative", default=NEG); a.add_argument("--seed", type=int, default=73519)
a.add_argument("--w", type=int, default=832); a.add_argument("--h", type=int, default=1216)
a.add_argument("--steps", type=int, default=6); a.add_argument("--cfg", type=float, default=1.5)
x = a.parse_args()
torch.set_num_threads(torch.get_num_threads())
t = time.time()
pipe = StableDiffusionXLPipeline.from_single_file(
    "https://huggingface.co/SG161222/RealVisXL_V5.0_Lightning/blob/main/RealVisXL_V5.0_Lightning_fp16.safetensors",
    torch_dtype=torch.bfloat16)
pipe.scheduler = DPMSolverMultistepScheduler.from_config(
    pipe.scheduler.config, algorithm_type="sde-dpmsolver++", use_karras_sigmas=True)
print(f"loaded in {time.time()-t:.0f}s", flush=True); t = time.time()
img = pipe(x.prompt, negative_prompt=x.negative, width=x.w, height=x.h, num_inference_steps=x.steps,
           guidance_scale=x.cfg, generator=torch.Generator().manual_seed(x.seed)).images[0]
img.save(x.out); print(f"saved {x.out} in {time.time()-t:.0f}s", flush=True)
