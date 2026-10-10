"""Deterministic combat rules, independent of rendering and audio."""
from dataclasses import dataclass, field
import random

ROSTER = {
    'Zen': dict(level='HARD', color=(116, 84, 190), special='PHANTOM CHECKMATE', description='A composed strategist who turns an enemy\'s certainty into a trap. Precision is his greatest weapon.'),
    'Kara': dict(level='MID', color=(181, 49, 78), special='SILK SNARE', description='A discreet operative with a sharp eye and an escape plan. Her ropegun creates the opening she needs.'),
    'Steve': dict(level='EASY', color=(57, 128, 192), special='STREET FURY', description='A 22-year-old street fighter in jeans and a varsity jacket. Scrappy, spirited, and never afraid to get back up.'),
    'Teresa': dict(level='EASY', color=(70, 133, 150), special='FIELD AID', description='A disciplined detective trained in emergency care. Her field medkit instantly restores 20 HP when activated.'),
    'Jay': dict(level='MID', color=(47, 161, 140), special='TITAN\'S ROAR', description='A towering spellfighter in rune-bound bracers and ceremonial teal robes. His ancient chant unleashes a devastating wave.'),
}
MAX_HP = 200
ROUND_TIME = 60.0
GROUND = 224
BODY_GAP = 58

class OpponentSelector:
    """Session-only skill estimate. Weighted randomness, never a fixed rotation."""
    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.results = []
        self.last = None

    def record(self, won):
        self.results = (self.results + [bool(won)])[-5:]

    @property
    def tier(self):
        if len(self.results) < 2: return 'EASY'
        rate = sum(self.results) / len(self.results)
        return 'HARD' if rate >= .75 else 'MID' if rate >= .4 else 'EASY'

    def choose(self, player):
        names = [n for n in ROSTER if n != player and n != self.last]
        weights = {'EASY':(6,3,1), 'MID':(2,6,2), 'HARD':(1,3,6)}[self.tier]
        self.last = self.rng.choices(names, [weights[('EASY','MID','HARD').index(ROSTER[n]['level'])] for n in names])[0]
        return self.last

@dataclass
class Fighter:
    name: str
    x: float
    facing: int
    hp: float = MAX_HP
    y: float = GROUND
    vy: float = 0
    state: str = 'idle'
    state_time: float = 0
    elapsed: float = 0
    attack: str = ''
    landed: set = field(default_factory=set)
    combo_cd: float = 0
    streak: int = 0
    ready: bool = False
    used: bool = False
    blocking: bool = False
    crouching: bool = False
    moving: bool = False
    bound: float = 0
    bound_by: str = ''
    rope_hits: int = 0
    stun: float = 0
    phantom: float = 0
    flash: float = 0
    heal_flash: float = 0
    queued: str = ''
    queue_time: float = 0
    posture: str = 'stand'
    air_move: float = 0
    def reset(self, x, facing):
        self.__dict__.update(Fighter(self.name, x, facing).__dict__)

# Active strike time, damage and range. Y does not contribute to the unlock streak.
ATTACKS = {
    'punch': [(0.11, 6, 68)],
    'kick': [(0.20, 9, 80)],
    'combo': [(0.16, 5, 68), (0.32, 5, 74), (0.49, 6, 82)],
    'Steve': [(0.12, 6, 500), (0.24, 6, 500), (0.36, 6, 500), (0.48, 6, 500), (0.60, 8, 500)],
    'Kara': [(0.25, 0, 500)],
    'Teresa': [],
    'Jay': [(0.72, 0, 500)],
}
DURATIONS = dict(punch=.32, kick=.48, combo=.80, Steve=.90, Kara=.65, Teresa=0.0, Jay=1.25)

class Match:
    def __init__(self, player='Zen', opponent='Kara', seed=None):
        self.fighters = [Fighter(player, 150, 1), Fighter(opponent, 330, -1)]
        self.score = [0, 0]
        self.round = 1
        self.timer = ROUND_TIME
        self.sudden = False
        self.phase = 'intro'
        self.phase_time = 2.2
        self.message = 'ROUND 1'
        self.result = None
        self.events = []
        self.rng = random.Random(seed)
        self.ai_wait = .4
        self.ai_action = {}
        self.ai_mode = 'observe'
        self.ai_burst = 0
        self.ai_phantom_notice = None
        self.ai_phantom_delay = 0
        self.impacts = []
        self.paused = False
        self.reported = False
        self.waves = []

    def start_round(self, sudden=False):
        for f, x, facing in zip(self.fighters, (150, 330), (1, -1)):
            f.reset(x, facing)
        self.timer = ROUND_TIME
        self.sudden = sudden
        self.phase = 'intro'
        self.phase_time = 2.2
        self.message = 'SUDDEN DEATH' if sudden else f'ROUND {self.round}'
        self.ai_wait = .4
        self.ai_action = {}
        self.ai_mode = 'observe'
        self.ai_burst = 0
        self.ai_phantom_notice = None
        self.ai_phantom_delay = 0
        self.impacts = []
        self.waves = []

    def bot(self, dt):
        bot, target = self.fighters[1], self.fighters[0]
        # Recognize each illusion once, rather than repeatedly rolling avoidance.
        if target.phantom<=0:
            self.ai_phantom_notice=None
            self.ai_phantom_delay=0
        elif self.ai_phantom_notice is None:
            tier=('EASY','MID','HARD').index(ROSTER[bot.name]['level'])
            self.ai_phantom_notice=self.rng.random()<(.15,.25,.35)[tier]
            self.ai_phantom_delay=(.35,.30,.25)[tier]
        self.ai_phantom_delay=max(0,self.ai_phantom_delay-dt)
        # Decision time elapses during recovery too: do not add a second idle delay.
        self.ai_wait = max(0,self.ai_wait-dt)
        if bot.state != 'idle' or bot.stun > 0 or bot.bound > 0:
            self.ai_action = {}
            return {}
        level = ROSTER[bot.name]['level']
        tier = ('EASY','MID','HARD').index(level)
        diff=target.x-bot.x; dist=abs(diff); toward=1 if diff>0 else -1
        if self.ai_wait > 0:
            # Stop walking into attack range; assess the exchange immediately.
            if self.ai_mode=='approach' and dist<=62:
                self.ai_wait=0
            else:
                return {k:v for k,v in self.ai_action.items() if k in ('move','block','guard_away')}
        self.ai_wait=self.rng.uniform(*((.16,.24),(.12,.20),(.09,.16))[tier])
        action={}
        threat=False
        if target.state=='attack' and target.attack not in ('Steve','Kara','Jay','counter') and target.elapsed>=(.10,.095,.08)[tier]:
            schedule=ATTACKS.get(target.attack,[])
            threat=any(j not in target.landed and 0<=when-target.elapsed<=.22 and dist<=reach+3
                       for j,(when,_,reach) in enumerate(schedule))
        # Wait out Checkmate instead of donating a hit; never peek at player input.
        if target.phantom>0 and self.ai_phantom_notice and self.ai_phantom_delay<=0:
            self.ai_mode='retreat'
            if dist<110 and 32<bot.x<448:action['move']=-toward
            else:action['block']=True
            self.ai_wait=.18
        elif bot.ready and bot.name=='Teresa' and bot.hp<=MAX_HP-20:
            self.ai_mode='special';action['attack']='special'
        elif target.state=='attack' and target.attack=='Jay' and target.elapsed<.55 and dist<=68:
            self.ai_mode='punish';action['attack']='punch'
        elif threat and self.rng.random() < (.26,.38,.46)[tier]:
            self.ai_mode='defend';action['block']=True
            self.ai_wait=self.rng.uniform(.10,.18)
        elif bot.ready and (bot.name!='Teresa') and (
                bot.name!='Zen' or target.state=='attack' or dist<72):
            # Earned resources are used promptly; Jay prefers room for his chant.
            if bot.name=='Jay' and dist<76 and target.stun<=0 and target.bound<=0 and self.rng.random()<.45:
                self.ai_mode='retreat';action={'move':-toward};self.ai_wait=.16
            else:
                self.ai_mode='special';action['attack']='special';self.ai_burst=0
        elif dist>64:
            self.ai_mode='approach';action['move']=toward
            # Check spacing often so short ranged punches are not thrown into air.
            self.ai_wait=min(self.ai_wait,.10)
        elif self.ai_burst >= (3,4,5)[tier]:
            self.ai_burst=0
            self.ai_mode='retreat' if self.rng.random()<.45 else 'observe'
            self.ai_wait=self.rng.uniform(.20,.30)
            if self.ai_mode=='retreat' and 32<bot.x<448:
                action={'move':-toward}
            # The brief stationary breather remains a punishable opening.
        else:
            self.ai_mode='attack'
            # Basic-hit chains earn the special. Y is occasional, never a substitute.
            if bot.combo_cd<=0 and bot.streak==0 and self.rng.random()<.12:
                action['attack']='combo'
            else:
                action['attack']='punch' if dist<=66 and self.rng.random()<.78 else 'kick'
            self.ai_burst+=1
            # A small CPU-only gap after recovery lets a human answer the exchange.
            # Keep elapsed recovery accounting; this is intentional, not a stalled timer.
            if self.rng.random()<.35:
                self.ai_wait=DURATIONS[action['attack']]+self.rng.uniform(*((.07,.12),(.05,.09),(.03,.06))[tier])
        self.ai_action=action
        return action

    def begin_attack(self, f, kind):
        if f.state != 'idle' or f.stun > 0 or f.bound > 0 or f.phantom > 0:
            return False
        if kind == 'combo':
            if f.combo_cd > 0: return False
            f.combo_cd = 5
        if kind == 'special':
            if not f.ready or f.used: return False
            f.used, f.ready = True, False
            self.events.append(('special', f.name))
            if f.name == 'Teresa':
                healed=min(20,MAX_HP-f.hp)
                f.hp=min(MAX_HP,f.hp+20)
                f.heal_flash=.65
                self.events.append(('heal',f.name))
                self.impacts.append(dict(kind='heal',x=f.x,y=f.y-62,source=f.name,target=f.name,attack='Teresa',damage=-healed))
                return True
            if f.name == 'Zen':
                f.phantom = 3
                f.state = 'phantom'
                return True
            kind = f.name
            if kind == 'Steve':
                target = self.fighters[1] if f is self.fighters[0] else self.fighters[0]
                f.x = max(25,min(455,target.x-f.facing*BODY_GAP))
                self.separate()
        f.state, f.attack, f.elapsed = 'attack', kind, 0
        f.state_time = DURATIONS[kind]
        f.landed.clear()
        f.blocking = False
        f.posture = 'air' if f.y < GROUND or f.vy < 0 else 'crouch' if f.crouching else 'stand'
        return True

    def separate(self):
        a,b = self.fighters
        if abs(a.y-b.y) >= 65 or abs(a.x-b.x) >= BODY_GAP: return
        direction = 1 if b.x >= a.x else -1
        mid = max(25+BODY_GAP/2, min(455-BODY_GAP/2, (a.x+b.x)/2))
        a.x, b.x = mid-direction*BODY_GAP/2, mid+direction*BODY_GAP/2

    @staticmethod
    def strike_height(f, kind):
        # Feet-based world coordinates, matching crouched and airborne art.
        if f.posture == 'crouch': return f.y-(13 if kind=='kick' else 38)
        if f.posture == 'air': return f.y-(34 if kind=='kick' else 45)
        return f.y-(53 if kind=='kick' else 60)

    def damage(self, source, target, amount, knockback=4, stun=.12, force=False, contact=None):
        contact = contact or source.attack
        if target.phantom > 0:
            target.phantom = 0
            target.state = 'attack'
            target.attack = 'counter'
            target.state_time = .55
            target.elapsed = 0
            target.landed.clear()
            target.x = max(25,min(455,source.x - source.facing * BODY_GAP))
            target.facing = 1 if source.x > target.x else -1
            self.events.append(('illusion', target.name))
            return 'counter'
        if target.blocking and not force:
            self.impacts.append(dict(kind='block', x=target.x-source.facing*14, y=self.strike_height(source,contact), source=source.name, target=target.name, attack=contact, damage=0))
            self.events.append(('block', target.name))
            return 'blocked'
        self.impacts.append(dict(kind='hit', x=target.x-source.facing*14, y=self.strike_height(source,contact), source=source.name, target=target.name, attack=contact, damage=amount))
        target.hp = max(0, target.hp - amount)
        target.streak = 0
        if target.bound > 0:
            if target.bound_by=='Kara' and target.rope_hits>0:
                target.rope_hits -= 1
                knockback = 0
            else:
                target.bound = 0
                target.bound_by = ''
                target.rope_hits = 0
        target.stun = max(target.stun, stun)
        target.flash = .13
        target.x = max(25, min(455, target.x + source.facing * knockback))
        # Ranged casts survive ordinary hits at close range, but still take damage.
        # Interrupting specials and KO remain counters; no invulnerability is granted.
        casting=target.state=='attack' and target.attack in ('Kara','Jay')
        if not casting or force or target.hp<=0:
            target.state = 'idle'
            target.attack = ''
        target.queued = ''
        self.events.append(('hit', target.name))
        return 'hit'

    def update(self, dt, player=None, opponent=None):
        self.events = []
        self.impacts = []
        if self.paused: return
        player = player or {}
        if self.phase != 'fight':
            self.phase_time -= dt
            if self.phase == 'intro':
                if self.phase_time <= .65: self.message = 'FIGHT!'
                if self.phase_time <= 0:
                    self.phase = 'fight'
                    self.message = ''
                    self.events.append(('fight',''))
            elif self.phase == 'result' and self.phase_time <= 0:
                if self.result == 'double': self.start_round(True)
                elif max(self.score) >= 2:
                    self.phase = 'victory'
                    self.message = 'YOU WIN' if self.score[0] == 2 else 'YOU LOSE'
                else:
                    self.round += 1
                    self.start_round()
            return
        self.message = ''
        actions = [player, self.bot(dt) if opponent is None else opponent]
        for i, f in enumerate(self.fighters):
            target = self.fighters[1-i]
            f.combo_cd = max(0, f.combo_cd-dt)
            f.heal_flash = max(0,f.heal_flash-dt)
            f.stun, f.bound, f.flash = (max(0,v-dt) for v in (f.stun,f.bound,f.flash))
            if f.bound <= 0: f.bound_by=''; f.rope_hits=0
            f.moving = False
            f.crouching = (f.posture=='crouch' if f.state=='attack' else bool(actions[i].get('crouch'))) and f.y >= GROUND
            f.queue_time = max(0,f.queue_time-dt)
            if f.queue_time <= 0: f.queued = ''
            if actions[i].get('attack'):
                f.queued, f.queue_time = actions[i]['attack'], .18
            if f.phantom > 0:
                f.phantom = max(0,f.phantom-dt)
                if f.phantom <= 0: f.state = 'idle'
            if f.state == 'attack':
                f.elapsed += dt
                f.state_time -= dt
                if f.state_time <= 0:
                    f.state, f.attack = 'idle',''
            if f.y < GROUND or f.vy < 0:
                f.vy += 410*dt
                f.y = min(GROUND, f.y + f.vy*dt)
                if f.y >= GROUND: f.vy = 0
                else: f.x = max(25,min(455,f.x+f.air_move*62*dt))
            f.facing = 1 if target.x > f.x else -1
            act = actions[i]
            can = f.state == 'idle' and f.stun <= 0 and f.bound <= 0
            move = act.get('move',0)
            f.blocking = can and f.y >= GROUND and (act.get('block',False) or (act.get('guard_away',True) and move*f.facing < 0))
            if can:
                if move and not f.crouching and f.y >= GROUND:
                    f.x = max(25,min(455,f.x + move*(48 if f.blocking else 76)*dt))
                    f.moving = True
                if act.get('jump') and f.y >= GROUND:
                    f.vy = -180
                    f.air_move = move
                    f.crouching = False
                    f.blocking = False
                if f.queued and self.begin_attack(f,f.queued):
                    f.queued = ''; f.queue_time = 0
        # Body boxes stay distinct, including corner pressure and landing.
        a,b = self.fighters
        self.separate()
        # Gather strikes before resolving, allowing genuine simultaneous knockouts.
        strikes=[]
        for i,f in enumerate(self.fighters):
            if f.state != 'attack': continue
            schedule = [(0.07,30,500)] if f.attack == 'counter' else ATTACKS[f.attack]
            for j,(when,amount,reach) in enumerate(schedule):
                if f.elapsed >= when and j not in f.landed:
                    f.landed.add(j)
                    contact='kick' if f.attack in ('combo','Steve','Teresa') and j%3==2 else f.attack
                    strikes.append((i,f.attack,amount,reach,contact))
                    self.events.append(('swing', f.name))
        for i,kind,amount,reach,contact in strikes:
            f,target=self.fighters[i],self.fighters[1-i]
            distance=abs(f.x-target.x)
            guaranteed=kind in ('Steve','Kara','counter')
            height = self.strike_height(f,contact)
            top = target.y-(55 if target.crouching else 86)
            vertical = top-7 <= height <= target.y+7
            in_range=kind in ('Kara','Jay') or (distance <= reach and (guaranteed or vertical))
            if not in_range:
                if kind in ('punch','kick'): f.streak=0
                self.events.append(('miss', f.name))
                continue
            if kind=='Kara' and target.phantom<=0:
                target.bound=3 if target.hp>MAX_HP/2 else 2
                target.bound_by='Kara'
                target.rope_hits=1
                target.state='idle'
                target.attack=''
                target.blocking=False
                target.streak=0
                self.events.append(('bind',target.name))
                continue
            if kind=='Jay' and amount==0:
                # A landed chant briefly freezes actions; its wave follows.
                # Illusions counter the wave, rather than this zero-damage cue.
                if target.phantom<=0:
                    target.bound=.25
                    target.bound_by='Jay'
                    target.rope_hits=0
                    target.blocking=False
                    target.state='idle'
                    target.attack=''
                self.waves.append(dict(source=i,x=f.x+f.facing*min(60,abs(target.x-f.x)*.5),y=f.y-65,age=0,hit=False,fade=0,direction=f.facing))
                self.events.append(('wave',f.name))
                continue
            force=kind in ('Steve','counter','Jay')
            stun=.30 if kind=='Teresa' else (.20 if kind=='counter' else .14 if kind=='Steve' else .12)
            outcome=self.damage(f,target,amount,knockback=22 if kind=='counter' else (2 if kind in ('Steve','punch') else 4),stun=stun,force=force,contact=contact)
            if outcome=='hit' and kind in ('punch','kick'):
                f.streak=min(5,f.streak+1)
                if f.streak==5 and not f.used and not f.ready:
                    f.ready=True
                    self.events.append(('ready',f.name))
            elif kind in ('punch','kick'): f.streak=0
        # The spell is a real travelling projectile; its visible contact deals damage once.
        for wave in self.waves:
            wave['age']+=dt
            if wave['hit']:
                wave['fade']+=dt
                continue
            source=self.fighters[wave['source']]
            target=self.fighters[1-wave['source']]
            dx=target.x-wave['x']; step=500*dt
            wave['direction']=1 if dx>=0 else -1
            wave['y']+=(target.y-52-wave['y'])*min(1,dt*12)
            if abs(dx)<=step+12:
                wave['x']=target.x
                wave['hit']=True
                self.damage(source,target,target.hp*.35,knockback=12,stun=.18,force=True,contact='Jay')
            else:
                wave['x']+=wave['direction']*step
        self.waves=[w for w in self.waves if w['fade']<.6]
        self.separate()
        if a.hp<=0 or b.hp<=0:
            if a.hp<=0 and b.hp<=0: self.finish('double','DOUBLE K.O.!')
            else: self.finish(0 if b.hp<=0 else 1,'K.O.!')
            return
        if not self.sudden:
            self.timer=max(0,self.timer-dt)
            if self.timer<=0:
                if a.hp==b.hp:
                    self.sudden=True
                    self.message='SUDDEN DEATH!'
                    self.events.append(('sudden',''))
                else: self.finish(0 if a.hp>b.hp else 1,'TIME UP!')

    def finish(self, winner, message):
        if self.phase!='fight': return
        self.result=winner
        self.phase='result'
        self.phase_time=2.0
        self.message=message
        if winner in (0,1): self.score[winner]+=1
        self.events.append(('round',message))
