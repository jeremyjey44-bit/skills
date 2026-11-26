import sys, shutil, re
from gradio_client import Client
md, outdir, space = sys.argv[1], sys.argv[2], sys.argv[3]
seeds = [int(s) for s in sys.argv[4:]]
t = open(md).read()
pos = re.search(r"## Positive prompt\n(.*?)\n## Negative", t, re.S).group(1).strip().replace("\n", " ")
c = Client(space, verbose=False)
for s in seeds:
    try:
        kw = dict(prompt=pos, seed=s, randomize_seed=False, width=768, height=1344, api_name="/infer")
        if "dev" in space: kw.update(guidance_scale=3.5, num_inference_steps=28)
        else: kw.update(num_inference_steps=4)
        img, seed = c.predict(**kw)
        p = img["path"] if isinstance(img, dict) else img
        dst = f"{outdir}/portrait_{s}.webp"; shutil.copy(p, dst); print("OK", dst)
    except Exception as e: print("ERR", s, repr(e)[:300])
