import requests
import base64
import json
import pandas as pd 
from datetime import datetime
import numpy as np

now = datetime.now()
value_list = []

output_df = pd.DataFrame(columns = ['Issue ID', 'Issue Name', 'Iteration Path', 'State', 'System Tags', 'Issue created datetime', 'Issue closed datetime', 'Total Time taken', 'Time in Need info', 'Net Time taken', 'Meet or Breach' ])
query_endpoint_url = "https://dev.azure.com/pavithraapv0237/Python%20project/PythonprojectTeam/_apis/wit/wiql?api-version=5.1"

def total_time_calculation(date1, date2):
    
    date3 = pd.to_datetime(date1,format="%Y-%m-%d %H:%M:%S").date()
    date4 = pd.to_datetime(date2,format="%Y-%m-%d %H:%M:%S").date()
    days =  np.busday_count(date3 , date4)
    
    date1 = pd.to_datetime(date1,format="%Y-%m-%d %H:%M:%S")
    date2 = pd.to_datetime(date2,format="%Y-%m-%d %H:%M:%S")

    output = date2 - date1
    output1 = pd.to_timedelta(output) - pd.to_timedelta(days) 
    to_sub = output.days - days 
    final_hrs = output.days - to_sub
    final_hrs = final_hrs*24 + output.seconds//3600
    return final_hrs

def need_info_time_calculation(id):
    revision_history_url = "https://dev.azure.com/pavithraapv0237/Python%20project/_apis/wit/workItems/" + str(id) + "/revisions/"
    res = requests.get(revision_history_url, headers=headers)
    revision_details = res.json()
    #revision_details = json.loads(value)
    datetime_now = pd.to_datetime(now,format="%Y-%m-%d %H:%M:%S")
    no_of_revision = revision_details['count'] 
    need_info_hrs = 0
    need_info_flag = 0
    for j in range(0, no_of_revision):
        
        state = revision_details['value'][j]['fields']['System.State']
        if state == 'Need Info'  :
            need_info_flag += 1
            need_info_open_time = revision_details['value'][j]['fields']['System.ChangedDate'][:-5]
            need_info_open_time = pd.to_datetime(need_info_open_time,format="%Y-%m-%d %H:%M:%S")
            
        else: 
            need_info_end_time = revision_details['value'][j]['fields']['System.ChangedDate'][:-5]
            need_info_end_time = pd.to_datetime(need_info_end_time,format="%Y-%m-%d %H:%M:%S")
            if need_info_flag == 1:
                need_info_time = total_time_calculation(need_info_end_time,need_info_open_time)
                #need_info_time =  need_info_end_time - need_info_open_time
                #need_info_time = need_info_time.days*24 + need_info_time.seconds//3600
                need_info_time += need_info_time
                need_info_flag = 0
            continue
            
        if need_info_flag == 1:
            need_info_time = total_time_calculation(datetime_now,need_info_open_time)
            #need_info_time = datetime_now - need_info_open_time
            #need_info_time = need_info_time.days*24 + need_info_time.seconds//3600
            need_info_hrs += need_info_time
    return need_info_hrs
    
             
def meet_or_breach(net_time_diff, category):
    breach_hour = 0
    if 'access management' in category:
        breach_hour = 24
    elif 'workflow management' in category:
        breach_hour = 48 
    elif category == 'No tag':
        return 'No tag'
    elif category == 'Not categorized':
        return 'Not categorized'
    if net_time_diff - breach_hour < 0 :
        return 'Met'
    else:
        return 'Breached'


#filter query
#body = {"query": "Select [System.Id], [System.Title], [System.State] From WorkItems where [System.IterationPath] = 'Python project\\Iteration 1' AND [System.AreaPath] = 'Python project\\New_script'"}

#test count query
body = {"query": "Select [System.Id], [System.Title], [System.State] From WorkItems"}

username = "" # This can be an arbitrary value or you can just let it empty
password = "o2hs4xenkxidoqc2vazzjxbrtxp3suoxeljflmcyukf4gmd3b7jq"
userpass = username + ":" + password
b64 = base64.b64encode(userpass.encode()).decode()
headers = {"Authorization" : "Basic %s" % b64} 

response = requests.post(query_endpoint_url, json = body, headers=headers)
r = response.json()

issue_count = len(r['workItems'])
for i in range(0,4):
    issue_endpoint_url = "https://dev.azure.com/pavithraapv0237/_apis/wit/workitems?ids=" + str(r['workItems'][i]['id']) + "&$expand=all&api-version=6.0"
    res = requests.get(issue_endpoint_url, headers=headers)
    issue_details = res.json()
    state = issue_details['value'][0]['fields']['System.State']
    output_df.at[i, 'Issue ID'] = issue_details['value'][0]['id']
    output_df.at[i, 'Issue Name'] = issue_details['value'][0]['fields']['System.Title']
    output_df.at[i, 'State'] = state
    if 'System.Tags' in issue_details['value'][0]['fields']:
        output_df.at[i, 'System Tags'] = issue_details['value'][0]['fields']['System.Tags']
    else:
        output_df.at[i, 'System Tags'] = 'No tag'
    #output_df.at[i, 'System Tags'] = issue_details['value'][0]['fields']['System.Tags'] 
    output_df.at[i, 'Iteration Path'] = issue_details['value'][0]['fields']['System.IterationPath']
    create_datetime = issue_details['value'][0]['fields']['System.CreatedDate'].split('.')[0]
    create_datetime_conv = datetime.strptime(create_datetime, '%Y-%m-%dT%H:%M:%S')
    output_df.at[i, 'Issue created datetime'] = create_datetime_conv
    
    
    output_df.at[i, 'Time in Need info'] = need_info_time_calculation(issue_details['value'][0]['id'])

    
    if state != 'Closed':
        output_df.at[i, 'Issue closed datetime'] = now.strftime("%Y-%m-%d %H:%M:%S")
    else: 
        closed_date = issue_details['value'][0]['fields']['System.ChangedDate'][:-8]
        output_df.at[i, 'Issue closed datetime'] = datetime.strptime(closed_date, '%Y-%m-%dT%H:%M%S')
    
    
output_df['Total Time taken'] = output_df.apply(lambda x: total_time_calculation(x['Issue created datetime'],x['Issue closed datetime']),axis=1)    


output_df['Net Time taken'] = output_df['Total Time taken'] - output_df['Time in Need info']
output_df['Meet or Breach'] = output_df.apply(lambda x: meet_or_breach(x['Net Time taken'],x['System Tags']),axis=1)    
#need_info_time_calculation(value)

#output_df.drop(columns = ['Issue created datetime', 'Issue closed datetime', 'Time in Need info'], inplace = True)

output_df.to_csv("output.csv", index = False)
output_df