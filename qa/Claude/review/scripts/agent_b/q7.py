# True sampling SD of the Part C simulation's plug-in point estimator, by Monte Carlo over 400 stratified audits
import duckdb, numpy as np
R="/tmp/claude-0/-home-claude/42cb9023-b3be-56b3-ab9a-06a6ce4302a7/scratchpad/repo"
con=duckdb.connect()
P=f"'{R}/part-c-ipm/errors/output/base/population.parquet'"; H=f"'{R}/part-c-ipm/errors/output/base/hcc_detail.parquet'"
u=con.sql(f"SELECT unit_id, stratum, (county_rate*months)::DOUBLE cm, missing_doc, add_fam, add_coef::DOUBLE add_coef, y::DOUBLE y, x::DOUBLE x FROM {P} ORDER BY unit_id").fetchnumpy()
h=con.sql(f"""SELECT h.enrollee_id, h.fam, h.severe, h.coef_paid::DOUBLE paid, (h.coef_severe-h.coef_mild)::DOUBLE mv, h.validation, p.missing_doc md
   FROM {H} h JOIN {P} p ON p.unit_id=h.enrollee_id ORDER BY h.enrollee_id""").fetchnumpy()
uid=np.asarray(u["unit_id"]); n=len(uid); X=u["x"].sum()
row_unit=np.searchsorted(uid, np.asarray(h["enrollee_id"]))
fam=np.array([ord(f)-65 for f in h["fam"].astype(str)]); hcc=fam*2+h["severe"].astype(int)
val=h["validation"].astype(str); md=h["md"].astype(bool)
failed=(val!="supported")|md
loss=np.where(md|(val=="deleted"), h["paid"], np.where(val=="hierarchy_move", h["mv"], 0.0))
cm=u["cm"]; cm_row=cm[row_unit]
N_k=np.bincount(hcc,minlength=20)
famcoef=con.sql("SELECT * FROM (VALUES ('A',0.105),('B',0.191),('C',0.250),('D',0.299),('E',0.318),('F',0.155),('G',0.209),('H',0.330),('I',0.441),('J',0.598)) t(f,c) ORDER BY f").fetchnumpy()["c"]
fam_mask=np.zeros(n,dtype=np.int64); np.bitwise_or.at(fam_mask,row_unit,1<<fam)
add_fam=np.array([-1 if f is None else ord(f)-65 for f in u["add_fam"].tolist()])
strat=u["stratum"].astype(str)
# population cm sums by HCC and by family-lacking for additions
cm_by_hcc=np.bincount(hcc,weights=cm_row,minlength=20)
lacks_cm=np.array([cm[((fam_mask>>f)&1)==0].sum() for f in range(10)])
rng=np.random.default_rng(0); ests=[]; ratios=[]
idx_by={s:np.flatnonzero(strat==s) for s in ("low","medium","high")}
for b in range(2000):
    aud=np.concatenate([rng.choice(idx_by[s],330,replace=False) for s in idx_by])
    am=np.zeros(n,bool); am[aud]=True
    ar=am[row_unit]
    n_k=np.bincount(hcc[ar],minlength=20); f_k=np.bincount(hcc[ar&failed],minlength=20)
    L_k=np.bincount(hcc[ar&failed],weights=loss[ar&failed],minlength=20)/np.maximum(f_k,1)
    p_k=f_k/np.maximum(n_k,1)
    over=(p_k*L_k*cm_by_hcc).sum()          # expected overpayment dollars (linearized, ignores audited-kept & netting)
    a_f=np.array([(am&(add_fam==f)).sum()/max((am&(((fam_mask>>f)&1)==0)).sum(),1) for f in range(10)])
    under=(a_f*famcoef*lacks_cm).sum()
    ests.append(((over+under)/X,(over-under)/X,over/X,under/X))
    w=n/990; ratios.append(np.abs(u["y"][aud]).sum()/u["x"][aud].sum())
e=np.array(ests)
print("plug-in simulation estimator, SD over 2000 audits (bp): gross %.1f net %.1f over %.1f under %.1f"%tuple(e.std(0,ddof=1)*1e4))
print("mean (bp): gross %.1f over %.1f under %.1f ; truth gross %.1f over %.1f under %.1f"%(e[:,0].mean()*1e4,e[:,2].mean()*1e4,e[:,3].mean()*1e4, np.abs(u["y"]).sum()/X*1e4, u["y"][u["y"]>0].sum()/X*1e4, -u["y"][u["y"]<0].sum()/X*1e4))
print("ratio estimator SD over same audits (bp): %.1f"%(np.std(ratios,ddof=1)*1e4))
