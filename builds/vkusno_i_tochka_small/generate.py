"""A walkable kiosk with roughly one ninth of the original footprint."""

from __future__ import annotations

import importlib.util
import json
import math
from collections import Counter
from pathlib import Path

from adv2mcp.build import BuildSpec, make_build

OUT=Path(__file__).resolve().parent
original=OUT.parent
module_spec=importlib.util.spec_from_file_location("restaurant_parts",original/"parts.py")
b=importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(b)

FRONT=-71.425
SIGN_Y=FRONT-20


def stroke(a,c):
    length=math.hypot(c[0]-a[0],c[1]-a[1])
    candidates=[(suffix,b.info(f"models/hunter/plates/plate025x{suffix}.mdl")["size"][1]) for suffix in ("025","05","075")]
    suffix,_=min(candidates,key=lambda item:abs(item[1]-length))
    angle=math.degrees(math.atan2(c[1]-a[1],c[0]-a[0]))
    b.plate(f"plate025x{suffix}",((a[0]+c[0])/2,SIGN_Y,(a[1]+c[1])/2),
            (0,-90,angle),b.WHITE,group="lettering")


def word(text,x,z):
    L=((0,-12),(0,12));R=((12,-12),(12,12))
    T=((0,12),(12,12));M=((0,0),(12,0));B=((0,-12),(12,-12))
    glyphs={
        "В":[L,((0,12),(10,12)),M,B,((10,0),(10,12)),((12,-12),(12,0))],
        "К":[L,((0,0),(12,12)),((0,0),(12,-12))],
        "У":[((0,12),(6,0)),((12,12),(6,0)),((6,0),(0,-12))],
        "С":[L,T,B],"Н":[L,R,M],"О":[L,R,T,B],
        "И":[L,R,((0,-12),(12,12))],"Т":[T,((6,-12),(6,12))],
        "Ч":[((0,12),(0,0)),M,R],
        "А":[((0,-12),(6,12)),((6,12),(12,-12)),((3,-2),(9,-2))],
    }
    for letter in text:
        for a,c in glyphs[letter]:
            stroke((a[0]+x,a[1]+z),(c[0]+x,c[1]+z))
        x+=18


def main():
    b.props.clear();b.scene.clear()
    floor_top=3.5
    # 238 x 143 units inside, plus a 48-unit entrance apron.
    head=b.plate("plate3x5",(0,0,1.75),(0,90,0),(111,108,98,255),group="floor")
    b.plate("plate1x5",(0,FRONT-23.975,1.75),(0,90,0),(111,108,98,255),group="floor")
    height=b.info("models/hunter/plates/plate2x5.mdl")["size"][0]
    top=floor_top+height
    b.plate("plate3x5",(0,0,top+1.75),(0,90,0),b.DARK,group="roof")
    for x in (-118.875,118.875):
        b.add("hunter/plates/plate2x3.mdl",(x,0,floor_top+height/2),(-90,0,0),
              b.CREAM,"brick/brick_model",group="walls")
    b.add("hunter/plates/plate2x5.mdl",(0,-FRONT,floor_top+height/2),(-90,90,0),
          b.CREAM,"brick/brick_model",group="walls")
    for side in (-1,1):
        b.plate("plate1x1",(side*84,FRONT,27.475),(-90,90,0),b.WHITE,group="facade")
        b.add("props_phx/construct/glass/glass_plate1x1.mdl",(side*84,FRONT,75),
              (0,0,90),(224,235,220,155),group="glazing")
        for x in (54,113):
            b.beam("2",(side*x,FRONT-2,floor_top+height/2),90,b.DARK,group="frames")
    b.beam("5",(0,FRONT-2,top),color=b.DARK,group="frames")
    # Both glass leaves are permanently open, with a 67-unit center passage.
    for side,yaw in ((-1,75),(1,105)):
        theta=math.radians(yaw)
        hinge=side*47.8
        b.add("props_phx/construct/glass/glass_plate1x2.mdl",
              (hinge+24*math.cos(theta),FRONT+24*math.sin(theta),floor_top+47.731),
              (0,yaw,90),(225,237,220,150),group="doors")
        b.plate("plate025x025",(hinge+42*math.cos(theta)+2*math.sin(theta),
                  FRONT+42*math.sin(theta)-2*math.cos(theta),52),
                (0,yaw,90),b.ORANGE,group="door_handles")
    b.plate("plate1x5",(0,FRONT,126),(-90,90,0),b.DARK,group="fascia")
    for i in range(5):
        b.beam("5",(0,FRONT-7,100+13*i),color=b.BROWN,group="fascia")
    for x in (-113,113):
        b.beam("1",(x,FRONT-15,126),90,(130,82,54,255),group="fascia")
    word("ВКУСНО",-35,143)
    stroke((-42,115),(-30,115))
    word("И",-18,115)
    word("ТОЧКА",12,115)
    b.add("props_c17/clock01.mdl",(-94,SIGN_Y-3,111),(0,0,90),b.RED,b.FLAT,group="logo")
    b.beam("05",(-79,SIGN_Y-3,129),118,b.ORANGE,group="logo")
    b.beam("05",(-64,SIGN_Y-3,129),118,b.ORANGE,group="logo")
    # Thin counter leaves a usable staff corridor at the rear and side access.
    counter_height=b.info("models/hunter/blocks/cube05x3x025.mdl")["size"][2]
    for i in range(3):
        b.add("hunter/blocks/cube05x3x025.mdl",(0,8,floor_top+counter_height*(i+.5)),
              (0,-90,0),(198,191,167,255),b.FLAT,group="counter")
    counter_top=floor_top+3*counter_height
    b.plate("plate05x3",(0,8,counter_top+1.75),(0,90,0),b.DARK,group="counter")
    b.on_floor("props_c17/tv_monitor01.mdl",-25,8,floor=counter_top+3.5,yaw=-90,group="tills")
    b.plate("plate1x2",(15,-FRONT-5,70),(-90,90,0),b.DARK,group="menus")
    for z in (63,77):
        b.plate("plate025x075",(15,-FRONT-12,z),(0,-90,0),b.ORANGE,group="menu_lines")
    b.on_floor("props_c17/furniturefridge001a.mdl",-98,45,yaw=-90,group="kitchen")
    for x in (-96,96):
        b.on_floor("props_c17/chair_stool01a.mdl",x,-37,color=b.ORANGE,material=b.FLAT,group="chairs")
    for x in (-92,92):
        b.on_floor("props/de_inferno/potted_plant1.mdl",x,FRONT-24,group="plants")
    for x in (-109,109):
        b.add("props_c17/lamp001a.mdl",(x,FRONT-24,156),(0,0,180),b.WHITE,b.FLAT,group="lamps")

    spec=BuildSpec(props=b.props,head_id=head,weld_to_head=True,ground_z=0,
        description="Vkusno - i tochka SMALL | compact walk-in kiosk | max 150 props")
    assert len(b.props)<=150
    b.policy.check(make_build(spec))
    vertices=[]
    for item in b.scene:
        rot=b.matrix(item["angle"])
        for x in (item["hull_min"][0],item["hull_max"][0]):
            for y in (item["hull_min"][1],item["hull_max"][1]):
                for z in (item["hull_min"][2],item["hull_max"][2]):
                    vertices.append([a+c for a,c in zip(b.rotate(rot,(x,y,z)),item["pos"])])
    bounds={"min":[round(min(v[i] for v in vertices),3) for i in range(3)],
            "max":[round(max(v[i] for v in vertices),3) for i in range(3)]}
    size=[round(c-a,3) for a,c in zip(bounds["min"],bounds["max"])]
    old=json.loads((OUT/"report.json").read_text(encoding="utf-8"))["previous_size_source_units"]
    report={"props":len(b.props),"prop_limit":150,"welds":len(b.props)-1,
        "groups":dict(Counter(item["group"] for item in b.scene)),"bounds":bounds,
        "size_source_units":size,"previous_size_source_units":old,
        "width_reduction_factor":round(old[0]/size[0],2),
        "footprint_reduction_factor":round(old[0]*old[1]/(size[0]*size[1]),2),
        "all_models_allowed":True,"all_models_indexed_locally":True,
        "entrance_min_clear_width":67,"staff_corridor_depth":46,
        "dupe_name":"mcp/vkusno_i_tochka_small.txt"}
    OUT.mkdir(parents=True,exist_ok=True)
    for name,data in (("build.json",spec.model_dump(mode="json")),("scene.json",b.scene),("report.json",report)):
        (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=True,indent=2))


if __name__=="__main__":
    main()
