#!/usr/bin/env python3
"""Pousse le gold (DuckDB) vers Postgres, pour Metabase."""
import duckdb
PG = "host=localhost port=5432 dbname=soc_gold user=soc password=soc"
con = duckdb.connect("data/soc.duckdb")
con.execute("INSTALL postgres; LOAD postgres;")
con.execute(f"ATTACH '{PG}' AS pg (TYPE postgres)")
for t in ["fact_triage", "dim_regle", "dim_technique", "bridge_triage_technique"]:
    con.execute(f"DROP TABLE IF EXISTS pg.{t}")
    con.execute(f"CREATE TABLE pg.{t} AS SELECT * FROM {t}")
    n = con.execute(f"SELECT COUNT(*) FROM pg.{t}").fetchone()[0]
    print(f"pg.{t}: {n} lignes")
con.close()
print("Gold pousse vers Postgres.")
