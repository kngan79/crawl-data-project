import json
import requests
import pandas as pd
import gspread
from apiclient import discovery
from oauth2client import client as o2c
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(r'D:\Data_Analyst\projects\crawl-data-project\client_secret_426605622047-l7cu37rlpc74rlfhhe772jene3podtp0.apps.googleusercontent.com.json', scope)
client = gspread.authorize(creds)

with open(r'D:\Data_Analyst\projects\crawl-data-project\authen.json', 'r') as file:
    authen = json.load(file)

# function used to write data to ggsheet
def play_with_gsheet(spreadsheetId=None, _range=None, dataframe=None, method='read', first_time=True, service=None):
    """
    method: {'read', 'write', 'clear', 'append'}
    """
    
    if first_time:
        credentials = o2c.Credentials.new_from_json(json.dumps(authen))
        service = discovery.build('sheets', 'v4', credentials=credentials)
    
    if method == 'read':
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheetId, range=_range).execute()
        values = result.get('values')
        if len(values) > 0:
            columns = values[0]
            df = pd.DataFrame(values[1:])
            df.columns = columns
        else: df = pd.DataFrame()
        return df
    
    if method == 'write':
        values = [dataframe.columns.values.astype(str).tolist()] + dataframe.astype(str).values.tolist()
        data = [
        {
            'range': _range,
            'values': values
        }
        ]
        body = {
            'valueInputOption':'USER_ENTERED',
            'data':data
        }
        result = service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()
    
    if method == 'clear':
        body = {
            'ranges':_range
        }
        result = service.spreadsheets().values().batchClear(spreadsheetId=spreadsheetId, body=body).execute()
        
    if method == 'append' and dataframe is not None:
        body = {
            'values': dataframe.astype(str).values.tolist()
        }
        result = service.spreadsheets().values().append(spreadsheetId=spreadsheetId, range=_range,
                                                        valueInputOption='USER_ENTERED', insertDataOption='INSERT_ROWS',
                                                        body=body).execute()

def categorize_level(years):
    if years <= 2:
        return 'junior'
    elif years >= 3 and years <= 5:
        return 'middle'
    elif years > 5:
        return 'senior'
    else:
        return 'unknown'

# function to call API
def get_companies_data(url):
    response = requests.get(url)

    if response.status_code == 200:
        result = response.json()
        return result
    else:
        pass

base_url = 'https://server.luongthang.net/companies'

all_company_data = get_companies_data(base_url)

df = pd.DataFrame()

# Iterate over the result and call crawl_detail_companies_data function for each slug
if all_company_data:
    for company in all_company_data['companies']:
        slug = company.get('slug')
        if slug:
            company_url = f"{base_url}/{slug}"
            each_company_data = get_companies_data(company_url)
            if each_company_data is not None:
                company_df = pd.DataFrame(each_company_data)
                company_df.rename(columns={'id': 'companyId'}, inplace=True)
                company_df.fillna('', inplace=True)
                # Extract and expand 'compensations' field
                compensations_df = pd.json_normalize(company_df['compensations'])
                compensations_df.rename(columns={'id': 'jobId'}, inplace=True)
                # Merge company_df with the expanded compensation_df
                company_df = pd.concat([company_df.drop(columns=['compensations']), compensations_df], axis=1)
                df = df.append(company_df, ignore_index=True)
                df.reset_index(drop=True, inplace=True)  # Reset the index after appending
        else:
            print("Slug not found in the company data:", company)

# Convert all 'id' fields to string and fill null values
df = df.astype({'companyId': str,'jobId': str})
df['yearOfExperience'] = df['yearOfExperience'].fillna(0).astype(int)
df['level_category'] = df['yearOfExperience'].apply(categorize_level)
df = df.fillna('')
print('Done processing data')

#  clear and write output data to ggsheet
play_with_gsheet('1PhI06ntaZTb5qKADTJ_eZgB4AcRYnJ4Rf-oH1q-pR_c', 'detail', dataframe=df, method='clear')
play_with_gsheet('1PhI06ntaZTb5qKADTJ_eZgB4AcRYnJ4Rf-oH1q-pR_c', 'detail', dataframe=df, method='write')

# data contains overall metrics only (exclude all fields parsed from 'compensations' field), write to another sheet
df_exclude_compensations = df[['companyId', 'name', 'compensationMin', 'compensationMax','compensationMedian', 'compensationCount', 'meanYearOfExperience']].drop_duplicates()
play_with_gsheet('1_UKqPkLDDAvHriui4BIxRNGhiHeZKl2ZB7G5Yv1r_v0', 'overall', dataframe=df_exclude_compensations, method='write')

