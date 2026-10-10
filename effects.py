"""Pixel-scale special effects driven by combat state and projectile positions."""
import math
import pygame

TEAL=(92,232,210)
GOLD=(246,186,70)
LIGHT=(247,242,192)

def ring(canvas,x,y,r,phase,color,flat=1):
    # Deliberately angular arcane geometry, drawn in the game's logical pixels.
    points=[(round(x+math.cos(phase+i*math.tau/12)*r*flat),round(y+math.sin(phase+i*math.tau/12)*r)) for i in range(12)]
    pygame.draw.polygon(canvas,color,points,1)
    for i in range(0,12,2):
        a=phase+i*math.tau/12
        p=(round(x+math.cos(a)*r*flat),round(y+math.sin(a)*r))
        pygame.draw.rect(canvas,LIGHT,(p[0]-1,p[1]-1,3,3))

def draw_specials(canvas,match,time,text):
    for i,f in enumerate(match.fighters):
        target=match.fighters[1-i]
        x,y=int(f.x),int(f.y)
        active=f.state=='attack'
        if active and f.attack=='Jay':
            charging=f.elapsed<.72
            radius=10+int(min(1,f.elapsed/.72)*15)
            hx=x+f.facing*(9 if charging else 60); hy=y-(60 if charging else 65)
            if f.elapsed<1.55:
                ring(canvas,hx,hy,radius,f.elapsed*3,GOLD,.62)
                ring(canvas,hx,hy,max(5,radius-6),-f.elapsed*4,TEAL,.62)
                if charging:
                    for j in range(6):
                        a=j*math.tau/6+time*4
                        pygame.draw.rect(canvas,TEAL,(round(hx+math.cos(a)*radius),round(hy+math.sin(a)*radius),2,2))
            pygame.draw.ellipse(canvas,(113,103,147),(x-24,y-4,48,8),1)
        if f.name=='Kara' and ((active and f.attack=='Kara') or (target.bound>0 and target.bound_by=='Kara')):
            gx=x+f.facing*24; gy=y-48
            pygame.draw.rect(canvas,(10,15,25),(gx-7,gy-4,15,9))
            pygame.draw.rect(canvas,(134,149,161),(gx-5,gy-3,11,5))
            pygame.draw.rect(canvas,GOLD,(gx-3,gy-2,4,3))
            tip=(gx+f.facing*9,gy)
            pygame.draw.line(canvas,(208,217,220),(gx,gy),tip,3)
            if target.bound>0 and target.bound_by=='Kara':
                ty=int(target.y)-35
                mid=((tip[0]+target.x)/2,max(gy,ty)+8)
                pygame.draw.lines(canvas,(75,42,30),False,[tip,mid,(target.x,ty)],3)
                pygame.draw.lines(canvas,(240,193,107),False,[tip,mid,(target.x,ty)],1)
                for off in (23,34,45):
                    pygame.draw.ellipse(canvas,(94,50,29),(target.x-18,target.y-off-4,36,10),3)
                    pygame.draw.ellipse(canvas,(239,191,101),(target.x-18,target.y-off-4,36,10),1)
                pygame.draw.rect(canvas,GOLD,(target.x-3,target.y-36,6,7))
        if f.name=='Teresa' and f.heal_flash>0:
            # A readable field kit with a neutral green first-aid emblem.
            kx=x+f.facing*13; ky=y-30
            pygame.draw.rect(canvas,(11,22,27),(kx-13,ky-10,27,21))
            pygame.draw.rect(canvas,(196,213,193),(kx-11,ky-8,23,17))
            pygame.draw.rect(canvas,(94,114,106),(kx-5,ky-13,10,5),2)
            pygame.draw.rect(canvas,(39,121,86),(kx-6,ky-5,13,11))
            pygame.draw.line(canvas,(225,244,207),(kx,ky-3),(kx,ky+4),3)
            pygame.draw.line(canvas,(225,244,207),(kx-4,ky),(kx+4,ky),3)
            text('FIELD AID',(x,y-90),12,(149,236,180),True)
    for wave in match.waves:
        x,y=round(wave['x']),round(wave['y']);d=wave['direction']
        if wave['hit']:
            radius=18+wave['fade']*45
            if wave['fade']<.4:
                ring(canvas,x,y,radius,wave['age']*3,GOLD)
                ring(canvas,x,y,max(3,radius-8),-wave['age']*2,TEAL)
        else:
            # A broad crescent front with angular trails makes travel unmistakable.
            for j in range(3):
                xx=x-d*j*10
                col=(25,111,126) if j else TEAL
                pygame.draw.lines(canvas,col,False,[(xx-d*13,y-25),(xx,y-15),(xx+d*7,y),(xx,y+15),(xx-d*13,y+25)],3 if j==0 else 2)
            ring(canvas,x,y,21,wave['age']*5,GOLD,.48)
            pygame.draw.line(canvas,LIGHT,(x-3,y-10),(x+3,y+10),2)
