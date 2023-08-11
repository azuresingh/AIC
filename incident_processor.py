import joblib
import json
import requests
import mysql.connector
import threading
import pandas as pd
import numpy as np
import datetime
import time
from topsis3 import *
from inc_db_fun import *
from servicenow_functions import update_assignment_group_in_servicenow, update_assignment_to_member_in_servicenow
from configparser import ConfigParser
from config.config import *

INSTANCE_URL = SERVICENOW_INSTANCE
USERNAME = SERVICENOW_USERNAME
PASSWORD = SERVICENOW_PASSWORD

class IncidentProcessor:
    def __init__(self):
        self.lock = threading.Lock()
        self.update_event = threading.Event()
        # Read configuration from config.ini file
        self.config = ConfigParser() 
        self.config.read(r'C:\Users\dharmales\OneDrive - FUJITSU\Desktop\AIC\AICMain220723\config.ini')
        self.pklfile = self.config.get('filepath', 'pklfile')
        self.host = self.config.get('MySQL', 'host')
        self.database = self.config.get('MySQL', 'database')
        self.user = self.config.get('MySQL', 'username')
        self.password = self.config.get('MySQL', 'password')
        self.previous_incident_number = '1'
        self.prob = '0'
    
    def get_latest_incident_number(self):
        url = INSTANCE_URL + '/api/now/table/incident?sysparm_query=ORDERBYurgency&sysparm_display_value=true&sysparm_exclude_reference_link=true&sysparm_fields=number%2Cstate%2Cshort_description%2Cassignment_group%2Csys_id%2Curgency&sysparm_limit=10&state=New&assignment_group=NULL'
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        time.sleep(20)
        response = requests.get(url, auth=(USERNAME, PASSWORD), headers=headers)

        if response.status_code != 200:
            print('Status:', response.status_code, 'Headers:', response.headers, 'Error Response:', response.json())       
        data = response.json()
        return data
    
    def get_predicted_assignment_group(self, short_desc):
        loaded_model = joblib.load(self.pklfile)
        print("model is runing",self.pklfile)
        X_test = [short_desc]
        pred_cat = loaded_model.predict(X_test)
        val1 = str(pred_cat[0])
        prob_val = loaded_model.predict_proba(X_test)
        val2 = max(prob_val[0])
        self.prob = val2 * 100
        return val1, self.prob


    def retrain_model(self):
        file_path = self.pklfile
        delimiter = '.'
        components = file_path.split(delimiter)
        base_file_path = components[-2].split('_')[0]
        version = components[-2].split('_')[1]
        cnt = int(components[-2].split('_')[2])
        print(cnt)
        
        mydb = mysql.connector.connect(
        host=self.host,
        user=self.user,
        password=self.password,
        database=self.database
        )
        
        query = "SELECT short_description, assignment_group FROM incidents where assignment_group IS NOT NULL"
        df = pd.read_sql_query(query, mydb)
        print("value of df",len(df))
        
        X = df['short_description']
        y = df['assignment_group']
        
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = .25, random_state=42)
        
        from sklearn.feature_extraction.text import CountVectorizer
        count_vect = CountVectorizer()
        X_train_counts = count_vect.fit_transform(X_train)
        
        from sklearn.feature_extraction.text import TfidfTransformer
        tfidf_transformer = TfidfTransformer()
        X_train_tfidf = tfidf_transformer.fit_transform(X_train_counts)
        
        from sklearn.naive_bayes import MultinomialNB
        clf = MultinomialNB().fit(X_train_tfidf, y_train)
        
        from sklearn.pipeline import Pipeline
        text_clf = Pipeline([('vect', CountVectorizer()),
                            ('tfidf', TfidfTransformer()), 
                            ('clf', MultinomialNB()),])
        
        text_clf.fit(X_train, y_train)
        # base_file_path = file_path
        cnt = cnt+1
        # version = "v"
        pklfile_path = f"{base_file_path}_{version}_{cnt}.pkl"
        joblib.dump(text_clf, pklfile_path)
        self.config.set('filepath', 'pklfile', pklfile_path)
        with open('config.ini', 'w') as configfile:
            self.config.write(configfile)
        self.pklfile = pklfile_path
        print("change valeu of pklfile",self.pklfile)
   
    
    def process_incident(self, short_desc, assignment_group, sys_id, number, urgency):
        print("process_incident is running")
        current_thread = threading.current_thread()
        thread_name = current_thread.name
        print(f"Thread '{thread_name}' is running")
        start_time = time.time()
        assignment_group, A_group_score = self.get_predicted_assignment_group(short_desc)
        print("################name of assignment grp",assignment_group)
        print("################name of A_to_score",A_group_score)
        # if assignment_group==
        topsisv1 = perform_topsis(assignment_group,sys_id)
        assigned_to = topsisv1[0]
        print("value of topsisv1",topsisv1)
        print(type(topsisv1))
        print(self.prob)
        print(assignment_group)
        print(number)
                    
        if self.prob >= 20:
            update_assignment_group_in_servicenow(sys_id, assignment_group)
            update_assignment_to_member_in_servicenow(sys_id, assigned_to)
            insert_incident_into_database(topsisv1[1], number, short_desc, assignment_group, topsisv1[0], urgency,A_group_score)
        else:
            insert_incident_into_database(topsisv1[1],number, short_desc, assignment_group, topsisv1[0], urgency,A_group_score)
        
    
    def fetch_incidents_servicenow(self):
        while True:
            try:
                data = self.get_latest_incident_number()
                
                threads = []
                if len(data) > 0:
                    for i, j in enumerate(data['result']):
                        assignment_group = data['result'][i]['assignment_group']                
                        short_desc = data['result'][i]['short_description']
                        sys_id = data['result'][i]['sys_id']
                        number = data['result'][i]['number']
                        print('number', number)
                        state = data['result'][i]['state']
                        urgency = data['result'][i]['urgency']
                        print("assignmentgroup", assignment_group, number, state)
            
                        if number != self.previous_incident_number and state == 'New' and assignment_group == '':
                            self.previous_incident_number = number
                            thread = threading.Thread(target=self.process_incident, args=(short_desc, assignment_group, sys_id, number,urgency))
                            threads.append(thread)
                            time.sleep(5)
                            thread.start()
                
                for thread in threads:
                    thread.join()
                    # self.update_event.set()
            except Exception as e:
                print(e)






