# -*- coding: utf-8 -*-
import hashlib
import pymysql


def password_encryption(password: str) -> str:
    hlmd5 = hashlib.md5()
    hlmd5.update(password.encode('utf-8'))
    return hlmd5.hexdigest()


class InfoManager():
    def __init__(self, db_host: str, db_user: str, db_name: str, db_password: str, db_table_name: str):
        self.__db_host = db_host
        self.__db_user = db_user
        self.__db_name = db_name
        self.__db_password = db_password
        self.__db_table_name = db_table_name
    
    def insert(self, student_id: str, password: str, qq_id: str):
        try:
            db = pymysql.connect(
                self.__db_host, self.__db_user, self.__db_password, self.__db_name
            )
            cursor = db.cursor()
            try:
                sql = """
                INSERT INTO {}(student_id, password, qq_id)
                VALUES ('{}', '{}', '{}')
                """.format(self.__db_table_name, student_id, password, qq_id)
                cursor.execute(sql)
                db.commit()
                db.close()
                return (True, '操作成功')
            except:
                db.rollback()
                db.close()
                return (False, '数据插入失败')
        except:
            return (False, '数据库连接失败')

    def query_qqid(self, qq_id: str):
        try:
            db = pymysql.connect(
                self.__db_host, self.__db_user, self.__db_password, self.__db_name
            )
            cursor = db.cursor()
            try:
                sql = """
                SELECT * FROM {}
                WHERE qq_id = '{}'
                """.format(self.__db_table_name, qq_id)
                cursor.execute(sql)
                db.close()
                return (True, cursor.fetchone())
            except:
                db.close()
                return (False, '数据查询失败')
        except:
            return (False, '数据库连接失败')

    def delete_qqid(self, qq_id: str):
        try:
            db = pymysql.connect(
                self.__db_host, self.__db_user, self.__db_password, self.__db_name
            )
            cursor = db.cursor()
            try:
                sql = """
                DELETE FROM {}
                WHERE qq_id = {}
                """.format(self.__db_table_name, qq_id)
                cursor.execute(sql)
                db.commit()
                db.close()
                return (True, '操作成功')
            except:
                db.rollback()
                db.close()
                return (False, '数据删除失败')
        except:
            return (False, '数据库连接失败')

