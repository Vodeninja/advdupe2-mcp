"""Compact casino, approximately twice the small restaurant footprint."""
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from adv2mcp.build import BuildSpec, make_build

OUT=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('parts',OUT.parent/'parts.py')
b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
BLACK=(27,25,32,255); GOLD=(224,176,65,255); RED=(108,19,39,255)
GREEN=(22,86,65,255); WHITE=(245,230,186,255)
F=3.5; FRONT=-119.125; BACK=119.125; TOP=146.35

def stroke(a,c):
    length=math.dist(a,c)
    suffix=min(('025','05','075'),key=lambda t:abs(b.info('models/hunter/plates/plate025x'+t+'.mdl')['size'][1]-length))
    theta=math.degrees(math.atan2(c[1]-a[1],c[0]-a[0]))
    b.plate('plate025x'+suffix,((a[0]+c[0])/2,FRONT-10,(a[1]+c[1])/2),(0,-90,theta),GOLD,group='lettering')

def main():
    b.props.clear();b.scene.clear()
    head=None
    for name,y in [('plate3x7',-47.7),('plate2x7',71.425)]:
        ident=b.plate(name,(0,y,1.75),(0,90,0),RED,group='floor')
        if head is None:head=ident
        b.plate(name,(0,y,TOP+1.75),(0,90,0),BLACK,group='roof')
    b.plate('plate1x7',(0,FRONT-23.975,1.75),(0,90,0),(67,65,72,255),group='entrance_apron')
    for x in (-166.325,166.325):
        b.plate('plate3x5',(x,0,F+71.425),(-90,0,0),BLACK,group='walls')
    b.plate('plate3x7',(0,BACK,F+71.425),(-90,90,0),RED,group='walls')
    # Glazed bays flank a permanently open, generous entrance.
    for x in (-119,119):
        b.add('props_phx/construct/glass/glass_plate2x2.mdl',(x,FRONT,F+47.731),(0,0,90),(204,222,229,130),group='windows')
        b.beam('2',(x,FRONT-3,F),color=GOLD,group='window_trim')
    for x in (-162,-71,71,162):
        b.beam('3',(x,FRONT-3,F+71.425),90,GOLD,group='columns')
    b.plate('plate1x7',(0,FRONT,122.375),(-90,90,0),BLACK,group='fascia')
    for z in (100,150):b.beam('7',(0,FRONT-5,z),color=GOLD,group='cornice')
    for x in (-166.325,166.325):
        b.add('hunter/blocks/cube025x5x025.mdl',(x,0,150),color=GOLD,material=b.FLAT,group='cornice')
    b.beam('7',(0,BACK,150),color=GOLD,group='cornice')
    L=((0,-12),(0,12));R=((12,-12),(12,12));T=((0,12),(12,12));M=((0,0),(12,0));B=((0,-12),(12,-12))
    glyph={'C':[L,T,B],'A':[((0,-12),(6,12)),((6,12),(12,-12)),((3,0),(9,0))],
           'S':[T,((0,0),(0,12)),M,((12,-12),(12,0)),B],
           'I':[((6,-12),(6,12))], 'N':[L,R,((0,12),(12,-12))],'O':[L,R,T,B]}
    for i,ch in enumerate('CASINO'):
        for a,c in glyph[ch]:stroke((a[0]-66+i*24,a[1]+125),(c[0]-66+i*24,c[1]+125))
    for x in (-128,128):
        b.plate('plate025x025',(x,FRONT-9,125),(0,-90,45),GOLD,group='sign_emblems')
    # Eight pairs of small marquee bulbs, represented by white prop caps.
    for x in range(-140,141,40):
        for z in (101,150):
            b.plate('plate025x025',(x,FRONT-12,z),(0,-90,0),WHITE,group='marquee_bulbs')
    # Three decorative slot cabinets along the left wall.
    for y in (-53,0,53):
        x=-132
        b.add('hunter/blocks/cube05x1x05.mdl',(x,y,27.475),(0,0,90),BLACK,b.FLAT,group='slot_cabinets')
        b.on_floor('hunter/blocks/cube05x05x05.mdl',x,y,floor=51.45,color=RED,material=b.FLAT,group='slot_cabinets')
        b.add('props_lab/monitor01b.mdl',(-111,y,61),(0,0,0),group='slot_screens')
        b.plate('plate025x05',(-115,y,45),(0,0,0),GOLD,group='slot_controls')
        # Three colored reels sit on the player-facing side.
        for dy,col in [(-9,GOLD),(0,RED),(9,GOLD)]:
            b.plate('plate025x025',(-103,y+dy,61),(0,0,90),col,group='slot_reels')
        b.on_floor('props_c17/chair_stool01a.mdl',-81,y,color=RED,material=b.FLAT,group='stools')
    # Two green card tables with chairs and chip piles.
    for y in (-34,57):
        b.on_floor('props_c17/furnituretable002a.mdl',89,y,yaw=90,group='card_tables')
        b.plate('plate1x2',(89,y,F+38.5),(0,90,0),GREEN,group='table_felt')
        for x in (33,145):
            b.on_floor('props_c17/chair_stool01a.mdl',x,y,color=RED,material=b.FLAT,group='stools')
        for dx,col in [(-24,GOLD),(0,RED),(24,WHITE)]:
            b.plate('plate025x025',(89+dx,y-7,F+42),color=col,group='chips')
    # Cashier counter at the rear; central aisle remains clear.
    for z in (9.68,22.04,34.4):
        b.add('hunter/blocks/cube05x2x025.mdl',(-37,91,z),(0,-90,0),RED,b.FLAT,group='cashier')
    b.plate('plate05x2',(-37,91,42.33),(0,90,0),GOLD,group='cashier')
    b.on_floor('props_c17/tv_monitor01.mdl',-44,91,floor=44.08,yaw=-90,group='cash_register')
    b.plate('plate1x2',(-37,BACK-3,94),(-90,90,0),BLACK,group='cashier_sign')
    for x in (-60,-37,-14):
        b.plate('plate025x025',(x,BACK-8,94),(0,-90,45),GOLD,group='cashier_sign')
    for x in (-148,148):
        b.on_floor('props/de_inferno/potted_plant1.mdl',x,FRONT-27,group='plants')
    for y in (-60,40):
        b.add('props_c17/lamp001a.mdl',(0,y,TOP-10),(0,0,180),GOLD,b.FLAT,group='ceiling_lamps')
    spec=BuildSpec(props=b.props,head_id=head,weld_to_head=True,ground_z=0,
        description='Compact CASINO | approx 2x small restaurant footprint | decorative slots and card tables | max 250 props')
    assert len(b.props)<=250
    b.policy.check(make_build(spec))
    vertices=[]
    import itertools
    for item in b.scene:
        rot=b.matrix(item['angle'])
        for v in itertools.product(*zip(item['hull_min'],item['hull_max'])):
            vertices.append([a+c for a,c in zip(b.rotate(rot,v),item['pos'])])
    lo=[min(v[i] for v in vertices) for i in range(3)];hi=[max(v[i] for v in vertices) for i in range(3)]
    size=[round(c-a,3) for a,c in zip(lo,hi)]
    old=json.loads((OUT.parent/'vkusno_i_tochka_small/report.json').read_text())['size_source_units']
    report={'props':len(b.props),'prop_limit':250,'welds':len(b.props)-1,'groups':dict(Counter(v['group'] for v in b.scene)),
        'bounds':{'min':lo,'max':hi},'size_source_units':size,'footprint_ratio_to_small':round(size[0]*size[1]/(old[0]*old[1]),3),
        'all_models_allowed':True,'entrance_clear_width':129,'functional_game_entities':False,'dupe_name':'mcp/casino_small.txt'}
    for name,value in [('build.json',spec.model_dump(mode='json')),('scene.json',b.scene),('report.json',report)]:
        (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__':main()
