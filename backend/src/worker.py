import os,time,pathlib,logging
import redis
from .database import Session
from .models import FitAssessment,Measurement,FitProfile
from .common import lock,rows,get,dump
from .fit_model import predict
q=redis.from_url(os.environ['REDIS_URL'],decode_responses=True,socket_connect_timeout=1,socket_timeout=4)
def requeue():
 try:
  with Session() as s:ids=[x.id for x in rows(s,FitAssessment) if x.state=='queued']
 except Exception:logging.exception('requeue scan failed');return
 for i in ids:
  try:q.rpush('resale:fit',i)
  except redis.RedisError:logging.warning('Redis interrupted, requeue paused');break
requeue()
idle=0
while True:
 pathlib.Path('/artifacts/resale-heartbeat').write_text(str(time.time()))
 try:item=q.blpop('resale:fit',timeout=2)
 except redis.RedisError:
  logging.warning('Redis interrupted, retrying');time.sleep(1);continue
 if not item:
  idle+=1
  if idle%15==0:requeue()
  continue
 with Session() as s:
  lock(s);x=s.get(FitAssessment,int(item[1]))
  if not x or x.state!='queued':continue
  try:
   m=get(s,Measurement,x.measurement_id);p=get(s,FitProfile,x.profile_id);x.result=predict(dump(m),dump(p));x.state='ready'
  except Exception as e:x.state='failed';x.error=str(e)[:500];logging.exception('fit failed')
  s.commit()
