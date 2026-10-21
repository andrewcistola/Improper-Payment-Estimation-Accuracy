import duckdb, numpy as np
R="/tmp/claude-0/-home-claude/42cb9023-b3be-56b3-ab9a-06a6ce4302a7/scratchpad/repo"
con=duckdb.connect()
# 1. DECIMAL(38,6)*DECIMAL(38,6) behaviour
print(con.sql("SELECT typeof(a*a), a*a FROM (SELECT 123456.123456::DECIMAL(38,6) a)"))
print(con.sql("SELECT typeof(sum(a*a)) FROM (SELECT 123456.123456::DECIMAL(38,6) a)"))
# 2. SRS inclusion uniformity for dense ids with the fast stream (EIPM-like), 3000 reps of 20 from 1000
for f in ["00_rng.sql"]:
    con.execute(open(f"{R}/shared/sql/lib/{f}").read())
r=con.sql("""WITH s AS (SELECT r.r, u.i FROM range(1,3001) r(r), range(1,1001) u(i)
  QUALIFY row_number() OVER (PARTITION BY r.r ORDER BY u01f(rbase(20261016,'srs',r.r,0), u.i), u.i) <= 20)
  SELECT i, count(*) c FROM s GROUP BY i""").fetchnumpy()
c=r["c"]; exp=3000*20/1000
chi=((c-exp)**2/exp).sum(); print("inclusion chi2 =",round(chi,1),"df=999 (mean 999, sd 44.7)", "min/max", c.min(), c.max())
# serial correlation in u01f for consecutive k
u=con.sql("SELECT u01f(rbase(1,'b',2,0), i) u FROM range(200000) t(i)").fetchnumpy()["u"]
print("lag1 corr", np.corrcoef(u[:-1],u[1:])[0,1], "lag2", np.corrcoef(u[:-2],u[2:])[0,1])
# cross-rep correlation of the same unit's key across reps (should be ~0)
a=con.sql("SELECT u01f(rbase(1,'srs',1,0), i) u FROM range(1,100001) t(i)").fetchnumpy()["u"]
b=con.sql("SELECT u01f(rbase(1,'srs',2,0), i) u FROM range(1,100001) t(i)").fetchnumpy()["u"]
print("cross-rep corr", np.corrcoef(a,b)[0,1])
# u01 string hash serial corr
u=con.sql("SELECT u01(42,'x',i) u FROM range(200000) t(i)").fetchnumpy()["u"]
print("u01 lag1", np.corrcoef(u[:-1],u[1:])[0,1])
# 3. regression df claim: sanity
from scipy import stats
print("t(972)", stats.t.ppf(0.975,972), "t(975)", stats.t.ppf(0.975,975))
