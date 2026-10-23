"""Projection helpers independent of installed game content and rendering side effects."""
import itertools
import math

def vertices(item):
    p,y,r=map(math.radians,item['angle'])
    sp,cp,sy,cy,sr,cr=math.sin(p),math.cos(p),math.sin(y),math.cos(y),math.sin(r),math.cos(r)
    m=((cp*cy,sp*sr*cy-cr*sy,sp*cr*cy+sr*sy),
       (cp*sy,sp*sr*sy+cr*cy,sp*cr*sy-sr*cy),(-sp,sr*cp,cr*cp))
    return [[sum(a*b for a,b in zip(row,v))+o for row,o in zip(m,item['pos'])]
            for v in itertools.product(*zip(item['hull_min'],item['hull_max']))]

def hull(points):
    pts=sorted(set(tuple(p) for p in points))
    if len(pts)<3:return pts
    def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    result=[]
    for seq in (pts,pts[::-1]):
        half=[]
        for p in seq:
            while len(half)>=2 and cross(half[-2],half[-1],p)<=0:half.pop()
            half.append(p)
        result+=half[:-1]
    return result
