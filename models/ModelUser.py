from .entities.User import User


class ModelUser():

    @classmethod
    def login(self, db, user):
        try:
            cursor = db.connection.cursor()
            #sql = """SELECT email, password, tipo FROM login 
            #        WHERE email = '{}'""".format(user.email)
            #cursor.execute(sql)
            cursor.execute('SELECT * FROM login WHERE email=%s', [user.id])
            row = cursor.fetchone()
            if row != None:
                cursor.execute(('SELECT * FROM ' + row[2] + ' WHERE email=%s'), [user.id])
                otros_datos = cursor.fetchone()
                if len(otros_datos) == 4 :
                    user = User(row[0], User.check_password(row[1], user.password), row[2], otros_datos[0], otros_datos[1], otros_datos[2], None, None, row[3])
                else :    
                    user = User(row[0], User.check_password(row[1], user.password), row[2], otros_datos[0], otros_datos[1], otros_datos[2], otros_datos[4], otros_datos[5], row[3])
                return user
            else:
                return None
        except Exception as ex:
            raise Exception(ex)

    @classmethod
    def get_by_email(self, db, email):
        try:
            cursor = db.connection.cursor()
            cursor.execute('SELECT email, tipo, extension FROM login WHERE email=%s', [email])
            row = cursor.fetchone()
            if row != None:
                cursor.execute(('SELECT * FROM ' + row[1] + ' WHERE email=%s'), [email])
                otros_datos = cursor.fetchone()
                if len(otros_datos) == 4 :
                    user = User(row[0], None, row[1], otros_datos[0], otros_datos[1], otros_datos[2], None, None, row[2])
                else :    
                    user = User(row[0], None, row[1], otros_datos[0], otros_datos[1], otros_datos[2], otros_datos[4], otros_datos[5], row[2])
                return user
            else:
                return None
        except Exception as ex:
            raise Exception(ex)