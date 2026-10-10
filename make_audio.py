"""Synthesize original chiptune notes and effects; no sampled recordings."""
import math, random, struct, wave
from pathlib import Path
RATE=22050
OUT=Path(__file__).parent/'assets'
OUT.mkdir(exist_ok=True)
def save(name,samples):
    with wave.open(str(OUT/(name+'.wav')),'wb') as w:
        w.setparams((1,2,RATE,0,'NONE','not compressed'))
        w.writeframes(b''.join(struct.pack('<h',int(max(-1,min(1,x))*16000)) for x in samples))
def note(midi): return 440*2**((midi-69)/12)
rng=random.Random(73)
# Original eight-bar motif in D minor, square lead, triangle bass and noise drums.
melody=[74,77,81,77,74,72,69,72, 74,77,79,77,72,69,65,69,
        70,74,77,74,70,69,65,69, 72,76,79,76,72,69,67,69,
        74,77,81,84,81,77,74,72, 74,79,82,79,77,74,72,69,
        70,74,77,81,77,74,70,69, 72,76,79,76,72,69,73,69]
step=.125
samples=[]
for i,m in enumerate(melody):
    bass=note([38,38,34,36,38,38,34,36][i//8])
    freq=note(m)
    for j in range(int(step*RATE)):
        t=j/RATE
        env=min(1,t/.006)*max(0,1-t/step)**.5
        lead=(1 if math.sin(2*math.pi*freq*t)>0 else -1)*.105*env
        tri=(2/math.pi)*math.asin(math.sin(2*math.pi*bass*(i*step+t)))*.11
        drum=0
        if i%4==0: drum=math.sin(2*math.pi*(110*t-260*t*t))*.22*math.exp(-t*30)
        elif i%4==2: drum=rng.uniform(-1,1)*.12*math.exp(-t*40)
        hat=rng.uniform(-1,1)*.025*math.exp(-t*90)
        samples.append(lead+tri+drum+hat)
save('arena',samples)
for name,duration,start,end in [('hit',.09,150,55),('block',.07,550,300),('special',.38,220,880),('round',.45,700,120),('fight',.2,300,600),('illusion',.3,1500,200),('bind',.15,650,120)]:
    data=[]
    for i in range(int(duration*RATE)):
        t=i/RATE; p=t/duration
        phase=2*math.pi*(start*t+(end-start)*t*t/(2*duration))
        tone=(1 if math.sin(phase)>0 else -1)*.17*(1-p)
        if name in ('hit','illusion'): tone+=rng.uniform(-1,1)*.18*(1-p)**2
        data.append(tone)
    save(name,data)
print('Generated original motif and seven effects.')

# Short airy attack swish, generated from seeded noise rather than samples.
save('swing',[rng.uniform(-1,1)*.14*math.sin(math.pi*i/(RATE*.10))**2 for i in range(int(RATE*.10))])

# Distinct contact sounds: tight punch crack and heavier bass kick thump.
for name,duration,freq,decay in [('punch',.115,170,33),('kick',.19,92,22)]:
    samples=[]
    for i in range(int(RATE*duration)):
        t=i/RATE
        thump=math.sin(math.tau*(freq*t-100*t*t))*.55*math.exp(-t*decay)
        crack=rng.uniform(-1,1)*.4*math.exp(-t*70)
        samples.append((thump+crack)*min(1,t/.002))
    save(name,samples)
