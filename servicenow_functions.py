import requests
from myconfig import *

INSTANCE_URL = SERVICENOW_INSTANCE
USERNAME = SERVICENOW_USERNAME
PASSWORD = SERVICENOW_PASSWORD

import requests


def update_assignment_group_in_servicenow( sys_id, assignment_group):
    url = INSTANCE_URL +'/api/now/table/incident/'+ sys_id
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    response = requests.patch(url, auth=(USERNAME, PASSWORD), headers=headers,
                                data="{\"assignment_group\":\""+assignment_group+"\"}")
    if response.status_code != 200:
        print('Status:', response.status_code, 'Headers:', response.headers, 'Error Response:', response.json())
    else:
        print('Status:', response.status_code)

def update_incident_state_in_servicenow(sys_id, state):
    url = INSTANCE_URL + '/api/now/table/incident/' + sys_id
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    data = {"state": state} 

    response = requests.patch(url, auth=(USERNAME, PASSWORD), headers=headers, json=data)

    if response.status_code != 200:
        print('Status:', response.status_code, 'Headers:', response.headers, 'Error Response:', response.json())
    else:
        print('Status:', response.status_code)

def update_assignment_to_member_in_servicenow(sys_id, assigned_to):
    url = INSTANCE_URL +'/api/now/table/incident/'+sys_id
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    response = requests.patch(url, auth=(USERNAME, PASSWORD), headers=headers,
                                data="{\"assigned_to\":\""+assigned_to+"\"}")
    if response.status_code != 200:
        print('Status:', response.status_code, 'Headers:', response.headers, 'Error Response:', response.json())
    else:
        print('Status:', response.status_code)

def update_service_now_incident(sys_id, assignment_group, assign_to):        
        url = INSTANCE_URL + '/api/now/table/incident/'+ sys_id + '?sysparm_display_value=true&sysparm_exclude_reference_link=true&sysparm_fields=assignment_group%2Cassigned_to%2Csys_updated_on'
        username = USERNAME
        password = PASSWORD
        try:
            headers = {"Content-Type":"application/json","Accept":"application/json"}
            payload = {
                "sys_id" : sys_id,
                "assignment_group": assignment_group,
                "assigned_to": assign_to
            }

            response = requests.patch(url, auth=(username, password), headers=headers ,json=payload)
            response.raise_for_status()  
            users = response.json().get('result', [])
            return users
        except requests.exceptions.RequestException as e:
            return f'Error fetching users from ServiceNow: {e}'
        except Exception as e:
            return f'Error: {e}'

def get_users_from_servicenow():
    url = INSTANCE_URL + "/api/now/table/sys_user?sysparm_query=true&sysparm_display_value=true&sysparm_exclude_reference_link=true&sysparm_fields=sys_id%2Cuser_name%2Cname%2Cuser_password%2Cemail%2Cactive"
    username = USERNAME
    password = PASSWORD

    try:
        response = requests.get(url, auth=(username, password))
        response.raise_for_status()  
        users = response.json().get('result', [])
        return users
    except requests.exceptions.RequestException as e:
        return f'Error fetching users from ServiceNow: {e}'
    except Exception as e:
        return f'Error: {e}'

def get_user_groups_from_servicenow():
    url = INSTANCE_URL + "/api/now/table/sys_user_group?sysparm_query=true&sysparm_display_value=true&sysparm_exclude_reference_link=true&sysparm_fields=sys_id%2Cname%2Cdescription%2Cmanager%2Cemail%2Cactive%2Csys_created_on"
    username = USERNAME
    password = PASSWORD

    try:
        response = requests.get(url, auth=(username, password))
        response.raise_for_status()
        user_groups = response.json().get('result', [])
        return user_groups
    except requests.exceptions.RequestException as e:
        return f'Error fetching user groups from ServiceNow: {e}'
    except Exception as e:
        return f'Error: {e}'

def get_group_members():
    url = INSTANCE_URL + "/api/now/table/sys_user_grmember?sysparm_display_value=true&sysparm_exclude_reference_link=true&sysparm_fields=sys_id%2Cgroup%2Cuser"
    username = USERNAME
    password = PASSWORD

    try:
        response = requests.get(url, auth=(username, password))
        response.raise_for_status()
        group_members = response.json().get('result', [])
        return group_members
    except requests.exceptions.RequestException as e:
        return f'Error fetching user groups from ServiceNow: {e}'
    except Exception as e:
        return f'Error: {e}'

def delete_group_member_from_servicenow(sys_id):
    url = INSTANCE_URL + '/api/now/table/sys_user_grmember/' + sys_id
    username = USERNAME
    password = PASSWORD

    try:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        response = requests.delete(url, auth=(username, password), headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return f'Error deleting group member from ServiceNow: {e}'
    except Exception as e:
        return f'Error: {e}'


def create_group_member(group, user):
    url=INSTANCE_URL + '/api/now/table/sys_user_grmember?sysparm_display_value=true&sysparm_exclude_reference_link=true&sysparm_fields=sys_id%2Cuser%2Cgroup'
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    auth = (USERNAME, PASSWORD) 
    payload = {"group": group, "user": user}

    try:
        response = requests.post(url, auth=auth, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json().get('result', [])
        return data
    except requests.exceptions.RequestException as e:
        print(f'Error creating group member: {e}')
        return None

