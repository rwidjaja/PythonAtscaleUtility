import jaydebeapi

conn = jaydebeapi.connect(
    "org.postgresql.Driver",
    "jdbc:postgresql://ubuntu-atscale.atscaledomain.com:15432/Sales Insights - Postgres",
    ["admin", "password"],
    "/Users/rudywidjaja/Library/tableau/Drivers/postgresql-42.7.3.jar"
)

curs = conn.cursor()
curs.execute("""
    SELECT "Internet Sales Cube".d_city AS d_city, SUM(Salesamount1)
    FROM "Internet Sales Cube - Postgres" "Internet Sales Cube"
    GROUP BY 1
""")
for row in curs.fetchall():
    print(row)
curs.close()
conn.close()
