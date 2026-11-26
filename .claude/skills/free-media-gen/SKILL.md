---
name: free-media-gen
description: Generate images (and short videos) for the AI influencer at zero cost, using free Hugging Face Spaces (FLUX.1-dev / FLUX.1-schnell via gradio_client) instead of paid MuAPI. Use whenever the user wants to generate without paying, or MuAPI balance is 0. Works with ugc-creator prompt files.
---

# free-media-gen

Zero-cost replacement for MuAPI generation. Prompts still come from `ugc-creator`
(identity card + 6 layers); only the backend changes.

## Backends (free)

| Backend | What | Limit |
|---|---|---|
| HF Space `black-forest-labs/FLUX.1-dev` | best free photoreal stills | anonymous: ~1 run, then quota. Free HF account token: more daily ZeroGPU quota |
| HF Space `black-forest-labs/FLUX.1-schnell` | faster, lower quality | same quota pool |
| Pollinations keyless (`image.pollinations.ai`) | fallback only | old model, low res, watermark, ignores details: do not use for the actor |
| Pollinations with free account key (see `pollinations-api` skill, device flow) | flux etc. with seed/size | free daily allowance |

Video is the expensive part: free options are HF Spaces for Wan image-to-video
(ZeroGPU quota, a few short clips per day with a free account). Keep clips 5 s.

## Setup

```bash
python3 -m venv .venv-gen && .venv-gen/bin/pip install gradio_client
# optional, more quota: free token from huggingface.co/settings/tokens (read scope)
export HF_TOKEN=...   # never commit it
```

## Run

```bash
.venv-gen/bin/python -I .claude/skills/free-media-gen/scripts/hf_flux.py \
  <prompt.md with "## Positive prompt" / "## Negative" sections> <outdir> \
  black-forest-labs/FLUX.1-dev <seed> [<seed> ...]
```

Always view each output before keeping it; reject any image that drops the
outfit, the green eyes or the identity marks, and regenerate.
