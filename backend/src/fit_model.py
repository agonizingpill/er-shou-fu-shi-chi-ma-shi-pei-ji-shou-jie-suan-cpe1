import hashlib,json
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import balanced_accuracy_score,confusion_matrix

def half_grid(lo,hi):
 n=int(round((hi-lo)*2));return [lo+i*.5 for i in range(n+1)]

def predict(measurement,profile):
 rng=np.random.default_rng(42);X=[];y=[]
 for cls in ['合身','偏紧','偏松']:
  for i in range(100):
   elasticity=float(rng.uniform(0,1));cut=int(rng.integers(0,3));ease=float(rng.uniform(5,12) if cls=='合身' else rng.uniform(-5,1) if cls=='偏紧' else rng.uniform(17,26));shoulder=float(rng.uniform(.5,2.5) if cls=='合身' else rng.uniform(-3,-.5) if cls=='偏紧' else rng.uniform(4,7));X.append([ease,shoulder,elasticity,cut]);y.append(cls)
 ids=np.arange(len(y));tr,te=train_test_split(ids,test_size=.25,stratify=y,random_state=42);X=np.array(X);y=np.array(y);model=Pipeline([('scale',StandardScaler()),('knn',KNeighborsClassifier(n_neighbors=5,weights='distance'))]);model.fit(X[tr],y[tr]);pred=model.predict(X[te])
 chests=half_grid(measurement['chest_min'],measurement['chest_max']);shoulders=half_grid(measurement['shoulder_min'],measurement['shoulder_max']);points=[[c,s]for c in chests for s in shoulders];feats=[[c-profile['chest'],s-profile['shoulder'],measurement['elasticity'],measurement['cut']]for c,s in points];labels=model.predict(feats)
 distinct=[str(k)for k in model.classes_ if (labels==k).any()];counts={str(k):int((labels==k).sum())for k in model.classes_ if (labels==k).any()};label=distinct[0]if len(distinct)==1 else'不一致';readings={}
 for k in distinct:readings[k]=points[int(np.argmax(labels==k))]
 mid=[(measurement['chest_min']+measurement['chest_max'])/2-profile['chest'],(measurement['shoulder_min']+measurement['shoulder_max'])/2-profile['shoulder'],measurement['elasticity'],measurement['cut']];probs=model.predict_proba([mid])[0]
 return {'algorithm':'StandardScaler+KNeighborsClassifier(k=5,distance)','seed':42,'label':label,'consistent':len(distinct)==1,'grid':{'step':.5,'chest':[measurement['chest_min'],measurement['chest_max']],'shoulder':[measurement['shoulder_min'],measurement['shoulder_max']],'points':len(points),'counts':counts},'readings':readings,'features':mid,'probabilities':{str(k):round(float(v),6) for k,v in zip(model.classes_,probs)},'balanced_accuracy':float(balanced_accuracy_score(y[te],pred)),'confusion_matrix':confusion_matrix(y[te],pred,labels=model.classes_).tolist(),'classes':model.classes_.tolist(),'train_count':len(tr),'holdout_count':len(te),'train_ids':tr.tolist(),'holdout_ids':te.tolist(),'training_sha256':hashlib.sha256(X.tobytes()+y.tobytes()).hexdigest(),'source_sha256':hashlib.sha256(json.dumps([measurement,profile],sort_keys=True).encode()).hexdigest(),'note':'模拟标注训练，用于辅助试衣，不保证真实穿着舒适度'}
