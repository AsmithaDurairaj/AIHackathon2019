#!/usr/bin/python

import sqlite3

def init():
    conn = sqlite3.connect('test.db')
    return conn;
def close(conn):
    conn.close();

def createDatabase(conn):
    print ("Opened database successfully");
    conn.execute('''CREATE TABLE test
             (empId text primary key, mouse text, keyboard text, monitor text, dockingstation text, headset text,msdn text,aws text,visio text);''')
    print ("Table created successfully");

def insert(c):
    c.execute("INSERT INTO test VALUES ('1234','yes','no','no','yes','yes','yes','no','no')")
    c.execute("INSERT INTO test VALUES ('1456','yes','no','no','no','yes','no','no','no')")
    c.execute("INSERT INTO test VALUES ('1546','yes','no','yes','yes','yes','yes','yes','yes')")
    c.execute("INSERT INTO test VALUES ('1489','no','yes','no','yes','yes','yes','yes','no')")
    c.execute("INSERT INTO test VALUES ('1589','yes','no','yes','yes','no','no','no','yes')")
    c.commit()
    print ("inserted values")

def check_eligible(conn,name,id):
    cursor = conn.execute("SELECT " +name+" from test where empId='"+id+"';")
    for row in cursor:
      return row[0]
