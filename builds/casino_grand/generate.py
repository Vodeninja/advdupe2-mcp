"""Larger Art Deco casino made entirely from permitted physics props."""
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
BLACK=(24,29,37,255); GOLD=(207,162,74,255); RED=(102,20,42,255)
CREAM=(225,217,192,255); GREEN=(19,79,66,255); LIGHT=(250,229,172,255)
F=3.5; FRONT=-190.05; BACK=190.05; TOP=194.3

def stroke(a,c):
    length=math.dist(a,c)
    suffix=min(('025','05','075','1','125'),key=lambda t:abs(b.info('models/hunter/plates/plate025x'+t+'.mdl')['size'][1]-length))
    theta=math.degrees(math.atan2(c[1]-a[1],c[0]-a[0]))
    b.plate('plate025x'+suffix,((a[0]+c[0])/2,FRONT-26,(a[1]+c[1])/2),(0,-90,theta),LIGHT,group='lettering')

def main():
    b.props.clear();b.scene.clear()
    head=None
    # Eight floor and roof panels enclose a 570 x 380 unit hall.
    for x in (-142.6,142.6):
        for y in (-142.6,-47.7,47.7,142.6):
            ident=b.plate('plate2x6',(x,y,1.75),(0,90,0),RED,group='floor')
            if head is None:head=ident
            b.plate('plate2x6',(x,y,TOP+1.75),(0,90,0),BLACK,group='roof')
        b.plate('plate2x6',(x,FRONT-47.7,1.75),(0,90,0),(61,66,73,255),group='entrance_apron')
        for z in (F+47.7,F+143.1):
            b.plate('plate2x6',(x,BACK,z),(-90,90,0),BLACK,group='walls')
    for x in (-285.2,285.2):
        for z in (F+47.7,F+143.1):
            b.plate('plate2x8',(x,0,z),(-90,0,0),BLACK,group='walls')
    # Four glazed bays sit over contrasting stone plinths.
    for x in (-190.6,-95.2,95.2,190.6):
        b.plate('plate1x2',(x,FRONT,F+23.975),(-90,90,0),CREAM,group='plinth')
        b.add('props_phx/construct/glass/glass_plate2x2.mdl',(x,FRONT,F+95.4),(0,0,90),(186,213,219,135),group='windows')
    for x in (-142.6,142.6):
        b.plate('plate1x6',(x,FRONT,170.325),(-90,90,0),BLACK,group='fascia')
    # Tall end pylons with recessed gold fins and projecting caps.
    for side in (-1,1):
        x=side*261.225
        b.plate('plate1x4',(x,FRONT-6,F+95.15),(0,0,90),BLACK,group='pylons')
        for dx in (-13,0,13):
            b.beam('4',(x+dx,FRONT-12,102),90,GOLD,group='pylon_fins')
        b.plate('plate1x1',(x,FRONT-10,205),color=GOLD,group='pylon_caps')
        b.plate('plate05x05',(x,FRONT-15,171),(45,0,90),GOLD,group='pylon_emblems')
    for x in (-237.6,-47.5,47.5,237.6):
        b.beam('4',(x,FRONT-8,F+95.15),90,GOLD,group='columns')
        for z in (10,190):
            b.add('hunter/blocks/cube05x05x025.mdl',(x,FRONT-8,z),color=GOLD,material=b.FLAT,group='column_caps')
    for x in (-142.6,142.6):
        for z in (147,198):b.beam('6',(x,FRONT-6,z),color=GOLD,group='cornice')
        b.beam('6',(x,BACK,198),color=GOLD,group='cornice')
    for x in (-285.2,285.2):
        b.add('hunter/blocks/cube025x8x025.mdl',(x,0,198),color=GOLD,material=b.FLAT,group='cornice')
    # Raised central sign and a deep entrance canopy.
    b.plate('plate1x6',(0,FRONT-18,220),(-90,90,0),BLACK,group='sign_board')
    for z in (195,245):b.beam('6',(0,FRONT-20,z),color=GOLD,group='sign_border')
    for x in (-142.6,142.6):b.beam('1',(x,FRONT-20,220),90,GOLD,group='sign_border')
    L=((0,-18),(0,18));R=((18,-18),(18,18));T=((0,18),(18,18));M=((0,0),(18,0));B=((0,-18),(18,-18))
    glyph={'C':[L,T,B],'A':[((0,-18),(9,18)),((9,18),(18,-18)),((4,0),(14,0))],
           'S':[T,((0,0),(0,18)),M,((18,-18),(18,0)),B],
           'I':[((9,-18),(9,18))],'N':[L,R,((0,18),(18,-18))],'O':[L,R,T,B]}
    for i,ch in enumerate('CASINO'):
        for a,c in glyph[ch]:stroke((a[0]-104+i*38,a[1]+220),(c[0]-104+i*38,c[1]+220))
    for x in range(-120,121,30):
        for z in (194,246):b.plate('plate025x025',(x,FRONT-28,z),(0,0,90),LIGHT,group='marquee_bulbs')
    b.plate('plate2x4',(0,FRONT-38,145),(0,90,0),BLACK,group='canopy')
    b.beam('4',(0,FRONT-86,145),color=RED,group='canopy_fascia')
    b.beam('4',(0,FRONT-87,151),color=GOLD,group='canopy_trim')
    b.beam('4',(0,FRONT-87,139),color=GOLD,group='canopy_trim')
    b.plate('plate2x2',(0,FRONT-47.7,5.25),color=RED,group='red_carpet')
    for x in (-204,-148,148,204):
        for dx,theta in ((-14,24),(14,-24)):
            b.plate('plate025x075',(x+dx,FRONT-14,173),(0,-90,theta),GOLD,group='facade_chevrons')
    # Brass queue posts and red rails frame the carpet without narrowing the door.
    for x in (-65,65):
        for y in (FRONT-20,FRONT-80):
            b.add('hunter/blocks/cube025x025x025.mdl',(x,y,9.68),color=GOLD,material=b.FLAT,group='queue_posts')
            b.beam('075',(x,y,27.5),90,GOLD,group='queue_posts')
            b.plate('plate025x025',(x,y,47.3),color=GOLD,group='queue_posts')
        b.add('hunter/blocks/cube025x125x025.mdl',(x,FRONT-50,40),color=RED,material=b.FLAT,group='queue_rails')
    # Six individual slot cabinets, controls, reels and seats.
    for y in (-130,-75,-20,35,90,145):
        x=-251
        b.add('hunter/blocks/cube05x1x05.mdl',(x,y,27.475),(0,0,90),BLACK,b.FLAT,group='slot_cabinets')
        b.on_floor('hunter/blocks/cube05x05x05.mdl',x,y,floor=51.45,color=RED,material=b.FLAT,group='slot_cabinets')
        b.add('props_lab/monitor01b.mdl',(x+21,y,61),group='slot_screens')
        b.plate('plate025x05',(x+17,y,45),color=GOLD,group='slot_controls')
        for dy,col in [(-9,LIGHT),(0,RED),(9,GOLD)]:
            b.plate('plate025x025',(x+29,y+dy,61),(0,0,90),col,group='slot_reels')
        b.on_floor('props_c17/chair_stool01a.mdl',x+55,y,color=RED,material=b.FLAT,group='stools')
    # Three card tables, oriented around a generous central circulation area.
    for x,y in [(-91,-18),(100,-18),(100,92)]:
        b.on_floor('props_c17/furnituretable002a.mdl',x,y,yaw=90,group='card_tables')
        b.plate('plate1x2',(x,y,F+38.5),(0,90,0),GREEN,group='table_felt')
        for dx in (-58,58):b.on_floor('props_c17/chair_stool01a.mdl',x+dx,y,color=RED,material=b.FLAT,group='stools')
        for dx,col in [(-24,GOLD),(0,RED),(24,LIGHT)]:
            b.plate('plate025x025',(x+dx,y-7,F+42),color=col,group='chips')
    # Rear-left cashier and rear-right bar.
    for cx,cy,length,group in [(-91,152,'3','cashier'),(242,82,'3','bar')]:
        yaw=-90 if group=='cashier' else 0
        for z in (9.68,22.04,34.4):
            b.add('hunter/blocks/cube05x'+length+'x025.mdl',(cx,cy,z),(0,yaw,0),RED,b.FLAT,group=group)
        b.plate('plate05x3',(cx,cy,42.33),(0,90 if group=='cashier' else 0,0),GOLD,group=group)
    b.on_floor('props_c17/tv_monitor01.mdl',-90,152,floor=44.08,yaw=-90,group='cash_register')
    b.plate('plate1x3',(-91,BACK-3,105),(-90,90,0),RED,group='cashier_sign')
    for x in (-127,-91,-55):b.plate('plate025x025',(x,BACK-8,105),(45,0,90),GOLD,group='cashier_sign')
    for y in (36,82,128):b.on_floor('props_c17/chair_stool01a.mdl',202,y,color=RED,material=b.FLAT,group='bar_stools')
    b.plate('plate05x3',(274,82,100),color=GOLD,group='bar_shelf')
    for y in (48,116):
        b.on_floor('props_c17/pottery02a.mdl',274,y,floor=101.75,color=GOLD,material=b.FLAT,group='bar_decor')
    # Lounge at front-right, with low coffee table and two sofas.
    for y in (-112,-48):
        b.on_floor('props/cs_office/sofa.mdl',230,y,yaw=90 if y==-112 else -90,color=RED,group='lounge')
    b.on_floor('props_c17/furnituretable003a.mdl',230,-80,yaw=90,group='lounge')
    b.on_floor('props_c17/pottery01a.mdl',230,-80,floor=25.27,color=CREAM,material=b.FLAT,group='lounge_decor')
    # Interior wall panels add rhythm to otherwise plain side walls.
    for y in (-120,-30,60,150):
        b.add('hunter/blocks/cube025x2x025.mdl',(281,y,111),(0,0,90),GOLD,b.FLAT,group='interior_trim')
    for x in (-255,-110,110,255):
        b.on_floor('props/de_inferno/potted_plant1.mdl',x,FRONT-56,group='plants')
    for x in (-130,130):
        for y in (-95,80):b.add('props_c17/lamp001a.mdl',(x,y,TOP-13),(0,0,180),GOLD,b.FLAT,group='ceiling_lamps')
    for x in (-215,215):
        b.add('props_c17/lampshade001a.mdl',(x,FRONT-30,126),color=LIGHT,material=b.FLAT,group='exterior_lamps')
    for prop,item in zip(b.props,b.scene):
        if prop.get('color')==list(GOLD):
            prop['material']=item['material']='models/shiny'
    spec=BuildSpec(props=b.props,head_id=head,weld_to_head=True,ground_z=0,
        description='GRAND CASINO | Art Deco facade, marquee, canopy, 6 decorative slots, 3 card tables, bar and lounge | max 250 props')
    assert len(b.props)<=250, len(b.props)
    b.policy.check(make_build(spec))
    vertices=[]
    for item in b.scene:
        rot=b.matrix(item['angle'])
        for v in itertools.product(*zip(item['hull_min'],item['hull_max'])):
            vertices.append([a+c for a,c in zip(b.rotate(rot,v),item['pos'])])
    lo=[min(v[i] for v in vertices) for i in range(3)];hi=[max(v[i] for v in vertices) for i in range(3)]
    size=[round(c-a,3) for a,c in zip(lo,hi)]
    old=json.loads((OUT.parent/'casino_small/report.json').read_text())['size_source_units']
    report={'props':len(b.props),'prop_limit':250,'welds':len(b.props)-1,'groups':dict(Counter(v['group'] for v in b.scene)),
        'bounds':{'min':lo,'max':hi},'size_source_units':size,'footprint_ratio_to_previous_casino':round(size[0]*size[1]/(old[0]*old[1]),3),
        'all_models_allowed':True,'entrance_clear_width':82.6,'functional_game_entities':False,'dupe_name':'mcp/casino_grand.txt'}
    for name,value in [('build.json',spec.model_dump(mode='json')),('scene.json',b.scene),('report.json',report)]:
        (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__':main()
