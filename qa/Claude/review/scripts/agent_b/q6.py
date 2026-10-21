import duckdb, numpy as np
R="/tmp/claude-0/-home-claude/42cb9023-b3be-56b3-ab9a-06a6ce4302a7/scratchpad/repo"
con=duckdb.connect()
P=f"'{R}/part-c-ipm/errors/output/base/population.parquet'"
d=con.sql(f"SELECT stratum, abs(y)::DOUBLE y, x::DOUBLE x, greatest(-y,0)::DOUBLE u FROM {P}").fetchnumpy()
X=d["x"].sum(); Y=d["y"].sum(); th=Y/X
alloc={"low":330,"medium":330,"high":330}
def design_se(resid):
    v=0
    for h,n in alloc.items():
        m=d["stratum"]==h; N=m.sum()
        v+=N*N*(1-n/N)*resid[m].var(ddof=1)/n
    return np.sqrt(v)
print("Part C exact design SE (bp): expansion(gross)",design_se(d["y"])/X*1e4,
      " ratio(gross)",design_se(d["y"]-th*d["x"])/X*1e4,
      " expansion(under)",design_se(d["u"])/X*1e4)
# EIPM
E=f"'{R}/eipm/errors/output/base/population.parquet'"
e=con.sql(f"SELECT stratum, y::DOUBLE y, x::DOUBLE x, y_technical::DOUBLE yt FROM {E}").fetchnumpy()
X=e["x"].sum(); th=e["y"].sum()/X
alloc={"P1":150,"P2":331,"P3":387,"P4":492,"P5":640}
def dse(resid):
    v=0
    for h,n in alloc.items():
        m=e["stratum"]==h; N=m.sum(); v+=N*N*(1-n/N)*resid[m].var(ddof=1)/n
    return np.sqrt(v)
print("EIPM exact design SE (bp): expansion(gross)",dse(e["y"])/X*1e4," ratio",dse(e["y"]-th*e["x"])/X*1e4, " technical", dse(e["yt"])/X*1e4)
