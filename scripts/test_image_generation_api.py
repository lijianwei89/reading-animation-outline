#!/usr/bin/env python3
"""Test the TAL OpenAI-compatible single-image generation endpoint."""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import os
import re
import struct
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


DEFAULT_ENDPOINT = (
    "http://ai-service.tal.com/openai-compatible/v1/images/generations"
)
SIZE_PATTERN = re.compile(r"^[1-9][0-9]*x[1-9][0-9]*$")


class ImageGenerationError(RuntimeError):
    """Base error for an invalid request or API response."""


class ResponseValidationError(ImageGenerationError):
    """Raised when a successful response cannot produce a valid image."""


@dataclass(frozen=True)
class SavedImage:
    path: Path
    image_format: str
    width: int
    height: int
    source: str


def get_api_key() -> str:
    """Read credentials without embedding them in source control."""
    direct_key = os.environ.get("TAL_MLOPS_API_KEY", "").strip()
    if direct_key:
        return direct_key

    app_id = os.environ.get("TAL_MLOPS_APP_ID", "").strip()
    app_key = os.environ.get("TAL_MLOPS_APP_KEY", "").strip()
    if app_id and app_key:
        return f"{app_id}:{app_key}"

    raise ImageGenerationError(
        "Missing credentials: set TAL_MLOPS_API_KEY or both "
        "TAL_MLOPS_APP_ID and TAL_MLOPS_APP_KEY."
    )


def build_payload(prompt: str, model: str, size: str) -> dict[str, str]:
    """Validate caller-controlled fields before a billed request is sent."""
    if not isinstance(prompt, str) or not prompt.strip():
        raise ImageGenerationError("Prompt must contain non-whitespace text.")
    if not isinstance(model, str) or not model.strip():
        raise ImageGenerationError("Model must contain non-whitespace text.")
    if not isinstance(size, str) or not SIZE_PATTERN.fullmatch(size):
        raise ImageGenerationError(
            "Size must use positive integer dimensions, for example 1024x1024."
        )
    return {"model": model.strip(), "prompt": prompt.strip(), "size": size}


def validate_endpoint(endpoint: str) -> None:
    parsed = urlparse(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ImageGenerationError("Endpoint must be an absolute HTTP(S) URL.")


def request_generation(
    endpoint: str,
    api_key: str,
    payload: dict[str, str],
    timeout: float,
) -> dict[str, Any]:
    validate_endpoint(endpoint)
    if timeout <= 0:
        raise ImageGenerationError("Timeout must be greater than zero.")
    if not api_key.strip():
        raise ImageGenerationError("API key must not be empty.")

    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "api-key": api_key,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", response.getcode())
            response_body = response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        raise ImageGenerationError(f"API rejected request (HTTP {exc.code}): {body}") from exc
    except urllib.error.URLError as exc:
        raise ImageGenerationError(f"API request failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise ImageGenerationError("API request timed out.") from exc

    if not 200 <= status < 300:
        raise ImageGenerationError(f"Unexpected HTTP status: {status}")
    try:
        parsed_response = json.loads(response_body)
    except json.JSONDecodeError as exc:
        raise ResponseValidationError("API returned non-JSON content.") from exc
    if not isinstance(parsed_response, dict):
        raise ResponseValidationError("API response must be a JSON object.")
    return parsed_response


def _png_dimensions(content: bytes) -> tuple[int, int] | None:
    if not content.startswith(b"\x89PNG\r\n\x1a\n") or len(content) < 24:
        return None
    if content[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", content[16:24])


def _jpeg_dimensions(content: bytes) -> tuple[int, int] | None:
    if not content.startswith(b"\xff\xd8"):
        return None
    offset = 2
    while offset + 9 < len(content):
        if content[offset] != 0xFF:
            offset += 1
            continue
        marker = content[offset + 1]
        if marker in {0xC0, 0xC1, 0xC2, 0xC3}:
            height, width = struct.unpack(">HH", content[offset + 5 : offset + 9])
            return width, height
        if marker in {0xD8, 0xD9}:
            offset += 2
            continue
        segment_length = struct.unpack(">H", content[offset + 2 : offset + 4])[0]
        if segment_length < 2:
            return None
        offset += segment_length + 2
    return None


def identify_image(content: bytes) -> tuple[str, int, int]:
    dimensions = _png_dimensions(content)
    if dimensions:
        return "png", dimensions[0], dimensions[1]
    dimensions = _jpeg_dimensions(content)
    if dimensions:
        return "jpeg", dimensions[0], dimensions[1]
    raise ResponseValidationError("Decoded data is not a valid PNG or JPEG image.")


def extract_image_bytes(response: dict[str, Any], timeout: float) -> tuple[bytes, str]:
    data = response.get("data")
    if not isinstance(data, list) or not data or not isinstance(data[0], dict):
        raise ResponseValidationError("Response has no generated image in data[0].")

    first_image = data[0]
    encoded = first_image.get("b64_json")
    if isinstance(encoded, str) and encoded:
        try:
            return base64.b64decode(encoded, validate=True), "b64_json"
        except (binascii.Error, ValueError) as exc:
            raise ResponseValidationError("Response b64_json is invalid base64.") from exc

    image_url = first_image.get("url")
    if isinstance(image_url, str) and image_url:
        validate_endpoint(image_url)
        try:
            with urllib.request.urlopen(image_url, timeout=timeout) as image_response:
                return image_response.read(), "url"
        except (urllib.error.URLError, TimeoutError) as exc:
            raise ResponseValidationError(f"Unable to download image URL: {exc}") from exc

    raise ResponseValidationError("Response includes neither b64_json nor an image URL.")


def save_generated_image(
    response: dict[str, Any], output_path: Path, timeout: float
) -> SavedImage:
    image_bytes, source = extract_image_bytes(response, timeout)
    image_format, width, height = identify_image(image_bytes)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(image_bytes)
    return SavedImage(output_path, image_format, width, height, source)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Call and validate the single-image generations endpoint."
    )
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--model", default="gpt-image-2")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--size", default="1024x1024")
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = build_payload(args.prompt, args.model, args.size)
        response = request_generation(
            args.endpoint, get_api_key(), payload, args.timeout
        )
        saved = save_generated_image(response, args.output, args.timeout)
    except ImageGenerationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    summary = {
        "status": "ok",
        "created": response.get("created"),
        "image_source": saved.source,
        "format": saved.image_format,
        "width": saved.width,
        "height": saved.height,
        "output": str(saved.path.resolve()),
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
