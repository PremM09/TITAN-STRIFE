"""Original day/night stage art, fitted to the fixed combat floor."""
import os
import pygame


def make_arena(day=False):
    path=os.path.join('assets','arena-day.png' if day else 'arena-night.png')
    art=pygame.image.load(path).convert()
    w,h=art.get_size()
    # Preserve the entire scene while placing the terrace behind fighters' feet.
    horizon=round(h*.742)
    stage=pygame.Surface((480,320))
    stage.blit(pygame.transform.scale(art.subsurface((0,0,w,horizon)),(480,204)),(0,0))
    stage.blit(pygame.transform.scale(art.subsurface((0,horizon,w,h-horizon)),(480,116)),(0,204))
    return stage
