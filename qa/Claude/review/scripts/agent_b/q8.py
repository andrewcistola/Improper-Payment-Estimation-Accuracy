# Netting check in the Part C kernel: additions landing on enrollees that also receive HCC failures
import os, sys
os.environ["NUMBA_CACHE_DIR"]="/tmp/claude-0/-home-claude/42cb9023-b3be-56b3-ab9a-06a6ce4302a7/scratchpad/agent_b/numba_cache"
R="/tmp/claude-0/-home-claude/42cb9023-b3be-56b3-ab9a-06a6ce4302a7/scratchpad/repo"
sys.path.insert(0, R+"/shared"); sys.dont_write_bytecode=True
import duckdb, numpy as np
from ipsim.engine import connect
from ipsim.simulation import load_kernel
con=connect(threads=2)
con.execute("SET VARIABLE repo_root = ?", [R]); con.execute("SET VARIABLE population_dir = ?", ["part-c-ipm/errors/output/base"])
con.execute(open(R+"/part-c-ipm/estimation/sql/40_simulation_inputs.sql").read())
K=load_kernel(R+"/part-c-ipm/estimation/simulation.py").Kernel(con,{"sim_rates":"fixed"})
strat=con.execute("SELECT stratum FROM sim_units ORDER BY unit_idx").fetchnumpy()["stratum"].astype(str)
rng=np.random.default_rng(11)
truth_under=-K.y_cents[K.y_cents<0].sum()/K.X; truth_over=K.y_cents[K.y_cents>0].sum()/K.X
res=[]
for b in range(8):
    aud=np.concatenate([rng.choice(np.flatnonzero(strat==s),330,replace=False) for s in ("low","medium","high")])
    am=np.zeros(K.units,bool); am[aud]=True
    K.prepare(1,am)
    # linear plug-in expectation of under: sum_f a_f*mild_f*sum cm over non-audited lacking f  (+ audited own under)
    cm=K.rate*K.months
    lin_under=sum(K.a_rate[f]*K.mild[f]*cm[K._recip_add[f]].sum() for f in range(10))/1000.0/K.X + (-K.y_cents[am&(K.y_cents<0)].sum())/K.X
    it=[K.iterate(aud,rng) for _ in range(60)]
    su=np.mean([r["national|under"] for r in it]); so=np.mean([r["national|over"] for r in it])
    res.append((lin_under*1e4, su*1e4, so*1e4))
res=np.array(res)
print("truth under bp %.1f over bp %.1f"%(truth_under*1e4,truth_over*1e4))
print("per audit: linear-expectation under | simulated under | simulated over (bp)"); print(np.round(res,1))
print("mean shortfall of simulated under vs its own linear expectation: %.1f bp (%.1f%%)"%((res[:,1]-res[:,0]).mean()*1, (res[:,1]/res[:,0]-1).mean()*100))
