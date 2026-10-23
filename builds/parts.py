"""Shared measured geometry helpers for the example generators."""
import math
from adv2mcp.build import make_build
from adv2mcp.models import ModelCatalog
from adv2mcp.storage import DEFAULT_DUPE_DIR, DupeStore

catalog=ModelCatalog(DEFAULT_DUPE_DIR.parent.parent)
policy=DupeStore(DEFAULT_DUPE_DIR).policy
props,scene=[],[]
cache={}
WHITE=(241,239,220,255)
BROWN=(109,66,42,255)
DARK=(42,43,39,255)
ORANGE=(245,143,43,255)
RED=(232,76,43,255)
CREAM=(216,203,180,255)
FLAT='models/debug/debugwhite'

def matrix(angle):
    p,y,r=map(math.radians,angle)
    sp,cp,sy,cy,sr,cr=math.sin(p),math.cos(p),math.sin(y),math.cos(y),math.sin(r),math.cos(r)
    return ((cp*cy,sp*sr*cy-cr*sy,sp*cr*cy+sr*sy),
            (cp*sy,sp*sr*sy+cr*cy,sp*cr*sy-sr*cy),(-sp,sr*cp,cr*cp))

def rotate(m,v):return tuple(sum(a*b for a,b in zip(row,v)) for row in m)

def info(model):
    if model not in cache:cache[model]=catalog.info(model)
    return cache[model]

def add(model,center,angle=(0,0,0),color=None,material=None,group='structure',label=''):
    if not model.startswith('models/'):model='models/'+model
    bounds=info(model);lo,hi=bounds['hull_min'],bounds['hull_max']
    correction=rotate(matrix(angle),tuple((a+b)/2 for a,b in zip(lo,hi)))
    pos=[round(c-d,6) for c,d in zip(center,correction)]
    prop={'id':len(props)+1,'model':model,'pos':pos,'angle':list(angle),'frozen':True}
    if color is not None:prop['color']=list(color)
    if material:prop['material']=material
    props.append(prop)
    scene.append({**prop,'center':list(center),'size':bounds['size'],'hull_min':lo,'hull_max':hi,'group':group,'label':label})
    return prop['id']

def on_floor(model,x,y,floor=3.5,yaw=0,**kwargs):
    full=model if model.startswith('models/') else 'models/'+model
    return add(full,(x,y,floor+info(full)['size'][2]/2),(0,yaw,0),**kwargs)

def plate(name,center,angle=(0,0,0),color=CREAM,**kwargs):
    return add('hunter/plates/'+name+'.mdl',center,angle,color,FLAT,**kwargs)

def beam(length,center,theta=0,color=BROWN,group='structure',label=''):
    return add(f'hunter/blocks/cube025x{length}x025.mdl',center,(0,-90,theta),color,FLAT,group,label)
