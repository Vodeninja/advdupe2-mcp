"""OLIVA: cream, olive and timber restaurant with a furnished terrace."""
import importlib.util
import itertools
import json
import math
from collections import Counter
from pathlib import Path
from adv2mcp.build import BuildSpec, make_build

OUT=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('parts',OUT.parent/'parts.py')
b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
CREAM=(221,214,192,255); WOOD=(116,79,49,255); OLIVE=(67,85,60,255)
DARK=(38,47,43,255); BRASS=(184,151,87,255); WHITE=(246,239,217,255)
F=3.5; FRONT=-190.05; BACK=190.05; TOP=194.3

def stroke(a,c):
    length=math.dist(a,c)
    suffix=min(('025','05','075','1'),key=lambda t:abs(b.info('models/hunter/plates/plate025x'+t+'.mdl')['size'][1]-length))
    theta=math.degrees(math.atan2(c[1]-a[1],c[0]-a[0]))
    b.plate('plate025x'+suffix,((a[0]+c[0])/2,FRONT-24,(a[1]+c[1])/2),(0,-90,theta),WHITE,group='lettering')

def main():
    b.props.clear();b.scene.clear();head=None
    for x in (-142.6,142.6):
        for y in (-142.6,-47.7,47.7,142.6):
            ident=b.plate('plate2x6',(x,y,1.75),(0,90,0),(148,139,120,255),group='floor')
            if head is None:head=ident
            b.plate('plate2x6',(x,y,TOP+1.75),(0,90,0),DARK,group='roof')
        b.plate('plate3x6',(x,FRONT-71.425,1.75),(0,90,0),WOOD,group='terrace_deck')
        for z in (F+47.7,F+143.1):
            b.add('hunter/plates/plate2x6.mdl',(x,BACK,z),(-90,90,0),CREAM,'brick/brick_model',group='walls')
    for x in (-285.2,285.2):
        for z in (F+47.7,F+143.1):
            b.add('hunter/plates/plate2x4.mdl',(x,95.15,z),(-90,0,0),CREAM,'brick/brick_model',group='walls')
        b.plate('plate1x4',(x,-95.15,F+23.975),(-90,0,0),OLIVE,group='side_plinth')
        b.plate('plate1x4',(x,-95.15,170.325),(-90,0,0),CREAM,group='side_header')
        for y in (-142.6,-47.7):
            b.add('props_phx/construct/glass/glass_plate2x2.mdl',(x,y,F+95.4),(0,90,90),(203,225,211,110),group='windows')
        b.beam('3',(x,-95.15,75),90,DARK,group='side_frames')
        b.add('hunter/blocks/cube025x4x025.mdl',(x,-95.15,146),color=DARK,material=b.FLAT,group='side_frames')
    # Tall glazing over an olive plinth; a clear central entrance.
    for x in (-209.6,-114.2,114.2,209.6):
        b.plate('plate1x2',(x,FRONT,F+23.975),(-90,90,0),OLIVE,group='plinth')
        b.add('props_phx/construct/glass/glass_plate2x2.mdl',(x,FRONT,F+95.4),(0,0,90),(203,225,211,110),group='windows')
    for x in (-277,-162,-62,62,162,277):
        b.beam('3',(x,FRONT-5,75),90,DARK,group='window_frames')
    # End cheeks close small gaps between the glazing and side walls.
    for x in (-274,274):
        b.plate('plate05x3',(x,FRONT,75),(0,0,90),CREAM,group='facade_cheeks')
    for x in (-142.6,142.6):
        b.plate('plate1x6',(x,FRONT,170.325),(-90,90,0),DARK,group='fascia')
        for z in (151,159,167,175,183,191):
            b.beam('6',(x,FRONT-9,z),color=WOOD,group='wood_louvers')
        for z in (144,200):b.beam('6',(x,FRONT-8,z),color=CREAM,group='cornice')
        b.beam('6',(x,BACK,200),color=CREAM,group='cornice')
    for x in (-285.2,285.2):
        b.add('hunter/blocks/cube025x8x025.mdl',(x,0,200),color=CREAM,material=b.FLAT,group='cornice')
    # Central nameplate projects in front of the timber louvers.
    b.plate('plate1x5',(0,FRONT-17,174),(-90,90,0),OLIVE,group='sign_board')
    L=((0,-15),(0,15));R=((18,-15),(18,15));T=((0,15),(18,15));B=((0,-15),(18,-15))
    glyph={'O':[L,R,T,B],'L':[L,B],'I':[((9,-15),(9,15))],
           'V':[((0,15),(9,-15)),((9,-15),(18,15))],
           'A':[((0,-15),(9,15)),((9,15),(18,-15)),((4,0),(14,0))]}
    for i,ch in enumerate('OLIVA'):
        for a,c in glyph[ch]:stroke((a[0]-85+i*38,a[1]+174),(c[0]-85+i*38,c[1]+174))
    for z in (149,199):b.beam('5',(0,FRONT-20,z),color=BRASS,group='sign_border')
    for side,yaw in ((-1,80),(1,100)):
        theta=math.radians(yaw);hinge=side*57
        b.add('props_phx/construct/glass/glass_plate1x2.mdl',(hinge+24*math.cos(theta),FRONT+24*math.sin(theta),F+47.731),
            (0,yaw,90),(204,225,214,110),group='doors')
        b.plate('plate025x025',(hinge+41*math.cos(theta)+2*math.sin(theta),FRONT+41*math.sin(theta)-2*math.cos(theta),54),
            (0,yaw,90),BRASS,group='door_handles')
    # Left terrace pergola; its open slats keep the terrace visually light.
    for x in (-285,-95):
        for y in (FRONT-10,FRONT-132):
            b.beam('3',(x,y,F+71.425),90,WOOD,group='pergola_posts')
    for y in (FRONT-8,FRONT-132):b.beam('4',(-190,y,153),color=WOOD,group='pergola_rim')
    for y in (FRONT-8,FRONT-33,FRONT-58,FRONT-83,FRONT-108,FRONT-133):
        b.beam('4',(-190,y,165),color=WOOD,group='pergola_slats')
    # Low timber railings leave a broad central route to the door.
    for side in (-1,1):
        for x in (side*90,side*270):b.beam('1',(x,FRONT-137,27.475),90,DARK,group='terrace_railing')
        for z in (22,46):b.beam('4',(side*180,FRONT-137,z),color=WOOD,group='terrace_railing')
    for y in (FRONT-22,FRONT-62,FRONT-102):
        for x in (-142.6,142.6):
            b.plate('plate025x125',(x,y,3.7),(0,90,0),CREAM,group='deck_inlay')
    # Four indoor tables and two terrace tables with real mugs and small vases.
    for x,y in [(-162,-75),(145,-75),(-162,24),(145,24),(-176,FRONT-70),(176,FRONT-70)]:
        b.on_floor('props_c17/furnituretable002a.mdl',x,y,yaw=90,group='dining_tables')
        for dx,yaw in ((-48,0),(48,180)):
            b.on_floor('props_c17/furniturechair001a.mdl',x+dx,y,yaw=yaw,color=OLIVE,material=b.FLAT,group='dining_chairs')
        table_top=F+b.info('models/props_c17/furnituretable002a.mdl')['size'][2]
        for dx in (-17,17):
            b.plate('plate025x025',(x+dx,y,table_top+1.75),color=CREAM,group='table_linen')
            b.on_floor('props/cs_office/coffee_mug2.mdl',x+dx,y+12,floor=table_top,group='tableware')
        b.on_floor('props_c17/pottery01a.mdl',x,y,floor=table_top,color=CREAM,material=b.FLAT,group='table_vases')
    # Service bar on the right, with a separate preparation area on the left.
    for z in (9.68,22.04,34.4):
        b.add('hunter/blocks/cube05x3x025.mdl',(163,129,z),(0,-90,0),OLIVE,b.FLAT,group='bar')
    b.plate('plate05x3',(163,129,42.33),(0,90,0),WOOD,group='bar')
    for x in (113,163,213):b.on_floor('props_c17/chair_stool01a.mdl',x,89,color=OLIVE,material=b.FLAT,group='bar_stools')
    b.on_floor('props_c17/tv_monitor01.mdl',116,129,floor=44.08,yaw=-90,group='till')
    for x in (168,207):b.on_floor('props/cs_office/coffee_mug2.mdl',x,129,floor=44.08,group='bar_tableware')
    for x in (-183,-115,-47):
        b.on_floor('props_wasteland/kitchen_counter001a.mdl',x,151,yaw=-90,group='kitchen')
    b.on_floor('props_c17/furniturefridge001a.mdl',-253,152,yaw=-90,group='kitchen')
    b.on_floor('props_c17/furniturestove001a.mdl',20,152,yaw=-90,group='kitchen')
    b.plate('plate1x6',(-142.6,78,27.475),(-90,90,0),OLIVE,group='kitchen_partition')
    # Small menu boards above the bar and decorative wall panels in the hall.
    for x in (111,165,219):
        b.plate('plate1x1',(x,BACK-5,115),(-90,90,0),DARK,group='menus')
        for z in (108,120):b.plate('plate025x075',(x,BACK-12,z),(0,-90,0),CREAM,group='menu_lines')
    for x in (-283,283):
        for y in (-80,35):
            b.plate('plate1x2',(x,y,100),(0,90,90),OLIVE,group='wall_panels')
            b.add('hunter/blocks/cube025x2x025.mdl',(x+(-3 if x>0 else 3),y,100),(0,0,90),BRASS,b.FLAT,group='wall_trim')
    for x in (-264,-78,78,264):
        b.on_floor('props/de_inferno/potted_plant1.mdl',x,FRONT-118,group='terrace_plants')
    for x in (-250,250):
        b.on_floor('props/cs_office/plant01.mdl',x,-151,group='indoor_plants')
    for x in (-240,240):
        b.on_floor('props/de_inferno/potted_plant1.mdl',x,57,group='indoor_plants')
    for x in (-160,145):
        for y in (-75,24):b.add('props_c17/lamp001a.mdl',(x,y,TOP-20),(0,0,180),CREAM,b.FLAT,group='ceiling_lamps')
    for x in (-243,243):
        b.add('props_c17/lampshade001a.mdl',(x,FRONT-27,133),color=WHITE,material=b.FLAT,group='facade_lamps')
    for x in (-219,-133):
        b.add('props_c17/lamp001a.mdl',(x,FRONT-70,142),(0,0,180),CREAM,b.FLAT,group='pergola_lamps')
    for prop,item in zip(b.props,b.scene):
        if prop.get('color')==list(BRASS):prop['material']=item['material']='models/shiny'
    spec=BuildSpec(props=b.props,head_id=head,weld_to_head=True,ground_z=0,
        description='OLIVA restaurant | cream, olive and timber | terrace pergola, six tables, bar, kitchen | max 250 props')
    assert len(b.props)<=250,len(b.props)
    b.policy.check(make_build(spec))
    vertices=[]
    for item in b.scene:
        rot=b.matrix(item['angle'])
        for v in itertools.product(*zip(item['hull_min'],item['hull_max'])):
            vertices.append([a+c for a,c in zip(b.rotate(rot,v),item['pos'])])
    lo=[min(v[i] for v in vertices) for i in range(3)];hi=[max(v[i] for v in vertices) for i in range(3)]
    report={'props':len(b.props),'prop_limit':250,'welds':len(b.props)-1,'groups':dict(Counter(v['group'] for v in b.scene)),
        'bounds':{'min':lo,'max':hi},'size_source_units':[round(c-a,3) for a,c in zip(lo,hi)],
        'all_models_allowed':True,'entrance_min_clear_width':92,'dupe_name':'mcp/restaurant_oliva.txt'}
    for name,value in [('build.json',spec.model_dump(mode='json')),('scene.json',b.scene),('report.json',report)]:
        (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__':main()
