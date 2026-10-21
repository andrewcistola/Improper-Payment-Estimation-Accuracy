import duckdb
R="/tmp/claude-0/-home-claude/42cb9023-b3be-56b3-ab9a-06a6ce4302a7/scratchpad/repo"
con=duckdb.connect()
P=f"'{R}/part-c-ipm/errors/output/base/population.parquet'"
H=f"'{R}/part-c-ipm/errors/output/base/hcc_detail.parquet'"
print(con.sql(f"""SELECT count(*) n, avg((y>0)::INT) p_over, avg((y<0)::INT) p_under, avg(missing_doc::INT) p_md,
  avg((error_type='missing_documentation')::INT) p_md2, sum(y) FILTER (WHERE y<0)/sum(x) under_rate,
  sum(y) FILTER (WHERE y>0)/sum(x) over_rate, avg(n_hcc) mean_hcc, avg(months) FROM {P}"""))
print(con.sql(f"SELECT stratum, count(*), avg((y>0)::INT), avg((y<0)::INT), avg(n_hcc) FROM {P} GROUP BY 1 ORDER BY 1"))
# MD clustering: among failed HCC instances, share due to MD
print(con.sql(f"""SELECT h.validation, p.missing_doc, count(*) FROM {H} h JOIN {P} p ON p.unit_id=h.enrollee_id GROUP BY 1,2 ORDER BY 1,2"""))
# how many HCC instances per MD enrollee
print(con.sql(f"SELECT avg(n_hcc), count(*) FROM {P} WHERE missing_doc"))
# expected netting loss: for enrollees with an overpayment, what would an addition be worth? approx a_f*mild*rate*months
print(con.sql(f"""SELECT sum(y) FILTER (WHERE y<0) AS under_dollars, sum(x) X FROM {P}"""))
