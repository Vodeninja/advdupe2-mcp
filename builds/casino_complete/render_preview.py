"""Top-down layout; geometry is schematic, not an in-game render."""
import importlib.util
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('geometry',OUT.parent/'preview_geometry.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
scene=json.loads((OUT/'scene.json').read_text())
im=Image.new('RGB',(1300,1500),(232,226,211));d=ImageDraw.Draw(im)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',23)
small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19)
title=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',35)
d.text((45,25),'WINSTAR / 100 + 150 = 250 ПРОПОВ',font=title,fill=(39,40,36))
d.text((45,77),'Интерьер: фонтан, колонны, бар, 4 столика, 4 декоративных автомата',font=small,fill=(65,66,60))
scale=1.48
def project(v):return (650+v[0]*scale,1190-v[1]*scale)
hidden={'hall_roof','portico_roof','tower_roof','roof_trim','portico_cornice','portico_side_trim','globe_rings','sign_board','sign_border','lettering','globe_crest','ceiling_rotunda','ceiling_oculus','hanging_lamps','wall_cornice','bar_art','hall_art','bar_shelves'}
for item in sorted(scene,key=lambda v:v['center'][2]):
    if item['group'] in hidden:continue
    verts=g.vertices(item);pts=g.hull([project(v) for v in verts])
    fill=tuple(item.get('color',[110,99,77])[:3]);group=item['group']
    if group in {'fountain_water','fountain_rim','fountain_plinth','rotunda_columns','lounge_tables'}:
        xs=[p[0] for p in pts];ys=[p[1] for p in pts]
        box=(min(xs),min(ys),max(xs),max(ys))
        if group=='fountain_rim':
            d.ellipse(box,fill=(174,132,62),outline=(75,61,37),width=3)
            margin=12
            d.ellipse((box[0]+margin,box[1]+margin,box[2]-margin,box[3]-margin),fill=(75,115,122))
        elif group=='fountain_water':
            margin=9
            d.ellipse((box[0]+margin,box[1]+margin,box[2]-margin,box[3]-margin),fill=(75,115,122))
        else:d.ellipse(box,fill=fill,outline=(74,69,54),width=2)
    elif group=='marble_statue':
        x,y=project(item['center'])
        d.ellipse((x-14,y-22,x+14,y+6),fill=(237,233,217),outline=(102,99,87),width=2)
        d.polygon([(x-7,y+1),(x-25,y+38),(x+25,y+38),(x+7,y+1)],fill=(237,233,217),outline=(102,99,87))
    elif group=='lounge_chairs':
        xs=[p[0] for p in pts];ys=[p[1] for p in pts]
        d.rounded_rectangle((min(xs),min(ys),max(xs),max(ys)),radius=12,fill=fill,outline=(37,48,36),width=2)
    elif len(pts)>2:d.polygon(pts,fill=fill,outline=tuple(int(v*.68) for v in fill))
def label(text,x,y):
    px,py=project((x,y,0));box=d.textbbox((0,0),text,font=small);width=box[2]
    d.rounded_rectangle((px-width/2-8,py-5,px+width/2+8,py+25),radius=5,fill=(237,230,211))
    d.text((px-width/2,py),text,font=small,fill=(38,44,39))
label('БАР',0,580)
label('ФОНТАН / СКУЛЬПТУРА',0,377)
label('ЛАУНЖ',-205,467);label('ЛАУНЖ',205,467)
label('ВХОД · 100 ПРОПОВ',0,-105)
d.text((45,1437),'План сверху. Потолок скрыт; вода, свет и автоматы — декоративные пропы.',font=small,fill=(66,66,59))
im.save(OUT/'preview.png')
print(OUT/'preview.png')
