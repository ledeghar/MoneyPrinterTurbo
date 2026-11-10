#!/usr/bin/env python3
"""Create a selectable 10-audio/10-subtitle MP4 from ONE shared visual master.

The ten independent narration tracks are preserved at natural speech rate.
Scene lengths in the master = longest local narration scene; other locales
are padded with silence, not sped up. Use the 10 separate localized MP4s for
social platforms that flatten alternate audio/subtitle tracks.

YouTube does NOT import these language selections just because an uploaded
MP4 contains 10 streams. Studio > Languages > Dub requires audio-only uploads.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MOTION = ROOT / "mn-short-motion"
PROPS = MOTION / "props"
PUBLIC = MOTION / "public"
OUTPUT = ROOT / "mn-short-output-motion"
LANGS = [
    ("es", "spa", "Español"),
    ("en", "eng", "English"),
    ("fr", "fra", "Français"),
    ("de", "deu", "Deutsch"),
    ("it", "ita", "Italiano"),
    ("pt", "por", "Português"),
    ("ru", "rus", "Русский"),
    ("zh", "zho", "中文"),
    ("ja", "jpn", "日本語"),
    ("ar", "ara", "العربية"),
]
FPS = 30


def execute(args):
    subprocess.run(args, check=True, timeout=600)


def read_props():
    result = {}
    for lang, _iso, _label in LANGS:
        path = PROPS / (lang + ".json")
        if not path.is_file():
            raise RuntimeError("Missing one of ten prepared voice props: " + str(path))
        result[lang] = json.loads(path.read_text(encoding="utf-8"))
    first = result["es"]["scenes"]
    if not first or len(first) > 18:
        raise RuntimeError("Unexpected canonical scene count")
    for lang, data in result.items():
        scenes = data["scenes"]
        if len(scenes) != len(first):
            raise RuntimeError("Inconsistent scene count in " + lang)
        if [x["kind"] for x in scenes] != [x["kind"] for x in first]:
            raise RuntimeError("Cannot multiplex different stories: " + lang)
        for scene in scenes:
            if "wordTimings" not in scene or not scene["wordTimings"]:
                raise RuntimeError("No real TTS timings for " + lang)
    return result


def master_durations(all_props):
    n = len(all_props["es"]["scenes"])
    return [
        max(all_props[lang]["scenes"][i]["durationFrames"] for lang, _, _ in LANGS)
        for i in range(n)
    ]


def create_plan():
    all_props = read_props()
    duration_frames = master_durations(all_props)
    scenes = []
    cursor = 0
    for i, (scene, frames) in enumerate(zip(all_props["es"]["scenes"], duration_frames)):
        visual = scene.copy()
        # A universal master never permanently burns Spanish narration captions.
        visual.pop("audio", None)
        visual.pop("wordTimings", None)
        visual["startFrame"] = cursor
        visual["durationFrames"] = frames
        visual["text"] = ""
        if visual["kind"] == "headline":
            visual["subject"] = "MNShort · MEDIA NEWS"
        if visual["kind"] == "metric":
            visual["subject"] = "MEDIA NEWS · " + str(visual.get("metric") or "")
        scenes.append(visual)
        cursor += frames

    master = {
        "language": "en", "publisher": "Media News",
        "storyTitle": "MNShort — multilingual master",
        "neutralMaster": True,
        "totalFrames": cursor,
        "scenes": scenes,
    }
    PROPS.mkdir(parents=True, exist_ok=True)
    (PROPS / "master.json").write_text(
        json.dumps(master, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    OUTPUT.mkdir(parents=True, exist_ok=True)
    plan = {
        "totalFrames": cursor, "fps": FPS,
        "framesPerScene": duration_frames,
        "masterProps": "mn-short-motion/props/master.json",
        "localeAudioTracks": [lang for lang, _, _ in LANGS],
        "expectedAudioTracks": 10, "expectedSubtitleTracks": 10,
    }
    (OUTPUT / "multiaudio-plan.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("Master duration:", round(cursor / FPS, 2), "seconds; 10 audio and subtitle tracks")
    return plan


def srt_clock(seconds):
    ms = max(0, int(round(seconds * 1000)))
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, rem = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{rem:03d}"


def create_srt(props, durations, target):
    cursor = 0
    cues = []
    for index, (scene, frames) in enumerate(zip(props["scenes"], durations), start=1):
        start = cursor / FPS
        # Make captions show the actual local sentence; never leak a different
        # language's burned captions into the shared universal video.
        end = (cursor + frames) / FPS
        caption = " ".join(str(scene["text"]).replace("\r", " ").replace("\n", " ").split())
        cues.append(f"{index}\n{srt_clock(start)} --> {srt_clock(end)}\n{caption}\n")
        cursor += frames
    target.write_text("\ufeff" + "\n".join(cues), encoding="utf-8")


def create_audio(lang, props, durations, destination):
    """Concatenate native-rate TTS clips padded to the common scene boundaries."""
    args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    for scene in props["scenes"]:
        rel = Path(str(scene["audio"]))
        if rel.is_absolute() or ".." in rel.parts:
            raise RuntimeError("Unsafe narration path")
        path = PUBLIC / rel
        if not path.is_file():
            raise RuntimeError("Audio file missing for " + lang + ": " + str(path))
        args += ["-i", str(path)]
    filters = []
    for i, frame_count in enumerate(durations):
        duration = frame_count / FPS
        filters.append(
            f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,"
            f"apad,atrim=duration={duration:.6f},asetpts=PTS-STARTPTS[a{i}]"
        )
    names = "".join(f"[a{i}]" for i in range(len(durations)))
    filters.append(names + f"concat=n={len(durations)}:v=0:a=1[out]")
    args += [
        "-filter_complex", ";".join(filters),
        "-map", "[out]", "-c:a", "aac", "-b:a", "144k",
        "-ar", "48000", "-ac", "2",
        str(destination),
    ]
    execute(args)


def mux_all():
    all_props = read_props()
    plan_path = OUTPUT / "multiaudio-plan.json"
    if not plan_path.is_file():
        raise RuntimeError("Run --plan before --package")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    durations = master_durations(all_props)
    if plan["framesPerScene"] != durations:
        raise RuntimeError("The voice tracks changed after the master video was rendered")
    video = OUTPUT / "MNShort_MASTER_SILENT.mp4"
    if not video.is_file():
        raise RuntimeError("Master video render missing")

    audios, subtitles = [], []
    for lang, iso, label in LANGS:
        dubbed = OUTPUT / ("YT_DUB_" + lang + ".m4a")
        captions = OUTPUT / ("SUBTITULOS_" + lang + ".srt")
        create_audio(lang, all_props[lang], durations, dubbed)
        create_srt(all_props[lang], durations, captions)
        audios.append(dubbed)
        subtitles.append(captions)

    final = OUTPUT / "MNShort_MASTER_10_AUDIO_10_SUBTITLES.mp4"
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(video),
    ]
    for file in audios + subtitles:
        cmd += ["-i", str(file)]
    cmd += ["-map", "0:v:0"]
    for i in range(len(audios)):
        cmd += ["-map", str(1 + i) + ":a:0"]
    for i in range(len(subtitles)):
        cmd += ["-map", str(1 + len(audios) + i) + ":s:0"]
    cmd += [
        "-c:v", "copy", "-c:a", "copy", "-c:s", "mov_text",
        "-movflags", "+faststart",
        "-disposition:a:0", "default",
        "-disposition:s:0", "default",
    ]
    for i, (_lang, iso, label) in enumerate(LANGS):
        cmd += ["-metadata:s:a:" + str(i), "language=" + iso]
        cmd += ["-metadata:s:a:" + str(i), "handler_name=" + label]
        cmd += ["-metadata:s:s:" + str(i), "language=" + iso]
        cmd += ["-metadata:s:s:" + str(i), "handler_name=" + label]
        if i > 0:
            cmd += ["-disposition:a:" + str(i), "0"]
            cmd += ["-disposition:s:" + str(i), "0"]
    cmd += [str(final)]
    execute(cmd)

    ffinfo = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries",
        "stream=codec_type:stream_tags=language",
        "-of", "json", str(final),
    ], text=True, timeout=30)
    streams = json.loads(ffinfo).get("streams") or []
    kinds = [x.get("codec_type") for x in streams]
    if kinds.count("video") != 1 or kinds.count("audio") != 10 or kinds.count("subtitle") != 10:
        raise RuntimeError("Corrupt multilingual package: expected 1 video, 10 audio, 10 subtitles")
    expected = [x[1] for x in LANGS]
    actual_audio = [x.get("tags", {}).get("language") for x in streams if x.get("codec_type") == "audio"]
    if actual_audio != expected:
        raise RuntimeError("Incorrect language track metadata: " + str(actual_audio))
    print("VERIFIED 1 VIDEO + 10 AUDIO + 10 SUBTITLE TRACKS:", final.name)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["plan", "package"])
    args = p.parse_args()
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise SystemExit("ffmpeg and ffprobe required")
    if args.action == "plan":
        create_plan()
    else:
        mux_all()


if __name__ == "__main__":
    main()
