#!/usr/bin/env python3
"""DISI/MNShort: safe source-based video brief and offline smoke preview.

A preview is NOT the approved Media News/DISI V9 output and never publishes.
No keys, remote model calls, automatic charges or social APIs are used.
"""
import argparse
import json
import math
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

STYLES = {
    "editorial": "Editorial claro, tipografía serif y ritmo informativo",
    "documentary": "Documental observacional, imágenes con procedencia",
    "cinematic": "Cinematográfico para recreaciones identificadas",
    "ugc": "Presentación personal directa a cámara",
    "noir": "Contraste dramático de bajo tono",
    "archive": "Material de archivo fechado y atribuido",
    "infographic": "Datos explicados mediante gráficos verificables",
    "stickman": "Animación ilustrada simple, no material documental",
}
DURATIONS = (3, 4, 3, 2)


def plan(brief):
    mode = brief.get("mode")
    if mode not in {"news", "book", "promo", "documentary"}:
        raise ValueError("mode must be news, book, promo or documentary")
    style = brief.get("style", "editorial")
    if style not in STYLES:
        raise ValueError(f"unknown style: {style}")
    if brief.get("authorize_payment") or brief.get("publish"):
        raise ValueError("This planning tool cannot authorize payment or publication")
    if mode in {"news", "documentary"}:
        sources = brief.get("sources", [])
        if not sources or any(not item.get("url") or not item.get("title") for item in sources):
            raise ValueError("news/documentary requires named, traceable sources")
        valid_ids = {item.get("id") for item in sources}
        claims = brief.get("claims", [])
        if not claims or any(not c.get("source_ids") or not set(c["source_ids"]).issubset(valid_ids) for c in claims):
            raise ValueError("every factual claim must cite source IDs from the brief")
    keys = ("hook", "context", "evidence", "cta")
    if any(not isinstance(brief.get(k), str) or not brief[k].strip() for k in keys):
        raise ValueError("hook, context, evidence and cta must be supplied")
    cursor = 0
    scenes = []
    for key, duration in zip(keys, DURATIONS):
        scenes.append({"section": key, "start_s": cursor, "duration_s": duration,
                       "text": brief[key].strip()})
        cursor += duration
    return {
        "schema": "disi-mnshort-intake/0.1", "created_utc": datetime.now(timezone.utc).isoformat(),
        "title": brief.get("title", "DISI sin título"), "mode": mode,
        "style": style, "style_direction": STYLES[style],
        "scenes": scenes, "duration_s": cursor,
        "sources": brief.get("sources", []), "claims": brief.get("claims", []),
        "provider": "none", "ai_rendering_performed": False,
        "original_assets_required": ["LOGO_MEDIA_NEWS_CANVA.png", "LOGO_DISI_CANVA.png",
                                     "MEDIA_CANVA_WORDMARK.png", "OUTRO_V6_ORIGINAL.mp4"],
        "approval": "PENDING_HUMAN_EDITOR", "publication_enabled": False,
        "notes": "El render real usa DISIV9Approved. Este paquete no incorpora logos ni V6 originales."
    }


def demo(output: Path, fps=15, width=360, height=640):
    """Procedural smoke preview; no approved brand assets or external model needed."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as e:
        raise RuntimeError("Pillow is needed for the offline preview") from e
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not installed")
    if width < 160 or height < 270 or fps < 1:
        raise ValueError("preview dimensions/fps are too small")
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    narration = ["Antes de compartir, verifica.", "Busca la fuente original.",
                 "Comprueba fechas y contexto.", "Media News por DISI."]
    # No claims about a real event: offline demonstration of an editorial workflow.
    example = plan({"mode": "promo", "title": "Cómo verificamos una noticia",
                    "style": "editorial", "hook": narration[0],
                    "context": narration[1], "evidence": narration[2], "cta": narration[3]})
    def font(sz, bold=False):
        paths = (["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"] if bold else
                 ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
        for p in paths:
            if Path(p).is_file():
                return ImageFont.truetype(p, sz)
        return ImageFont.load_default()
    ft = font(max(17, round(width * .055)), True)
    small = font(max(12, round(width * .033)))
    dark = (6, 20, 38)
    red = (226, 38, 68)
    N = fps * example["duration_s"]
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td)/"voice.wav"
        if shutil.which("espeak"):
            subprocess.run(["espeak", "-v", "es", "-s", "135", "-w", str(wav),
                            " ".join(narration)], check=True, capture_output=True)
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
               "-pixel_format", "rgb24", "-video_size", f"{width}x{height}",
               "-framerate", str(fps), "-i", "-"]
        if wav.is_file():
            cmd += ["-i", str(wav), "-map", "0:v:0", "-map", "1:a:0", "-c:a", "aac", "-b:a", "96k", "-af", "apad"]
        cmd += ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "26",
                "-pix_fmt", "yuv420p", "-frames:v", str(N), "-t", str(example["duration_s"]),
                "-movflags", "+faststart", str(output)]
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        assert process.stdin is not None
        for n in range(N):
            t = n / fps
            scene = next(s for s in example["scenes"] if s["start_s"] <= t < s["start_s"] + s["duration_s"])
            im = Image.new("RGB", (width, height), dark)
            d = ImageDraw.Draw(im)
            d.rectangle((0, 0, width, int(height*.055)), fill=red)
            d.text((width*.07, height*.095), "MNShort · PRUEBA", font=ft, fill="white")
            # Time-dependent animated editorial progress and source verification motif.
            track_x = int(width*.12)
            cy = int(height*.40)
            d.rounded_rectangle((track_x, cy, width-track_x, cy+width*.08), radius=7, outline=(105, 136, 172), width=2)
            p = max(0.0, min(1.0, (t-scene["start_s"])/scene["duration_s"]))
            if p:
                d.rectangle((track_x+4, cy+4, track_x+4+int((width-2*track_x-8)*p), cy+width*.08-4), fill=red)
            lines = [scene["text"]]
            if len(lines[0]) > 23:
                words = lines[0].split()
                split = max(1, len(words)//2)
                lines = [" ".join(words[:split]), " ".join(words[split:])]
            for i, line in enumerate(lines):
                bbox = d.textbbox((0, 0), line, font=ft)
                d.text(((width-(bbox[2]-bbox[0]))/2, height*.55+i*width*.085), line, font=ft, fill="white")
            d.text((width*.07, height*.82), "BORRADOR · NO PUBLICAR", font=small, fill=(237, 157, 168))
            d.text((width*.07, height*.89), "Sin logotipos ni cierre V6", font=small, fill=(180, 199, 221))
            d.rectangle((0, height-5, int(width*(n+1)/N), height), fill=red)
            try:
                process.stdin.write(im.tobytes())
            except BrokenPipeError:
                break
        process.stdin.close()
        error = process.stderr.read().decode(errors="replace")
        code = process.wait()
        if code:
            raise RuntimeError(f"ffmpeg error {code}: {error[-1500:]}")
    return {"video": str(output), "seconds": example["duration_s"], "frames": N,
            "editorial_state": "TEST_ONLY", "publication_enabled": False}


def main():
    a = argparse.ArgumentParser(description=__doc__)
    sub = a.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--brief", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    v = sub.add_parser("demo")
    v.add_argument("--output", type=Path, required=True)
    v.add_argument("--fps", type=int, default=15)
    v.add_argument("--width", type=int, default=360)
    v.add_argument("--height", type=int, default=640)
    args = a.parse_args()
    if args.cmd == "plan":
        result = plan(json.loads(args.brief.read_text(encoding="utf8")))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
    else:
        result = demo(args.output, args.fps, args.width, args.height)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
