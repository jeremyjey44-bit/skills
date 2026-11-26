---
name: anime-tiktok-edit
description: Turn an anime scene (screen recording or clip the user provides) into a vertical 9:16 4K TikTok edit with a hook caption, punch-in zooms, a flash and camera shake on the climax, a blurred background and TikTok-level loudness, plus optional ducked music. Also covers researching which anime moments are trending on TikTok. Use when the user sends an anime clip and asks for TikTok, Reels or Shorts format, "4K", "viral" or "edit" versions of it.
---

# Anime → TikTok 4K edit

## Requirements

- `ffmpeg` / `ffprobe` (6.x) and `python3`. No pip packages are needed.
- Optional: a bold font. The script uses Inter Black, or falls back to DejaVu Sans Bold.
- Optional: music generation through muapi.ai (`suno-create-music`, instrumental). This costs
  credits, so ask the user before calling it.

## Source footage

Only edit footage the user supplies: their own screen recordings or clips. Do not download
episodes from streaming or pirate sites, and do not rip videos from YouTube or TikTok. Tell the
user that reposting copyrighted anime can get the sound muted or the video removed.

## Workflow

1. **Inspect** the clip: `python3 scripts/tiktok_edit.py IN --analyze`. This prints the detected
   crop (black bars from screen recordings are removed automatically), the scene cuts, the climax
   and the punch-in times. Extract 3–4 frames, look at them, and check the crop and the climax.
2. **Pick a hook.** Write 2 short lines in the viewer's language, in capitals, under 20 characters
   per line, built on the scene's emotion ("QUAND ELLE DÉCIDE|DE TOUT DONNER..."). Read the burned-in
   subtitles for context. Never guess the anime's name.
3. **Render**:
   ```bash
   python3 scripts/tiktok_edit.py IN -o OUT.mp4 --hook "LINE 1|LINE 2" [--start S --end E] [--climax T]
   ```

   - The default style is `blur`: the picture at full width over a blurred copy of itself. It
     keeps burned-in subtitles whole. Use `--style crop` for full-screen footage without subtitles.
   - Zooms are anchored to the bottom of the picture, so the subtitles stay visible.
   - Output: 2160×3840, H.264 CRF 16, 60 fps, AAC 192k, -14 LUFS, faststart.
   - It renders at about 0.12× real time. Use `--preset medium` for a faster preview.
4. **Verify**: extract frames at the punch-in times and at the climax, and check that the
   subtitles are not cut and the text is readable.
5. **Music** (optional): `--music track.mp3 --music-start <offset> --music-volume 0.35`. The music
   is ducked under the voice with a sidechain compressor and faded out over the last second. Tell
   the user that a trending sound added in the TikTok app usually gets more reach than music baked
   into the file.

## Finding viral moments

Search the web for current trends: TikTok discover pages ("trending anime edits"), the TikTok
Creative Center, this season's episode threads on Reddit/MyAnimeList, and episode scores on
Anime News Network. Report the series, the episode and the moment (fight climax, transformation,
emotional speech, power-up reveal) with sources. Clips that work well are short (8–20 s), start
on the action or a strong line within the first second, and end on an impact or a cliffhanger,
which encourages rewatches.

## Posting checklist for the user

- Caption: a question that invites comments, plus #anime #animeedit and the series name.
- Turn on "Upload HD" in TikTok's posting settings.
- Add a trending sound in the app at 20–30% volume and keep the original audio at 100%.
