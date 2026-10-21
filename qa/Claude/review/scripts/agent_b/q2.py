import duckdb
R="/tmp/claude-0/-home-claude/42cb9023-b3be-56b3-ab9a-06a6ce4302a7/scratchpad/repo"
con=duckdb.connect()
for prog in ["part-c-ipm","eipm"]:
    print("==",prog)
    rows=con.sql(f"""SELECT domain, method, round(avg(se)*1e4,3) mean_se_bp, round(stddev_samp(estimate)*1e4,3) emp_se_bp,
        round(avg(estimate)*1e4,2) mean_est_bp, round(median(estimate)*1e4,2) med_est_bp,
        round(avg((upper-lower)/2)/avg(se),3) hw_over_se
        FROM '{R}/{prog}/estimation/results/base/estimates.parquet' GROUP BY 1,2 ORDER BY 1,2""").fetchall()
    for r in rows: print(r)
# across-method correlation of estimates per rep (same audit)
print(con.sql(f"""WITH e AS (SELECT * FROM '{R}/part-c-ipm/estimation/results/base/estimates.parquet' WHERE domain='national|gross')
SELECT a.rep, round(a.estimate*1e4,1) ratio, round(b.estimate*1e4,1) sim, round(c.estimate*1e4,1) reg, round(d.estimate*1e4,1) expn
FROM e a JOIN e b USING(rep) JOIN e c USING(rep) JOIN e d USING(rep)
WHERE a.method='ratio' AND b.method='simulation' AND c.method='regression' AND d.method='expansion' ORDER BY rep""").fetchall())
