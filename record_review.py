"""Render a scripted in-engine visual review; no changes to shipped combat rules."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import subprocess
from pathlib import Path
import pygame
from main import Game
from combat import Match

def main():
    os.chdir(Path(__file__).parent)
    g=Game();g.scene='select';g.selected='Jay';g.draw()
    pygame.image.save(g.screen,'preview/jay-approval.png')
    g.scene='menu';g.draw();pygame.image.save(g.screen,'preview/menu-approval.png')
    output=Path('preview/Jay-Gameplay-Review.mp4')
    proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size','960x640','-framerate','30','-i','-','-an','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(output)],stdin=subprocess.PIPE)
    g.scene='select'
    for _ in range(60):
        g.time+=1/30;g.draw();proc.stdin.write(pygame.image.tobytes(g.screen,'RGB'))
    g.scene='match';g.arena=g.arenas[1];g.match=Match('Jay','Steve',seed=19)
    m=g.match;m.phase='fight';m.ai_wait=999;m.ai_action={}
    f,t=m.fighters;f.x=190;t.x=248
    times=[.1,.7,1.3,1.9,2.5];pressed=set();special=False;shot=False
    for frame in range(300):
        tm=frame/30
        action={}
        for j,when in enumerate(times):
            if tm>=when and j not in pressed:action['attack']='punch';pressed.add(j)
        if 3.15<=tm<4.65:action['move']=-1
        if tm>=5.0 and not special:action['attack']='special';special=True
        g.player_action=lambda a=action:dict(a)
        g.update(1/30);g.draw()
        if m.waves and not m.waves[0]['hit'] and m.waves[0]['age']>.1 and not shot:
            pygame.image.save(g.screen,'preview/jay-wave-approval.png');shot=True
        proc.stdin.write(pygame.image.tobytes(g.screen,'RGB'))
    proc.stdin.close()
    if proc.wait()!=0:raise RuntimeError('Preview encoding failed')
    assert f.used and abs(t.hp-110.5)<.0001,(f.streak,f.used,t.hp)
    print('Review video: five earned basic hits, reposition, spell release, 35% of remaining HP at impact.',output)
    pygame.quit()

if __name__=='__main__':main()
