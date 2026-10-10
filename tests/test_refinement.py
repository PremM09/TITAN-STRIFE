import random
import unittest
from combat import Match, OpponentSelector, ROSTER, GROUND, BODY_GAP, MAX_HP
from test_combat import ready, advance, DT

class Refinement(unittest.TestCase):
    def test_crouched_basics_hit_standing_and_crouched_targets(self):
        for kind,damage in [('punch',6),('kick',9)]:
            for crouch in (False,True):
                m=ready();a,b=m.fighters
                m.update(DT,{'crouch':True,'attack':kind},{'crouch':crouch})
                advance(m,.30,{'crouch':True},{'crouch':crouch})
                self.assertEqual(b.hp,MAX_HP-damage,(kind,crouch))
                self.assertEqual(a.streak,1)

    def test_air_basics_connect_and_out_of_reach_whiff(self):
        for kind,damage in [('punch',6),('kick',9)]:
            m=ready();a,b=m.fighters
            m.update(DT,{'jump':True,'attack':kind},{})
            advance(m,.25)
            self.assertLess(a.y,GROUND)
            self.assertEqual(b.hp,MAX_HP-damage)
            m=ready();a,b=m.fighters;a.y=GROUND-140
            m.update(DT,{'attack':kind},{})
            advance(m,.25)
            self.assertEqual(b.hp,MAX_HP)

    def test_late_air_kick_hits_grounded_opponent(self):
        m=ready();a,b=m.fighters
        m.update(DT,{'jump':True},{})
        advance(m,.32)
        m.update(DT,{'attack':'kick'},{})
        advance(m,.25)
        self.assertEqual(b.hp,MAX_HP-9)

    def test_input_buffer_fires_after_recovery(self):
        m=ready();a,b=m.fighters
        m.update(DT,{'attack':'punch'},{})
        advance(m,.23)
        m.update(DT,{'crouch':True,'attack':'kick'},{})
        advance(m,.34,{'crouch':True})
        self.assertEqual(b.hp,MAX_HP-15)

    def test_five_punches_charge_without_manual_reposition(self):
        m=ready();a,b=m.fighters
        for _ in range(5):
            m.update(DT,{'attack':'punch'},{})
            advance(m,.4)
        self.assertEqual(b.hp,MAX_HP-30)
        self.assertTrue(a.ready)
        self.assertEqual(a.streak,5)

    def test_blocking_preserves_defenders_own_streak(self):
        m=ready();a,b=m.fighters;b.streak=4
        m.update(DT,{'attack':'punch'},{'block':True})
        advance(m,.25,{}, {'block':True})
        self.assertEqual(b.streak,4)
        self.assertEqual(a.streak,0)

    def test_corner_and_landing_keep_body_gap(self):
        for x in (25,220,455):
            m=ready();a,b=m.fighters;a.x=b.x=x
            a.y=GROUND-2;a.vy=120
            for _ in range(30):
                m.update(DT,{'move':1},{'move':-1})
                self.assertGreaterEqual(abs(a.x-b.x),BODY_GAP-1e-6)
                self.assertTrue(25<=a.x<=455 and 25<=b.x<=455)

    def test_opponents_exclude_self_and_immediate_repeats(self):
        selector=OpponentSelector(random.Random(72));last=None;seen=set()
        for _ in range(200):
            name=selector.choose('Steve')
            self.assertNotEqual(name,'Steve');self.assertNotEqual(name,last)
            seen.add(name);last=name
        self.assertEqual(seen,set(ROSTER)-{'Steve'})

    def test_skill_weighting_changes_after_results(self):
        easy=OpponentSelector(random.Random(28));hard=OpponentSelector(random.Random(28))
        for _ in range(5): hard.record(True)
        rank={'EASY':1,'MID':2,'HARD':3}
        a=sum(rank[ROSTER[easy.choose('Steve')]['level']] for _ in range(2000))
        b=sum(rank[ROSTER[hard.choose('Steve')]['level']] for _ in range(2000))
        self.assertGreater(b,a+400)
        for _ in range(5):hard.record(False)
        self.assertEqual(hard.tier,'EASY')

    def test_cpu_defends_sometimes_but_leaves_openings(self):
        for name in ROSTER:
            m=ready('Kara' if name=='Zen' else 'Zen',name)
            m.rng=random.Random(73)
            guards=0;attacks=0;openings=0
            for _ in range(600):
                a,b=m.fighters;a.state='attack';a.attack='punch';a.elapsed=.10
                m.ai_wait=0
                action=m.bot(DT)
                guards+=bool(action.get('block'))
                attacks+=bool(action.get('attack'))
                openings+=not action.get('attack') and not action.get('block')
            self.assertGreater(guards,0,name)
            self.assertLess(guards/600,.65,name)
            self.assertGreater(attacks,100,name)
            self.assertGreater(openings,30,name)

if __name__=='__main__':unittest.main()
