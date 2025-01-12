#!/usr/bin/env python3
import json
import math
from typing import TypedDict

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
    
# TODO: add flag to choose distance function
def distance_between_points(a: ColorInfo, b: ColorInfo) -> float:
    # We need to linearize the hue distance and chroma distance,
    # because they are in different scales compared to lightness.
    #l_dist = scaled_dist(a["l"], b["l"], 1)
    c_dist = scaled_dist(a["c"], b["c"], 0.4)
    h_dist = scaled_dist(a["h"], b["h"], 360)
    
    return math.sqrt(h_dist ** 2 + c_dist ** 2)


def top_k_closest_points(color_infos: list[ColorInfo], point: ColorInfo, k: int) -> list[ColorInfo]:
    """Returns k closest points to a given point"""
    distances = [(distance_between_points(point, ci), ci) for ci in color_infos if ci != point]
    distances.sort(key=lambda x: x[0])
    return [ci for _, ci in distances[:k]]

def main():
    with open("color_infos.jsonl") as f:
        color_infos: list[ColorInfo] = []
        for line in f.readlines():
            color_infos.append(json.loads(line))

    for ci in color_infos:
        top_k = top_k_closest_points(color_infos, ci, 5)
        print(ci["name"], ci["oklch_css"])
        for k in top_k:
            print("  ", k["name"], k["oklch_css"])
        
main()