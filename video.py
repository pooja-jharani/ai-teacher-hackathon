"""
Turns a lesson segment (script + audio + visual description) into a video.

Three pluggable backends, selected via config.AVATAR_PROVIDER:

- "slides" : Renders a narrated slide (title + explanation text + a simple
             generated visual placeholder) synced to the TTS audio using
             MoviePy. Works fully offline, no API key.
- "did"    : Stub for D-ID talking-avatar integration.
- "heygen" : Stub for HeyGen talking-avatar integration.

The default "slides" backend keeps the complete pipeline working locally.
"""

from __future__ import annotations

import os
import textwrap
import config

from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, AudioFileClip


# ---------------------------------------------------------------------
# Main renderer
# ---------------------------------------------------------------------

def render_segment_video(
    segment: dict,
    audio_path: str,
    out_path: str
) -> str:

    provider = config.AVATAR_PROVIDER

    if provider == "slides":
        return _render_slide_video(segment, audio_path, out_path)

    elif provider == "did":
        return _render_did_video(segment, audio_path, out_path)

    elif provider == "heygen":
        return _render_heygen_video(segment, audio_path, out_path)

    raise ValueError(f"Unknown AVATAR_PROVIDER: {provider}")


# ---------------------------------------------------------------------
# Slide generation
# ---------------------------------------------------------------------

def _make_slide_image(
    segment: dict,
    size=(1280, 720)
) -> Image.Image:

    img = Image.new(
        "RGB",
        size,
        color=(18, 22, 34)
    )

    draw = ImageDraw.Draw(img)

    # -------------------------------------------------------------
    # Fonts
    # -------------------------------------------------------------

    try:
        font_title = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            42
        )

        font_body = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            28
        )

        font_small = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
            22
        )

    except OSError:
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # -------------------------------------------------------------
    # Title
    # -------------------------------------------------------------

    title = segment.get(
        "title",
        "Lesson Segment"
    )

    draw.text(
        (60, 40),
        title,
        font=font_title,
        fill=(255, 255, 255)
    )

    # -------------------------------------------------------------
    # Visual placeholder
    # -------------------------------------------------------------

    draw.rectangle(
        [60, 120, 1220, 340],
        outline=(90, 140, 255),
        width=3
    )

    visual_type = segment.get(
        "visual_type",
        "visual"
    ).upper()

    visual_description = segment.get(
        "visual_description",
        ""
    )

    draw.text(
        (80, 135),
        f"[{visual_type}]",
        font=font_body,
        fill=(90, 140, 255)
    )

    wrapped_visual = textwrap.fill(
        visual_description,
        width=90
    )

    draw.text(
        (80, 175),
        wrapped_visual,
        font=font_small,
        fill=(180, 190, 210)
    )

    # -------------------------------------------------------------
    # Explanation / captions
    # -------------------------------------------------------------

    explanation = segment.get(
        "explanation",
        ""
    )

    wrapped_explanation = textwrap.fill(
        explanation,
        width=70
    )

    draw.multiline_text(
        (60, 380),
        wrapped_explanation,
        font=font_body,
        fill=(230, 230, 235),
        spacing=10
    )

    return img


# ---------------------------------------------------------------------
# Slide + TTS audio renderer
# ---------------------------------------------------------------------

def _render_slide_video(
    segment: dict,
    audio_path: str,
    out_path: str
) -> str:

    # Create slide image
    slide = _make_slide_image(segment)

    # Save temporary slide
    tmp_img_path = out_path.replace(
        ".mp4",
        "_slide.png"
    )

    slide.save(tmp_img_path)

    # -------------------------------------------------------------
    # Load audio
    # -------------------------------------------------------------

    audio = AudioFileClip(audio_path)

    # -------------------------------------------------------------
    # Create video exactly as long as audio
    # -------------------------------------------------------------

    image_clip = (
        ImageClip(tmp_img_path)
        .with_duration(audio.duration)
        .with_audio(audio)
    )

    # -------------------------------------------------------------
    # Write video
    # -------------------------------------------------------------

    image_clip.write_videofile(
        out_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        logger=None
    )

    # -------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------

    image_clip.close()
    audio.close()

    return out_path


# ---------------------------------------------------------------------
# D-ID backend
# ---------------------------------------------------------------------

def _render_did_video(
    segment: dict,
    audio_path: str,
    out_path: str
) -> str:

    if not config.DID_API_KEY:
        raise RuntimeError(
            "DID_API_KEY not set. "
            "Set AVATAR_PROVIDER=slides for the offline fallback, "
            "or add your D-ID key to .env."
        )

    raise NotImplementedError(
        "D-ID integration is currently stubbed. "
        "Implement the upload/poll/download flow here "
        "using config.DID_API_KEY and config.AVATAR_IMAGE_PATH."
    )


# ---------------------------------------------------------------------
# HeyGen backend
# ---------------------------------------------------------------------

def _render_heygen_video(
    segment: dict,
    audio_path: str,
    out_path: str
) -> str:

    if not config.HEYGEN_API_KEY:
        raise RuntimeError(
            "HEYGEN_API_KEY not set. "
            "Set AVATAR_PROVIDER=slides for the offline fallback, "
            "or add your HeyGen key to .env."
        )

    raise NotImplementedError(
        "HeyGen integration is currently stubbed. "
        "Implement the video-generation request/poll/download flow "
        "using config.HEYGEN_API_KEY."
    )


# ---------------------------------------------------------------------
# Concatenate lesson segments
# ---------------------------------------------------------------------

def concatenate_segment_videos(
    video_paths: list[str],
    out_path: str
) -> str:

    """
    Stitches all rendered lesson segments into one video.

    Each segment already contains its own correctly synchronized
    audio track, so we concatenate the complete video clips directly.
    """

    from moviepy import (
        concatenate_videoclips,
        VideoFileClip
    )

    if not video_paths:
        raise ValueError(
            "No video segments were provided."
        )

    clips = []

    try:
        # Load all segment videos
        for path in video_paths:
            clips.append(
                VideoFileClip(path)
            )

        # Concatenate complete A/V clips
        final = concatenate_videoclips(
            clips,
            method="compose"
        )

        # Write final lesson
        final.write_videofile(
            out_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            logger=None
        )

        final.close()

    finally:
        # Always close input clips
        for clip in clips:
            clip.close()

    return out_path