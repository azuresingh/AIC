import MySQLdb
from flask_mysqldb import MySQL
import datetime
import mysql.connector
from myconfig import *
#from app import mysql

def is_team_name_exists(team_name):
    from app import mysql
    cursor = mysql.connection.cursor()    
    query = "SELECT COUNT(*) FROM teams WHERE team_name = %s"
    cursor.execute(query, (team_name,))
    result = cursor.fetchone()
    cursor.close()
    mysql.connection.close()
    return result[0] > 0


def insert_users(users):
    from app import mysql
    cur = mysql.connection.cursor()
    for user in users:
        active_value = 1 if user.get('active') == 'true' else 0
        try:
            cur.execute("INSERT INTO users (sys_id, user_name, password, name, email, active) VALUES (%s, %s, %s, %s, %s, %s)",
                        (user.get('sys_id'), user.get('user_name'), user.get('user_password'), user.get('name'), user.get('email'), active_value))
            mysql.connection.commit()
        except MySQLdb.IntegrityError as e:
            if e.args[0] == 1062:  # Duplicate entry error code
                continue  # Skip the record and continue with the next one
            else:
                raise  # Reraise the exception for other integrity errors
    cur.close()

def create_team(team_name, description, team_lead, status, assignment_groups):
    from app import mysql
    try:
        conn = mysql.connection
        cursor = conn.cursor()

        # Insert team into teams table
        query = "INSERT INTO teams (team_name, description, team_lead_name, status, created_on, updated_on) " \
                "VALUES (%s, %s, %s, %s, %s, %s)"
        values = (team_name, description, team_lead, status, datetime.datetime.now(), datetime.datetime.now())
        cursor.execute(query, values)
        conn.commit()

        team_id = cursor.lastrowid

        # Update team_id in assignment_group table
        update_query = "UPDATE assignment_group SET team_id = %s WHERE group_name = %s"
        update_values = [(team_id, group_name) for group_name in assignment_groups]
        cursor.executemany(update_query, update_values)
        conn.commit()

        return True  # Team created successfully
    
    except Exception as e:
        return f'Failed to create team: {e}'


def update_incident(sys_id, assignment_group, assigned_to):
    from app import mysql
    query = '''
        UPDATE incidents
        SET assignment_group = %s,
            assigned_to = %s,
            updated = %s,
            `Manually_assigned` = 1
        WHERE sys_id = %s
        '''
    current_time = datetime.datetime.now()

    with mysql.connection.cursor() as cursor:
        try:
            cursor.execute(query, (assignment_group, assigned_to, current_time, sys_id))
            mysql.connection.commit()
            print(f"Incident with sys_id {sys_id} updated successfully.")
        except mysql.connector.Error as error:
            print(f"Error updating incident: {error}")
            mysql.connection.rollback()

    
def get_incidents():
    from app import mysql
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM incidents ORDER BY incident_number DESC")
    incidents = cur.fetchall()
    cur.close()
    return incidents

def get_incident_detail(sys_id):
    from app import mysql
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM incidents WHERE sys_id = %s", (sys_id,))
    incident = cur.fetchall()
    cur.close()
    return incident


def get_teams():
    from app import mysql
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM teams")
    teams = cur.fetchall()
    cur.close()
    return teams
def fetch_users():
    from app import mysql
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users ORDER BY name ASC")
    users = cur.fetchall()
    cur.close()
    return users

def get_groups():
    from app import mysql
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM assignment_group ORDER BY group_name ASC")
    u_groups = cur.fetchall()
    cur.close()
    return u_groups
def get_users_for_this_group(group_id):
    from app import mysql
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users where group_id= group_id")
    members = cur.fetchall()
    cur.close()
    return members

def get_team_details(team_id):
    from app import mysql
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM teams WHERE id = %s", (team_id,))
    team = cur.fetchone()
    cur.execute("SELECT * FROM assignment_group WHERE team_id = %s", (team_id,))
    groups = cur.fetchall()
    cur.close()
    return team, groups

def get_group_details(group_id, group_name):
    from app import mysql
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM assignment_group WHERE sys_id = %s", (group_id,))
    group = cur.fetchone()
    cur.callproc('group_members', (group_name,))
    users = cur.fetchall()
    cur.close()
    return group, users


def create_user(group_id, username, password):
    from app import mysql
    cur = mysql.connection.cursor()
    sql = "INSERT INTO users (group_id, username, password) VALUES (%s, %s, %s)"
    values = (group_id, username, password)
    cur.execute(sql, values)
    mysql.connection.commit()
    cur.close()

def delete_user(user_id):
    from app import mysql
    cur = mysql.connection.cursor()
    sql = "DELETE FROM users WHERE id = %s"
    values = (user_id,)
    cur.execute(sql, values)
    mysql.connection.commit()
    cur.close()

def insert_group_member(sys_id, user_name, group_name):
    from app import mysql
    try:
        conn = mysql.connection
        cursor = conn.cursor()

        query = "INSERT INTO group_members (sys_id, user_name, group_name) VALUES (%s, %s, %s)"
        values = (sys_id, user_name, group_name)
        cursor.execute(query, values)
        conn.commit()
        cursor.close()

        return True  # Insertion successful

    except Exception as e:
        return f'Failed to insert group member: {e}'
    
def insert_user_groups_from_service_now(user_groups):
    from app import mysql
    cur = mysql.connection.cursor()
    for u_group in user_groups:
        active_value = 1 if u_group.get('active') == 'true' else 0
        try:
            cur.execute("INSERT INTO assignment_group (sys_id, group_name, description, manager, active, created_on) VALUES (%s, %s, %s, %s, %s, %s)",
                        (u_group.get('sys_id'), u_group.get('name'), u_group.get('description'), u_group.get('manager'), active_value, u_group.get('sys_created_on')))
            mysql.connection.commit()
        except MySQLdb.IntegrityError as e:
            if e.args[0] == 1062:  # Duplicate entry error code
                continue
            else:
                raise  # Reraise the exception for other integrity errors
    cur.close()

def insert_group_members_from_service_now(group_members):
    from app import mysql
    cur = mysql.connection.cursor()
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

def get_users_by_group(group_name):
    from app import mysql
    try:
        conn = mysql.connection
        cursor = conn.cursor()

        query = """
            SELECT u.name, u.Tier, u.FTE, u.teams_avail, u.workload
            FROM users u
            JOIN group_members gm ON u.name = gm.user_name
            JOIN assignment_group ag ON gm.group_name = ag.group_name
            WHERE ag.group_name = %s
        """

        cursor.execute(query, (group_name,))
        result = cursor.fetchall()

        # Create a list of dictionaries representing the rows
        users = []
        for row in result:
            user = {
                'name': row[0],
                'tier': row[1],
                'fte': row[2],
                'teams_avail': row[3],
                'workload': row[4]
            }
            users.append(user)

        cursor.close()
        return users

    except Exception as e:
        print(f'Failed to fetch users by group: {e}')
        return None

def insert_incident_into_database(self, sys_id, number, short_desc, assignment_group, assigned_to, urgency,A_group_score):
    from app import mysql
    conn = mysql.connection
    cursor = conn.cursor()
    query = "INSERT INTO incidents (sys_id, incident_number, description, assignment_group, assigned_to, urgency, A_group_score) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    values = [(sys_id, number, short_desc, assignment_group, assigned_to, urgency, A_group_score)]
    cursor.executemany(query, values)
    conn.commit()
    cursor.close()
    conn.close()
    print('Incident details inserted into the database:', number)
