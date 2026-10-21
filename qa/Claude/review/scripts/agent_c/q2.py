import duckdb, numpy as np
R="/tmp/claude-0/-home-claude/42cb9023-b3be-56b3-ab9a-06a6ce4302a7/scratchpad/repo"
con=duckdb.connect(); con.execute("SET threads=2")
P=f"'{R}/part-d-ipm/errors/output/base/pde_detail.parquet'"
cut=con.execute(f"SELECT quantile_cont(gdc_submitted::DOUBLE,0.10) FROM {P} WHERE NOT ltc").fetchone()[0]
print("low cut",cut)
df=con.execute(f"""
WITH r AS (SELECT CASE WHEN ltc THEN 0 WHEN gdc_submitted<= {cut} THEN 1 ELSE 2 END h,
   (gdc_submitted-gdc_corrected)::DOUBLE d, gdc_submitted::DOUBLE s, active, specialty FROM {P}),
a AS (SELECT h, sum(d)/sum(s) rh, avg(s) sbar, count(*) N, sum(s) S, sum(d) D, avg(active::INT) p, stddev_pop(d) sd_d,
      sum(d) FILTER (WHERE specialty)/sum(d) spec_err_share, avg(specialty::INT) spec_pde_share FROM r GROUP BY h)
SELECT a.h, any_value(a.rh) rh, any_value(a.sbar) sbar, any_value(a.N) N, any_value(a.S) S, any_value(a.D) D, any_value(a.p) p, any_value(a.sd_d) sd_d,
       any_value(spec_err_share) spec_err_share, any_value(spec_pde_share) spec_pde_share,
       var_pop(r.d - a.rh*r.s)/any_value(a.sbar)^2 AS relvar_unit FROM r JOIN a USING (h) GROUP BY a.h ORDER BY a.h""").fetchdf()
print(df.to_string())
N=df.N.values; sd=df.sd_d.values
n=5000*N*sd/(N*sd).sum(); print("Neyman n_h approx", np.round(n))
for i,row in df.iterrows():
    nh=max(2,round(n[i])); 
    rel_se_r=np.sqrt(row.relvar_unit/nh)/row.rh
    rel_se_p=np.sqrt(row.p*(1-row.p)/nh)/row.p
    print(f"h={row.h} n_h={nh} rel SE dollar rate r_h={rel_se_r:.3f}  rel SE count rate p_h={rel_se_p:.3f}  err-dollar share={row.D/df.D.sum():.3f}  expected errors in sample={nh*row.p:.1f}")
