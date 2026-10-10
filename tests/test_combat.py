import unittest
from combat import Match, ROSTER, MAX_HP, ROUND_TIME

DT=1/60
def ready(a='Zen',b='Kara'):
    m=Match(a,b); m.phase='fight'; m.fighters[0].x=200; m.fighters[1].x=225
    return m

def advance(m,seconds,a=None,b=None):
    for i in range(round(seconds/DT)): m.update(DT,a or {},b or {})

class Rules(unittest.TestCase):
    def test_timeout_awards_higher_hp_once(self):
        m=ready(); m.timer=.001; m.fighters[0].hp=80; m.fighters[1].hp=70
        m.update(DT,{},{}); self.assertEqual(m.score,[1,0]); self.assertEqual(m.message,'TIME UP!')
        advance(m,1); self.assertEqual(m.score,[1,0])
    def test_tie_keeps_current_hp_no_timer(self):
        m=ready(); m.timer=.001
        for f in m.fighters: f.hp=41
        m.update(DT,{},{}); self.assertTrue(m.sudden); self.assertEqual(m.phase,'fight')
        advance(m,2); self.assertEqual([f.hp for f in m.fighters],[41,41]); self.assertEqual(m.score,[0,0])
    def test_ko_precedes_timeout(self):
        m=ready(); m.timer=.001; m.fighters[1].hp=0
        m.update(DT,{},{}); self.assertEqual(m.message,'K.O.!'); self.assertEqual(m.score,[1,0])
    def test_double_ko_replays_no_point(self):
        m=ready()
        for f in m.fighters: f.hp=0
        m.update(DT,{},{}); advance(m,2.1)
        self.assertEqual(m.score,[0,0]); self.assertEqual(m.round,1); self.assertTrue(m.sudden)
        self.assertEqual([f.hp for f in m.fighters],[MAX_HP,MAX_HP])
    def test_two_zero_ends_without_round_three(self):
        m=ready(); m.score=[1,0]; m.fighters[1].hp=0
        m.update(DT,{},{}); advance(m,2.1)
        self.assertEqual(m.phase,'victory'); self.assertEqual(m.score,[2,0]); self.assertEqual(m.round,1)
    def test_two_one_ends(self):
        m=ready(); m.score=[1,1]; m.round=3; m.fighters[0].hp=0
        m.update(DT,{},{}); advance(m,2.1)
        self.assertEqual(m.phase,'victory'); self.assertEqual(m.score,[1,2])
    def test_round_reset(self):
        m=ready(); f=m.fighters[0]; f.ready=True; f.used=True; f.streak=5; f.bound=1; f.combo_cd=4
        m.start_round()
        self.assertEqual((f.hp,f.ready,f.used,f.streak,f.bound,f.combo_cd),(MAX_HP,False,False,0,0,0))
    def test_pause_freezes(self):
        m=ready(); m.paused=True; advance(m,2)
        self.assertEqual(m.timer,ROUND_TIME)
    def test_combo_cooldown(self):
        m=ready(); f=m.fighters[0]; self.assertTrue(m.begin_attack(f,'combo'))
        advance(m,1); self.assertFalse(m.begin_attack(f,'combo')); advance(m,4.1)
        self.assertTrue(m.begin_attack(f,'combo')); self.assertEqual(f.streak,0)
    def test_five_basics_unlock_once(self):
        m=ready(); f,target=m.fighters
        for _ in range(5):
            f.x,target.x=200,225
            m.update(DT,{'attack':'punch'},{}); advance(m,.4)
        self.assertTrue(f.ready); self.assertEqual(f.streak,5)
        self.assertTrue(m.begin_attack(f,'special')); self.assertTrue(f.used)
        advance(m,3.2); self.assertFalse(m.begin_attack(f,'special'))
    def test_miss_block_damage_reset_streak(self):
        m=ready(); f,t=m.fighters; f.streak=4; t.x=400
        m.update(DT,{'attack':'punch'},{}); advance(m,.4); self.assertEqual(f.streak,0)
        f.streak=4; t.x=225
        advance(m,.4,{'attack':'punch'},{'block':True}); self.assertEqual(f.streak,0)
        f.streak=4; m.damage(t,f,6); self.assertEqual(f.streak,0)
    def test_ready_survives_streak_break(self):
        m=ready(); f,t=m.fighters; f.ready=True; f.streak=5
        m.damage(t,f,6); self.assertTrue(f.ready)
    def test_phantom_counter_and_knockback(self):
        m=ready(); z,t=m.fighters; z.ready=True
        m.begin_attack(z,'special'); m.update(DT,{}, {'attack':'punch'}); advance(m,.5)
        self.assertEqual(z.hp,MAX_HP); self.assertEqual(t.hp,MAX_HP-30); self.assertTrue(z.used)
    def test_phantom_wait_out(self):
        m=ready(); z,t=m.fighters; z.ready=True; m.begin_attack(z,'special'); advance(m,3.2)
        self.assertEqual(t.hp,MAX_HP); self.assertEqual(z.state,'idle'); self.assertTrue(z.used)
    def test_kara_bind_threshold_and_break(self):
        for hp,duration in ((101,3),(100,2)):
            m=ready('Kara','Steve'); f,t=m.fighters; f.ready=True; t.hp=hp
            m.begin_attack(f,'special'); advance(m,.27)
            self.assertGreater(t.bound,duration-.1); self.assertLessEqual(t.bound,duration)
            m.damage(f,t,6); self.assertGreater(t.bound,0)
            m.damage(f,t,6); self.assertEqual(t.bound,0)
    def test_steve_double_combo_damage_guaranteed(self):
        m=ready('Steve','Jay'); f,t=m.fighters; f.ready=True; t.x=400
        m.begin_attack(f,'special'); advance(m,.9,{}, {'block':True})
        self.assertEqual(t.hp,MAX_HP-32)
    def test_jay_wave_damage_and_interrupt(self):
        m=ready('Jay','Steve'); f,t=m.fighters; f.ready=True
        m.begin_attack(f,'special'); advance(m,1)
        self.assertEqual(t.hp,MAX_HP-70)
        m=ready('Jay','Steve'); f,t=m.fighters; f.ready=True
        m.begin_attack(f,'special'); m.damage(t,f,6,force=True); advance(m,1)
        self.assertEqual(t.hp,MAX_HP); self.assertTrue(f.used)
    def test_teresa_heals_without_hitting_enemy(self):
        m=ready('Teresa','Jay'); f,t=m.fighters; f.ready=True; f.hp=130
        m.begin_attack(f,'special'); advance(m,2.1)
        self.assertEqual(f.hp,150); self.assertEqual(t.hp,MAX_HP)
    def test_genuine_simultaneous_hits(self):
        m=ready('Steve','Teresa')
        for f in m.fighters: f.hp=6
        m.update(DT,{'attack':'punch'},{'attack':'punch'}); advance(m,.15)
        self.assertEqual(m.result,'double'); self.assertEqual(m.score,[0,0])
    def test_seeded_bot_matches_terminate(self):
        for name in ROSTER:
            m=Match('Zen' if name!='Zen' else 'Kara',name,seed=31)
            for frame in range(60*260):
                f,t=m.fighters; direction=1 if t.x>f.x else -1
                action={'move':direction} if abs(t.x-f.x)>64 else {'attack':'special' if f.ready else 'combo' if f.combo_cd<=0 else 'punch'}
                m.update(DT,action)
                for fighter in m.fighters: self.assertGreaterEqual(fighter.hp,0)
                if m.phase=='victory': break
            self.assertEqual(m.phase,'victory',name)
            self.assertEqual(max(m.score),2)

if __name__=='__main__': unittest.main()
