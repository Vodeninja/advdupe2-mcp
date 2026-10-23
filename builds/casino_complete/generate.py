"""Keep the 100-prop entrance and add exactly 150 interior/building props."""
import importlib.util
import itertools
import json
from collections import Counter
from pathlib import Path
from adv2mcp.build import BuildSpec,make_build

OUT=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('parts',OUT.parent/'parts.py')
b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
GOLD=(190,143,65,255); CREAM=(210,199,168,255); MARBLE=(225,220,202,255)
DARK=(30,30,33,255); RED=(89,16,30,255); GREEN=(64,80,56,255); WARM=(247,205,125,255)
F=3.5; FRONT=47.7; BACK=619.1; TOP=289.2

def main():
    original=json.loads((OUT/'build.json').read_text())
    original['props']=original['props'][:100]
    b.props[:]=original['props']
    b.scene[:]=json.loads((OUT/'scene.json').read_text())[:100]
    # A double-height hall attaches to the rear edge of the existing entrance.
    for x in (-142.6,142.6):
        for y in (119.125,261.975,404.825,547.675):
            b.plate('plate3x6',(x,y,1.75),(0,90,0),(53,49,43,255),group='hall_floor')
            b.plate('plate3x6',(x,y,TOP+1.75),(0,90,0),CREAM,group='hall_roof')
        for z in (74.925,217.775):
            b.plate('plate3x6',(x,BACK,z),(-90,90,0),DARK,group='hall_walls')
    for x in (-285.2,285.2):
        for y in (190.3,475.5):
            for z in (74.925,217.775):
                b.plate('plate3x6',(x,y,z),(-90,0,0),RED,group='hall_walls')
    # Continuous front facade, with a 190 x 143 unit central doorway.
    for x in (-190.05,190.05):
        b.plate('plate4x4',(x,FRONT,98.65),(0,0,90),CREAM,group='front_facade')
    for x in (-142.6,142.6):
        b.plate('plate2x6',(x,FRONT,241.5),(-90,90,0),CREAM,group='front_facade')
    b.plate('plate1x4',(0,FRONT,170.325),(-90,90,0),CREAM,group='front_facade')
    # Marble rotunda columns, each with a broad base and capital.
    for x in (-125,125):
        for y in (160,440):
            b.on_floor('hunter/tubes/tube1x1x6b.mdl',x,y,floor=F,color=GOLD,material='models/shiny',group='rotunda_columns')
            for z in (9.68,282.8):b.plate('plate1x1',(x,y,z),color=MARBLE,group='column_caps')
    # Circular fountain basin, shallow water surface, central plinth and marble angel.
    b.on_floor('hunter/tubes/tube4x4x05.mdl',0,300,floor=F,color=GOLD,material='models/shiny',group='fountain_rim')
    b.add('hunter/tubes/circle4x4.mdl',(0,300,15),color=(53,89,98,255),material='models/shiny',group='fountain_water')
    b.on_floor('hunter/tubes/tube2x2x05.mdl',0,300,floor=21,color=MARBLE,material=b.FLAT,group='fountain_plinth')
    b.add('hunter/tubes/circle2x2.mdl',(0,300,46.975),color=MARBLE,material=b.FLAT,group='fountain_plinth')
    b.on_floor('props_c17/gravestone_statue001a.mdl',0,300,floor=48.725,yaw=-90,color=MARBLE,material=b.FLAT,group='marble_statue')
    # An ornamental ceiling ring and blue central oculus above the fountain.
    b.add('hunter/tubes/tube4x4x05.mdl',(0,300,274),color=GOLD,material='models/shiny',group='ceiling_rotunda')
    b.add('hunter/tubes/tube2x2x025.mdl',(0,300,284),color=MARBLE,material=b.FLAT,group='ceiling_rotunda')
    b.add('hunter/tubes/circle2x2.mdl',(0,300,287),color=(66,105,137,255),material=b.FLAT,group='ceiling_oculus')
    # Long rear bar with stools, tableware, back shelves and framed artwork.
    for z in (9.68,22.04,34.4):
        b.add('hunter/blocks/cube05x6x025.mdl',(0,535,z),(0,-90,0),RED,b.FLAT,group='bar')
    for x in (-71.425,71.425):b.plate('plate05x3',(x,535,42.33),(0,90,0),DARK,group='bar')
    for x in (-112,-56,0,56,112):b.on_floor('props_c17/chair_stool01a.mdl',x,486,color=GREEN,material=b.FLAT,group='bar_stools')
    for x in (-73,0,73):b.on_floor('props/cs_office/coffee_mug2.mdl',x,535,floor=44.08,group='bar_tableware')
    for x in (-120,120):b.on_floor('props_c17/pottery02a.mdl',x,535,floor=44.08,color=GOLD,material='models/shiny',group='bar_decor')
    b.on_floor('props_c17/tv_monitor01.mdl',-40,541,floor=44.08,yaw=-90,group='bar_terminal')
    for x in (-71.425,71.425):b.plate('plate05x3',(x,605,85),(0,90,0),GOLD,group='bar_shelves')
    for x in (-90,0,90):b.add('props/cs_office/offpaintinga.mdl',(x,615,145),group='bar_art')
    for x in (-71.425,71.425):
        for z in (8,36):b.beam('3',(x,521,z),color=WARM,group='bar_light_strips')
    # Four lounge tables in the two side wings.
    for x,y in [(-218,200),(218,200),(-218,405),(218,405)]:
        b.on_floor('props_c17/furnituretable001a.mdl',x,y,color=(138,91,43,255),material='models/shiny',group='lounge_tables')
        for dx,yaw in ((-42,0),(42,180)):
            b.on_floor('props/cs_office/sofa_chair.mdl',x+dx,y,yaw=yaw,color=GREEN,material=b.FLAT,group='lounge_chairs')
        for dx in (-13,13):b.on_floor('props/cs_office/coffee_mug2.mdl',x+dx,y,floor=40.527996,group='lounge_tableware')
        b.on_floor('props_lab/desklamp01.mdl',x,y+7,floor=40.527996,color=GOLD,material='models/shiny',group='table_lamps')
    # Four decorative gaming machines on the side walls, facing the hall.
    for side in (-1,1):
        for y in (280,335):
            x=side*260;face=-side
            b.add('hunter/blocks/cube05x1x05.mdl',(x,y,27.475),(0,0,90),DARK,b.FLAT,group='slot_cabinets')
            b.on_floor('hunter/blocks/cube05x05x05.mdl',x,y,floor=51.45,color=RED,material=b.FLAT,group='slot_cabinets')
            b.add('props_lab/monitor01b.mdl',(x+face*21,y,61),(0,0 if face>0 else 180,0),group='slot_screens')
            b.plate('plate025x05',(x+face*17,y,45),color=GOLD,group='slot_controls')
            for dy,col in [(-9,WARM),(0,RED),(9,GOLD)]:
                b.plate('plate025x025',(x+face*29,y+dy,61),(0,0,90),col,group='slot_reels')
            b.on_floor('props_c17/chair_stool01a.mdl',x+face*55,y,color=RED,material=b.FLAT,group='slot_stools')
    # Perimeter cornices, greenery, lamps and two approach carpets.
    for x in (-71.425,71.425):b.beam('3',(x,BACK-5,210),color=GOLD,group='wall_cornice')
    for x in (-280,280):
        for y in (190.3,475.5):
            b.add('hunter/blocks/cube025x6x025.mdl',(x,y,210),color=GOLD,material='models/shiny',group='wall_cornice')
    for x in (-238,238):
        for y in (87,563):b.on_floor('props/cs_office/plant01.mdl',x,y,group='hall_plants')
    for x in (-182,182):
        for y in (200,405):b.add('props_c17/lamp001a.mdl',(x,y,264),(0,0,180),GOLD,'models/shiny',group='hanging_lamps')
    for y in (120,486):b.plate('plate1x3',(0,y,5.25),color=RED,group='carpets')
    assert len(b.props)==250,f'Expected 250 total / 150 new props, got {len(b.props)}'
    assert b.props[:100]==original['props'],'Entrance must remain unchanged'
    spec=BuildSpec(props=b.props,head_id=original['head_id'],weld_to_head=True,ground_z=0,
        description='WINSTAR CASINO COMPLETE | original 100-prop entrance + 150-prop interior | marble fountain rotunda, lounge, bar and decorative slots')
    b.policy.check(make_build(spec))
    vertices=[]
    for item in b.scene:
        rot=b.matrix(item['angle'])
        for v in itertools.product(*zip(item['hull_min'],item['hull_max'])):
            vertices.append([a+c for a,c in zip(b.rotate(rot,v),item['pos'])])
    lo=[min(v[i] for v in vertices) for i in range(3)];hi=[max(v[i] for v in vertices) for i in range(3)]
    facade=[]
    for item in b.scene:
        if item['group']!='front_facade':continue
        rot=b.matrix(item['angle'])
        points=[[a+c for a,c in zip(b.rotate(rot,v),item['pos'])] for v in itertools.product(*zip(item['hull_min'],item['hull_max']))]
        facade.append(([min(v[i] for v in points) for i in range(3)],[max(v[i] for v in points) for i in range(3)]))
    for x in range(-284,285,4):
        for z in range(5,289,4):
            covered=any(lo[0]-.01<=x<=hi[0]+.01 and lo[2]-.01<=z<=hi[2]+.01 for lo,hi in facade)
            doorway=abs(x)<95 and z<146.35
            assert covered != doorway,(x,z,'front facade coverage')
    report={'props':len(b.props),'entrance_props':100,'interior_props':150,'entrance_preserved':True,'prop_limit':250,'welds':249,
        'groups':dict(Counter(v['group'] for v in b.scene)),'bounds':{'min':lo,'max':hi},
        'size_source_units':[round(c-a,3) for a,c in zip(lo,hi)],'all_models_allowed':True,
        'front_facade_checked':True,'doorway_clear_size':[190,142.85],
        'water_and_lighting':'decorative props only','dupe_name':'mcp/casino_complete_250.txt'}
    for name,value in [('build.json',spec.model_dump(mode='json')),('scene.json',b.scene),('report.json',report)]:
        (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__':main()
