import os, sys, json
R="/tmp/claude-0/-home-claude/42cb9023-b3be-56b3-ab9a-06a6ce4302a7/scratchpad/repo"
sys.path.insert(0, R+"/shared"); sys.dont_write_bytecode=True
import numpy as np, yaml, time
from ipsim.engine import connect
from ipsim.simulation import load_kernel
con=connect(threads=2)
con.execute("SET VARIABLE repo_root = ?", [R]); con.execute("SET VARIABLE population_dir = ?", ["eipm/errors/output/base"])
con.execute(open(R+"/eipm/estimation/sql/40_simulation_inputs.sql").read())
cfg=yaml.safe_load(open(R+"/eipm/errors/config.yaml"))["defaults"]
K=load_kernel(R+"/eipm/estimation/simulation.py").Kernel(con,{**cfg,"sim_rates":"fixed"})
alloc={0:150,1:331,2:387,3:492,4:640}
rng=np.random.default_rng(5); t0=time.time()
y=K.improper_cents(K.finding, np.where(K.finding==1,K.true_fpl,K.fpl))
truth={k:v.sum()/K.X for k,v in y.items()}
ests=[]; ratio=[]
for b in range(300):
    aud=np.concatenate([rng.choice(np.flatnonzero(K.kind==h),alloc[h],replace=False) for h in alloc])
    am=np.zeros(K.units,bool); am[aud]=True
    K.prepare(1,am)
    it=[K.iterate(aud,rng) for _ in range(12)]
    ests.append([np.mean([r[f"national|{k}"] for r in it]) for k in ("gross","technical","monetary")])
    ratio.append(y["gross"][aud].astype(float).sum()/K.x[aud].sum())
e=np.array(ests)
print("elapsed",round(time.time()-t0),"s")
print("truth bp", {k:round(v*1e4,1) for k,v in truth.items()})
print("EIPM fixed-rate sim point estimator: mean bp", np.round(e.mean(0)*1e4,1), " sampling SD bp", np.round(e.std(0,ddof=1)*1e4,2), "(includes ~12-iter MC noise)")
print("ratio estimator sampling SD bp %.2f  mean %.1f"%(np.std(ratio,ddof=1)*1e4, np.mean(ratio)*1e4))
