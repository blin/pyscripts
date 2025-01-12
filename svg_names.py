#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "colour-science",
#     "matplotlib",
# ]
# ///
import json
import math
import sys
from typing import TypedDict

import colour
import numpy
from colour.models import (
    Oklab_to_Oklch,
    RGB_COLOURSPACE_sRGB,
    RGB_to_XYZ,
    XYZ_to_Oklab,
    eotf_sRGB,
)
from colour.notation import CSS_COLOR_3, HEX_to_RGB


def rgb_to_oklch(rgb_hex: str) -> numpy.ndarray:
    rgb = HEX_to_RGB(rgb_hex)
    rgb_lin = eotf_sRGB(rgb)

    xyz = RGB_to_XYZ(rgb_lin, RGB_COLOURSPACE_sRGB)
    oklab = XYZ_to_Oklab(xyz)
    oklch: numpy.ndarray = Oklab_to_Oklch(oklab)
    return oklch


class ColorInfo(TypedDict):
    name: str
    rgb_hex: str
    oklch_css: str
    l: float
    c: float
    h: int
    l_pct: int
    c_pct: int
    dist_to_peak: int


def scaled_dist(x: float, y: float, max: float) -> float:
    return abs(x - y) / max


def distance_to_peak(l: float, c: float) -> int:
    # https://www.w3.org/TR/css-color-4/images/OKLCH-blue-slice.png
    l_dist = scaled_dist(l, 0.5, 1)
    c_dist = scaled_dist(c, 0.4, 0.4)
    return int(math.sqrt(l_dist**2 + c_dist**2) * 100)


def build_color_info(name: str, rgb_hex: str, oklch: numpy.ndarray) -> str:
    l = round(oklch[0], 5)
    c = round(oklch[1], 5)
    h = int(oklch[2])
    l_pct = int(l * 100)
    c_pct = int((c / 0.4) * 100)
    css = f"oklch({l_pct}% {c_pct}% {h})"
    dist_to_peak = distance_to_peak(l, c)

    return {
        "name": name,
        "rgb_hex": rgb_hex,
        "oklch_css": css,
        "l": l,
        "c": c,
        "h": h,
        "l_pct": l_pct,
        "c_pct": c_pct,
        "dist_to_peak": dist_to_peak,
    }


def extract_color(
    colors: list[ColorInfo], hue: int, dist_to_peak: int
) -> ColorInfo | None:
    for ci in colors:
        if ci["h"] == hue and ci["dist_to_peak"] == dist_to_peak:
            return ci
    return None


def has_any_prefix(n: str, prefixes: list[str]) -> bool:
    for prefix in prefixes:
        if n != prefix and n.startswith(prefix):
            return True
    return False


def has_any_suffix(n: str, suffixes: list[str]) -> bool:
    for suffix in suffixes:
        if n != suffix and n.endswith(suffix):
            return True
    return False


# This is terryfyingly slow. TODO: optimize
def has_banned_name(n: str, names: list[str]) -> bool:
    joined_names = set()
    for name1 in names:
        for name2 in names:
            joined_names.add(name1 + name2)

    if has_any_prefix(n, names):
        return True
    if has_any_suffix(n, names):
        return True
    if n in joined_names:
        return True
    if n in ["fuchsia", "aqua", "orchid", "chartreuse"]:
        return True
    return False


def build_color_infos(colors: dict[str, str]) -> list[ColorInfo]:
    color_infos = list()

    for name, rgb_hex in colors.items():
        oklch = rgb_to_oklch(rgb_hex)
        ci = build_color_info(name, rgb_hex, oklch)
        n = ci["name"]
        if has_banned_name(n, list(colors.keys())):
            continue
        # colors with low chroma or high lightness are hard to distinguish
        # This excludes some good classic colors like lavender and pink,
        # I might re-introduce them by name, or allow a broader set of colors.
        if ci["c_pct"] < 18:
            continue
        if ci["l_pct"] > 96:
            continue
        color_infos.append(ci)
    return color_infos


def main_print_json():
    cis = build_color_infos(CSS_COLOR_3)
    for ci in cis:
        print(json.dumps(ci))


def main_print_html():
    color_infos = build_color_infos(CSS_COLOR_3)

    # TODO: jinja template or something?
    print(
        """
    <!DOCTYPE html>
    <meta charset="utf-8">
    <title>CSS Color 4: OKLab and OKLCH</title>
    <style>
    .swatch {
        position: relative;
        z-index: 1;
        display: inline-block;
        vertical-align: calc(-.1em - 3px);
        padding: 1.6em;
        background-color: var(--color);
        border: 3px solid white;
        border-radius: 3px;
        box-shadow: 1px 1px 1px rgba(0,0,0,.15)
    }
    td {
        white-space: nowrap;
        padding: 10px;
        text-align: center;
    }
    </style>
    <body>
    """
    )

    # TODO: add a flag
    show_empty = True
    if show_empty:
        hues = range(0, 360)

        max_dist_to_peaks = max([c["dist_to_peak"] for c in color_infos])
        dist_to_peaks = [i for i in range(0, max_dist_to_peaks + 1)]
    else:
        hues = sorted(set([c["h"] for c in color_infos]))
        hues = hues
        dist_to_peaks = sorted(
            set([c["dist_to_peak"] for c in color_infos]), reverse=False
        )
    # TODO: add a flag to chose y-axis

    print("<table>")
    print("<tr>")
    print("<td></td>")
    for hue in hues:
        print(f"<td>{hue}</td>")
    print("</tr>")

    for dist_to_peak in dist_to_peaks:
        print("<tr>")
        print(f"<td>{dist_to_peak}</td>")
        for hue in hues:
            c = extract_color(color_infos, hue, dist_to_peak)
            if c is None:
                print("<td>")
                print("</td>")
                continue

            print("<td>")
            print(
                f"""<span class="swatch" style="--color: {c["oklch_css"]}" tabindex="0"></span>"""
            )
            print("<br/>")
            print(c["name"])
            print("<br/>")
            print(c["oklch_css"])
            print("</td>")
        print("</tr>")
    print("</table>")

    print("</body>")


# TODO: two commands
if sys.argv[1] == "json":
    main_print_json()
else:
    main_print_html()
