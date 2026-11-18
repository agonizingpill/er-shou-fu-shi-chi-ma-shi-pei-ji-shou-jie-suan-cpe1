from .models import *
from .common import *
def measure(s,d):
 c=lock(s);g=garment(s,d['garment_id']);a=get(s,Agreement,g.agreement_id)
 if g.state not in ['unmeasured','listed'] or time(c.now)>=time(a.ends):fail('仅在有效寄售期未留衣前可实测')
 prev=[x for x in rows(s,Measurement) if x.garment_id==g.id]
 if prev:
  p=prev[-1]
  inside=d['chest_min']>=p.chest_min and d['chest_max']<=p.chest_max and d['shoulder_min']>=p.shoulder_min and d['shoulder_max']<=p.shoulder_max
  narrower=d['chest_min']>p.chest_min or d['chest_max']<p.chest_max or d['shoulder_min']>p.shoulder_min or d['shoulder_max']<p.shoulder_max
  if not(inside and narrower):fail('复量须在原读数范围内至少缩小半厘米')
 x=Measurement(**d);s.add(x)
 if g.state=='unmeasured':g.state='listed'
 s.flush();return x
def profile(s,d):
 lock(s);x=FitProfile(**d);s.add(x);s.flush();return x
def assess(s,d):
 lock(s);g=garment(s,d['garment_id']);get(s,FitProfile,d['profile_id'])
 ms=[x for x in rows(s,Measurement) if x.garment_id==g.id]
 if not ms:fail('未实测服饰不得推荐尺码')
 if g.state not in ['listed','held']:fail('服饰不在可试穿状态')
 m=ms[-1]
 old=[x for x in rows(s,FitAssessment) if x.garment_id==g.id and x.profile_id==d['profile_id'] and x.measurement_id==m.id]
 if old:
  x=old[-1]
  if x.state=='failed':x.state='queued';x.error='';s.flush()
  return x
 x=FitAssessment(garment_id=g.id,profile_id=d['profile_id'],measurement_id=m.id);s.add(x);s.flush();return x
