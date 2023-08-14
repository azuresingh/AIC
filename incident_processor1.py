import joblib
import json
import requests
import mysql.connector
import threading
import pandas as pd
import numpy as np
from datetime import datetime
import time
from topsis3 import *
from inc_db_fun import *
from servicenow_functions import *
from configparser import ConfigParser
from config import *
from concurrent.futures import ThreadPoolExecutor

INSTANCE_URL = SERVICENOW_INSTANCE
USERNAME = SERVICENOW_USERNAME
PASSWORD = SERVICENOW_PASSWORD

class IncidentProcessor:
    def __init__(self):
        self.lock = threading.Lock()
        self.update_event = threading.Event()
        # Read configuration from config.ini file
        self.pklfile = pklfile  
        self.host = MYSQL_HOST
        self.database = MYSQL_DATABASE
        self.user = MYSQL_USERNAME
        self.password = MYSQL_PASSWORD
        self.previous_incident_number = '1'
        self.prob = '0'
        self.executor = ThreadPoolExecutor(max_workers=5)  # Adjust the max_workers value as needed
        
    def get_latest_incident_number(self):
        
        url = INSTANCE_URL + '/api/now/table/incident?sysparm_query=ORDERBYurgency&sysparm_display_value=true&sysparm_exclude_reference_link=true&sysparm_fields=number%2Cstate%2Cshort_description%2Cassignment_group%2Csys_created_on%2Csys_id%2Curgency&sysparm_limit=10&state=New&assignment_group=NULL'
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        response = requests.get(url, auth=(USERNAME, PASSWORD), headers=headers)

        if response.status_code != 200:
            print('Status:', response.status_code, 'Headers:', response.headers, 'Error Response:', response.json())       
        data = response.json()
        return data
    
    def get_predicted_assignment_group(self, short_desc):
        loaded_model = joblib.load(self.pklfile)
        print("model is running", self.pklfile)
        X_test = [short_desc]
        pred_cat = loaded_model.predict(X_test)
        val1 = str(pred_cat[0])
        prob_val = loaded_model.predict_proba(X_test)
        val2 = max(prob_val[0])
        self.prob = val2 * 100
        return val1, self.prob

    def process_incident(self, short_desc, assignment_group, sys_id, number, urgency):      
        current_thread = threading.current_thread()
        thread_name = current_thread.name
        print(f"Thread '{thread_name}' is running")
        assignment_group, A_group_score = self.get_predicted_assignment_group(short_desc)       
        if self.prob >=20:
            topsisv1 = perform_topsis(assignment_group, sys_id)
            assigned_to = topsisv1[0]
            update_assignment_group_in_servicenow(sys_id, assignment_group)
            update_assignment_to_member_in_servicenow(sys_id, assigned_to)
            insert_incident_into_database(topsisv1[1], number, short_desc, assignment_group, topsisv1[0], urgency, A_group_score)
        else:
            state = 'In Progress'
            update_incident_state_in_servicenow(sys_id, state)
            insert_incident_into_database(sys_id, number, short_desc, assignment_group, "", urgency, A_group_score)
    
    def process_incidents_threaded(self, incidents):
        with self.lock:
            threads = []
            for incident in incidents:
                assignment_group = incident['assignment_group']                
                short_desc = incident['short_description']
                sys_id = incident['sys_id']
                number = incident['number']
                print('number', number)
                state = incident['state']
                urgency = incident['urgency']
                print("assignmentgroup", assignment_group, number, state)

                if number != self.previous_incident_number and state == 'New' and assignment_group == '':
                    self.previous_incident_number = number
                    thread = threading.Thread(target=self.process_incident, args=(short_desc, assignment_group, sys_id, number, urgency))
                    threads.append(thread)
                    time.sleep(5)
                    thread.start()
                print("number of threads running",len(threads))
            for thread in threads:
                thread.join()

    def fetch_and_process_incidents(self):
            start_time = time.time()
            try:
                data = self.get_latest_incident_number()
                if 'result' in data:
                    incidents = data['result']
                    batch_size = 2  # Number of incidents to process in each batch
                    for i in range(0, len(incidents), batch_size):
                        batch = incidents[i:i+batch_size]
                        self.executor.submit(self.process_incidents_threaded, batch)
                else:
                    print("No New incident has raised")                
            except Exception as e:
                print("exception has occur")
            end_time = time.time()
            execution_time = end_time - start_time
            print(f"Execution time: {execution_time:.5f} seconds")
            
            



