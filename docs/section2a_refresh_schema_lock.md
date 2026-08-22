# Section 2A refresh schema-lock correction

Production iPhone verification showed that Epcot historical data could return `0` on the first load and then return its real history count after switching away and back. The underlying refresh path was still executing `CREATE/ALTER TABLE ... IF NOT EXISTS` operations on `wait_times` during normal background collection.

Those schema operations can take strong PostgreSQL table locks and interfere with concurrent dashboard reads.

This correction moves schema setup to application startup and routes production refreshes through a collector that performs only Queue Times fetches and wait-time inserts. Normal refresh requests no longer run schema DDL.
