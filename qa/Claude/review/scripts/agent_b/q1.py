import duckdb
R="/tmp/claude-0/-home-claude/42cb9023-b3be-56b3-ab9a-06a6ce4302a7/scratchpad/repo"
con=duckdb.connect()
for prog in ["part-c-ipm","eipm"]:
    for d in ["results","results_fixed"]:
        print("==",prog,d)
        print(con.sql(f"""SELECT domain, method, count(*) n, avg(se) mean_se, stddev_samp(estimate) emp_se,
            median((upper-lower)/2) med_hw, avg((upper-lower)/2) mean_hw, min(rep), max(rep)
            FROM '{R}/{prog}/estimation/{d}/base/estimates.parquet' GROUP BY 1,2 ORDER BY 1,2"""))
print(con.sql(f"SELECT * FROM read_json('{R}/eipm/estimation/results/base/truth.json')"))
print(con.sql(f"SELECT * FROM read_json('{R}/part-c-ipm/estimation/results/base/truth.json')"))
