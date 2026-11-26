"""Free video on Hugging Face ZeroGPU Spaces (needs a free HF account token for quota).
Dance (motion transfer, Wan2.2-Animate):
  python -I video_hf.py dance <driving_dance.mp4> <actor_image.png> <out.mp4> [--seconds 5] [--mode "Character Swap"|"Animation"] [--hd]
Lip-sync (LatentSync):
  python -I video_hf.py lipsync <actor_video.mp4> <audio.mp3|wav> <out.mp4>
Token: HF_TOKEN env var, or a proxy-injected credential for huggingface.co."""
import sys, shutil, argparse, os
from gradio_client import Client, handle_file
a=argparse.ArgumentParser(); a.add_argument("job",choices=["dance","lipsync"]); a.add_argument("a"); a.add_argument("b"); a.add_argument("out")
a.add_argument("--seconds",type=float,default=5); a.add_argument("--mode",default="Animation"); a.add_argument("--hd",action="store_true")
x=a.parse_args(); tok=os.environ.get("HF_TOKEN") or None
def path(r): return r["video"] if isinstance(r,dict) and "video" in r else (r["path"] if isinstance(r,dict) else r)
if x.job=="dance":
    c=Client("alexnasa/Wan2.2-Animate-ZEROGPU",token=tok,verbose=False)
    r=c.predict(input_video={"video":handle_file(x.a)},max_duration_s=x.seconds,edited_frame=handle_file(x.b),
                rc_str=x.mode,resolution_choice="High Res" if x.hd else "Low Res",api_name="/animate_scene")
    shutil.copy(path(r[0]),x.out)
else:
    c=Client("fffiloni/LatentSync",token=tok,verbose=False)
    r=c.predict(input_video_path={"video":handle_file(x.a)},input_audio_path=handle_file(x.b),api_name="/generate_lip_sync_video")
    shutil.copy(path(r),x.out)
print("OK",x.out)
