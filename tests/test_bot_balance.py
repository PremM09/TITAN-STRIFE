"""Behavioral regressions for the active CPU and instant Field Aid revision."""
import unittest
from combat import Match, ROSTER

DT=1/60

class BotBalance(unittest.TestCase):
    def test_each_cpu_can_earn_and_use_special_against_paced_attacks(self):
        for name in ROSTER:
            uses=0
            for seed in range(4):
                m=Match('Steve' if name!='Steve' else 'Kara',name,seed=seed)
                m.phase='fight';earned=False;spent=0
                for frame in range(60*60):
                    p,b=m.fighters;delta=b.x-p.x;action={}
                    if abs(delta)>62:action['move']=1 if delta>0 else -1
                    elif frame%30==0 and p.state=='idle' and p.stun<=0:action['attack']='punch'
                    m.update(DT,action)
                    for event,who in m.events:
                        if who==name and event=='ready':earned=True
                        if who==name and event=='special':
                            self.assertTrue(earned,name+' received an unearned special')
                            spent+=1;uses+=1
                    if m.phase!='fight':break
                self.assertLessEqual(spent,1)
            self.assertGreater(uses,0,name)

    def test_recovery_does_not_add_a_second_idle_pause(self):
        m=Match('Steve','Kara',seed=1);m.phase='fight'
        b=m.fighters[1];m.ai_wait=.15
        m.begin_attack(b,'kick')
        for _ in range(20):m.update(DT,{})
        self.assertEqual(m.ai_wait,0)
        self.assertEqual(m.ai_action,{})

    def test_cpu_stays_active_and_uses_defense_under_pressure(self):
        for name in ROSTER:
            idle=frames=blocks=0
            for seed in range(4):
                m=Match('Steve' if name!='Steve' else 'Kara',name,seed=seed);m.phase='fight'
                for _ in range(60*60):
                    p,b=m.fighters;delta=b.x-p.x
                    action={'move':1 if delta>0 else -1} if abs(delta)>62 else {'attack':'punch'}
                    m.update(DT,action);frames+=1
                    idle+=int(b.state=='idle' and not b.moving and not b.blocking and b.stun<=0 and b.bound<=0)
                    blocks+=sum(event=='block' and who==name for event,who in m.events)
                    if m.phase!='fight':break
            self.assertLess(idle/frames,.22,name)
            self.assertGreater(blocks,0,name)

    def test_kara_waits_out_checkmate_and_teresa_saves_full_health_kit(self):
        m=Match('Zen','Kara',seed=3);m.phase='fight';z,k=m.fighters
        m.ai_phantom_notice=True;m.ai_phantom_delay=0;z.phantom=3;z.state='phantom';z.x=200;k.x=260
        safe=0
        for _ in range(30):
            m.ai_wait=0
            safe+=not m.bot(DT).get('attack')
        self.assertGreater(safe,20)
        m=Match('Steve','Teresa',seed=3);m.phase='fight';p,t=m.fighters
        t.ready=True;m.ai_wait=0
        self.assertNotEqual(m.bot(DT).get('attack'),'special')
        t.hp=180;m.ai_wait=0
        m.update(DT,{})
        self.assertEqual(t.hp,200);self.assertTrue(t.used)

    def test_cpu_punishes_nearby_jay_chant_but_basic_hit_does_not_cancel(self):
        m=Match('Jay','Kara',seed=3);m.phase='fight';j,k=m.fighters
        j.x=200;k.x=258;j.ready=True;m.ai_wait=0
        m.begin_attack(j,'special')
        for _ in range(20):m.update(DT,{})
        self.assertTrue(j.used);self.assertLess(j.hp,200)
        self.assertEqual(j.attack,'Jay')

    def test_near_charged_streak_does_not_skip_cpu_breather(self):
        for name,burst in [('Steve',3),('Kara',4),('Zen',5)]:
            m=Match('Teresa',name,seed=8);m.phase='fight'
            p,b=m.fighters;p.x=200;b.x=258;b.streak=4
            m.ai_wait=0;m.ai_burst=burst
            self.assertNotIn('attack',m.bot(DT))
            self.assertEqual(m.ai_burst,0)
            self.assertGreaterEqual(m.ai_wait,.20)
            self.assertEqual(b.streak,4)

    def test_jay_and_kara_share_basic_cpu_pressure(self):
        for seed in range(20):
            actions=[]
            for name in ('Kara','Jay'):
                m=Match('Steve',name,seed=seed);m.phase='fight'
                p,b=m.fighters;p.x=200;b.x=258;m.ai_wait=0
                actions.append((m.bot(DT),m.ai_wait))
            self.assertEqual(actions[0],actions[1])
