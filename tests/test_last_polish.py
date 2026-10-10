import unittest
from combat import Match

class LastPolish(unittest.TestCase):
    def test_ranged_casts_work_at_every_spacing_and_facing_under_basic_hit(self):
        for name in ('Kara','Jay'):
            for left,right in ((25,455),(200,258),(258,200),(455,25)):
                for airborne in (False,True):
                    m=Match(name,'Steve');m.phase='fight';f,t=m.fighters
                    f.x,t.x=left,right;f.facing=1 if right>left else -1
                    if airborne:t.y=170;t.vy=-80
                    f.ready=True;m.begin_attack(f,'special')
                    m.damage(t,f,6)
                    for _ in range(110):m.update(1/60,{},{})
                    self.assertEqual(f.hp,194)
                    if name=='Jay':self.assertAlmostEqual(t.hp,130)
                    else:self.assertEqual(t.bound_by,'Kara');self.assertGreater(t.bound,0)

    def test_checkmate_has_both_success_and_avoidance_for_each_bot(self):
        for name in ('Steve','Teresa','Kara','Jay','Zen'):
            fooled=avoided=0
            for seed in range(60):
                m=Match('Zen',name,seed=seed);m.phase='fight';z,b=m.fighters
                z.x=200;b.x=258;z.ready=True;m.begin_attack(z,'special')
                recognized=None
                for _ in range(190):
                    m.update(1/60,{})
                    if m.ai_phantom_notice is not None:recognized=m.ai_phantom_notice
                    if any(e=='illusion' for e,_ in m.events):fooled+=1;break
                else:avoided+=1
            self.assertGreater(fooled,30,name)
            self.assertGreater(avoided,2,name)

    def test_recognition_does_not_reroll_during_one_activation(self):
        m=Match('Zen','Kara',seed=2);m.phase='fight';z,b=m.fighters
        z.phantom=3;z.state='phantom';m.bot(1/60);notice=m.ai_phantom_notice
        for _ in range(60):m.ai_wait=0;m.bot(1/60);self.assertEqual(m.ai_phantom_notice,notice)
        z.phantom=0;m.bot(1/60);self.assertIsNone(m.ai_phantom_notice)
