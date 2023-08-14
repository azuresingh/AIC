import numpy as np
import pandas as pd
import datetime
import mysql.connector
from config import *

conn = mysql.connector.connect(
    host=MYSQL_HOST,
    user=MYSQL_USERNAME,
    password=MYSQL_PASSWORD,
    database=MYSQL_DATABASE
)

def perform_topsis(assignment_group, sys_id):
    print('we are in perform_topsis')
    try:
        cursor = conn.cursor()
        query = """
            SELECT u.name, u.Tier, u.FTE, u.teams_avail, u.workload
            FROM users u
            JOIN group_members gm ON u.name = gm.user_name
            JOIN assignment_group ag ON gm.group_name = ag.group_name
            WHERE ag.group_name = %s
        """
        cursor.execute(query, (assignment_group,))
        result = cursor.fetchall()
        conn.commit()
        cursor.close()
        # print('result',result)
        column_names = ['name', 'Tier', 'FTE', 'teams_avail', 'workload']

        df = pd.DataFrame(result, columns=column_names)
        print(df)
        matrix = df.iloc[:, 1:].astype(float)

        wt = [0.2, 0.1, 0.4, 0.3]
        attributes = np.array(matrix.columns.tolist())
        candidates = np.array(df['name'])
        raw_data = np.array(matrix.values)

        weights = np.array(wt)
        benefit_attributes = {0, 1, 2}

        m = len(raw_data)
        n = len(attributes)

        divisors = np.empty(n)
        for j in range(n):
            column = raw_data[:, j]
            divisors[j] = np.sqrt(column @ column)

        raw_data /= divisors
        raw_data *= weights

        a_pos = np.zeros(n)
        a_neg = np.zeros(n)
        for j in range(n):
            column = raw_data[:, j]
            max_val = np.max(column)
            min_val = np.min(column)
            if j in benefit_attributes:
                a_pos[j] = max_val
                a_neg[j] = min_val
            else:
                a_pos[j] = min_val
                a_neg[j] = max_val

        sp = np.zeros(m)
        sn = np.zeros(m)
        cs = np.zeros(m)

        for i in range(m):
            diff_pos = raw_data[i] - a_pos
            diff_neg = raw_data[i] - a_neg
            sp[i] = np.sqrt(diff_pos @ diff_pos)
            sn[i] = np.sqrt(diff_neg @ diff_neg)
            cs[i] = sn[i] / (sp[i] + sn[i])

        max_index = np.argmax(cs)
        print('********max_index=', max_index)
        empname = df.iloc[max_index, 0]
        print('********emp_name=', empname)

        cur = conn.cursor()
        cur.callproc('update_workload', (empname,))
        conn.commit()
        cur.close()

        return empname, sys_id

    except mysql.connector.Error as error:
        print("Error occurred while connecting to MySQL:", error)

    # finally:
    #     if conn.is_connected():
    #         conn.close()


# empname, sys_id = perform_topsis('Hardware', 'sys_id')
# print("Employee Name:", empname)
# print("System ID:", sys_id)
