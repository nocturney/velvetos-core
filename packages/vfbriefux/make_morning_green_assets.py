#!/usr/bin/env python3
"""Generate deterministic decorative JPEG assets for Morning Green."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import math

ROOT = Path(__file__).resolve().parent / "assets" / "morning-green"
ROOT.mkdir(parents=True, exist_ok=True)

GREEN=(21,53,43); GREEN2=(36,74,60); CREAM=(239,230,210); GOLD=(190,154,92); BROWN=(113,88,62); LIGHT=(249,245,235)

def gradient(size, a, b, horizontal=False):
    w,h=size; im=Image.new('RGB', size); px=im.load()
    span=w if horizontal else h
    for i in range(span):
        t=i/max(1,span-1); c=tuple(round(a[k]*(1-t)+b[k]*t) for k in range(3))
        if horizontal:
            for y in range(h): px[i,y]=c
        else:
            for x in range(w): px[x,i]=c
    return im

def leaf(draw, cx, cy, length, width, angle, fill, alpha=255):
    pts=[]
    ca,sa=math.cos(angle),math.sin(angle)
    for s in range(17):
        t=s/16; x=(t-.5)*length; y=math.sin(math.pi*t)*width
        pts.append((cx+x*ca-y*sa, cy+x*sa+y*ca))
    for s in range(16,-1,-1):
        t=s/16; x=(t-.5)*length; y=-math.sin(math.pi*t)*width
        pts.append((cx+x*ca-y*sa, cy+x*sa+y*ca))
    draw.polygon(pts, fill=fill)

def botanical(size, base_a, base_b, seed_shift=0):
    im=gradient(size,base_a,base_b,True).convert('RGBA'); d=ImageDraw.Draw(im,'RGBA')
    w,h=size
    d.ellipse((-w*.16,h*.08,w*.34,h*.95), fill=(255,248,230,18))
    d.line((w*.05,h*.95,w*.38,h*.08), fill=(196,164,105,130), width=max(2,w//360))
    for i in range(9):
        t=(i+1)/10; cx=w*(.06+.30*t); cy=h*(.92-.82*t)
        ang=-.85 + (0.55 if i%2 else -0.45)
        leaf(d,cx,cy,w*.12,h*.09,ang,(91,119,80,155))
    d.line((w*.78,h*1.05,w*.62,-h*.08), fill=(218,190,129,85), width=max(2,w//420))
    for i in range(7):
        t=(i+1)/8; cx=w*(.77-.14*t); cy=h*(.95-.92*t)
        leaf(d,cx,cy,w*.09,h*.065,.7 if i%2 else 2.3,(120,142,91,90))
    return im.convert('RGB').filter(ImageFilter.GaussianBlur(.35))

def make_top():
    botanical((920,250), GREEN, (47,75,57)).save(ROOT/'morning-top.jpg','JPEG',quality=78,optimize=True,progressive=True)

def make_story():
    im=gradient((460,350), CREAM, LIGHT, False).convert('RGBA'); d=ImageDraw.Draw(im,'RGBA')
    d.rectangle((0,245,460,350), fill=(194,172,136,150))
    d.ellipse((118,112,277,305), fill=(214,197,169,255), outline=(156,131,96,100), width=2)
    d.ellipse((150,94,245,140), fill=(232,220,198,255))
    d.line((202,110,268,25), fill=(89,102,70,210), width=5)
    for i in range(5):
        leaf(d,245+i*4,55+i*20,58,21,-.5 if i%2 else .55,(83,106,68,210))
    d.ellipse((290,270,405,316), fill=(108,83,59,55))
    im.convert('RGB').filter(ImageFilter.GaussianBlur(.25)).save(ROOT/'morning-story.jpg','JPEG',quality=78,optimize=True,progressive=True)

def make_radar():
    im=botanical((300,220),(38,72,55),(85,101,69)).convert('RGBA'); d=ImageDraw.Draw(im,'RGBA')
    d.ellipse((190,-45,360,125), fill=(240,220,170,25))
    im.convert('RGB').save(ROOT/'morning-radar.jpg','JPEG',quality=78,optimize=True,progressive=True)

def make_footer():
    im=gradient((920,182),(29,61,49),(17,45,37),True).convert('RGBA'); d=ImageDraw.Draw(im,'RGBA')
    d.ellipse((570,72,980,360), fill=(203,174,111,34))
    d.line((80,210,245,-25), fill=(198,166,104,105), width=3)
    for i in range(8):
        leaf(d,115+i*17,155-i*24,90,28,.7 if i%2 else 2.4,(94,122,77,135))
    im.convert('RGB').filter(ImageFilter.GaussianBlur(.3)).save(ROOT/'morning-footer.jpg','JPEG',quality=78,optimize=True,progressive=True)

if __name__ == '__main__':
    make_top(); make_story(); make_radar(); make_footer()
    for p in sorted(ROOT.glob('*.jpg')): print(p.name, p.stat().st_size)