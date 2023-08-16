import MySQLdb
from flask_mysqldb import MySQL
import datetime
import mysql.connector
from myconfig import *
mysql = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USERNAME,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
        )



def insert_user_groups_from_service_now(user_groups):
    cur = mysql.cursor()
    for u_group in user_groups:
        active_value = 1 if u_group.get('active') == 'true' else 0
        try:
            cur.execute("INSERT INTO assignment_group (sys_id, group_name, description, manager, active, created_on) VALUES (%s, %s, %s, %s, %s, %s)",
                        (u_group.get('sys_id'), u_group.get('name'), u_group.get('description'), u_group.get('manager'), active_value, u_group.get('sys_created_on')))
            mysql.commit()
        except MySQLdb.IntegrityError as e:
            if e.args[0] == 1062:  # Duplicate entry error code
                continue
            else:
                raise  # Reraise the exception for other integrity errors
    cur.close()

def insert_group_members_from_service_now(group_members):
    cur = mysql.cursor()
    for group_member in group_members:
        sys_id = group_member.get('sys_id', '')
        user_name = group_member.get('user', '')
        group_name = group_member.get('group', '')
        try:
            cur.execute("INSERT INTO group_members (sys_id, user_name, group_name) VALUES (%s, %s, %s)",
                        (sys_id, user_name, group_name))
            mysql.connection.commit()
        except MySQLdb.IntegrityError as e:
            if e.args[0] == 1062:  
                continue  
            else:
                raise  # Reraise the exception for other integrity errors
    cur.close()

def insert_incident_into_database( sys_id, number, short_desc, assignment_group, assigned_to, urgency,A_group_score):
    cursor = mysql.cursor()
    query = "INSERT INTO incidents (sys_id, incident_number, description, assignment_group, assigned_to, urgency, A_group_score) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    values = [(sys_id, number, short_desc, assignment_group, assigned_to, urgency, A_group_score)]
    cursor.executemany(query, values)
    mysql.commit()
    cursor.close()
  
    print('Incident details inserted into the database:', number)
