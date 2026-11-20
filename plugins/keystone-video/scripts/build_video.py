#!/usr/bin/env python3
"""Turn a keystone deck and its talk into a narrated video.

  build_video.py <deck-dir> [--out build/video.mp4] [--brand brand.json] [--only id,id]
                 [--voice-id ID] [--model eleven_v4] [--direction TEXT] [--speed 1.0] [--no-voice]

1. The talk: each slide's spoken text from talk.md. `**Click:**` / `**Clic:**` markers are where the
   next step of the slide fires.
2. The voice: ElevenLabs text-to-speech with character timestamps (needs ELEVENLABS_API_KEY in the
   environment; never written to disk). Audio is cached per text, so re-runs cost nothing.
   meta.voice in deck.json can set {"id", "model", "direction", "speed"}. Without a key, or with
   --no-voice, each slide gets 2.6 words per second of silence and the video comes out mute.
3. The picture: the stage deck is recorded slide by slide (Chrome DevTools screencast); each slide
   lasts as long as its voice, and clicks fire when the voice reaches the marker.
4. The cut: every slide clip gets its voice; clips are joined; loudness is normalised once, with a
   fixed gain (per-slide loudness normalisation flattens a voice).

Needs: playwright (+ Chrome or `playwright install chromium`), imageio-ffmpeg or ffmpeg on PATH.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
CLICK = re.compile(r"\*\*(click|clic):\*\*", re.I)


def ffmpeg():
    for c in (os.environ.get("FFMPEG"), shutil.which("ffmpeg")):
        if c and Path(c).exists():
            return c
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        raise SystemExit("ffmpeg not found: install it, set $FFMPEG, or pip install imageio-ffmpeg")


def run(*cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode:
        sys.stderr.write(r.stderr[-2000:])
        raise SystemExit(f"failed: {cmd[0]} …")
    return r


def duration(ff, path):
    r = subprocess.run([ff, "-i", str(path)], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
    return int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else 0.0


def sibling(plugin, rel, env):
    import glob
    cands = [os.environ.get(env), str(PLUGIN.parent / plugin / rel)]
    cands += sorted(glob.glob(os.path.expanduser(f"~/.claude/plugins/cache/*/{plugin}/*/{rel}")), reverse=True)
    for c in cands:
        if c and Path(c).exists():
            return Path(c)
    raise SystemExit(f"{plugin} not found: install it or set ${env}")


# ------------------------------------------------------------------ talk

def talk_segments(talk_md: Path) -> dict:
    """slide id -> list of text segments split at click markers (raw, before stripping)."""
    out, cur = {}, None
    for line in talk_md.read_text(encoding="utf-8").splitlines():
        h = re.match(r"^##\s+([A-Za-z0-9_-]+)", line)
        if h:
            cur = h.group(1); out[cur] = []
            continue
        if line.startswith("# "):
            cur = None if re.match(r"^#\s+(appendix|anexo)", line, re.I) else cur
            continue
        if cur is None or not line.strip() or re.match(r"^\*\*[^*]+:\*\*", line.strip()) and not CLICK.match(line.strip()):
            continue
        out[cur].append(line.strip())
    segs = {}
    for sid, lines in out.items():
        text = " ".join(lines)
        segs[sid] = [p.strip() for p in CLICK.split(text) if p.strip() and p.lower() not in ("click", "clic")]
    return segs


# ------------------------------------------------------------------ voice

def tts(text, voice, cache: Path, key):
    """ElevenLabs TTS with timestamps. Returns (mp3 path, list of char end times)."""
    payload = {"text": (f"[{voice['direction']}] " if voice.get("direction") else "") + text,
               "model_id": voice.get("model", "eleven_v4")}
    if voice.get("speed"):
        payload["voice_settings"] = {"speed": voice["speed"]}
    h = hashlib.sha1(json.dumps([voice.get("id"), payload], sort_keys=True).encode()).hexdigest()[:16]
    mp3, meta = cache / f"{h}.mp3", cache / f"{h}.json"
    if mp3.exists() and meta.exists():
        return mp3, json.loads(meta.read_text())
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice['id']}/with-timestamps?output_format=mp3_44100_128",
        data=json.dumps(payload).encode(), headers={"xi-api-key": key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        j = json.loads(r.read())
    mp3.write_bytes(base64.b64decode(j["audio_base64"]))
    al = j.get("alignment") or {}
    info = {"prompt_chars": len(payload["text"]) - len(text), "ends": al.get("character_end_times_seconds", [])}
    meta.write_text(json.dumps(info))
    return mp3, info


# ------------------------------------------------------------------ recording

def record_slide(page, cdp, n, seconds, clicks_at):
    frames = []

    def on(ev):
        frames.append((ev["metadata"]["timestamp"], base64.b64decode(ev["data"])))
        try:
            cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]})
        except Exception:
            pass
    cdp.on("Page.screencastFrame", on)
    cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92, "maxWidth": 1920, "maxHeight": 1080})
    page.wait_for_timeout(200)
    t0 = time.time()
    page.evaluate(f"window.__deck.ir({n}, false)")
    for t in sorted(clicks_at):
        wait = t - (time.time() - t0)
        if wait > 0:
            page.wait_for_timeout(int(wait * 1000))
        page.keyboard.press("ArrowRight")
    rest = seconds - (time.time() - t0)
    if rest > 0:
        page.wait_for_timeout(int(rest * 1000))
    cdp.send("Page.stopScreencast")
    cdp.remove_listener("Page.screencastFrame", on)
    frames.sort(key=lambda f: f[0])
    while len(frames) > 1 and frames[1][0] <= t0:
        frames.pop(0)
    frames = [(max(t, t0), d) for t, d in frames]
    end = t0 + seconds
    return frames, end


def encode(frames, end, out_mp4, ff, audio=None, lead=0.0):
    with tempfile.TemporaryDirectory() as td:
        lines = []
        for i, (t, d) in enumerate(frames):
            Path(td, f"f{i:05d}.jpg").write_bytes(d)
            nxt = frames[i + 1][0] if i + 1 < len(frames) else end
            lines.append(f"file 'f{i:05d}.jpg'\nduration {max(0.001, nxt - t):.4f}")
        lines.append(f"file 'f{len(frames) - 1:05d}.jpg'")
        Path(td, "l.txt").write_text("\n".join(lines) + "\n")
        args = [ff, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", Path(td, "l.txt")]
        if audio:
            args += ["-i", audio, "-filter_complex", f"[1:a]adelay={int(lead * 1000)}:all=1,apad[a]", "-map", "0:v", "-map", "[a]", "-shortest"]
        else:
            args += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-map", "0:v", "-map", "1:a", "-shortest"]
        args += ["-r", "30", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                 "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2", out_mp4]
        run(*args)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("--out")
    ap.add_argument("--brand")
    ap.add_argument("--only")
    ap.add_argument("--voice-id")
    ap.add_argument("--model")
    ap.add_argument("--direction")
    ap.add_argument("--speed", type=float)
    ap.add_argument("--no-voice", action="store_true")
    ap.add_argument("--per-slide", action="store_true", help="one voice take per slide (default: one take for the whole talk)")
    ap.add_argument("--lead", type=float, default=0.5, help="seconds before the voice starts on each slide")
    ap.add_argument("--tail", type=float, default=0.8, help="seconds after the voice ends on each slide")
    a = ap.parse_args(argv)

    deck_dir = Path(a.deck).resolve()
    ff = ffmpeg()
    stage_build = sibling("keystone-html", "scripts/build_stage.py", "KEYSTONE_HTML")
    args = [sys.executable, stage_build, deck_dir, "--out", deck_dir / "build" / "stage", "--no-check"]
    if a.brand:
        args += ["--brand", a.brand]
    run(*args)
    meta = json.loads((deck_dir / "deck.json").read_text(encoding="utf-8"))["meta"]
    v = {**meta.get("voice", {})}
    for k in ("voice_id", "model", "direction", "speed"):
        val = getattr(a, k)
        if val:
            v["id" if k == "voice_id" else k] = val
    key = os.environ.get("ELEVENLABS_API_KEY")
    use_voice = bool(key and v.get("id") and not a.no_voice)
    if not use_voice and not a.no_voice:
        print("no ELEVENLABS_API_KEY or voice id: building a silent video")

    segs = talk_segments(deck_dir / "talk.md")
    slides = json.loads((deck_dir / "build" / "deck.resolved.json").read_text())["slides"]
    ids = [s["id"] for s in slides]
    hold = {s["id"]: float(s.get("hold", 0)) for s in slides}  # extra seconds a scene needs after the voice
    if a.only:
        ids = [i for i in ids if i in a.only.split(",")]
    cache = deck_dir / "build" / "voice"
    cache.mkdir(parents=True, exist_ok=True)

    plan = []
    take = None
    if use_voice and not a.per_slide:
        # One take for the whole talk: per-slide takes of short lines make the model repeat itself.
        texts = [" ".join(segs.get(sid, [])) for sid in ids]
        full_all = "\n\n".join(texts)
        mp3_all, info_all = tts(full_all, v, cache, key)
        ends, off = info_all["ends"], info_all["prompt_chars"]
        bounds, pos = [], 0
        for t in texts:
            start_c, end_c = off + pos, off + pos + len(t) - 1
            bounds.append((ends[max(0, start_c - 1)] if start_c > 0 else 0.0, ends[min(end_c, len(ends) - 1)]))
            pos += len(t) + 2
        take = (mp3_all, bounds, ends, off)
    for i_sid, sid in enumerate(ids):
        parts = segs.get(sid, [])
        full = " ".join(parts)
        if take and full:
            mp3_all, bounds, ends, off = take
            b0, b1 = bounds[i_sid]
            mp3 = cache / f"{sid}-cut.wav"
            # end where the next line starts (minus a breath), never inside it
            nxt = bounds[i_sid + 1][0] if i_sid + 1 < len(bounds) else b1 + 0.6
            cut_end = min(b1 + 0.35, nxt - 0.12) if nxt > b1 else b1
            cut_start = max(0.0, b0 - 0.03)   # b0 is where this line starts, after the direction prompt
            run(ff, "-v", "error", "-y", "-ss", f"{cut_start:.3f}", "-to", f"{cut_end:.3f}", "-i", mp3_all,
                "-af", "afade=t=out:st=" + f"{max(0, cut_end - cut_start - 0.08):.3f}" + ":d=0.08", "-ar", "44100", mp3)
            voice_len = duration(ff, mp3)
            clicks, pos = [], 0
            base = sum(len(" ".join(segs.get(x, []))) + 2 for x in ids[:i_sid])
            for p_ in parts[:-1]:
                pos += len(p_) + 1
                idx = min(off + base + pos, len(ends) - 1)
                clicks.append(max(0.0, ends[idx] - b0))
        elif use_voice and full:
            mp3, info = tts(full, v, cache, key)
            ends, off = info["ends"], info["prompt_chars"]
            # click k fires where segment k+1 starts in the full text
            clicks, pos = [], 0
            for p in parts[:-1]:
                pos += len(p) + 1
                idx = min(off + pos, len(ends) - 1) if ends else 0
                clicks.append(ends[idx] if ends else 0)
            voice_len = duration(ff, mp3)
        else:
            mp3, words = None, len(full.split())
            voice_len = max(2.5, words / 2.6)
            clicks = [voice_len * (k + 1) / len(parts) for k in range(len(parts) - 1)] if len(parts) > 1 else []
        plan.append({"id": sid, "audio": mp3, "len": voice_len, "hold": hold.get(sid, 0), "clicks": [a.lead + c for c in clicks]})
        print(f"  {sid}: {voice_len:.1f}s voice, {len(clicks)} click(s)")

    from playwright.sync_api import sync_playwright
    import functools, http.server, threading
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(deck_dir / "build"))
    handler.log_message = lambda *x, **k: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}/stage/index.html#1"
    clips = []
    try:
        with sync_playwright() as p:
            try:
                b = p.chromium.launch(channel="chrome", args=["--window-size=1920,1080", "--autoplay-policy=no-user-gesture-required"])
            except Exception:
                b = p.chromium.launch(args=["--window-size=1920,1080", "--autoplay-policy=no-user-gesture-required"])
            page = b.new_page(viewport={"width": 1920, "height": 1080})
            page.goto(url); page.wait_for_timeout(2500)
            cdp = page.context.new_cdp_session(page)
            all_ids = page.evaluate("window.__deck.ids")
            for it in plan:
                secs = a.lead + it["len"] + a.tail + it["hold"]
                frames, end = record_slide(page, cdp, all_ids.index(it["id"]), secs, it["clicks"])
                out = deck_dir / "build" / "video" / f"{it['id']}.mp4"
                out.parent.mkdir(parents=True, exist_ok=True)
                encode(frames, end, out, ff, it["audio"], a.lead)
                clips.append(out)
            b.close()
    finally:
        srv.shutdown()

    target = Path(a.out) if a.out else deck_dir / "build" / "video.mp4"
    lst = deck_dir / "build" / "video" / "list.txt"
    lst.write_text("".join(f"file '{c}'\n" for c in clips))
    run(ff, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "copy",
        "-af", "volume=2.0,alimiter=limit=0.9", "-c:a", "aac", "-b:a", "160k", target)
    print(f"wrote {target}: {len(clips)} slides, {duration(ff, target):.1f}s, voice={'on' if use_voice else 'off'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
