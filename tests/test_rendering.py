"""Headless integration checks for the renderer and combat feedback bridge."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import unittest
import pygame
from main import Game
from combat import Match, ROSTER, MAX_HP, ROUND_TIME

class Rendering(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.game=Game()
    def test_roster_menus_and_specials_draw_both_directions(self):
        g=self.game
        for scene in ('menu','select','characters','settings'):
            g.scene=scene;g.draw()
        g.scene='match'
        for name in ROSTER:
            for facing in (-1,1):
                g.match=Match(name,'Zen' if name!='Zen' else 'Kara');m=g.match;m.phase='fight'
                f,t=m.fighters;f.x,t.x=(225,200) if facing<0 else (200,225)
                f.ready=True;m.begin_attack(f,'special')
                for _ in range(90):
                    m.update(1/60,{},{});g.time+=1/60;g.draw()
    def test_hit_feedback_freezes_simulation_and_resumes(self):
        g=self.game;g.scene='match';g.paused=False;g.hitstop=0;g.accumulator=0
        g.match=Match('Steve','Kara');m=g.match;m.phase='fight'
        f,t=m.fighters;f.x,t.x=200,225;m.ai_wait=99;m.ai_action={}
        m.begin_attack(f,'punch')
        for _ in range(8):g.update(1/60)
        self.assertTrue(g.impacts);self.assertGreater(g.hitstop,0)
        timer=m.timer;g.update(.005);self.assertEqual(m.timer,timer)
        for _ in range(12):g.update(1/60)
        self.assertLess(m.timer,timer)
    def test_pause_freezes_timer_and_effect_lifetimes(self):
        g=self.game;g.scene='match';g.match=Match();g.match.phase='fight';g.paused=True
        g.impacts=[dict(kind='hit',x=200,y=180,life=.2)];g.hitstop=.04
        g.update(.1)
        self.assertEqual(g.match.timer,ROUND_TIME);self.assertEqual(g.impacts[0]['life'],.2)
        self.assertEqual(g.hitstop,.04);g.paused=False

    def test_touch_stick_and_attack_are_independent(self):
        g=self.game;g.scene='match';g.match=Match();g.match.phase='fight'
        g.pointers={1:('stick',(57,310)),2:('kick',(414,305))};g.taps=['kick']
        action=g.player_action()
        self.assertTrue(action['crouch']);self.assertEqual(action['attack'],'kick')
        g.pointers.clear();g.taps.clear()

    def test_victory_reports_result_only_once(self):
        g=self.game;g.scene='match';g.match=Match();g.match.phase='victory';g.match.score=[2,0]
        before=len(g.opponents.results)
        for _ in range(5):g.update(1/60)
        self.assertEqual(len(g.opponents.results),min(5,before+1))
