from typing import Dict
import pymysql


class DatabaseMySql:
    def __init__(self):
        host = "127.0.0.1"
        user = "root"
        password = ""
        db = "nextfac_bd"
        self.con = pymysql.connect(host=host, user=user, password=password, db=db, cursorclass=pymysql.cursors.
                                   DictCursor)
        self.cur = self.con.cursor()


    def insert(self, data: Dict):
        self.cur.execute()
        #self.cur.execute("SELECT first_name, last_name, gender FROM employees LIMIT 50")
        #result = self.cur.fetchall()
        #Database.
        #Database.insert(data)

