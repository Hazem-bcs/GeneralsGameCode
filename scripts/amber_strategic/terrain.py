"""Topology model: deterministic elevations, navigable pads and texture classes."""
import math
import random
from .config import TerrainConfig

def smooth(a, b, value):
    t = max(0.0, min(1.0, (value-a)/(b-a)))
    return t*t*(3-2*t)

def segment_distance(x,y,segment):
    x1,y1,x2,y2=segment[:4]
    dx,dy=x2-x1,y2-y1
    t=max(0.0,min(1.0,((x-x1)*dx+(y-y1)*dy)/(dx*dx+dy*dy)))
    return math.hypot(x-x1-t*dx,y-y1-t*dy)

def mound(x,y,cx,cy,rx,ry):
    return math.exp(-((x-cx)/rx)**2-((y-cy)/ry)**2)

class TerrainField:
    def __init__(self, layout, config=TerrainConfig()):
        self.c=config
        self.starts=[tuple(p) for p in layout['starts']]
        self.supplies=[tuple(p) for p in layout['supplies']]
        self.tech=[tuple(p) for p in layout['tech']]
        self.roads=[tuple(p) for p in layout['roads']]
        rng=random.Random(config.seed)
        self.phases=[rng.uniform(-math.pi,math.pi) for _ in range(4)]

    def raw_elevation(self,x,y):
        wx=min(x,6000-x)
        mx=abs(x-3000)
        p,q,r,s=self.phases
        dunes=15.0*math.sin(wx/152+p)*math.cos(y/178+q)+12.0*math.cos(wx/225-y/310+r)+9*math.sin(y/115+s)
        ridge=sum(147*mound(mx-85*math.sin(y/185+p)-60*math.cos(y/97+r),y,0,cy,485,650) for cy in (1900,4120))
        ridge*=.92+.09*math.sin(mx/93+q)+.06*math.cos(y/105+p)
        mesas=sum(45*(1-smooth(290,510,math.hypot(wx-a,y-b))) for a,b in ((2280,1710),(2220,4320)))
        hills=sum(h*mound(wx,y,a,b,480,350) for a,b,h in ((1610,1470,32),(1610,4530,32),(1900,2800,30),(1900,3390,30)))
        dry_washes=sum(-22*mound(wx,y,a,b,475,365) for a,b in ((2070,2420),(2070,3650)))
        edge=max(0,180-min(x,y,6000-x,6000-y))/180
        return self.c.base_height+dunes+ridge+mesas+hills+dry_washes+76*edge**2

    def clearance(self,x,y):
        roads=min(segment_distance(x,y,road)-road[4] for road in self.roads)
        pads=min(math.hypot(x-a,y-b)-self.c.base_pad_radius for a,b in self.starts)
        docks=min(math.hypot(x-a,y-b)-self.c.resource_radius for a,b,_ in self.supplies)
        tech=min(math.hypot(x-a,y-b)-self.c.tech_radius for a,b,_ in self.tech)
        return min(roads,pads,docks,tech),roads,pads,docks

    def sample(self,x,y):
        clearance,road,pad,dock=self.clearance(x,y)
        grade=1-smooth(0,self.c.grade_transition,clearance)
        h=max(15,min(251,round(self.raw_elevation(x,y)*(1-grade)+self.c.base_height*grade)))
        delta=h-self.c.base_height
        cliff=delta>=self.c.cliff_height and clearance>=65
        if road < -15 and pad > -100 and dock > -90: material=1
        elif delta>76: material=2
        elif delta>26: material=6 if math.sin(x/104+y/127)>-.2 else 3
        elif delta< -8: material=5
        elif math.sin(min(x,6000-x)/183)+math.cos(y/225)>.5: material=4
        else: material=0
        return h,material,cliff

    def generate(self,width,rows,border):
        n=width*rows
        heights,materials,cliffs=bytearray(n),bytearray(n),bytearray(n)
        for gy in range(rows):
            y=(gy-border)*self.c.cell_world
            for gx in range(width):
                x=(gx-border)*self.c.cell_world
                i=gy*width+gx
                h,m,c=self.sample(x,y)
                heights[i],materials[i],cliffs[i]=h,m,c
        return heights,materials,cliffs
