"""
Shows basic usage of the Sheets API. Prints values from a Google Spreadsheet.
"""
from __future__ import print_function
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

# Setup the Sheets API
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
store = file.Storage('credentials.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
    creds = tools.run_flow(flow, store)
service = build('sheets', 'v4', http=creds.authorize(Http()))

# Call the Sheets API
SPREADSHEET_ID = '1GjKN4I_XNwCYDCaG_1V7CoA-vw4w3WsU0P77LQ1LP84'
RANGE_NAME = 'Data!A2:B'
result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID,
                                             range=RANGE_NAME).execute()
values = result.get('values', [])
if not values:
    print('No data found.')
else:
    print('pinyin_name, Chinese_name :')
    for row in values:

    	# Here I'll feed the result into a variable for the entire column
    	print(row)

# Connect to the database (using boto3 access RDS Postgresql instance).
#   Leave connection open until all data is migrated.

# Insert values into database table (select specific table).
#   Migrate data into as seperate sql statements.

# Close connection after all sql statements are executed.  


# Outstanding questions:
#     How do I use batchget to migrate the data all at once?
#     