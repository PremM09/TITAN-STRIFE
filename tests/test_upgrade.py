import unittest
from combat import ROSTER, MAX_HP
from test_combat import ready, advance, DT

class Upgrade(unittest.TestCase):
    def test_all_specials_unlock_spend_reset(self):
        for name in ROSTER:
            with self.subTest(name=name):
                m=ready(name,'Steve' if name!='Steve' else 'Jay');f=m.fighters[0]
                self.assertFalse(m.begin_attack(f,'special'))
                for _ in range(5):
                    f.x,m.fighters[1].x=200,225
                    m.update(DT,{'attack':'punch'},{});advance(m,.4)
                self.assertTrue(f.ready);self.assertTrue(m.begin_attack(f,'special'))
                advance(m,3.5);f.ready=True
                self.assertFalse(m.begin_attack(f,'special'))
                m.start_round();self.assertFalse(f.used);self.assertFalse(f.ready)
    def test_all_other_specials_trigger_phantom(self):
        for name in ('Kara','Steve','Jay'):
            with self.subTest(name=name):
                m=ready(name,'Zen');f,z=m.fighters;f.ready=z.ready=True
                m.begin_attack(z,'special');m.begin_attack(f,'special');advance(m,1.6)
                self.assertEqual(z.hp,MAX_HP);self.assertEqual(f.hp,MAX_HP-30)
                self.assertTrue(f.used);self.assertTrue(z.used)
    def test_teresa_full_health_still_spends_charge(self):
        m=ready('Teresa','Jay');f,t=m.fighters;t.x=420;f.ready=True
        m.begin_attack(f,'special');advance(m,2.1)
        self.assertEqual(f.hp,MAX_HP);self.assertEqual(t.hp,MAX_HP);self.assertTrue(f.used)
    def test_steve_interrupted_stays_spent(self):
        m=ready('Steve','Kara');f,t=m.fighters;f.ready=True
        m.begin_attack(f,'special');advance(m,.15);self.assertEqual(t.hp,MAX_HP-6)
        m.damage(t,f,6);advance(m,1)
        self.assertEqual(t.hp,MAX_HP-6);self.assertTrue(f.used)
    def test_bot_retreats_and_pauses_every_level(self):
        for name in ROSTER:
            m=ready('Kara' if name=='Zen' else 'Zen',name);modes=set()
            for _ in range(200):
                m.ai_wait=0;m.fighters[1].x=225
                action=m.bot(DT);modes.add(m.ai_mode)
                if m.ai_mode in ('retreat','observe'):self.assertNotIn('attack',action)
            self.assertIn('retreat',modes,name);self.assertIn('observe',modes,name)
    def test_no_bot_attack_queued_while_stunned(self):
        m=ready();m.ai_action={'attack':'punch'};m.ai_wait=0;m.fighters[1].stun=.3
        self.assertEqual(m.bot(DT),{})
    def test_contact_only_impacts_and_blocks(self):
        m=ready('Steve','Kara');f,t=m.fighters;m.begin_attack(f,'punch');seen=[]
        for _ in range(20):
            m.update(DT,{}, {'block':True});seen.extend(m.impacts)
        self.assertEqual([e['kind'] for e in seen],['block']);self.assertEqual(t.hp,MAX_HP)
        t.x=450;m.begin_attack(f,'punch');seen=[]
        for _ in range(25):
            m.update(DT,{},{});seen.extend(m.impacts)
        self.assertEqual(seen,[])
    def test_y_three_contacts_sixteen_damage(self):
        m=ready('Steve','Kara');f,t=m.fighters;m.begin_attack(f,'combo');seen=[]
        for _ in range(60):
            m.update(DT,{},{});seen.extend(m.impacts)
        self.assertEqual(t.hp,MAX_HP-16);self.assertEqual(len(seen),3);self.assertEqual(f.streak,0)
