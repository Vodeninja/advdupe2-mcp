"""Measured front/plan preview. Furniture is represented by its model hull."""

import itertools
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parent
scene=json.loads((ROOT/"scene.json").read_text(encoding="utf-8"))
report=json.loads((ROOT/"report.json").read_text(encoding="utf-8"))
W,H=1800,1500
image=Image.new("RGB",(W,H),(235,232,222))
d=ImageDraw.Draw(image)
font_path="C:/Windows/Fonts/arial.ttf"
font=ImageFont.truetype(font_path,25)
small=ImageFont.truetype(font_path,20)
title=ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf",38)


def transform(v,angle,pos):
    p,y,r=map(math.radians,angle)
    sp,cp,sy,cy,sr,cr=math.sin(p),math.cos(p),math.sin(y),math.cos(y),math.sin(r),math.cos(r)
    m=((cp*cy,sp*sr*cy-cr*sy,sp*cr*cy+sr*sy),
       (cp*sy,sp*sr*sy+cr*cy,sp*cr*sy-sr*cy),(-sp,sr*cp,cr*cp))
    return [sum(a*b for a,b in zip(row,v))+o for row,o in zip(m,pos)]


def vertices(item):
    lo,hi=item["hull_min"],item["hull_max"]
    return [transform(v,item["angle"],item["pos"]) for v in itertools.product(*zip(lo,hi))]


def hull(points):
    pts=sorted(set(tuple(p) for p in points))
    if len(pts)<3:return pts
    def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lower=[]
    for p in pts:
        while len(lower)>=2 and cross(lower[-2],lower[-1],p)<=0:lower.pop()
        lower.append(p)
    upper=[]
    for p in reversed(pts):
        while len(upper)>=2 and cross(upper[-2],upper[-1],p)<=0:upper.pop()
        upper.append(p)
    return lower[:-1]+upper[:-1]


def color(item):
    return tuple(item.get("color",[96,110,91])[:3])


front_scale=min(1550/report["size_source_units"][0],510/report["size_source_units"][2])
def front_point(v):return (W/2+v[0]*front_scale,655-v[2]*front_scale)


def draw_item(item,project,glass=False):
    pts=hull([project(v) for v in vertices(item)])
    fill=color(item)
    if glass:
        layer=Image.new("RGBA",image.size)
        ld=ImageDraw.Draw(layer)
        ld.polygon(pts,fill=(130,183,172,65),outline=(49,72,65,160),width=2)
        image.paste(layer,(0,0),layer)
    elif item["group"] in ("pc_fans","desk_clock","shelf_clock") and project is front_point:
        xs=[v[0] for v in pts]; ys=[v[1] for v in pts]
        box=(min(xs),min(ys),max(xs),max(ys))
        d.ellipse(box,fill=fill,outline=(50,53,52),width=2)
        if item["group"]=="pc_fans":
            cx=(min(xs)+max(xs))/2;cy=(min(ys)+max(ys))/2
            radius=(max(xs)-min(xs))*.28
            d.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),fill=(27,30,32))
    else:
        d.polygon(pts,fill=fill,outline=tuple(int(v*.65) for v in fill),width=1)


d.text((60,35),"PC SETUP / DESK CORNER",fill=(40,46,39),font=title)
subtitle="Ultrawide / showcase PC / shelves / accessories"
d.text((60,89),f'{report["props"]} пропов / 250 · {subtitle} · все модели в разрешённом списке',fill=(70,76,68),font=font)
d.rounded_rectangle((45,145,1755,705),radius=14,fill=(51,57,53))
# Far-to-near order; glass composited so the counter can be seen behind it.
for item in sorted(scene,key=lambda p:p["center"][1],reverse=True):
    draw_item(item,front_point,item["group"] in ("glazing","doors","windows","pc_glass"))
d.line((80,655,1720,655),fill=(156,156,136),width=2)
d.text((65,671),"Фасад: геометрия пропов; фактические игровые текстуры и освещение отличаются",fill=(218,219,204),font=small)

d.text((60,747),"ВИД СВЕРХУ — ПОЛКИ И СТЕНА СКРЫТЫ",fill=(40,46,39),font=font)
scale=min(760/report["size_source_units"][0],520/report["size_source_units"][1])
center_y=(report["bounds"]["min"][1]+report["bounds"]["max"][1])/2
def plan_point(v):return (900+v[0]*scale,1120-(v[1]-center_y)*scale)
hide={"back_wall","curtain","curtain_folds","shelves","shelf_light_strips","books","framed_print","shelf_clock","camera","shelf_vase","figurines","small_plants","plant_leaves","trailing_plant","wall_art","accessory_board","accessory_tray","headphones"}
for item in sorted(scene,key=lambda p:p["center"][2]):
    if item["group"] not in hide:
        draw_item(item,plan_point,item["group"] in ("glazing","doors","windows","pc_glass"))
d.text((1305,855),"Монитор / ПК",font=small,fill=(44,51,43))
d.text((1305,1050),"Стол",font=small,fill=(44,51,43))
d.text((1305,1390),"Кресло",font=small,fill=(44,51,43))
d.text((65,1450),"Предпросмотр по измеренным габаритам MDL. Мебель показана упрощённо; это не скриншот GMod.",font=small,fill=(70,76,68))
image.save(ROOT/"preview.png")
print(ROOT/"preview.png")
