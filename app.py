from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from flask import jsonify
from flask import redirect
import datetime
import MySQLdb
import threading
from servicenow_functions import *
from database_functions import *
import mysql.connector
from config.config import *
from incident_processor1 import IncidentProcessor
from apscheduler.schedulers.background import BackgroundScheduler 



app = Flask(__name__)
app.secret_key= SECRET_KEY
# MySQL configurations
app.config['MYSQL_HOST'] = MYSQL_HOST
app.config['MYSQL_USER'] = MYSQL_USERNAME
app.config['MYSQL_PASSWORD'] = MYSQL_PASSWORD
app.config['MYSQL_DB'] = MYSQL_DATABASE
mysql = MySQL(app)
print("******************",MYSQL_HOST)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE user_name = %s AND password = %s", (username, password))
        user = cur.fetchone()
        cur.close()
        if user:
            session['username'] = username
            return redirect(url_for('index'))
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/index')
def index():
    if 'username' in session:
        teams = get_teams()
        return render_template('index.html', teams=teams)
    return redirect(url_for('login'))

@app.route('/update_users_list', methods=['GET'])
def update_users_list():
    teams = get_teams()
    users = get_users_from_servicenow()
    if isinstance(users, list):
        insert_users(users)
        message = "Users list updated successfully"
        return message
    else:
        return users
@app.route('/update_user_groups_list', methods=['GET'])
def update_user_groups_list():
    teams = get_teams()
    user_groups = get_user_groups_from_servicenow()
    group_members = get_group_members()
    if isinstance(user_groups, list):
        insert_user_groups_from_service_now(user_groups)
        message = "Groups list updated successfully"
    
    if isinstance(group_members, list):
        insert_group_members_from_service_now(group_members)
        message = "Group members list updated successfully"
        return message
    else:
        return group_members

@app.route('/teams', methods=['GET'])
def teams():
    if 'username' in session:
        teams = get_teams()
        return render_template('teams.html', teams=teams)
    return redirect(url_for('login'))

@app.route('/inc_mgmt')
def inc_mgmt():
    if 'username' in session:
        incidents = get_incidents()
        u_groups = get_groups()
        return render_template('inc_mgmt.html', incidents=incidents, u_groups=u_groups)
    return redirect(url_for('login'))

@app.route('/inc_mgmt/<string:sys_id>', methods=['GET'])
def incident_details(sys_id):
    if 'username' in session:
        incident = get_incident_detail(sys_id)
        u_groups = get_groups()
        return render_template('edit_form.html', incident=incident, u_groups=u_groups)
    return redirect(url_for('login'))

@app.route('/get-users-by-group', methods=['POST'])
def get_users_by_group_route():
    data = request.get_json()
    group_name = data['group']
    users = get_users_by_group(group_name)
    return jsonify(users=users)

@app.route('/save-incident', methods=['POST'])
def save_incident():
    if 'username' in session:
        data = request.get_json()
        sys_id = data['sys_id']
        assignment_group = data['assignmentGroup']
        assign_to = data['assignTo']
        prev_assign_to = data ['prev_assign_to']

        update_incident(sys_id, assignment_group, assign_to)
        update_service_now_incident(sys_id, assignment_group, assign_to)
        if prev_assign_to:
            with mysql.connection.cursor() as cursor:
                cursor.callproc('update_previous_workload', (prev_assign_to,))
                cursor.callproc('update_workload', (assign_to,))
                mysql.connection.commit()
        else:
            with mysql.connection.cursor() as cursor:
                cursor.callproc('update_workload', (assign_to,))
                mysql.connection.commit()
        message = "Incident has assigned to {} successfully.".format(assign_to)
        return message
    return redirect(url_for('login'))




@app.route('/teams/create', methods=['GET', 'POST'])
def create_team_route(): 
    if 'username' in session:
        users = fetch_users()
        u_groups = get_groups()  
        if request.method == 'POST':
            team_name = request.form['team_name']
            description = request.form['description']
            team_lead = request.form['team_lead']
            status = request.form['status']
            assignment_groups = request.form.getlist('assignment_group')  # Retrieve as a list
            
            if create_team(team_name, description, team_lead, status, assignment_groups):
                flash('Team created successfully!', 'success')
            else:
                flash('Failed to create team', 'error')
            
            return redirect(url_for('index'))
        
        return render_template('create_team.html', users=users, u_groups=u_groups)
    
    return redirect(url_for('login'))


@app.route('/teams/<int:team_id>', methods=['GET'])
def team_details(team_id):
    if 'username' in session:
        team, groups = get_team_details(team_id)
        u_groups = get_groups() 
        return render_template('team_details.html', team=team, groups=groups, u_groups=u_groups)
    return redirect(url_for('login'))


@app.route('/groups/<string:group_id>/<string:group_name>', methods=['GET'])
def group_details(group_id, group_name):
    if 'username' in session:
        group, users = get_group_details(group_id,group_name)
        # members = get_users_for_this_group(group_id)
        all_users = fetch_users()
        return render_template('group_details.html', group=group, users=users, all_users=all_users)
    return redirect(url_for('login'))

@app.route('/users/create/<int:group_id>', methods=['GET', 'POST'])
def create_user(group_id):
    if 'username' in session:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            create_user(group_id, username, password)
            return redirect(url_for('group_details', group_id=group_id))
        return render_template('create_user.html', group_id=group_id)
    return redirect(url_for('login'))

@app.route('/users/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'username' in session:
        delete_user(user_id)
        return redirect(url_for('group_details', group_id=group_id))
    return redirect(url_for('login'))

@app.route('/update-user', methods=['POST'])
def update_user():
    data = request.get_json()
    # print("update_user_rout data",data)
    user_id = data['userId']
    field = data['field']
    value = data['value']

    cursor = mysql.connection.cursor()
    update_query = f"UPDATE users SET {field} = {value} WHERE sys_id = '{user_id}'"
    cursor.execute(update_query)
    mysql.connection.commit()
    cursor.close()
    return jsonify({'message': 'User updated successfully'})

@app.route('/delete_member', methods=['POST'])
def delete_member():
    try:
        data = request.get_json()
        user_name = data['username']
        group_name = data['group_name']
        cursor = mysql.connection.cursor()
        cursor.callproc('FetchSysIdByUserNameAndGroupName', [user_name, group_name, ''])
        cursor.execute("SELECT @_FetchSysIdByUserNameAndGroupName_2")
        result = cursor.fetchone()
        sys_id = result[0]
        print(sys_id)
        cursor.close()
        cur = mysql.connection.cursor()
        cur.callproc('DeleteMemberFromGroup', (sys_id,))
        mysql.connection.commit()
        cur.close()
        delete_group_member_from_servicenow(sys_id)

        return redirect(request.referrer)
    except Exception as e:
        return "An error occurred: " + str(e)


@app.route('/add-member', methods=['POST'])
def add_member():
    data = request.get_json()
    group_sys_id = data['group_sys_id']
    user_sys_id = data['user_sys_id']
    data = create_group_member(group_sys_id, user_sys_id)
    insert_group_member(data.get('sys_id'), data.get('user'), data.get('group'))

    return "Member added successfully"

@app.route('/add_group', methods=['POST'])
def add_group():
    group_name = request.form['group_name']
    team_id = request.form['team_id']
    cursor = mysql.connection.cursor()
    cursor.callproc('AddGroupToTeam', (group_name, team_id))
    mysql.connection.commit()
    cursor.close()
    return "Group added successfully"


@app.route('/remove_group', methods=['POST'])
def remove_group():
    group_id = request.form['group_id']
    team_id = request.form['team_id']
    cursor = mysql.connection.cursor()
    cursor.callproc('remove_group_from_team', (group_id,))
    mysql.connection.commit()
    cursor.close()
    return "Group removed successfully"

@app.route('/delete_team', methods=['POST'])
def delete_team():
    team_id = request.form['team_id']
    cursor = mysql.connection.cursor()
    cursor.callproc('DeleteTeam', (team_id,))
    mysql.connection.commit()
    cursor.close()
    return "Team deleted successfully"

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    if 'username' in session:
        username = session['username']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE user_name = %s", (username,))
        user = cur.fetchone()
        cur.close()

        profile = {
            'ID': user[0],
            'username': user[1],
            'name': user[3],
            'email': user[4]
        }

        return render_template('profile.html', profile=profile)
    return redirect(url_for('login'))

def call_process_incident():
    processor = IncidentProcessor()
    processor.fetch_and_process_incidents()


if __name__ == '__main__':
    # model_process = multiprocessing.Process(target=call_process_incident)
    # model_process.start()
    scheduler = BackgroundScheduler(max_instances=1)
    scheduler.add_job(call_process_incident, 'interval', seconds=20)  # Adjust the interval as needed
    scheduler.start()
    app.run()