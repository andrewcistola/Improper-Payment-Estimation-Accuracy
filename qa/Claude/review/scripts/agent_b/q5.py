import duckdb
R="/tmp/claude-0/-home-claude/42cb9023-b3be-56b3-ab9a-06a6ce4302a7/scratchpad/repo"
con=duckdb.connect()
H=f"'{R}/part-c-ipm/errors/output/base/hcc_detail.parquet'"; P=f"'{R}/part-c-ipm/errors/output/base/population.parquet'"
f=990/330253
print("Part C: expected audited instances and failures per HCC code in a 990-enrollee audit")
print(con.sql(f"""SELECT h.fam, h.severe, count(*) N_k, round(count(*)*{f},1) exp_n_k,
   round(sum((h.validation<>'supported' OR p.missing_doc)::INT)*{f},2) exp_fail_k,
   round(exp(-sum((h.validation<>'supported' OR p.missing_doc)::INT)*{f}),3) p_zero_fail
   FROM {H} h JOIN {P} p ON p.unit_id=h.enrollee_id GROUP BY 1,2 ORDER BY 1,2"""))
# Does failure correlate with months / county_rate? (sim assumes no)
print(con.sql(f"""SELECT p.missing_doc OR h.validation<>'supported' AS failed, avg(p.months) m, avg(p.county_rate) cr, count(*)
  FROM {H} h JOIN {P} p ON p.unit_id=h.enrollee_id GROUP BY 1"""))
E=f"'{R}/eipm/errors/output/base/population.parquet'"
print("EIPM: expected audited errors per stratum with allocation 150/331/387/492/640")
print(con.sql(f"""SELECT stratum, count(*) N_h, avg((error_type='technical')::INT) p_t, avg((error_type='monetary')::INT) p_m,
  round(avg((error_type='monetary')::INT)*CASE stratum WHEN 'P1' THEN 150 WHEN 'P2' THEN 331 WHEN 'P3' THEN 387 WHEN 'P4' THEN 492 ELSE 640 END,1) exp_monetary_donors,
  round(avg((error_type='technical')::INT)*CASE stratum WHEN 'P1' THEN 150 WHEN 'P2' THEN 331 WHEN 'P3' THEN 387 WHEN 'P4' THEN 492 ELSE 640 END,1) exp_technical
  FROM {E} GROUP BY 1 ORDER BY 1"""))
# monetary y share of x among monetary errors (sizes), and dependence of y/x on fpl
print(con.sql(f"SELECT stratum, avg(y/x) taint, stddev(y/x), avg(true_fpl_pct/fpl_pct) FROM {E} WHERE error_type='monetary' GROUP BY 1 ORDER BY 1"))
