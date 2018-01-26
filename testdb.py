import psycopg2
import sys
 
 
con = None
 
try:
    con = psycopg2.connect("host='localhost' dbname='testdb' user='spotify' password=''")   
    cur = con.cursor()
    cur.execute("CREATE TABLE Products(Id INTEGER PRIMARY KEY, Name VARCHAR(20), Price INT)")
    cur.execute("INSERT INTO Products VALUES(1,'Milk',5)")
    cur.execute("INSERT INTO Products VALUES(2,'Sugar',7)")
    cur.execute("INSERT INTO Products VALUES(3,'Coffee',3)")
    cur.execute("INSERT INTO Products VALUES(4,'Bread',5)")
    cur.execute("INSERT INTO Products VALUES(5,'Oranges',3)")
    con.commit()
except psycopg2.DatabaseError as e:
    if con:
        con.rollback()
 
    print('Error ', str(e))
    sys.exit(1)
 
finally:   
    if con:
        con.close()
