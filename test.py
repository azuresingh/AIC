import requests
import json

# Replace these values with your ServiceNow instance credentials
INSTANCE_URL = "https://dev65891.service-now.com/"
USERNAME = "admin"
PASSWORD = "uInOV4g*p/E4"


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
    
members = ['Bow Ruggeri','David Dan','Don Goodliffe','Alene Rabeck']

for user in members:
    create_group_member('Hardware', user)
    print('added', user)