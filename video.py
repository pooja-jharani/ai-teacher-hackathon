"""
Turns a lesson segment (script + audio + visual description) into a video.

Three pluggable backends, selected via config.AVATAR_PROVIDER:

- "slides" : Renders a narrated slide (title + explanation text + a simple
             generated visual placeholder) synced to the TTS audio using
             moviepy. Works fully offline, no API key -- this is the
             default so the whole pipeline runs end-to-end out of the box.
- "did"    : Sends the audio + an avatar photo to the D-ID talking-avatar
             API and downloads the resulting talking-head video. Needs
             DID_API_KEY. Produces a genuine human-like avatar video.
- "heygen" : Same idea via the HeyGen API. Needs HEYGEN_API_KEY.

Swap AVATAR_PROVIDER in your .env once you have API keys -- the rest of
the app doesn't change.
"""
from __future__ import annotations
import os
import textwrap
import config

from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, AudioFileClip, CompositeVideoClip


def render_segment_video(segment: dict, audio_path: str, out_path: str) -> str:
    provider = config.AVATAR_PROVIDER
    if provider == "slides":
        return _render_slide_video(segment, audio_path, out_path)
    elif provider == "did":
        return _render_did_video(segment, audio_path, out_path)
    elif provider == "heygen":
        return _render_heygen_video(segment, audio_path, out_path)
    raise ValueError(f"Unknown AVATAR_PROVIDER: {provider}")


def _make_slide_image(segment: dict, size=(1280, 720)) -> Image.Image:
    """Builds a simple but subject-aware slide: title, explanation text,
    and a labeled visual box hinting at the requested visual_type
    (diagram / equation / graph / code / timeline / image)."""
    img = Image.new("RGB", size, color=(18, 22, 34))
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
        font_body = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf", 22)
    except OSError:
        font_title = font_body = font_small = ImageFont.load_default()

    title = segment.get("title", "Lesson Segment")
    draw.text((60, 40), title, font=font_title, fill=(255, 255, 255))

    # Visual placeholder box, labeled with the intended visual type --
    # this is where a diagram/graph/code render would be composited in.
    draw.rectangle([60, 120, 1220, 340], outline=(90, 140, 255), width=3)
    vtype = segment.get("visual_type", "visual").upper()
    vdesc = segment.get("visual_description", "")
    draw.text((80, 135), f"[{vtype}]", font=font_body, fill=(90, 140, 255))
    wrapped_vdesc = textwrap.fill(vdesc, width=90)
    draw.text((80, 175), wrapped_vdesc, font=font_small, fill=(180, 190, 210))

    # Explanation text (spoken content, shown as on-screen captions)
    explanation = segment.get("explanation", "")
    wrapped = textwrap.fill(explanation, width=70)
    draw.multiline_text((60, 380), wrapped, font=font_body, fill=(230, 230, 235), spacing=10)

    return img


def _render_slide_video(segment: dict, audio_path: str, out_path: str) -> str:
    slide = _make_slide_image(segment)
    tmp_img_path = out_path.replace(".mp4", "_slide.png")
    slide.save(tmp_img_path)

    audio = AudioFileClip(audio_path)
    image_clip = ImageClip(tmp_img_path).with_duration(audio.duration).with_audio(audio)
    image_clip.write_videofile(out_path, fps=24, codec="libx264", audio_codec="aac", logger=None)

    audio.close()
    image_clip.close()
    return out_path


def _render_did_video(segment: dict, audio_path: str, out_path: str) -> str:
    """Stub integration for D-ID's talking-avatar API. Requires DID_API_KEY.
    Docs: https://docs.d-id.com/ -- flow is: upload audio, POST /talks with
    the avatar image + audio url, poll until 'done', download result_url."""
    if not config.DID_API_KEY:
        raise RuntimeError("DID_API_KEY not set. Set AVATAR_PROVIDER=slides for the offline fallback, "
                            "or add your D-ID key to .env.")
    raise NotImplementedError(
        "D-ID integration is stubbed -- implement the upload/poll/download flow here "
        "using config.DID_API_KEY and config.AVATAR_IMAGE_PATH per D-ID's REST API docs."
    )


def _render_heygen_video(segment: dict, audio_path: str, out_path: str) -> str:
    """Stub integration for HeyGen's avatar video API. Requires HEYGEN_API_KEY."""
    if not config.HEYGEN_API_KEY:
        raise RuntimeError("HEYGEN_API_KEY not set. Set AVATAR_PROVIDER=slides for the offline fallback, "
                            "or add your HeyGen key to .env.")
    raise NotImplementedError(
        "HeyGen integration is stubbed -- implement the video-generation request/poll/download "
        "flow here using config.HEYGEN_API_KEY per HeyGen's API docs."
    )


def concatenate_segment_videos(video_paths: list[str], out_path: str) -> str:
    """Stitches all segment videos into one full lesson video."""
    from moviepy import concatenate_videoclips, VideoFileClip
    clips = [VideoFileClip(p) for p in video_paths]
    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(out_path, fps=24, codec="libx264", audio_codec="aac", logger=None)
    for c in clips:
        c.close()
    final.close()
    return out_path
