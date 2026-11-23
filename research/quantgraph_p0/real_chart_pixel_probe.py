"""Small original-PNG quantitative smoke test, NOT a model benchmark.

Source and two windows are pinned AFTER visually inspecting one example.
The axis pixel locations are human-read assumptions and must NOT be described
as independent automated detection, formal certified uncertainty, or novelty.
The expected answer is not an input to pixel color segmentation.
"""
import hashlib
import json
import statistics
import urllib.request
from pathlib import Path
from PIL import Image
import io
from quantgraph_p0 import Axis, Mark, Tick, CorrelatedChart

COMMIT="044eabfc306abfe9340c5741f0093aefc5973d06"
ORIGINAL_PNG_SHA="ce394c49e5272c52ffe0e8c6d945c440b835c4a4fdd6ef7e5539eb604d881e4d"
URL=f"https://raw.githubusercontent.com/vis-nlp/ChartQA/{COMMIT}/ChartQA%20Dataset/val/png/4576.png"
# ROI and axis tick y are visual-review choices, NOT learned or blind. 2007/2018 blue.
WINDOWS={"2018_blue":(388,398,160,183),"2013_blue":(225,235,190,212)}
AXIS_TOP_PIXEL=104
AXIS_BOTTOM_PIXEL=340


def extract_blue(image,box):
    x1,x2,y1,y2=box
    pixels=[]
    for x in range(x1,x2+1):
        for y in range(y1,y2+1):
            red,green,blue=image.getpixel((x,y))
            if blue>red+30 and blue>green+25 and green>40 and red<120:
                pixels.append(y)
    if len(pixels)<15:
        raise ValueError("Insufficient original blue curve pixels in frozen ROI")
    return {"min":min(pixels),"max":max(pixels),"median":statistics.median(pixels),
            "n_pixels":len(pixels)}


def run(image_data):
    if hashlib.sha256(image_data).hexdigest()!=ORIGINAL_PNG_SHA:
        raise ValueError("Pinned original public chart source SHA mismatch")
    chart=Image.open(io.BytesIO(image_data)).convert("RGB")
    if chart.size!=(415,467):
        raise ValueError("Original image resolution/source changed")
    measured={name:extract_blue(chart,box) for name,box in WINDOWS.items()}
    axis=Axis(ORIGINAL_PNG_SHA,"4576.png","percent","decreasing","linear",
         (Tick(AXIS_TOP_PIXEL,100,100),Tick(AXIS_BOTTOM_PIXEL,0,0)),
          True)  # Caller asserts manually checked; not cryptographic visual proof
    world=CorrelatedChart(axis,[
      Mark("2018_blue",measured["2018_blue"]["min"],measured["2018_blue"]["max"]),
      Mark("2013_blue",measured["2013_blue"]["min"],measured["2013_blue"]["max"])])
    a=world.bound({"2018_blue":1})
    b=world.bound({"2013_blue":1})
    d=world.bound({"2018_blue":1,"2013_blue":-1})
    if not (a[0]<=72<=a[1] and b[0]<=60<=b[1]):
        raise ValueError("Original chart printed value lies outside putative geometry bounds")
    return {
        "schema":"quantgraph-original-ChartQA-PNG-pixel-source-smoke-v1",
        "original_image_repo":"vis-nlp/ChartQA","source_commit":COMMIT,
        "original_png_sha256":ORIGINAL_PNG_SHA,"original_png_dimensions":list(chart.size),
        "original_question":"What is the max value of blue line?",
        "original_gold_label_as_fraction":"0.72",
        "human_visually_verified_original_printed_max_2018_pct":72,
        "human_visually_verified_original_printed_2013_pct":60,
        "automated_original_image_blue_RGB_pixels":measured,
        "blue_2018_value_interval_pct":a,
        "blue_2013_value_interval_pct":b,
        "difference_2018_minus_2013_interval_pp":d,
        "gold_72_percent_inside_feasible_interval":a[0]<=72<=a[1],
        "precise_point_from_color_pixel_only":world.answer({"2018_blue":1},0.1)["decision"],
        "pixel_windows_selected_after_inspection":True,
        "axis_tick_positions_manually_assumed":True,
        "printed_numeric_annotations_are_available_so_OCR_may_be_stronger":True,
        "no_model_baseline_or_original_2026_method_implemented":True,
        "not_a_blind_benchmark_novelty_or_real_scientific_chart":True,
        "not_a_certified_probability_or_formal_optimality_proof":True,
    }


def main():
    with urllib.request.urlopen(URL,timeout=40) as resp:
        raw=resp.read(2000001)
    if len(raw)>2000000:raise ValueError("Original chart input too large")
    report=run(raw)
    out=Path("results_quantgraph_p0")
    out.mkdir(exist_ok=True)
    (out/"original_pixel_probe.json").write_text(json.dumps(report,indent=2))
    print("ORIGINAL_PNG_PIXEL_EVIDENCE_SMOKE",json.dumps(report,indent=2),flush=True)


if __name__=="__main__":
    main()
