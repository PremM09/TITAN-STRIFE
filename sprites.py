"""Approved arcade artwork: alpha-isolated atlas poses, state-driven animation."""
import math
import os
import pygame
from combat import ROSTER, ATTACKS, GROUND

class SpriteBank:
    def __init__(self):
        atlas=pygame.image.load(os.path.join('assets','fighters.png')).convert_alpha()
        # Isolate whole connected sprites instead of relying on approximate AI grid spacing.
        components=pygame.mask.from_surface(atlas,100).connected_components(800)
        if len(components)!=20:
            raise ValueError('Expected 20 fighter poses in fighters.png')
        components.sort(key=lambda m:m.get_bounding_rects()[0].top)
        self.frames={}
        for row,name in enumerate(ROSTER):
            group=sorted(components[row*4:row*4+4],key=lambda m:m.get_bounding_rects()[0].left)
            idle_height=group[0].get_bounding_rects()[0].height
            frames=[]
            for mask in group:
                rect=mask.get_bounding_rects()[0]
                sprite=atlas.subsurface(rect).copy()
                isolation=mask.to_surface(setcolor=(255,255,255,255),unsetcolor=(0,0,0,0)).subsurface(rect)
                sprite.blit(isolation,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
                ratio=88/idle_height
                frames.append(pygame.transform.scale(sprite,(round(rect.width*ratio),round(rect.height*ratio))))
            self.frames[name]=frames
        self.cache={}
        # Dedicated crouch / air artwork rather than compressing standing poses.
        jay=pygame.image.load(os.path.join('assets','jay.png')).convert_alpha()
        parts=sorted(pygame.mask.from_surface(jay,100).connected_components(800), key=lambda m:m.get_bounding_rects()[0].left)
        if len(parts)!=4: raise ValueError('Expected four Jay poses')
        ratio=88/parts[0].get_bounding_rects()[0].height
        self.frames['Jay']=[self.extract(jay,m,ratio) for m in parts]
        extra=pygame.image.load(os.path.join('assets','movement.png')).convert_alpha()
        parts=sorted(pygame.mask.from_surface(extra,100).connected_components(800), key=lambda m:m.get_bounding_rects()[0].top)
        if len(parts)!=25: raise ValueError('Expected 25 movement poses')
        for row,name in enumerate(ROSTER):
            group=sorted(parts[row*5:row*5+5],key=lambda m:m.get_bounding_rects()[0].left)
            ratio=61/group[0].get_bounding_rects()[0].height
            self.frames[name].extend(self.extract(extra,m,ratio) for m in group)
        # Approval candidate: same nearest-neighbor treatment as the original roster.
        jay=pygame.image.load(os.path.join('assets','jay-review.png')).convert_alpha()
        parts=sorted(pygame.mask.from_surface(jay,100).connected_components(800),key=lambda m:m.get_bounding_rects()[0].top)
        if len(parts)!=12: raise ValueError('Expected twelve revised Jay poses')
        ordered=[]
        for row in range(3):
            ordered.extend(sorted(parts[row*4:row*4+4],key=lambda m:m.get_bounding_rects()[0].left))
        ratio=88/ordered[0].get_bounding_rects()[0].height
        self.frames['Jay']=[self.extract(jay,m,ratio,pixel=True) for m in ordered]

    @staticmethod
    def extract(atlas,mask,ratio,pixel=False):
        rect=mask.get_bounding_rects()[0]
        sprite=atlas.subsurface(rect).copy()
        isolation=mask.to_surface(setcolor=(255,255,255,255),unsetcolor=(0,0,0,0)).subsurface(rect)
        sprite.blit(isolation,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
        resize=pygame.transform.scale if pixel else pygame.transform.smoothscale
        return resize(sprite,(round(rect.w*ratio),round(rect.h*ratio)))

    def draw(self,canvas,f,time,scale=1,at=None,pose=None):
        idx=0; lean=0; bob=0
        attacking=f.state=='attack'
        if f.stun>0 or f.hp<=0:
            idx=3
        elif attacking:
            schedule=[(.07,30,500)] if f.attack=='counter' else ATTACKS.get(f.attack,[])
            for j,(when,_,_) in enumerate(schedule):
                if when-.055 <= f.elapsed <= when+.09:
                    idx=2 if f.attack=='kick' or (f.attack in ('combo','Steve','Teresa') and j%3==2) else 1
                    break
            lean=2 if idx else -1
        elif f.moving:
            bob=abs(math.sin(time*12))*2
            lean=math.sin(time*12)*2
        elif not f.blocking:
            bob=math.sin(time*3)*.6
        if idx!=3 and at is None:
            if f.crouching: idx={0:4,1:5,2:6}[idx]; bob=0
            elif f.y<GROUND or f.vy<0: idx=8 if idx==2 else 7; bob=0
        if pose=='victory': idx=0; lean=0; bob=0
        if f.name=='Jay':
            if pose=='victory': idx=11
            elif attacking and f.attack=='Jay': idx=9 if f.elapsed<.72 else 10; bob=0; lean=0
        elif attacking and f.attack=='Teresa': idx=4; bob=0
        key=(f.name,idx,f.facing,scale,f.crouching)
        if key not in self.cache:
            sprite=self.frames[f.name][idx]
            if f.facing<0: sprite=pygame.transform.flip(sprite,True,False)
            self.cache[key]=pygame.transform.scale(sprite,(max(1,round(sprite.get_width()*scale)),max(1,round(sprite.get_height()*scale))))
        sprite=self.cache[key]
        x,y=at or (f.x,f.y)
        # Anchor the body, not the extended fist/foot, to its simulation position.
        anchor=(.5,.39,.27,.5,.5,.38,.25,.42,.28,.5,.37,.5)[idx]
        if f.facing<0: anchor=1-anchor
        dest=(round(x-sprite.get_width()*anchor+lean*f.facing*scale),round(y-sprite.get_height()-bob*scale))
        ground=y if at else GROUND
        pygame.draw.ellipse(canvas,(17,19,32),(x-20*scale,ground-3*scale,40*scale,6*scale))
        if f.phantom>0:
            ghost=sprite.copy(); ghost.set_alpha(65)
            canvas.blit(ghost,(dest[0]-7*f.facing,dest[1]))
            sprite=sprite.copy(); sprite.set_alpha(170)
        if f.flash>0:
            sprite=sprite.copy(); sprite.fill((75,50,30,0),special_flags=pygame.BLEND_RGBA_ADD)
        canvas.blit(sprite,dest)
        if f.blocking:
            r=pygame.Rect(x-19,y-66,38,42)
            pygame.draw.arc(canvas,(125,199,242),r,-math.pi/2 if f.facing>0 else math.pi/2,math.pi/2 if f.facing>0 else math.pi*1.5,2)
        if f.bound>0 and f.bound_by=='Kara':
            for off in (30,36,42): pygame.draw.line(canvas,(225,179,98),(x-13,y-off),(x+13,y-off),2)
