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


def stt_words(mp3, key, cache):
    """ElevenLabs speech-to-text with word timestamps (cached next to the take)."""
    out = Path(str(mp3) + ".stt.json")
    if out.exists():
        return json.loads(out.read_text())
    import uuid
    b = "----ks" + uuid.uuid4().hex
    body = b"".join([
        f"--{b}\r\nContent-Disposition: form-data; name=\"model_id\"\r\n\r\nscribe_v1\r\n".encode(),
        f"--{b}\r\nContent-Disposition: form-data; name=\"timestamps_granularity\"\r\n\r\nword\r\n".encode(),
        f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"take.mp3\"\r\nContent-Type: audio/mpeg\r\n\r\n".encode(),
        Path(mp3).read_bytes(), f"\r\n--{b}--\r\n".encode()])
    req = urllib.request.Request("https://api.elevenlabs.io/v1/speech-to-text", data=body,
                                 headers={"xi-api-key": key, "Content-Type": f"multipart/form-data; boundary={b}"})
    with urllib.request.urlopen(req, timeout=300) as r:
        j = json.loads(r.read())
    words = [w for w in j.get("words", []) if w.get("type", "word") == "word"]
    out.write_text(json.dumps(words))
    return words


def _norm(w):
    import unicodedata
    w = unicodedata.normalize("NFKD", w.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in w if not unicodedata.combining(c)))


def align_lines(lines, words):
    """For each script line, the (start, end) seconds where it was actually spoken. Skips anything the
    voice added (a read-aloud prompt, a repeated chunk) by matching each line's words in order."""
    from difflib import SequenceMatcher
    spoken = [_norm(w["text"]) for w in words]
    cur, out = 0, []
    for line in lines:
        target = [t for t in (_norm(x) for x in re.split(r"[\s\-\u2013\u2014]+", line)) if t]
        n = len(target)
        best = (0.0, None)
        for i in range(cur, max(cur + 1, len(spoken) - max(1, n // 2) + 1)):
            for L in (n - 1, n, n + 1):
                if L <= 0 or i + L > len(spoken):
                    continue
                sc = SequenceMatcher(None, target, spoken[i:i + L]).ratio()
                if sc > best[0]:
                    best = (sc, (i, i + L))
        if not best[1] or best[0] < 0.6:
            raise SystemExit(f"voice check failed: line not found in the take ({best[0]:.2f}): {line[:60]}")
        i, j = best[1]
        out.append((words[i]["start"], words[j - 1]["end"], best[0]))
        cur = j
    return out


# ------------------------------------------------------------------ recording

def record_slide(page, cdp, n, seconds, clicks_at, line=None, caption=None, lead=0.0, cap_dur=None):
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
    # Scenes read window.KS_DUR to fit their motion to the spoken line instead of the other way round.
    page.evaluate(f"window.KS_DUR = {line or seconds:.3f}")
    page.evaluate(f"window.__deck.ir({n}, false)")
    page.wait_for_timeout(450)       # skip the cross-fade from the previous slide
    t0 = time.time()
    if caption:
        page.evaluate(CAPTION_JS, {"text": caption, "dur": cap_dur or line or seconds, "lead": lead})
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
    if frames:  # Chrome only sends a frame when something changes: the first one covers from t0
        frames[0] = (t0, frames[0][1])
    end = t0 + seconds
    return frames, end


XFADE = 0.35   # seconds two slides blend into each other

CAPTION_JS = """({text, dur, lead}) => {
  // One sentence at a time, timed by its share of the characters in the line.
  document.getElementById('ks-cap')?.remove()
  const el = document.createElement('div'); el.id = 'ks-cap'
  el.style.cssText = 'position:fixed;left:50%;bottom:26px;transform:translateX(-50%);max-width:1500px;z-index:99998;' +
    'font:600 40px/1.3 var(--ks-font-body, sans-serif);color:#fff;background:rgba(15,23,42,.82);padding:14px 30px;border-radius:12px;text-align:center;opacity:0;transition:opacity .15s'
  document.body.appendChild(el)
  const parts = text.match(/[^.!?]+[.!?]*/g).map(x => x.trim()).filter(Boolean)
  const total = parts.reduce((n, x) => n + x.length, 0)
  let t = lead * 1000
  parts.forEach(x => { setTimeout(() => { el.textContent = x; el.style.opacity = 1 }, t); t += (dur - lead) * 1000 * x.length / total })
}"""


def silences(ff, path, min_gap, noise="-38dB"):
    """Spans with no voice longer than min_gap seconds, from ffmpeg's silencedetect."""
    r = subprocess.run([ff, "-hide_banner", "-i", str(path), "-af", f"silencedetect=noise={noise}:d={min_gap}", "-f", "null", "-"],
                       capture_output=True, text=True)
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    end = duration(ff, path)
    return [(s0, s1) for s0, s1 in zip(st, en + [end] * (len(st) - len(en))) if s1 < end - 0.05]


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
        # -shortest overshoots by an AAC frame or more; clips that run long drift the concat and add silence.
        args += ["-t", f"{end - frames[0][0]:.3f}", "-r", "30", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
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
    ap.add_argument("--jobs", type=int, default=3, help="slides recorded in parallel")
    ap.add_argument("--lead", type=float, default=0.15, help="seconds before the voice starts on each slide")
    ap.add_argument("--tail", type=float, default=0.3, help="seconds after the voice ends on each slide")
    ap.add_argument("--captions", action="store_true", help="burn the talk in as subtitles (social video plays muted)")
    ap.add_argument("--max-gap", type=float, default=0.8, help="fail if the narrated video has a silence longer than this (0 = off)")
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
        # Cut where each line was actually spoken: transcribe the take and align line by line.
        al = align_lines([t for t in texts if t], stt_words(mp3_all, key, cache))
        it_al = iter(al)
        bounds = [(lambda a_: (a_[0], a_[1]))(next(it_al)) if t else (0.0, 0.0) for t in texts]
        for sid_, t, a_ in zip([x for x, t in zip(ids, texts) if t], [t for t in texts if t], al):
            print(f"  voice check {sid_}: {a_[2]:.2f} match")
        take = (mp3_all, bounds, ends, off)
        # The take plays whole under the video: slides change in the pause between two lines,
        # so no word is ever cut. Window i runs from the middle of the pause before line i to the
        # middle of the pause after it.
        sp = [b_ for b_ in bounds]
        win = []
        for i_ in range(len(ids)):
            b0, b1 = sp[i_]
            w0 = max(0.0, b0 - 0.25) if i_ == 0 else (sp[i_ - 1][1] + b0) / 2
            w1 = b1 + 0.8 if i_ == len(ids) - 1 else (b1 + sp[i_ + 1][0]) / 2
            win.append((w0, w1))
    for i_sid, sid in enumerate(ids):
        parts = segs.get(sid, [])
        full = " ".join(parts)
        if take and full:
            mp3_all, bounds, ends, off = take
            b0, b1 = bounds[i_sid]
            w0, w1 = win[i_sid]
            clicks, pos = [], 0
            base = sum(len(" ".join(segs.get(x, []))) + 2 for x in ids[:i_sid])
            for p_ in parts[:-1]:
                pos += len(p_) + 1
                idx = min(off + base + pos, len(ends) - 1)
                clicks.append(max(0.0, ends[idx] - b0))
            lead_i = b0 - w0
            plan.append({"id": sid, "text": CLICK.sub(" ", full), "audio": None, "len": w1 - w0, "lead": lead_i,
                         "voice": b1 - b0, "hold": 0, "clicks": [lead_i + c for c in clicks]})
            print(f"  {sid}: {w1 - w0:.1f}s on screen, voice {b1 - b0:.1f}s")
            continue
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
        plan.append({"id": sid, "text": CLICK.sub(" ", full), "audio": mp3, "len": voice_len, "hold": hold.get(sid, 0), "clicks": [a.lead + c for c in clicks]})
        print(f"  {sid}: {voice_len:.1f}s voice, {len(clicks)} click(s)")

    from playwright.sync_api import sync_playwright
    import functools, http.server, threading
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(deck_dir / "build"))
    handler.log_message = lambda *x, **k: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}/stage/index.html#1"
    clips = [None] * len(plan)
    # Cache: a slide is re-recorded only if its scene, its voice or its timing changed.
    stage_html = (deck_dir / "build" / "stage" / "index.html").read_bytes()
    js = b"".join(f.read_bytes() for f in sorted((deck_dir / "build" / "stage").glob("*.js")))
    resolved_txt = (deck_dir / "build" / "deck.resolved.json").read_text()
    todo = []
    for i_, it in enumerate(plan):
        sl = next(x for x in json.loads(resolved_txt)["slides"] if x["id"] == it["id"])
        audio_h = hashlib.sha1(Path(it["audio"]).read_bytes()).hexdigest() if it["audio"] else "silent"
        key_ = hashlib.sha1(json.dumps([sl, audio_h, it["len"], it["hold"], it["clicks"], a.lead, a.tail, a.captions, it.get("lead"), XFADE if take else 0], sort_keys=True, default=str).encode()
                            + hashlib.sha1(stage_html + js).digest()).hexdigest()[:16]
        out = deck_dir / "build" / "video" / f"{it['id']}-{key_}.mp4"
        clips[i_] = out
        if not out.exists():
            todo.append((i_, it, out))
    print(f"  recording {len(todo)} of {len(plan)} slides ({len(plan) - len(todo)} cached), {a.jobs} in parallel")

    def worker(batch):
        with sync_playwright() as p:
            try:
                b = p.chromium.launch(channel="chrome", args=["--window-size=1920,1080", "--autoplay-policy=no-user-gesture-required"])
            except Exception:
                b = p.chromium.launch(args=["--window-size=1920,1080", "--autoplay-policy=no-user-gesture-required"])
            page = b.new_page(viewport={"width": 1920, "height": 1080})
            page.goto(url); page.wait_for_timeout(2500)
            # A 1-px element that changes every frame keeps the screencast emitting frames even when
            # only an iframe repaints (otherwise iframe-only motion records as a frozen frame).
            if os.environ.get("KS_TICK", "0") == "1": page.add_style_tag(content="@keyframes ks-tick{from{opacity:.01}to{opacity:.02}}"
                               "#ks-tick{position:fixed;left:0;top:0;width:1px;height:1px;background:#000;"
                               "animation:ks-tick .1s linear infinite alternate;z-index:99999;pointer-events:none}")
            page.evaluate("document.body.insertAdjacentHTML('beforeend','<div id=ks-tick></div>')")
            cdp = page.context.new_cdp_session(page)
            all_ids = page.evaluate("window.__deck.ids")
            # Warm-up: open every slide of the batch once so iframes, fonts and media are cached
            # before recording (otherwise the first seconds of a heavy slide record blank).
            if os.environ.get("KS_WARMUP", "0") == "1":
                for i_, it, out in batch:
                    page.evaluate(f"window.__deck.ir({all_ids.index(it['id'])}, true)")
                    page.wait_for_timeout(int(1000 * min(6, 2 + it["hold"])))
            for i_, it, out in batch:
                if take:   # continuous take: the clip is the window, plus the cross-fade into the next slide
                    secs = it["len"] + (XFADE if i_ < len(plan) - 1 else 0)
                    frames, end = record_slide(page, cdp, all_ids.index(it["id"]), secs, it["clicks"], it["len"],
                                               caption=it["text"] if a.captions else None, lead=it["lead"],
                                               cap_dur=it["lead"] + it["voice"])
                else:
                    secs = a.lead + it["len"] + a.tail + it["hold"]
                    frames, end = record_slide(page, cdp, all_ids.index(it["id"]), secs, it["clicks"], it["len"] + a.tail,
                                               caption=it["text"] if a.captions else None, lead=a.lead)
                out.parent.mkdir(parents=True, exist_ok=True)
                encode(frames, end, out, ff, it["audio"], a.lead)
            b.close()

    from concurrent.futures import ThreadPoolExecutor
    batches = [todo[k::a.jobs] for k in range(a.jobs)]
    try:
        with ThreadPoolExecutor(max_workers=a.jobs) as ex:
            list(ex.map(worker, [b_ for b_ in batches if b_]))
    finally:
        srv.shutdown()

    target = Path(a.out) if a.out else deck_dir / "build" / "video.mp4"
    if take:
        # Cross-fade the slides and lay the untouched take underneath.
        args, chain, prev, t = [ff, "-v", "error", "-y"], [], "0:v", 0.0
        for c in clips:
            args += ["-i", c]
        for k in range(1, len(clips)):
            t += plan[k - 1]["len"]
            chain.append(f"[{prev}][{k}:v]xfade=transition=fade:duration={XFADE}:offset={t:.3f}[x{k}]")
            prev = f"x{k}"
        total = sum(it["len"] for it in plan)
        args += ["-ss", f"{win[0][0]:.3f}", "-i", take[0], "-filter_complex",
                 ";".join(chain) + f";[{len(clips)}:a]volume=2.0,alimiter=limit=0.9,apad,atrim=0:{total:.3f}[a]",
                 "-map", f"[{prev}]" if chain else "0:v", "-map", "[a]", "-t", f"{total:.3f}",
                 "-r", "30", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                 "-c:a", "aac", "-b:a", "160k", target]
        run(*args)
    else:
        lst = deck_dir / "build" / "video" / "list.txt"
        lst.write_text("".join(f"file '{c}'\n" for c in clips))
        run(ff, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "copy",
            "-af", "volume=2.0,alimiter=limit=0.9", "-c:a", "aac", "-b:a", "160k", target)
    print(f"wrote {target}: {len(clips)} slides, {duration(ff, target):.1f}s, voice={'on' if use_voice else 'off'}")
    if use_voice and a.max_gap:
        gaps = silences(ff, target, a.max_gap)
        if gaps:
            print("silences longer than %.1fs (shorten the scene or its hold):" % a.max_gap)
            for s0, s1 in gaps:
                print(f"  {s0:6.1f}s → {s1:6.1f}s  ({s1 - s0:.1f}s)")
            return 3
        print(f"no silence longer than {a.max_gap}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
