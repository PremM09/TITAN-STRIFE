import unittest
from combat import Match, MAX_HP, ROUND_TIME
from test_combat import ready, advance, DT

class FinalReview(unittest.TestCase):
    def test_new_match_and_round_resources(self):
        m=Match();self.assertEqual(MAX_HP,200);self.assertEqual(ROUND_TIME,60)
        self.assertEqual([f.hp for f in m.fighters],[200,200])
        m.timer=1;m.start_round();self.assertEqual(m.timer,60)

    def test_medkit_heals_on_activation_caps_and_does_not_repeat(self):
        for initial,expected in ((100,120),(195,200),(200,200)):
            m=ready('Teresa','Steve');f,t=m.fighters;f.hp=initial;f.ready=True
            self.assertTrue(m.begin_attack(f,'special'))
            self.assertEqual(f.hp,expected)
            self.assertEqual(f.state,'idle')
            advance(m,2);self.assertEqual(f.hp,expected)
            self.assertFalse(m.begin_attack(f,'special'))
            self.assertEqual(t.hp,200)

    def test_hit_after_medkit_does_not_undo_heal_or_refund(self):
        m=ready('Teresa','Steve');f,t=m.fighters;f.hp=100;f.ready=True
        m.begin_attack(f,'special');m.damage(t,f,6);advance(m,2)
        self.assertEqual(f.hp,114);self.assertTrue(f.used)

    def test_medkit_does_not_trigger_phantom(self):
        m=ready('Teresa','Zen');f,t=m.fighters;f.hp=100;f.ready=t.ready=True
        m.begin_attack(f,'special');m.begin_attack(t,'special');advance(m,2.1)
        self.assertEqual(f.hp,120);self.assertEqual(t.hp,200)
        self.assertGreater(t.phantom,0)

    def test_kara_first_hit_preserves_second_breaks_rope(self):
        m=ready('Kara','Steve');f,t=m.fighters;f.ready=True
        m.begin_attack(f,'special');advance(m,.3)
        self.assertEqual(t.bound_by,'Kara');self.assertGreater(t.bound,2.8)
        m.damage(f,t,6);self.assertEqual(t.hp,194);self.assertGreater(t.bound,0)
        m.damage(f,t,9);self.assertEqual(t.hp,185);self.assertEqual(t.bound,0)

    def test_rope_expires_and_resets_each_round(self):
        m=ready('Kara','Steve');f,t=m.fighters;f.ready=True
        m.begin_attack(f,'special');advance(m,3.4)
        self.assertEqual((t.bound,t.bound_by,t.rope_hits),(0,'',0))
        t.bound=2;t.bound_by='Kara';t.rope_hits=1;m.start_round()
        self.assertEqual((t.bound,t.bound_by,t.rope_hits),(0,'',0))

    def test_wave_travels_then_damages_once(self):
        m=ready('Jay','Steve');f,t=m.fighters;f.x=80;t.x=400;f.ready=True
        m.begin_attack(f,'special');advance(m,.8)
        self.assertTrue(m.waves);self.assertFalse(m.waves[0]['hit'])
        self.assertEqual(t.hp,200);self.assertGreater(m.waves[0]['x'],f.x+34)
        advance(m,.7);self.assertEqual(t.hp,130)
        advance(m,2);self.assertEqual(t.hp,130);self.assertEqual(m.waves,[])

    def test_jay_finishes_attack_recovery_at_one_and_quarter_seconds(self):
        m=ready('Jay','Steve');f,t=m.fighters;f.ready=True
        m.begin_attack(f,'special');advance(m,1.20)
        self.assertEqual(f.state,'attack')
        advance(m,.10);self.assertEqual(f.state,'idle')
        self.assertEqual(t.hp,130)

    def test_wave_uses_remaining_health_not_maximum(self):
        for hp in (200,170,100,40,1):
            m=ready('Jay','Steve');f,t=m.fighters;f.ready=True;t.hp=hp
            m.begin_attack(f,'special');advance(m,1.5)
            self.assertAlmostEqual(t.hp,hp*.65)
            self.assertGreater(t.hp,0)

    def test_wave_percentage_is_calculated_at_contact(self):
        m=ready('Jay','Steve');f,t=m.fighters;f.x=80;t.x=400;f.ready=True
        m.begin_attack(f,'special');advance(m,.8)
        self.assertTrue(m.waves);self.assertFalse(m.waves[0]['hit'])
        t.hp=100
        advance(m,.8);self.assertEqual(t.hp,65)

    def test_basic_hit_does_not_cancel_unreleased_wave(self):
        m=ready('Jay','Steve');f,t=m.fighters;f.ready=True
        m.begin_attack(f,'special');advance(m,.4);m.damage(t,f,6);advance(m,2)
        self.assertEqual(t.hp,130);self.assertTrue(f.used);self.assertEqual(f.hp,194)

    def test_released_wave_survives_interruption(self):
        m=ready('Jay','Steve');f,t=m.fighters;f.x=80;t.x=400;f.ready=True
        m.begin_attack(f,'special');advance(m,.8);m.damage(t,f,6);advance(m,1)
        self.assertEqual(t.hp,130)

    def test_pause_freezes_wave_and_round_reset_clears_it(self):
        m=ready('Jay','Steve');f,t=m.fighters;f.x=80;t.x=400;f.ready=True
        m.begin_attack(f,'special');advance(m,.8);x=m.waves[0]['x']
        m.paused=True;advance(m,1);self.assertEqual(m.waves[0]['x'],x)
        m.start_round();self.assertEqual(m.waves,[])
