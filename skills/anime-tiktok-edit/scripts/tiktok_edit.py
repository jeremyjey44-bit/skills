#!/usr/bin/env python3
"""Turn a landscape anime clip into a vertical 4K TikTok edit.

Pipeline (all automatic, ffmpeg only):
  1. detect black bars / letterboxing and crop them away
  2. detect scene cuts and pick the climax (strongest cut in the second half)
  3. compose 2160x3840: blurred background (top part of the frame, so burned-in
     subtitles do not ghost) + sharp foreground at full width
  4. punch-in zooms on the strongest cuts, white flash + camera shake on the climax
  5. hook text above the picture (outside TikTok's UI safe zones)
  6. loudness normalised to -14 LUFS; optional music bed ducked under the voice

Usage:
  python3 tiktok_edit.py INPUT.mp4 -o OUT.mp4 --hook "QUAND ELLE DÉCIDE|DE TOUT DONNER..."
  python3 tiktok_edit.py INPUT.mp4 -o OUT.mp4 --music epic.mp3 --music-start 12 --music-volume 0.35
  python3 tiktok_edit.py INPUT.mp4 --analyze        # print detected crop / cuts / climax only
"""

import argparse
import collections
import json
import os
import re
import subprocess
import sys
import tempfile

W, H = 2160, 3840
FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/inter/Inter-Black.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def run(cmd, capture=True):
    r = subprocess.run(cmd, capture_output=capture, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-3000:] if r.stderr else "")
        raise SystemExit(f"command failed: {' '.join(cmd[:4])} ...")
    return r


def probe(path):
    r = run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path])
    info = json.loads(r.stdout)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    has_audio = any(s["codec_type"] == "audio" for s in info["streams"])
    w, h = int(v["width"]), int(v["height"])
    rot = 0
    for sd in v.get("side_data_list", []):
        if "rotation" in sd:
            rot = int(float(sd["rotation"]))
    if "rotate" in v.get("tags", {}):
        rot = int(v["tags"]["rotate"])
    if abs(rot) % 180 == 90:
        w, h = h, w  # ffmpeg auto-rotates, so work in display orientation
    return {"w": w, "h": h, "duration": float(info["format"]["duration"]), "audio": has_audio}


def time_args(a):
    out = []
    if a.start is not None:
        out += ["-ss", str(a.start)]
    if a.end is not None:
        out += ["-to", str(a.end)]
    return out


def detect_crop(path, a, info):
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", *time_args(a), "-i", path, "-vf", "fps=4,cropdetect=24:2:0",
         "-an", "-f", "null", "-"], capture_output=True, text=True)
    crops = re.findall(r"crop=(\d+):(\d+):(\d+):(\d+)", r.stderr)
    if not crops:
        return (info["w"], info["h"], 0, 0)
    cnt = collections.Counter(crops)
    total = sum(cnt.values())
    # union of every crop seen in >=5% of samples (dark shots give smaller crops)
    keep = [tuple(map(int, c)) for c, n in cnt.items() if n / total >= 0.05] or [tuple(map(int, cnt.most_common(1)[0][0]))]
    x0 = min(c[2] for c in keep); y0 = min(c[3] for c in keep)
    x1 = max(c[2] + c[0] for c in keep); y1 = max(c[3] + c[1] for c in keep)
    cw, ch = (x1 - x0) // 2 * 2, (y1 - y0) // 2 * 2
    if cw * ch < 0.25 * info["w"] * info["h"]:
        return (info["w"], info["h"], 0, 0)
    return (cw, ch, x0, y0)


def detect_cuts(path, a, crop):
    cw, ch, cx, cy = crop
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", *time_args(a), "-i", path, "-vf",
         f"crop={cw}:{ch}:{cx}:{cy},scale=320:-2,select='gte(scene,0)',metadata=print:key=lavfi.scene_score",
         "-an", "-f", "null", "-"], capture_output=True, text=True)
    cuts, t = [], None
    for line in r.stderr.splitlines():
        m = re.search(r"pts_time:([\d.]+)", line)
        if m:
            t = float(m.group(1))
        m = re.search(r"scene_score=([\d.]+)", line)
        if m and t is not None and float(m.group(1)) >= 0.2:
            cuts.append((t, float(m.group(1))))
    return cuts


def pick_moments(cuts, duration):
    cuts = [c for c in cuts if 0.5 < c[0] < duration - 0.8]
    if not cuts:
        return None, []
    late = [c for c in cuts if c[0] >= 0.4 * duration] or cuts
    climax = max(late, key=lambda c: c[1])[0]
    punches = [climax]
    for t, _ in sorted(cuts, key=lambda c: -c[1]):
        if all(abs(t - p) >= 1.5 for p in punches):
            punches.append(t)
        if len(punches) >= 3:
            break
    return climax, sorted(punches)


def esc(expr):
    return expr.replace(",", "\\,")


def build(a):
    info = probe(a.input)
    dur = info["duration"]
    if a.end is not None:
        dur = min(dur, a.end)
    if a.start is not None:
        dur -= a.start
    crop = detect_crop(a.input, a, info)
    cuts = detect_cuts(a.input, a, crop)
    climax, punches = pick_moments(cuts, dur)
    if a.climax is not None:
        climax = a.climax
        punches = sorted(set([climax] + [p for p in punches if abs(p - climax) >= 1.5]))[:3]
    if a.punches:
        punches = sorted(float(x) for x in a.punches.split(","))
        if climax is not None and all(abs(climax - p) > 0.05 for p in punches):
            punches = sorted(punches + [climax])
    report = {"duration": round(dur, 2), "crop": crop, "cuts": [round(c[0], 2) for c in cuts],
              "climax": climax, "punches": punches}
    print(json.dumps(report), file=sys.stderr)
    if a.analyze:
        return

    cw, ch, cx, cy = crop
    aspect = cw / ch
    vertical = aspect <= 0.75 or a.style == "crop"

    zoom_terms = ["1.04"]
    for p in punches:
        amp, k = (0.14, 3.5) if p == climax else (0.10, 5)
        zoom_terms.append(f"{amp}*between(t,{p:.3f},{p + 1.2:.3f})*exp(-(t-{p:.3f})*{k})")
    Z = "+".join(zoom_terms)
    SH = f"between(t,{climax + 0.45:.3f},{climax + 1.3:.3f})*16*sin(t*95)" if climax else "0"

    font = next((f for f in FONT_CANDIDATES if os.path.exists(f)), None)
    tmp = tempfile.mkdtemp()
    filters = [f"[0:v]crop={cw}:{ch}:{cx}:{cy},setsar=1" + ("[b]" if vertical else ",split=2[a][b]")]

    if vertical:
        fg_w, fg_h = W, H
        scale_w = f"trunc(max({W}/{cw}\\,{H}/{ch})*{cw}*({esc(Z)})/2)*2"
        scale_h = f"trunc(max({W}/{cw}\\,{H}/{ch})*{ch}*({esc(Z)})/2)*2"
        ybase = "(in_h-oh)/2"
    else:
        fg_w, fg_h = W, int(W / aspect) // 2 * 2
        top = max(1, int(ch * 0.55)) // 2 * 2
        filters.append(f"[a]crop={cw}:{top}:0:0,scale=-2:{H}:flags=bicubic,crop={W}:{H},"
                       "boxblur=45:3,eq=brightness=-0.18:saturation=1.15[bg]")
        scale_w = f"trunc({W}*({esc(Z)})/2)*2"
        scale_h = f"trunc({W}*({esc(Z)})*{ch}/{cw}/2)*2"
        ybase = "in_h-oh"  # zoom anchored to the bottom so burned-in subtitles stay whole
    filters.append(
        f"[b]scale=w='{scale_w}':h='{scale_h}':eval=frame:flags=lanczos,"
        f"crop={fg_w}:{fg_h}:x='(in_w-out_w)/2+{esc(SH)}':y='max(0\\,{ybase}-abs(0.6*{esc(SH)}))',"
        "unsharp=5:5:0.6:5:5:0,eq=contrast=1.06:saturation=1.12[fg]")

    post = []
    if climax:
        post.append(f"drawbox=x=0:y=0:w=iw:h=ih:color=white@0.75:t=fill:enable='between(t,{climax:.3f},{climax + 0.08:.3f})'")
    if a.hook and font:
        lines = [l.strip() for l in a.hook.split("|") if l.strip()][:2]
        size = min(150, int(1950 / (0.68 * max(len(l) for l in lines))))
        content_top = (H - fg_h) // 2 if not vertical else 700
        y = max(330, content_top - 120 - size * 1.3 * len(lines)) if not vertical else 520
        colors = ["white", "0xFF3B30"] if len(lines) == 2 else ["white"]
        for i, (line, col) in enumerate(zip(lines, colors)):
            tf = os.path.join(tmp, f"l{i}.txt")
            open(tf, "w").write(line)
            post.append(f"drawtext=fontfile={font}:textfile={tf}:fontsize={size}:fontcolor={col}:"
                        f"borderw={max(6, size // 15)}:bordercolor=black:x=(w-tw)/2:y={int(y + i * size * 1.27)}:"
                        f"alpha='min(max(t-{0.25 * i},0)/0.3,1)'")
    post.append("format=yuv420p")
    if vertical:
        filters.append("[fg]" + ",".join(post) + "[v]")
    else:
        filters.append("[bg][fg]overlay=(W-w)/2:(H-h)/2," + ",".join(post) + "[v]")

    cmd = ["ffmpeg", "-v", "error", "-stats", "-y", *time_args(a), "-i", a.input]
    amap = []
    if a.music:
        cmd += ["-ss", str(a.music_start), "-i", a.music]
        fo = max(0.0, dur - 1.0)
        mus = (f"[1:a]atrim=0:{dur:.3f},asetpts=PTS-STARTPTS,volume={a.music_volume},"
               f"afade=t=in:d=0.3,afade=t=out:st={fo:.3f}:d=1,aformat=channel_layouts=stereo[m]")
        if info["audio"]:
            filters += [f"[0:a]aformat=channel_layouts=stereo,asplit=2[vo][key]", mus,
                        "[m][key]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[md]",
                        "[vo][md]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[aout]"]
        else:
            filters += [mus, "[m]loudnorm=I=-14:TP=-1.5:LRA=11[aout]"]
        amap = ["-map", "[aout]"]
    elif info["audio"]:
        filters.append("[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
        amap = ["-map", "[aout]"]

    cmd += ["-filter_complex", ";".join(filters), "-map", "[v]", *amap,
            "-c:v", "libx264", "-preset", a.preset, "-crf", "16", "-profile:v", "high", "-level", "5.2",
            "-r", str(a.fps), "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", a.output]
    subprocess.run(cmd, check=True)
    print(f"wrote {a.output}", file=sys.stderr)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input")
    p.add_argument("-o", "--output", default="tiktok_4k.mp4")
    p.add_argument("--hook", help='hook text, two lines separated by "|"')
    p.add_argument("--style", choices=["blur", "crop"], default="blur")
    p.add_argument("--start", type=float, help="trim: start second in the source")
    p.add_argument("--end", type=float, help="trim: end second in the source")
    p.add_argument("--climax", type=float, help="override detected climax time (seconds, after trim)")
    p.add_argument("--punches", help="comma-separated punch-in zoom times (seconds), overrides detection")
    p.add_argument("--music", help="music file to mix under the voice (ducked)")
    p.add_argument("--music-start", type=float, default=0.0, help="offset into the music file")
    p.add_argument("--music-volume", type=float, default=0.35)
    p.add_argument("--fps", type=int, default=60)
    p.add_argument("--preset", default="slow")
    p.add_argument("--analyze", action="store_true", help="only print detection results")
    build(p.parse_args())


if __name__ == "__main__":
    main()
