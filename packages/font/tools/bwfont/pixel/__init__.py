"""Bloxwap Pixel — bitmap-grid family with rounded pixels.

`generate_pixel(outdir)` writes the UFO masters (wght × ROND × ital) and
`BloxwapPixel.designspace` into `outdir` (normally sources/pixel/).
"""
from .build import generate_pixel  # noqa: F401
