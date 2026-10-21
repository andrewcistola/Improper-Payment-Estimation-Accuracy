import duckdb, numpy as np
R="/tmp/claude-0/-home-claude/42cb9023-b3be-56b3-ab9a-06a6ce4302a7/scratchpad/repo"
con=duckdb.connect(); con.execute("SET threads=2")
P=f"'{R}/perm-cert/errors/output/perm/state_elig_grid/population.parquet'"
df=con.execute(f"""SELECT state_id, stratum, count(*) N, stddev_pop((y*fmap)::DOUBLE) s_h, avg((y>0)::INT) p_err, avg((y_elig>0)::INT) p_elig,
 sum(y*fmap)/sum(x*fmap) rate FROM {P} WHERE state_id IN (1,5) GROUP BY 1,2 ORDER BY 1,2""").fetchdf()
for s,g in df.groupby('state_id'):
    raw=520*g.N*g.s_h/(g.N*g.s_h).sum()
    g=g.assign(n_raw=raw.values)
    print(g.to_string())
# beneficiaries: n payments per bene vs eligibility error
print(con.execute(f"""SELECT state_id, count(DISTINCT bene_id) benes, count(*) pay, sum(x*fmap) fed FROM {P} GROUP BY 1 ORDER BY 1""").fetchdf().to_string())
