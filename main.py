"""Titan Strife — original pixel arcade prototype. Desktop and async web loop."""
import asyncio
import math
import os
import random
import sys
import pygame
from combat import Match, ROSTER, GROUND, OpponentSelector, MAX_HP
from arena import make_arena
from effects import draw_specials
from sprites import SpriteBank

W,H=480,320
STICK_CENTER=(60,278)
TOUCH_BUTTONS=(("X","punch",372,277,(84,144,216)),
               ("A","kick",404,293,(89,179,127)),
               ("Y","combo",404,257,(218,177,79)),
               ("B","special",436,277,(204,87,99)))
INK=(13,16,31); GOLD=(239,196,111); WHITE=(234,231,219); MUTED=(139,153,179)

def browser_size():
    if sys.platform!='emscripten': return None
    import platform
    return (max(1,int(platform.window.innerWidth)),max(1,int(platform.window.innerHeight)))

class Game:
    def __init__(self):
        pygame.init()
        self.screen=pygame.display.set_mode(browser_size() or (960,640),pygame.RESIZABLE)
        pygame.display.set_caption('Titan Strife')
        self.canvas=pygame.Surface((W,H))
        self.font_paths={s:os.path.join('assets','ui-heading.ttf' if s>=16 else 'ui-body.ttf') for s in (12,14,16,20,24,32,42,52)}
        self.fonts={s:pygame.font.Font(path,round(s*.75)) for s,path in self.font_paths.items()}
        self.text_draws=[]; self.display_fonts={}
        self.scene='menu'; self.selected='Zen'; self.match=None
        self.time=0; self.running=True; self.paused=False
        self.buttons=[]; self.focus=0; self.pointers={}; self.taps=[]
        self.music_volume=.35; self.sfx_volume=.65; self.audio=False; self.music_started=False
        self.rotate=False; self.viewport=pygame.Rect(0,0,960,640)
        self.rng=random.Random()
        self.opponents=OpponentSelector()
        self.sfx={}; self.particles=[]; self.feedback=[]
        self.accumulator=0
        self.sprites=SpriteBank()
        self.impacts=[]; self.hitstop=0; self.shake=0
        self.hit_chain={}; self.chain_age={}
        self.arenas=[make_arena(True),make_arena(False)]
        self.arena=self.arenas[0]
        try:
            pygame.mixer.init(frequency=22050)
            for name in ('hit','block','special','round','fight','illusion','bind','swing','punch','kick'):
                self.sfx[name]=pygame.mixer.Sound(os.path.join('assets',name+'.ogg'))
            pygame.mixer.music.load(os.path.join('assets','arena.ogg'))
            self.audio=True
        except (pygame.error,FileNotFoundError): pass

    def text(self, text, pos, size=16, color=WHITE, center=False):
        surf=self.fonts[size].render(str(text),True,color)
        rect=surf.get_rect(center=pos) if center else surf.get_rect(topleft=pos)
        # Draw glyphs at final display resolution, keeping the sprites crisp.
        self.text_draws.append((str(text),pos,size,color,center))
        return rect

    def panel(self, rect, fill=(24,30,48), border=(68,75,96)):
        pygame.draw.rect(self.canvas,fill,rect)
        pygame.draw.rect(self.canvas,border,rect,1)

    def button(self,label,rect,action,accent=False):
        rect=pygame.Rect(rect)
        hover=rect.collidepoint(self.mouse_pos()) or len(self.buttons)==self.focus
        self.panel(rect,(64,53,63) if hover else (27,33,51),GOLD if hover or accent else (70,78,100))
        self.text(label.upper(),rect.center,20,GOLD if hover or accent else WHITE,True)
        self.buttons.append((rect,action))

    def mouse_pos(self):
        x,y=pygame.mouse.get_pos()
        return self.logical(x,y)

    def logical(self,x,y):
        r=self.viewport
        return ((x-r.x)*W/max(1,r.w),(y-r.y)*H/max(1,r.h))

    def draw_fighter(self,f,scale=1,at=None,pose=None):
        self.sprites.draw(self.canvas, f, self.time, scale, at, pose)

    def start_match(self):
        opponent=self.opponents.choose(self.selected)
        self.arena=self.rng.choice(self.arenas)
        self.match=Match(self.selected,opponent,self.rng.randrange(100000))
        self.scene='match'; self.paused=False; self.focus=0
        self.pointers.clear(); self.taps.clear(); self.feedback.clear(); self.particles.clear(); self.accumulator=0
        self.impacts.clear(); self.hitstop=0; self.shake=0; self.hit_chain.clear(); self.chain_age.clear()

    def activate(self,action):
        self.focus=0; self.pointers.clear(); self.taps.clear()
        if action=='play': self.scene='select'
        elif action=='characters': self.scene='characters'
        elif action=='settings': self.scene='settings'
        elif action=='menu': self.scene='menu'; self.match=None
        elif action=='start' or action=='new': self.start_match()
        elif action=='resume': self.paused=False; self.match.paused=False
        elif action=='fullscreen':
            if sys.platform!='emscripten':
                if self.screen.get_flags() & pygame.FULLSCREEN:
                    self.screen=pygame.display.set_mode((960,640),pygame.RESIZABLE)
                else: self.screen=pygame.display.set_mode((0,0),pygame.FULLSCREEN)
        elif action.startswith('select:'): self.selected=action.split(':')[1]
        elif action.startswith('music:'): self.music_volume=max(0,min(1,self.music_volume+float(action.split(':')[1])))
        elif action.startswith('sfx:'): self.sfx_volume=max(0,min(1,self.sfx_volume+float(action.split(':')[1])))
        if self.audio:
            pygame.mixer.music.set_volume(self.music_volume)
            for sound in self.sfx.values(): sound.set_volume(self.sfx_volume)

    def start_audio(self):
        if self.audio and not self.music_started:
            try:
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play(-1)
                for sound in self.sfx.values(): sound.set_volume(self.sfx_volume)
                self.music_started=True
            except pygame.error: pass

    def handle(self,event):
        if event.type==pygame.QUIT: self.running=False
        if event.type==pygame.WINDOWFOCUSLOST:
            self.pointers.clear(); self.taps.clear()
            if self.scene=='match' and self.match.phase!='victory':
                self.paused=True; self.match.paused=True; self.focus=0
        if event.type==pygame.KEYDOWN:
            self.start_audio()
            if event.key==pygame.K_ESCAPE:
                if self.scene=='match' and self.match.phase!='victory':
                    self.paused=not self.paused; self.match.paused=self.paused; self.pointers.clear(); self.focus=0
                else: self.activate('menu')
            elif self.scene!='match' or self.paused or self.match.phase=='victory':
                if event.key in (pygame.K_DOWN,pygame.K_RIGHT): self.focus=(self.focus+1)%max(1,len(self.buttons))
                elif event.key in (pygame.K_UP,pygame.K_LEFT): self.focus=(self.focus-1)%max(1,len(self.buttons))
                elif event.key in (pygame.K_RETURN,pygame.K_SPACE) and self.buttons:
                    self.activate(self.buttons[min(self.focus,len(self.buttons)-1)][1])
            else:
                mapping={pygame.K_j:'punch',pygame.K_k:'kick',pygame.K_l:'combo',pygame.K_i:'special',pygame.K_SPACE:'jump',pygame.K_w:'jump',pygame.K_UP:'jump'}
                if event.key in mapping: self.taps.append(mapping[event.key])
        down=event.type in (pygame.MOUSEBUTTONDOWN,pygame.FINGERDOWN)
        motion=event.type in (pygame.MOUSEMOTION,pygame.FINGERMOTION)
        up=event.type in (pygame.MOUSEBUTTONUP,pygame.FINGERUP)
        if not (down or motion or up): return
        finger=event.type in (pygame.FINGERDOWN,pygame.FINGERMOTION,pygame.FINGERUP)
        if not finger and getattr(event,'touch',False): return
        if not finger and (down or up) and event.button!=1: return
        pid=event.finger_id if finger else 'mouse'
        if finger:
            sw,sh=self.screen.get_size(); pos=self.logical(event.x*sw,event.y*sh)
        else: pos=self.logical(*event.pos)
        if up: self.pointers.pop(pid,None); return
        if down:
            self.start_audio()
            for rect,action in self.buttons:
                if rect.collidepoint(pos): self.activate(action); return
            if self.scene=='match' and not self.paused and self.match.phase!='victory':
                if pygame.Rect(436,3,40,16).collidepoint(pos):
                    self.paused=True; self.match.paused=True; return
                role=self.control_at(pos)
                if role:
                    self.pointers[pid]=(role,pos)
                    if role in ('punch','kick','combo','special','jump'): self.taps.append(role)
        elif pid in self.pointers:
            role,_=self.pointers[pid]
            self.pointers[pid]=(role,pos)

    def control_at(self,pos):
        x,y=pos
        if math.hypot(x-STICK_CENTER[0],y-STICK_CENTER[1])<31: return 'stick'
        for _,name,cx,cy,_ in TOUCH_BUTTONS:
            if math.hypot(x-cx,y-cy)<15: return name
        return None

    def player_action(self):
        keys=pygame.key.get_pressed()
        action={'move':int(keys[pygame.K_d] or keys[pygame.K_RIGHT])-int(keys[pygame.K_a] or keys[pygame.K_LEFT]),'crouch':bool(keys[pygame.K_s] or keys[pygame.K_DOWN]),'block':bool(keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])}
        for role,(x,y) in self.pointers.values():
            if role=='stick':
                dx,dy=x-STICK_CENTER[0],y-STICK_CENTER[1]
                if abs(dx)>8: action['move']=1 if dx>0 else -1
                if dy>12: action['crouch']=True
                if dy < -14: action['jump']=True
        for tap in self.taps:
            if tap=='jump': action['jump']=True
            else: action['attack']=tap
        return action

    def update(self,dt):
        self.time+=dt
        consumed=False
        if self.scene=='match' and self.match.phase!='victory':
            self.match.paused=self.paused or self.screen.get_width()<self.screen.get_height()
            action=self.player_action()
            frozen = self.match.paused
            stopped = self.hitstop > 0
            if stopped and not frozen: self.hitstop=max(0,self.hitstop-dt)
            self.accumulator += 0 if frozen or stopped else min(dt,.1)
            first=True
            while self.accumulator>=1/60:
                self.match.update(1/60,action)
                for event,name in self.match.events:
                    if self.audio and event in self.sfx and event!='hit':
                        self.sfx[event].play()
                    if event in ('hit','block','illusion','bind'):
                        f=next((f for f in self.match.fighters if f.name==name),None)
                        if f:
                            color=GOLD if event!='illusion' else (178,129,246)
                            for _ in range(9): self.particles.append([f.x,f.y-40,self.rng.uniform(-80,80),self.rng.uniform(-90,10),.35,color])
                    if event=='special': self.feedback.append([ROSTER[name]['special'],1.3])
                    if event=='ready': self.feedback.append([name.upper()+' SPECIAL READY!',1.4])
                    if event=='sudden': self.feedback.append(['SUDDEN DEATH!',2])
                for impact in self.match.impacts:
                    self.impacts.append(dict(impact, life=.8 if impact['kind']=='heal' else .22))
                    if impact['kind']=='hit':
                        if self.audio:
                            self.sfx['kick' if impact['attack'] in ('kick','Jay','counter') else 'punch'].play()
                        self.hitstop=max(self.hitstop,.055 if impact['attack'] in ('kick','counter','Jay') else .035)
                        self.shake=.13
                        source=impact['source']
                        self.hit_chain[impact['target']]=0
                        self.hit_chain[source]=self.hit_chain.get(source,0)+1
                        self.chain_age[source]=.85
                self.accumulator-=1/60
                if self.hitstop>0: self.accumulator=0
                consumed=True
                if first:
                    action={k:v for k,v in action.items() if k!='attack'}
                    first=False
        if self.scene=='match' and self.match.phase=='victory' and not self.match.reported:
            self.opponents.record(self.match.score[0]==2)
            self.match.reported=True
        if consumed or self.scene!='match': self.taps.clear()
        if not self.paused and not (self.scene=='match' and self.match.paused):
            self.shake=max(0,self.shake-dt)
            for impact in self.impacts: impact['life']-=dt
            self.impacts=[impact for impact in self.impacts if impact['life']>0]
            for name in list(self.chain_age):
                self.chain_age[name]-=dt
                if self.chain_age[name]<=0: self.hit_chain[name]=0
            for p in self.particles: p[0]+=p[2]*dt; p[1]+=p[3]*dt; p[4]-=dt
            self.particles=[p for p in self.particles if p[4]>0]
            for f in self.feedback: f[1]-=dt
            self.feedback=[f for f in self.feedback if f[1]>0]

    def header(self,title,subtitle):
        self.text(title,(240,29),32,GOLD,True)
        self.text(subtitle,(240,52),14,MUTED,True)

    def draw_menu(self):
        self.canvas.blit(self.arenas[0],(0,0))
        # A restrained title panel leaves the entire arena visible.
        veil=pygame.Surface((480,124),pygame.SRCALPHA)
        for y in range(124):
            pygame.draw.line(veil,(12,21,38,max(0,215-y)),(0,y),(480,y))
        self.canvas.blit(veil,(0,0))
        self.text('TITAN STRIFE',(240,39),52,WHITE,True)
        pygame.draw.line(self.canvas,GOLD,(185,72),(295,72),2)
        self.text('WELCOME TO THE ARENA',(240,96),24,GOLD,True)
        for label,y,action in [('Play',218,'play'),('View characters',249,'characters'),('Settings',280,'settings')]:
            self.button(label,(148,y,184,26),action)

    def stars(self,level,center):
        count={'EASY':1,'MID':2,'HARD':3}[level]
        for i in range(3):
            x,y=center[0]+(i-1)*14,center[1]
            points=[]
            for j in range(10):
                a=-math.pi/2+j*math.pi/5; r=5 if j%2==0 else 2.2
                points.append((x+math.cos(a)*r,y+math.sin(a)*r))
            pygame.draw.polygon(self.canvas,GOLD if i<count else (68,77,96),points)

    def draw_select(self,view=False):
        self.header('THE FIVE', 'Explore your rivals' if view else 'Choose your fighter. Rivals adapt to your results.')
        from combat import Fighter
        for idx,name in enumerate(ROSTER):
            x=12+idx*94
            rect=pygame.Rect(x,73,86,134)
            chosen=name==self.selected
            self.panel(rect,(43,38,62) if chosen else (24,30,48),GOLD if chosen else (58,66,86))
            self.draw_fighter(Fighter(name,0,1),1,(x+43,169))
            self.text(name.upper(),(x+43,182),20,GOLD if chosen else WHITE,True)
            self.stars(ROSTER[name]['level'],(x+43,198))
            self.buttons.append((rect,'select:'+name))
        data=ROSTER[self.selected]
        self.text(data['special'],(240,223),20,GOLD,True)
        desc=data['description']
        words=desc.split(); lines=['']
        for word in words:
            if self.fonts[14].size(lines[-1]+word)[0]>440: lines.append('')
            lines[-1]+=word+' '
        for i,line in enumerate(lines): self.text(line.strip(),(240,243+i*13),14,WHITE,True)
        self.button('BACK',(13,282,95,27),'menu')
        if not view: self.button('ENTER ARENA',(284,282,182,27),'start',True)

    def draw_settings(self):
        self.header('SETTINGS','Session only. Nothing is saved.')
        for label,y,value,key in [('MUSIC',82,self.music_volume,'music'),('SOUND FX',125,self.sfx_volume,'sfx')]:
            self.text(label,(45,y+7),20,WHITE)
            self.text(str(round(value*100))+'%',(260,y+13),20,GOLD,True)
            self.button('-',(309,y,45,27),key+':-0.1')
            self.button('+',(366,y,45,27),key+':0.1')
        self.text('MOVE: WASD / ARROWS   |   JUMP: SPACE / UP',(240,175),14,MUTED,True)
        self.text('J: PUNCH   K: KICK   L: COMBO   I: SPECIAL',(240,195),14,MUTED,True)
        self.text('BLOCK: HOLD AWAY / SHIFT   |   ESC: PAUSE',(240,215),14,MUTED,True)
        self.text('Touch: left stick + right X / A / Y / B buttons',(240,235),14,MUTED,True)
        self.button('FULLSCREEN',(248,270,180,31),'fullscreen')
        self.button('BACK',(45,270,120,31),'menu')

    def draw_controls(self):
        pygame.draw.rect(self.canvas,(14,19,34),(0,239,W,81))
        pygame.draw.line(self.canvas,(72,86,112),(0,239),(480,239))
        pygame.draw.circle(self.canvas,(8,12,24),(60,280),30)
        pygame.draw.circle(self.canvas,(35,43,65),STICK_CENTER,29)
        pygame.draw.circle(self.canvas,(80,91,116),STICK_CENTER,29,1)
        pygame.draw.line(self.canvas,(55,65,90),(36,278),(84,278),2)
        pygame.draw.line(self.canvas,(55,65,90),(60,254),(60,302),2)
        knob=STICK_CENTER
        for role,(x,y) in self.pointers.values():
            if role=='stick':
                dx,dy=x-STICK_CENTER[0],y-STICK_CENTER[1]; length=max(1,math.hypot(dx,dy)); ratio=min(1,19/length)
                knob=(int(STICK_CENTER[0]+dx*ratio),int(STICK_CENTER[1]+dy*ratio))
        pygame.draw.circle(self.canvas,(143,151,176),knob,11)
        pygame.draw.circle(self.canvas,(207,218,238),(knob[0]-2,knob[1]-3),6,1)
        self.text('J PUNCH / K KICK',(115,266),12,MUTED)
        self.text('L COMBO / I SPECIAL',(115,280),12,MUTED)
        self.text('5 BASIC HITS = SPECIAL',(115,299),12,GOLD)
        for label,name,cx,cy,col in TOUCH_BUTTONS:
            ready=True
            f=self.match.fighters[0]
            if name=='combo': ready=f.combo_cd<=0
            if name=='special': ready=f.ready and not f.used
            pressed=any(role==name for role,_ in self.pointers.values())
            pygame.draw.circle(self.canvas,(5,8,17),(cx,cy+2),15)
            pygame.draw.circle(self.canvas,col if ready else (42,49,67),(cx,cy),14)
            pygame.draw.circle(self.canvas,WHITE if pressed else col,(cx,cy),15,2 if pressed else 1)
            pygame.draw.arc(self.canvas,tuple(min(255,c+40) for c in col),(cx-11,cy-11,22,22),.4,2.6,1)
            self.text(label,(cx,cy),20,INK if ready else MUTED,True)
            progress=1-f.combo_cd/5 if name=='combo' else (1 if f.ready else f.streak/5) if name=='special' and not f.used else 0
            if progress>0 and name in ('combo','special'):
                pygame.draw.arc(self.canvas,GOLD,(cx-16,cy-16,32,32),-math.pi/2,-math.pi/2+max(.01,progress)*math.tau,2)

    def draw_match(self):
        m=self.match
        self.canvas.blit(self.arena,(0,0))
        # Spirit motes in the arena's background.
        for i in range(8):
            x=int((i*61+self.time*3)%W); y=int(105+math.sin(self.time+i)*22)
            pygame.draw.rect(self.canvas,(153,142,207),(x,y,2,2))
        pygame.draw.rect(self.canvas,INK,(0,0,W,64))
        self.text('TITAN STRIFE',(8,5),12,MUTED)
        self.text('PAUSE',(455,10),12,GOLD,True)
        self.text('R'+str(m.round),(240,9),14,GOLD,True)
        for i,f in enumerate(m.fighters):
            x=12 if i==0 else 288
            self.text(f.name.upper(),(x,20),20,WHITE)
            self.panel((x,38,180,10),(42,29,40),(116,96,89))
            width=int(176*max(0,min(MAX_HP,f.hp))/MAX_HP)
            bx=x+2 if i==0 else x+178-width
            pygame.draw.rect(self.canvas,GOLD if f.hp>MAX_HP*.3 else (207,79,80),(bx,40,width,6))
            self.text(str(math.ceil(f.hp)),(x+151,22),14,MUTED)
            for j in range(2): pygame.draw.rect(self.canvas,GOLD if m.score[i]>j else (64,67,87),(x+j*9,53,6,4))
            status='USED' if f.used else ('READY' if f.ready else str(f.streak)+'/5')
            self.text('SPECIAL '+status,(x+30,51),12,(179,140,236) if f.ready else MUTED)
            self.text('Y '+('READY' if f.combo_cd<=0 else f'{f.combo_cd:.1f}s'),(x+123,51),12,MUTED)
        self.text('SD' if m.sudden else str(math.ceil(m.timer)),(240,35),32,GOLD,True)
        for f in sorted(m.fighters,key=lambda f:f.y): self.draw_fighter(f)
        for p in self.particles: pygame.draw.rect(self.canvas,p[5],(int(p[0]),int(p[1]),3,3))
        draw_specials(self.canvas,m,self.time,self.text)
        for impact in self.impacts:
            x,y=int(impact['x']),int(impact['y'])
            age=1-impact['life']/(.8 if impact['kind']=='heal' else .22)
            radius=max(2,int(14*(1-age)))
            if impact['kind']=='heal':
                self.text('+'+str(int(-impact['damage']))+' HP',(x,y-age*18),20,(140,245,169),True)
            elif impact['kind']=='block':
                pygame.draw.arc(self.canvas,(123,207,255),(x-radius,y-radius,radius*2,radius*2),0,math.tau,2)
            else:
                points=[]
                for j in range(16):
                    angle=j*math.pi/8
                    r=radius if j%2==0 else radius*.3
                    points.append((x+math.cos(angle)*r,y+math.sin(angle)*r))
                pygame.draw.polygon(self.canvas,(255,181,67),points)
                pygame.draw.circle(self.canvas,(255,249,211),(x,y),max(1,radius//3))
        # Shake the arena only; HUD and touch controls stay readable and stable.
        if self.shake>0:
            stage=self.canvas.subsurface((0,64,W,190)).copy()
            offset=2 if int(self.time*60)%2 else -2
            self.canvas.blit(stage,(offset,64))
        for i,f in enumerate(m.fighters):
            count=f.streak
            if count>=2 and not f.used:
                self.text(str(count)+'/5 BASICS',(61 if i==0 else 419,92),16,GOLD,True)
        self.draw_controls()
        if m.phase in ('intro','result'):
            self.panel((85,105,310,49),(19,22,40),(123,106,116))
            self.text(m.message,(240,129),32,GOLD,True)
            if m.phase=='result':
                label='ROUND REPLAY' if m.result=='double' else m.fighters[m.result].name.upper()+' WINS THE ROUND'
                self.text(label,(240,166),16,WHITE,True)
        elif self.feedback:
            self.text(self.feedback[-1][0],(240,80),20,GOLD,True)
        if m.phase=='victory':
            self.text_draws.clear()
            overlay=pygame.Surface((W,H),pygame.SRCALPHA); overlay.fill((8,11,24,210)); self.canvas.blit(overlay,(0,0))
            winner=m.fighters[0 if m.score[0]==2 else 1]
            self.text(m.message,(240,36),42,GOLD,True)
            self.text(winner.name.upper()+' VICTORIOUS',(240,66),20,WHITE,True)
            self.draw_fighter(winner,1.5,(90,215),pose='victory')
            self.text(f'{m.score[0]} - {m.score[1]}',(90,239),32,GOLD,True)
            self.button('NEW MATCH',(200,108,235,32),'new')
            self.button('CHARACTER SELECTION',(200,153,235,32),'play')
            self.button('MAIN MENU',(200,198,235,32),'menu')
        elif self.paused:
            self.text_draws=[t for t in self.text_draws if not pygame.Rect(110,94,260,151).collidepoint(t[1])]
            self.panel((110,94,260,151),(18,23,40),GOLD)
            self.text('PAUSED',(240,115),32,GOLD,True)
            self.button('RESUME',(143,144,194,30),'resume')
            self.button('MAIN MENU',(143,192,194,30),'menu')

    def draw(self):
        size=browser_size()
        if size and self.screen.get_size()!=size:
            self.screen=pygame.display.set_mode(size,pygame.RESIZABLE)
            self.display_fonts.clear()
        self.buttons=[]
        self.text_draws=[]
        self.canvas.fill(INK)
        if self.scene=='menu': self.draw_menu()
        elif self.scene=='select': self.draw_select()
        elif self.scene=='characters': self.draw_select(True)
        elif self.scene=='settings': self.draw_settings()
        elif self.scene=='match': self.draw_match()
        sw,sh=self.screen.get_size()
        scale=min(sw/W,sh/H)
        vw,vh=max(1,int(W*scale)),max(1,int(H*scale))
        self.viewport=pygame.Rect((sw-vw)//2,(sh-vh)//2,vw,vh)
        self.screen.fill((6,8,18))
        self.screen.blit(pygame.transform.scale(self.canvas,(vw,vh)),self.viewport)
        for label,pos,size,color,center in self.text_draws:
            pixels=max(8,round(size*.75*scale))
            key=(self.font_paths[size],pixels)
            if key not in self.display_fonts:
                self.display_fonts[key]=pygame.font.Font(key[0],pixels)
            surf=self.display_fonts[key].render(label,True,color)
            p=(round(self.viewport.x+pos[0]*scale),round(self.viewport.y+pos[1]*scale))
            rect=surf.get_rect(center=p) if center else surf.get_rect(topleft=p)
            if size>=16:
                shadow=self.display_fonts[key].render(label,True,(7,10,22))
                self.screen.blit(shadow,rect.move(max(1,round(scale*.5)),max(1,round(scale*.5))))
            self.screen.blit(surf,rect)
        if sw<sh:
            veil=pygame.Surface((sw,sh),pygame.SRCALPHA); veil.fill((8,10,24,230)); self.screen.blit(veil,(0,0))
            font=pygame.font.Font(None,max(20,int(sw/15)))
            for i,line in enumerate(('ROTATE YOUR PHONE','Landscape gives your fighters room.')):
                surf=font.render(line,False,GOLD)
                self.screen.blit(surf,surf.get_rect(center=(sw//2,sh//2+i*35)))
        pygame.display.flip()

async def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    game=Game(); clock=pygame.time.Clock()
    while game.running:
        dt=min(clock.tick(0 if sys.platform=='emscripten' else 60)/1000,.1)
        for event in pygame.event.get(): game.handle(event)
        game.update(dt)
        game.draw()
        await asyncio.sleep(0)
    pygame.quit()

if __name__=='__main__': asyncio.run(main())
