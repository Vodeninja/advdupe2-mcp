"""Photo-inspired PC desk with prop-built ultrawide and showcase PC."""
import importlib.util
import itertools
import json
import math
from collections import Counter
from pathlib import Path
from adv2mcp.build import BuildSpec,make_build

OUT=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('parts',OUT.parent/'parts.py')
b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
WHITE=(218,215,204,255); BLACK=(20,23,25,255); GRAY=(73,74,72,255)
WARM=(255,228,181,255); GREEN=(53,76,44,255); WOOD=(102,85,69,255)
DESK=43.885498

def strip(length,center,angle=(0,90,0),group='light_strips'):
    b.plate('plate025x'+length,center,angle,WARM,group=group)

def pot(x,y,z,trailing=False):
    b.on_floor('props_c17/pottery01a.mdl',x,y,floor=z,color=BLACK,material=b.FLAT,group='small_plants')
    for dx,a in [(-5,-30),(0,0),(5,30)]:
        b.plate('plate025x025',(x+dx,y,z+13),(0,0,a),GREEN,group='plant_leaves')
    if trailing:
        for i in range(4):
            b.plate('plate025x025',(x+(-3 if i%2 else 3),y-4,z+3-i*9),(15,20*i,45),GREEN,group='trailing_plant')

def main():
    b.props.clear();b.scene.clear()
    # A small room corner anchors the floating shelves and wall decor.
    b.plate('plate3x4',(0,-25,1.75),(0,90,0),WOOD,group='floor')
    b.plate('plate4x4',(0,40,98.65),(0,0,90),(112,108,100,255),group='back_wall')
    # Drawer pedestal and a slender metal frame support the desktop at normal height.
    b.on_floor('props_c17/furnituredrawer001a.mdl',-46,0,floor=3.5,yaw=-90,color=WHITE,material=b.FLAT,group='drawer_pedestal')
    desk_top=DESK+3.5
    head=b.plate('plate1x3',(0,0,DESK+1.75),(0,90,0),WHITE,group='desktop')
    # Native pedestal top is 43.8855; desktop top is 47.3855.
    for y in (-17,17):
        b.add('hunter/blocks/cube025x075x025.mdl',(62,y,DESK-18.04375),(0,0,90),BLACK,b.FLAT,group='desk_frame')
        b.add('hunter/blocks/cube025x025x025.mdl',(62,y,9.68),color=BLACK,material=b.FLAT,group='desk_frame')
    b.add('hunter/blocks/cube025x075x025.mdl',(62,0,9.68),color=BLACK,material=b.FLAT,group='desk_frame')
    # Thin illuminated-looking edges are physical colored props.
    for x in (-47.55,0,47.55):strip('1',(x,-24.9,DESK+.5),(0,-90,0))
    b.plate('plate05x2',(-13,-10,desk_top+1.75),(0,90,0),BLACK,group='desk_mat')
    # Monitor riser, clock underneath and separate monitor stand.
    riser_z=desk_top+14.1125
    for x in (-54,27):b.plate('plate025x025',(x,10,desk_top+6.18125),(0,0,90),WHITE,group='monitor_riser')
    b.plate('plate05x2',(-13,10,riser_z),(0,90,0),WHITE,group='monitor_riser')
    b.add('props_c17/clock01.mdl',(-13,6,desk_top+7.89),(0,0,90),group='desk_clock')
    strip('075',(-13,-2,riser_z-2),(0,-90,0))
    b.plate('plate025x05',(-13,11,riser_z+3.5),(0,90,0),BLACK,group='monitor_stand')
    b.plate('plate025x025',(-13,16,riser_z+9.68),(0,0,90),BLACK,group='monitor_stand')
    screen_z=riser_z+21
    # Three slightly angled panels give the monitor a concave ultrawide shape.
    for dx,y,yaw in [(-23.8,13.9,100),(0,16,90),(23.8,13.9,80)]:
        b.plate('plate05x05',(-13+dx,y,screen_z),(-90,yaw,0),BLACK,group='monitor_screen')
        # Abstract monochrome mountain wallpaper made from thin white strokes.
        for off,theta in [(-5,28),(5,-28)]:
            b.plate('plate025x025',(-13+dx+off,y-3,screen_z-5),(0,-90,theta),(138,148,147,255),group='screen_art')
    b.plate('plate025x075',(-13,13,screen_z+14),(0,-90,0),BLACK,group='monitor_lightbar')
    strip('025',(-13,10,screen_z+13),(0,-90,0))
    b.on_floor('props_c17/computer01_keyboard.mdl',-18,-12,floor=desk_top+3.5,yaw=90,color=WHITE,material=b.FLAT,group='keyboard')
    b.on_floor('props/cs_office/computer_mouse.mdl',13,-12,floor=desk_top+3.5,yaw=90,color=WHITE,material=b.FLAT,group='mouse')
    # Transparent PC side, three real wheel props as fan rotors, component chassis.
    pc_z=desk_top+23.975
    for z in (desk_top+1.75,desk_top+46.2):b.plate('plate05x1',(53,0,z),color=BLACK,group='pc_case')
    b.plate('plate05x1',(53,22,pc_z),(0,0,90),BLACK,group='pc_case')
    b.plate('plate05x1',(53,-22,pc_z),(0,0,90),BLACK,group='pc_case')
    b.plate('plate1x1',(66,0,pc_z),(0,90,90),BLACK,group='pc_case')
    b.add('props_phx/construct/glass/glass_plate1x1.mdl',(40,0,pc_z),(0,90,90),(202,222,230,65),group='pc_glass')
    b.add('props/cs_office/computer_case.mdl',(52,0,desk_top+19),(0,90,0),BLACK,b.FLAT,group='pc_components')
    for z in (desk_top+8,desk_top+24,desk_top+40):
        b.add('props_borealis/door_wheel001a.mdl',(53,-26,z),(0,-90,0),WARM,b.FLAT,group='pc_fans')
    for z in (desk_top+4,desk_top+44):strip('1',(38,0,z),(0,0,0),group='pc_light_strips')
    # Desk accessories: mic, controller, mug, table lamp, pen cup.
    b.plate('plate025x025',(28,-7,desk_top+1.75),color=BLACK,group='microphone')
    b.plate('plate025x025',(28,-7,desk_top+9.68),(0,0,90),BLACK,group='microphone')
    b.on_floor('props_c17/pottery01a.mdl',28,-7,floor=desk_top+14,color=BLACK,material=b.FLAT,group='microphone')
    b.on_floor('maxofs2d/button_06.mdl',12,11,floor=riser_z+1.75,color=BLACK,material=b.FLAT,group='controller')
    b.on_floor('props/cs_office/coffee_mug2.mdl',-59,-12,floor=desk_top,group='mug')
    b.on_floor('props_lab/desklamp01.mdl',-60,11,floor=desk_top,yaw=-70,color=BLACK,material=b.FLAT,group='desk_lamp')
    b.on_floor('props_c17/pottery01a.mdl',-40,-14,floor=desk_top,color=GRAY,material=b.FLAT,group='pen_cup')
    # Two long floating shelves, each with a warm underside strip.
    for z in (111,145):
        for x in (-47.55,0,47.55):
            b.plate('plate025x1',(x,31,z),(0,90,0),GRAY,group='shelves')
            strip('1',(x,24,z-2),(0,-90,0),group='shelf_light_strips')
    pot(-57,30,146.75,True);pot(-28,31,146.75)
    pot(-44,29,112.75)
    # A run of upright books, a leaning framed print, a soundbar and figurines.
    for i in range(6):
        b.plate('plate025x05',(-6+i*4,31,159),(0,-90,90),(45+i*7,47+i*6,44+i*5,255),group='books')
    b.plate('plate025x05',(33,31,160),(0,0,90),BLACK,group='framed_print')
    b.plate('plate025x025',(33,28,160),(0,0,90),WHITE,group='framed_print')
    b.plate('plate025x05',(54,31,151),(0,-90,0),BLACK,group='soundbar')
    for x in (57,65):b.on_floor('props_lab/huladoll.mdl',x,30,floor=146.75,color=GRAY,material=b.FLAT,group='figurines')
    b.on_floor('maxofs2d/camera.mdl',-23,29,floor=112.75,group='camera')
    b.add('props_c17/clock01.mdl',(0,29,120.64),(0,0,90),group='shelf_clock')
    b.on_floor('props_lab/huladoll.mdl',24,30,floor=112.75,color=BLACK,material=b.FLAT,group='figurines')
    b.on_floor('props_c17/pottery01a.mdl',43,30,floor=112.75,color=GRAY,material=b.FLAT,group='shelf_vase')
    b.on_floor('props_lab/huladoll.mdl',63,30,floor=112.75,group='figurines')
    # A compact accessory panel with hanging headphones and a shallow tray.
    b.plate('plate05x075',(53,37,108),(0,0,90),GRAY,group='accessory_board')
    b.plate('plate025x05',(53,30,117),(0,90,0),WHITE,group='accessory_tray')
    for x in (46,60):
        b.plate('plate025x025',(x,29,104),(0,-90,90),BLACK,group='headphones')
        b.add('props/cs_office/computer_mouse.mdl',(x,24,100),(90,0,0),BLACK,b.FLAT,group='headphones')
    b.plate('plate025x025',(53,29,111),(0,-90,0),BLACK,group='headphones')
    # Wall art, a full-size plant, office chair, rug and curtain folds.
    b.add('props/cs_office/offpaintinga.mdl',(-78,37,94),color=(166,158,139,255),group='wall_art')
    b.on_floor('props/cs_office/plant01.mdl',84,8,floor=3.5,group='floor_plant')
    b.on_floor('props/cs_office/chair_office.mdl',7,-56,floor=7,yaw=90,color=BLACK,material=b.FLAT,group='office_chair')
    b.plate('plate1x2',(7,-56,5.25),(0,90,0),(118,111,99,255),group='rug')
    b.plate('plate1x3',(91,15,121),(0,90,90),(84,83,80,255),group='curtain')
    for y in (-5,5,15,25,35):
        b.add('hunter/blocks/cube025x3x025.mdl',(87,y,121),(0,0,90),(71 if y%20 else 89,70,67,255),b.FLAT,group='curtain_folds')
    spec=BuildSpec(props=b.props,head_id=head,weld_to_head=True,ground_z=0,
        description='Photo-inspired PC SETUP | desk, curved ultrawide, glass PC, shelves, headset, camera, books, plants and chair | prop-only')
    assert len(b.props)<=250,len(b.props)
    b.policy.check(make_build(spec))
    vertices=[]
    for item in b.scene:
        rot=b.matrix(item['angle'])
        for v in itertools.product(*zip(item['hull_min'],item['hull_max'])):
            vertices.append([a+c for a,c in zip(b.rotate(rot,v),item['pos'])])
    lo=[min(v[i] for v in vertices) for i in range(3)];hi=[max(v[i] for v in vertices) for i in range(3)]
    report={'props':len(b.props),'prop_limit':250,'welds':len(b.props)-1,'groups':dict(Counter(v['group'] for v in b.scene)),
        'bounds':{'min':lo,'max':hi},'size_source_units':[round(c-a,3) for a,c in zip(lo,hi)],'all_models_allowed':True,
        'desktop_height':desk_top,'light_strips':'colored physical props, no dynamic light entities',
        'approximations':['curved screen from three panels','analog clocks','prop-built mic, controller, headphones and plants'],
        'dupe_name':'mcp/pc_setup.txt'}
    for name,value in [('build.json',spec.model_dump(mode='json')),('scene.json',b.scene),('report.json',report)]:
        (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__':main()
