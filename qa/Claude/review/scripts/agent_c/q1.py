import duckdb
R="/tmp/claude-0/-home-claude/42cb9023-b3be-56b3-ab9a-06a6ce4302a7/scratchpad/repo"
con=duckdb.connect()
print(con.execute(f"""SELECT method, domain, count(*) n, avg(estimate) mean, stddev(estimate) sd_est, avg(se) mean_se, avg(upper-lower)/2 hw
FROM '{R}/part-d-ipm/estimation/results/base/estimates.parquet' WHERE domain='national|gross' GROUP BY 1,2 ORDER BY 1""").fetchdf().to_string())
print(con.execute(f"""SELECT method, rep, estimate, lower, upper FROM '{R}/part-d-ipm/estimation/results/base/estimates.parquet' WHERE domain='national|gross' AND method in ('expansion','simulation') ORDER BY rep, method""").fetchdf().to_string())
