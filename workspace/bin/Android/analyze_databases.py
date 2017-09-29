# Imports
import os
import sqlite3
import xlwt
import time
import shutil

import aft_log
import format_data
import database_connector

deviceID = 0

def analyze_phone_details(curr_dir, database_dir, os_version, device_manufacturer, device_model, device_name, device_IMEI, examination_time):
    aft_log.log("analyzeDBs: ->[ Obtaining Phone Details ]<-", 2)
    # Format Phone Details
    p = format_data.format_phone_details(os_version, device_manufacturer)
    os_version3 = p[0]
    device_manufacturer = p[1]
    
    # Send to database
    database_connector.export_phone_details(curr_dir, os_version3, device_manufacturer, device_model, device_name, device_IMEI, examination_time)
    
def obtain_applications_list(curr_dir, application_list, device_name):
    global deviceID
    aft_log.log("analyzeDBs: ->[ Obtaining Applications list ]<-", 2)
    try:
        deviceID = database_connector.get_device_id(curr_dir, device_name)
        
        for application in application_list:
            if application != "":
                # Send to database
                database_connector.export_application(curr_dir, deviceID, application)    
        aft_log.log("extractDBs: Applications list extracted successfully!", 2)
    except:
        aft_log.log("connectDB: Unable to extract applications list!", 2)
        
def analyze_contacts_database(curr_dir, database_dir):
    global deviceID
    aft_log.log("analyzeDBs: ->[ Obtaining Contacts Information ]<-", 2)
    # Preparation to connect to the contacts database
    try:
        conn = sqlite3.connect(os.path.join(database_dir, "contacts2.db"))
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) from contacts")
        # Obtain the number of contacts in the device
        num_entries = cursor.fetchone()[0]
        
        if num_entries > 0:
            aft_log.log("analyzeDBs: -> Getting " + str(num_entries) + " contacts information...", 0)
            cursor.execute("SELECT _id, display_name from raw_contacts")
            people = cursor.fetchall()
            
            for person in people:
                personID = person[0]
                personName = person[1]
                # Insert data into Contact table and get contact id found in the database
                contactID = database_connector.export_contact(curr_dir, deviceID, personName)
                cursor.execute("SELECT mimetype_id, data1, data2, data4 FROM data where raw_contact_id = '{0}'".format(personID))
                # Collect all the relevant records for the user id
                records = cursor.fetchall()
                # Export to database for each records
                for record in records:
                    mimetype = record[0]
                    dataType = record[2]
                    data = record[1]
                    # Check if it is an email
                    if mimetype == 1:
                        emailType = ""
                        # Obtain the type
                        if dataType == '1':
                            emailType = "Home"
                        elif dataType == '2':
                            emailType = "Work"
                        elif dataType == '3':
                            emailType = "Other"
                        elif dataType == '4':
                            emailType = "Mobile"
                        elif dataType == '5':
                            emailType = "Custom"
                        else:
                            emailType = "Other"
                        database_connector.export_contact_email(curr_dir, contactID, emailType, data)
                    # Check if it is IM
                    elif mimetype == 2:
                        detailType = "IM"
                        database_connector.export_contact_details(curr_dir, contactID, detailType, data)
                    # Check if it is a nickname
                    elif mimetype == 3:
                        detailType = "Nickname"
                        database_connector.export_contact_details(curr_dir, contactID, detailType, data)
                    # Check if it is an organization
                    elif mimetype == 4:
                        detailType = "Organization"
                        data4 = record[3]
                        if data4:
                            organization = data4 + "," + data
                        else :
                            organization = data
                        database_connector.export_contact_details(curr_dir, contactID, detailType, organization)
                    # Check if it is a phone number
                    elif mimetype == 5:
                        numberType = ""
                        # Obtain the type
                        if dataType == '1':
                            numberType = "Home"
                        elif dataType == '2':
                            numberType = "Mobile"
                        elif dataType == '3':
                            numberType = "Work"
                        elif dataType == '4':
                            numberType = "Work Fax"
                        elif dataType == '5':
                            numberType = "Home Fax"
                        elif dataType == '6':
                            numberType = "Pager"
                        elif dataType == '7':
                            numberType = "Other"
                        elif dataType == '8':
                            numberType = "Custom"
                        elif dataType == '9':
                            numberType = "Car"
                        else:
                            numberType = "Other"
                        # Remove spaces in between numbers
                        data = data.replace(" ", "")
                        data = data.replace("-", "")
                        data = data.replace("(", "")
                        data = data.replace(")", "")
                        # Convert str to int
                        data = int(data) 
                        database_connector.export_contact_number(curr_dir, contactID, numberType, data)
                    # Check if it is a sip address
                    elif mimetype == 6:
                        detailType = "SIP_Address"
                        database_connector.export_contact_details(curr_dir, contactID, detailType, data)
                    # Check if it is an address
                    elif mimetype == 8:
                        detailType = ""
                        # Obtain the type
                        if dataType == '1':
                            detailType = "Address"
                        elif dataType == '2':
                            detailType = "Address(Work)"
                        elif dataType == '3':
                            detailType = "Address(Other)"
                        elif dataType == '4':
                            detailType = "Address(Custom)"
                        else:
                            detailType = "Address(Other)"
                        database_connector.export_contact_details(curr_dir, contactID, detailType, data)
            aft_log.log("extractDBs: Contacts extracted successfully!", 2)
        else:
            aft_log.log("analyzeDBs: There are no contacts!", 2)
    except:
        aft_log.log("connectDB: Contacts database not found!", 2)
      
def analyze_call_logs(curr_dir, database_dir):
    global deviceID
    aft_log.log("analyzeDBs: ->[ Obtaining Call Logs ]<-", 2)
    # Preparation to connect to the call logs database
    try:
        # Preparation to connect to the call logs database
        conn = sqlite3.connect(os.path.join(database_dir, "contacts2.db"))
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) from calls")
        # Obtain the number of call logs in the device
        num_entries = cursor.fetchone()[0]
        
        if num_entries > 0:
            cursor.execute("SELECT date, duration, number, type FROM calls")
            logs = cursor.fetchall()
            
            for log in logs:
                date = log[0]
                duration = log[1]
                number = log[2]
                callTypeID = log[3]
                
                # Convert date to human readable format
                realdate = time.strftime('%Y-%m-%d %H:%M:%S',  time.gmtime(date/1000))
                realDuration = time.strftime('%H:%M:%S', time.gmtime(duration))
                
                # Interpret call type
                callType = "none"
                if callTypeID == 1:
                    callType = "Incoming"
                elif callTypeID == 2:
                    callType = "Outgoing"
                elif callTypeID == 3:
                    callType = "Missed call"
                    
                database_connector.export_call_logs(curr_dir, deviceID, number, realDuration, realdate, callType)
                
            aft_log.log("extractDBs: Call logs extracted successfully!", 2)
        else:
            aft_log.log("analyzeDBs: There are no call logs!", 2)
    except:
        aft_log.log("connectDB: Call Logs database not found!", 2)

def analyze_browser_history(curr_dir, database_dir):
    global deviceID
    aft_log.log("analyzeDBs: ->[ Obtaining Browser History ]<-", 2)
    # Preparation to connect to the browser history database
    try:
        os.chdir('..')
        sqlite_dir = os.path.join(os.getcwd(), "browser2.db")
        file_dir = os.path.join(database_dir, "browser2.db")
        shutil.move(file_dir, sqlite_dir)
        sql = 'SELECT title, url, date, visits FROM history'
        events_arr = database_connector.read_sqlite('browser2.db', sql)
        shutil.move(sqlite_dir, file_dir)
        os.chdir(curr_dir)
        if len(events_arr) > 0:
            
            for i in range(0, len(events_arr), 4):
                title = str.strip(events_arr[i]).split(' = ')[1]
                url = (str.strip(events_arr[i+1]).split(' = '))[1]
                date = str.strip(events_arr[i+2]).split(' = ')[1]
                visits = str.strip(events_arr[i+3]).split(' = ')[1]
                
                dateTime = int(date)
                
                # Convert date to human readable format
                realdate = time.strftime('%Y-%m-%d %H:%M:%S',  time.gmtime(dateTime/1000))
                
                database_connector.export_browser_history(curr_dir, deviceID, "Android Default Browser", title, url, realdate, visits)
                
            aft_log.log("extractDBs: Browser History extracted successfully!", 2)
        else:
            aft_log.log("analyzeDBs: There are no browser history!", 2)
    except:
        aft_log.log("connectDB: Browser History database not found!", 2)

def analyze_browser_bookmark(curr_dir, database_dir):
    global deviceID
    aft_log.log("analyzeDBs: ->[ Obtaining Browser Bookmark ]<-", 2)

#     LOG_FILENAME = 'logging_example.out'
#     logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG,)
#     logging.debug('This message should go to the log file')
    
    # Preparation to connect to the browser bookmark database
    try:
        os.chdir('..')
        sqlite_dir = os.path.join(os.getcwd(), "browser2.db")
        file_dir = os.path.join(database_dir, "browser2.db")
        shutil.move(file_dir, sqlite_dir)
        sql = 'SELECT title, url, created FROM bookmarks'
        events_arr = database_connector.read_sqlite('browser2.db', sql)
        shutil.move(sqlite_dir, file_dir)
        os.chdir(curr_dir)
        if len(events_arr) > 0:
            for i in range(3, len(events_arr), 3):
                title = str.strip(events_arr[i]).split(' = ')[1]
                url = (str.strip(events_arr[i+1]).split(' = '))[1]
                date = str.strip(events_arr[i+2]).split(' = ')[1]
                
                dateTime = int(date)                
                # Convert date to human readable format
                realdate = time.strftime('%Y-%m-%d %H:%M:%S',  time.gmtime(dateTime/1000))
                database_connector.export_browser_bookmarks(curr_dir, deviceID, "Android Default Browser", title, url, realdate) 
                    
            aft_log.log("extractDBs: Browser Bookmarks extracted successfully!", 2)
        else:            
            aft_log.log("analyzeDBs: There are no browser bookmarks!", 2)
    except:
        aft_log.log("connectDB: Browser Bookmarks database not found!", 2)

def analyze_browser_search(curr_dir, database_dir):
    global deviceID
    aft_log.log("analyzeDBs: ->[ Obtaining Browser Search ]<-", 2)
    # Preparation to connect to the browser history database
    try:
        os.chdir('..')
        sqlite_dir = os.path.join(os.getcwd(), "browser2.db")
        file_dir = os.path.join(database_dir, "browser2.db")
        shutil.move(file_dir, sqlite_dir)
        sql = 'SELECT search, date FROM searches'
        events_arr = database_connector.read_sqlite('browser2.db', sql)
        shutil.move(sqlite_dir, file_dir)
        os.chdir(curr_dir)
        if len(events_arr) > 0:
            
            for i in range(0, len(events_arr), 2):
                search = str.strip(events_arr[i]).split(' = ')[1]
                date = (str.strip(events_arr[i+1]).split(' = '))[1]
                
                dateTime = int(date)
                
                # Convert date to human readable format
                realdate = time.strftime('%Y-%m-%d %H:%M:%S',  time.gmtime(dateTime/1000))
                
                database_connector.export_browser_search(curr_dir, deviceID, "Android Default Browser", search, realdate)
                
            aft_log.log("extractDBs: Browser Search extracted successfully!", 2)
        else:
            aft_log.log("analyzeDBs: There are no browser search!", 2)
    except:
        aft_log.log("connectDB: Browser Search database not found!", 2)

def analyze_sms(curr_dir, database_dir):
    global deviceID
    aft_log.log("analyzeDBs: ->[ Obtaining SMS ]<-", 2)
    # Preparation to connect to the contacts database
    try:
        # Preparation to connect to the contacts database
        conn = sqlite3.connect(os.path.join(database_dir, "mmssms.db"))
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM sms")
        # Obtain the number of call logs in the device
        num_entries = cursor.fetchone()[0]
        
        if num_entries > 0:
            cursor.execute("SELECT address, type, body, date FROM sms")
            results = cursor.fetchall()
            
            for result in results:
                address = result[0]
                message = result[1]
                body = result[2]
                date = result[3]
                
                address = address.replace(" ", "")
                address = address.replace("-", "")
                address = address.replace("(", "")
                address = address.replace(")", "")
                
                # Determine if it is an incoming or outgoing message
                if message == 1:
                    messageType = "Incoming"
                elif message == 2:
                    messageType = "Outgoing"
                elif message == 3:
                    messageType = "Draft"
                    
                # Convert date to human readable format
                realdate = time.strftime('%Y-%m-%d %H:%M:%S',  time.gmtime(date/1000))
                    
                database_connector.export_sms(curr_dir, deviceID, address, messageType, body, realdate)
                
            aft_log.log("extractDBs: SMS History extracted successfully!", 2)
        else:
            aft_log.log("analyzeDBs: There are no SMS history!", 2)
    except:
        aft_log.log("connectDB: SMS History database not found!", 2)

def analyze_skype(curr_dir, database_dir):
    global deviceID
    aft_log.log("analyzeDBs: ->[ Obtaining Skype Details ]<-", 2)
    # Detect the number of skype users
    skype_users = []
    skype_dir = os.path.join(database_dir, "Skype")
    skype_users = os.listdir(skype_dir)
    if not skype_users:
        aft_log.log("connectDB: There are no skype database!", 2)
    else:
        for user in skype_users:
            skype_database = os.path.join(skype_dir, user, "main.db")
            try:
                # Connect to the skype database
                conn = sqlite3.connect(skype_database)
                cursor = conn.cursor()
                
                ##############################
                # Get Skype accounts
                cursor.execute("SELECT skypename, fullname, liveid_membername, birthday, gender, languages, country, province, city, phone_home, phone_office, phone_mobile, about, emails, profile_timestamp, mood_text, mood_timestamp FROM Accounts")
                skypeAccounts = cursor.fetchall()
                
                for account in skypeAccounts:
                    skypeName = account[0]
                    fullName = account[1]
                    liveid_membername = str(account[2])
                    birthday = str(account[3])
                    gender = account[4]
                    language = account[5]
                    country = account[6]
                    province = account[7]
                    city = account[8]
                    phone_home = account[9]
                    phone_office = account[10]
                    phone_mobile = account[11]
                    aboutMe = account[12]
                    emails = account[13]
                    lastUpdatedProfile = account[14]
                    moodText = account[15]
                    lastUpdatedMood = account[16]  
                    
                    # Format the data
                    if liveid_membername == "None":
                        liveid_membername = ""
                    if birthday != '0':
                        birthday = birthday[:4] + '-' + birthday[4:]
                        birthday = birthday[:7] + '-' + birthday[7:]
                    elif birthday == '0':
                        birthday = ''
                    if gender == 1:
                        gender = "Male"
                    elif gender == 2:
                        gender = "Female"
                    elif gender == 0:
                        gender = ""
                    if phone_home is None:
                        phone_home = ""
                    if phone_office is None:
                        phone_office = ""
                    if phone_mobile is None:
                        phone_mobile = ""
                    try:
                        dateUnix = float(lastUpdatedProfile)
                        lastUpdatedProfile = time.strftime('%Y-%m-%d %H:%M:%S',  time.gmtime(dateUnix))
                    except:
                        lastUpdatedProfile = str(lastUpdatedProfile)
                        if lastUpdatedProfile == "None":
                            lastUpdatedProfile = ''
                    try:
                        dateUnix = float(lastUpdatedMood)
                        lastUpdatedMood = time.strftime('%Y-%m-%d %H:%M:%S',  time.gmtime(dateUnix))
                    except:
                        lastUpdatedMood = str(lastUpdatedMood)
                        if lastUpdatedMood == "None":
                            lastUpdatedMood = ''
                    
                    database_connector.export_skype_account(curr_dir, deviceID, skypeName, fullName, liveid_membername, birthday, gender, language, country, province, city, phone_home, phone_office, phone_mobile, aboutMe, emails, lastUpdatedProfile, moodText, lastUpdatedMood)
                ##############################
                
                skypeAccountID = database_connector.get_skype_account_id(curr_dir, deviceID, skypeName)
                # Get Skype Contacts
                cursor.execute("SELECT skypename, displayname, lastonline_timestamp, birthday, gender, languages, country, province, city, phone_home, phone_office, phone_mobile, about, emails, profile_timestamp, mood_text FROM Contacts WHERE is_permanent = 1")
                skypeContacts = cursor.fetchall()
                
                for contact in skypeContacts:       
                    skypeName = contact[0]
                    displayName = contact[1]
                    lastOnlineTimestamp = contact[2]
                    birthday = contact[3]
                    gender = contact[4]
                    language = contact[5]
                    country = contact[6]
                    province = contact[7]
                    city = contact[8]
                    phone_home = contact[9]
                    phone_office = contact[10]
                    phone_mobile = contact[11]
                    aboutMe = contact[12]
                    emails = contact[13]
                    lastUpdatedProfile = contact[14]
                    moodText = str(contact[15])
                    
                    # Format the data             
                    displayName = displayName.encode('utf-8')
                    if birthday is None:
                        birthday = ""
                    if birthday != "":
                        birthday = str(birthday)
                        birthday = birthday[:4] + '-' + birthday[4:]
                        birthday = birthday[:7] + '-' + birthday[7:]
                    if gender == 1:
                        gender = "Male"
                    elif gender == 2:
                        gender = "Female"
                    elif gender is None:
                        gender = ""
                    if language is None:
                        language = ""
                    if country is None:
                        country = ""
                    if province is None:
                        province = ""
                    if city is None:
                        city = ""
                    if phone_home is None:
                        phone_home = ""
                    if phone_office is None:
                        phone_office = ""
                    if phone_mobile is None:
                        phone_mobile = ""
                    if aboutMe is None:
                        aboutMe = ""
                    if emails is None:
                        emails = ""
                    moodText = moodText.replace('\'', '\'\'')
                    if moodText == "None":
                        moodText = ""
                    try:
                        dateUnix = float(lastOnlineTimestamp)
                        lastOnlineTimestamp = time.strftime('%Y-%m-%d %H:%M:%S',  time.gmtime(dateUnix))
                    except:
                        lastOnlineTimestamp = str(lastOnlineTimestamp)
                        if lastOnlineTimestamp == "None":
                            lastOnlineTimestamp = ''
                    try:
                        dateUnix = float(lastUpdatedProfile)
                        lastUpdatedProfile = time.strftime('%Y-%m-%d %H:%M:%S',  time.gmtime(dateUnix))
                    except:
                        lastUpdatedProfile = str(lastUpdatedProfile)
                        if lastUpdatedProfile == "None":
                            lastUpdatedProfile = ''
                    
                    database_connector.export_skype_contact(curr_dir, skypeAccountID, skypeName, displayName, lastOnlineTimestamp, birthday, gender, language, country, province, city, phone_home, phone_office, phone_mobile, aboutMe, emails, lastUpdatedProfile, moodText)
                ##############################
                # Get Skype Conversations
                cursor.execute("SELECT author, from_dispname, dialog_partner, identities, type, body_xml, param_value, timestamp FROM Messages")
                skypeConversations = cursor.fetchall()
                
                for conversation in skypeConversations:
                    message = ''
                    callDuration = 0       
                    author = conversation[0]
                    author_Fullname = conversation[1]
                    dialog_Partner = str(conversation[2])
                    conversationType = conversation[4]  
                    timestamp = conversation[7]
                    
                    # Format the data             
                    if dialog_Partner == "None":
                        dialog_partner = conversation[3]
                        if dialog_partner == "None":
                            dialog_partner = ''
                    if conversationType == 30:
                        conversationType = "Call (Start)"
                        callDuration = conversation[6]
                    elif conversationType == 39:
                        conversationType = "Call (End)"
                        callDuration = conversation[6]
                    elif conversationType == 61:
                        conversationType = "Text Message"
                        message = conversation[5]
                    elif conversationType == 50:
                        conversationType = "Contact Invitation"
                    elif conversationType == 51:
                        conversationType = "Contact Acceptance"
                    
                    dateUnix = float(timestamp)
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S',  time.gmtime(dateUnix))
                    
                    database_connector.export_skype_conversation(curr_dir, skypeAccountID, author, author_Fullname, dialog_Partner, conversationType, message, callDuration, timestamp)
                aft_log.log("analyzeDbs: Skype details extracted successfully!", 2)
                conn.close()    
            except:
                aft_log.log("connectDB: Unable to connect to the skype database!", 2)
    
def analyze_account(curr_dir, database_dir):
    global deviceID
    aft_log.log("analyzeDBs: ->[ Obtaining Account details ]<-", 2)
    # Preparation to connect to the accounts database
    try:
        # Preparation to connect to the accounts database
        conn = sqlite3.connect(os.path.join(database_dir, "accounts.db"))
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM accounts")
        # Obtain the number of accounts in the device
        num_entries = cursor.fetchone()[0]
        
        if num_entries > 0:
            cursor.execute("SELECT name, type FROM accounts")
            results = cursor.fetchall()
            
            for result in results:
                name = result[0]
                account_type = result[1]
                    
                database_connector.export_accounts(curr_dir, deviceID, name, account_type)
                
            aft_log.log("extractDBs: Accounts extracted successfully!", 2)
        else:
            aft_log.log("analyzeDBs: There are no Accounts!", 2)
    except:
        aft_log.log("connectDB: Accounts database not found!", 2)
        
def analyze_mail(curr_dir, database_dir):
    global deviceID
    aft_log.log("analyzeDBs: ->[ Obtaining Emails ]<-", 2)
    
    database_list = os.listdir(database_dir)
    mail_accounts = []
    for database in database_list:
        if database.startswith('mailstore'):
            mail_accounts.append(database)
    
    for account in mail_accounts:
        # Preparation to connect to the email database
        emailAddress = account.replace("mailstore.", '')
        emailAddress = emailAddress.replace(".db", '')
        accountID = database_connector.get_account_id(curr_dir, emailAddress)
        if accountID == 0:
            database_connector.export_accounts(curr_dir, deviceID, emailAddress, "com.google")
            accountID = database_connector.get_account_id(curr_dir, emailAddress)
        
        os.chdir('..')
        sqlite_dir = os.path.join(os.getcwd(), account)
        file_dir = os.path.join(database_dir, account)
        shutil.move(file_dir, sqlite_dir)
        
        sql = 'SELECT fromAddress, toAddresses, dateSentMS, subject, snippet FROM messages'
        events_arr = database_connector.read_sqlite(account, sql)
        shutil.move(sqlite_dir, file_dir)
        os.chdir(curr_dir)
        if len(events_arr) > 0:
            
            for i in range(0, len(events_arr), 5):
                fromAddress = str.strip(events_arr[i]).split(' = ')[1]
                toAddresses = (str.strip(events_arr[i+1]).split(' = '))[1]
                dateSendMS = str.strip(events_arr[i+2]).split(' = ')[1]
                subject = str.strip(events_arr[i+3]).split(' = ')[1]
                snippet = str.strip(events_arr[i+4]).split(' = ')[1]
                
                dateTime = int(dateSendMS)
                
                # Convert date to human readable format
                realdate = time.strftime('%Y-%m-%d %H:%M:%S',  time.gmtime(dateTime/1000))
                
                database_connector.export_email(curr_dir, accountID, fromAddress, toAddresses, realdate, subject, snippet)
                
            aft_log.log("extractDBs: Email extracted successfully!", 2)
        else:
            aft_log.log("analyzeDBs: There are no emails", 2)

def exportToXLSDeep(sheet, dataColumns, dataRows):
    colStyle = xlwt.easyxf('pattern: pattern solid, fore_color yellow;font: name Times New Roman, color-index red, bold on', num_format_str='#,##0.00')

    count = 0

    for col in dataColumns:
        sheet.write(0, count, col, colStyle)
        sheet.col(count).width = 256 * (len(col) + 1) 
        count = count + 1

    countRow = 1

    for row in dataRows:
        countCol = 0 
        for rowData in row:
            if isinstance(rowData,basestring):
                rowData = rowData.encode('utf-8')
            sheet.write(countRow, countCol, rowData)
            if sheet.col(countCol).width < 256 * (len(str(rowData)) + 1):
                if 256 * (len(str(rowData)) + 1) > 15000:
                    sheet.col(countCol).width = 15000
                else:
                    sheet.col(countCol).width = 256 * (len(str(rowData)) + 1) 
            countCol = countCol + 1
        countRow = countRow + 1
  
def export_to_xls(curr_dir, xls_dir, dateTime):
    aft_log.log("\n============== Export Results ================\n", 2)
    global deviceID
    
    book = xlwt.Workbook(encoding="utf-8")
    
    # Connect to the local database
    os.chdir('..')
    conn = sqlite3.connect('SMDF.sqlite')
    cursor = conn.cursor()
    
    # Device table
    sheet = book.add_sheet("Device Information")
    cursor.execute("SELECT serialNumber, model, os, manufacturer, IMEI, timeExtracted FROM Device WHERE deviceID = '{0}'".format(deviceID))
    dataRows = cursor.fetchall() # Retrieve a list of rows
    dataColumns = list(map(lambda x: x[0], cursor.description)) # Retrieve a list of column
    exportToXLSDeep(sheet, dataColumns, dataRows)
    
    # Applications table
    sheet = book.add_sheet("Application")
    cursor.execute("SELECT application_name FROM Application WHERE deviceID = '{0}'".format(deviceID))
    dataRows = cursor.fetchall() # Retrieve a list of rows
    dataColumns = list(map(lambda x: x[0], cursor.description)) # Retrieve a list of columns
    exportToXLSDeep(sheet, dataColumns, dataRows)
    
    # Contact table
    sheet = book.add_sheet("Contact")
    cursor.execute("SELECT contactID, contactName FROM Contact WHERE deviceID = '{0}'".format(deviceID))
    dataRows = cursor.fetchall() # Retrieve a list of rows
    dataColumns = list(map(lambda x: x[0], cursor.description)) # Retrieve a list of columns
    exportToXLSDeep(sheet, dataColumns, dataRows)
    
    # Get contact id associated with this device
    cursor.execute("SELECT contactID FROM Contact WHERE deviceID = '{0}'".format(deviceID))
    contactIDs = cursor.fetchall()
    contactIDLists = []
    for contactID in contactIDs:
        for data in contactID:
            contactIDLists.append(str(data))
            
    if len(contactIDLists) == 1:
        contactIDQuery = contactIDLists[0]
    elif len(contactIDLists) > 1:
        contactIDQuery = ','.join(contactIDLists)
        
    # ContactDetails table
    sheet = book.add_sheet("Contact Details")
    cursor.execute("SELECT contactID, detailType, detail FROM ContactDetails WHERE contactID IN ({0})".format(contactIDQuery))
    dataRows = cursor.fetchall() # Retrieve a list of rows
    dataColumns = list(map(lambda x: x[0], cursor.description)) # Retrieve a list of columns
    exportToXLSDeep(sheet, dataColumns, dataRows)
    
    # ContactEmail table
    sheet = book.add_sheet("Contact Email")
    cursor.execute("SELECT contactID, emailType, email FROM ContactEmail WHERE contactID IN ({0})".format(contactIDQuery))
    dataRows = cursor.fetchall() # Retrieve a list of rows
    dataColumns = list(map(lambda x: x[0], cursor.description)) # Retrieve a list of columns
    exportToXLSDeep(sheet, dataColumns, dataRows)
    
    # ContactNumber table
    sheet = book.add_sheet("Contact Number")
    cursor.execute("SELECT contactID, numberType, number FROM ContactNumber WHERE contactID IN ({0})".format(contactIDQuery))
    dataRows = cursor.fetchall() # Retrieve a list of rows
    dataColumns = list(map(lambda x: x[0], cursor.description)) # Retrieve a list of columns
    exportToXLSDeep(sheet, dataColumns, dataRows)
    
    # CallLogs table
    sheet = book.add_sheet("Call Logs")
    cursor.execute("SELECT number, status, duration, timeCalled FROM CallLogs WHERE deviceID = '{0}'".format(deviceID))
    dataRows = cursor.fetchall() # Retrieve a list of rows
    dataColumns = list(map(lambda x: x[0], cursor.description)) # Retrieve a list of columns
    exportToXLSDeep(sheet, dataColumns, dataRows)
    
    # Browser History table
    sheet = book.add_sheet("Browser History")
    cursor.execute("SELECT browserType, title, url, lastVisited, visitCount FROM BrowserHistory WHERE deviceID = '{0}'".format(deviceID))
    dataRows = cursor.fetchall() # Retrieve a list of rows
    dataColumns = list(map(lambda x: x[0], cursor.description)) # Retrieve a list of columns
    exportToXLSDeep(sheet, dataColumns, dataRows)
    
    # Browser Bookmark table
    sheet = book.add_sheet("Browser Bookmark")
    cursor.execute("SELECT browserType, title, URL, dateCreated FROM BrowserBookmark WHERE deviceID = '{0}'".format(deviceID))
    dataRows = cursor.fetchall() # Retrieve a list of rows
    dataColumns = list(map(lambda x: x[0], cursor.description)) # Retrieve a list of columns
    exportToXLSDeep(sheet, dataColumns, dataRows)
    
    # Browser Search table
    sheet = book.add_sheet("Browser Search")
    cursor.execute("SELECT browserType, search, date FROM BrowserSearch WHERE deviceID = '{0}'".format(deviceID))
    dataRows = cursor.fetchall() # Retrieve a list of rows
    dataColumns = list(map(lambda x: x[0], cursor.description)) # Retrieve a list of columns
    exportToXLSDeep(sheet, dataColumns, dataRows)
    
    # SMS table
    sheet = book.add_sheet("SMS History")
    cursor.execute("SELECT address, dateTime, messageType, message FROM SMSHistory WHERE deviceID = '{0}'".format(deviceID))
    dataRows = cursor.fetchall() # Retrieve a list of rows
    dataColumns = list(map(lambda x: x[0], cursor.description)) # Retrieve a list of columns
    exportToXLSDeep(sheet, dataColumns, dataRows)
    
    # SkypeAccount table
    sheet = book.add_sheet("Skype Account")
    cursor.execute("SELECT skypeAccountID, skypename, fullname, liveid_membername, birthday, gender, languages, country, province, city, phone_home, phone_office, phone_mobile, about_me, emails, lastUpdated_profile, mood_text, lastUpdated_mood FROM SkypeAccount WHERE deviceID = '{0}'".format(deviceID))
    dataRows = cursor.fetchall() # Retrieve a list of rows
    dataColumns = list(map(lambda x: x[0], cursor.description)) # Retrieve a list of columns
    exportToXLSDeep(sheet, dataColumns, dataRows)
    
    cursor.execute("SELECT skypeAccountID FROM SkypeAccount WHERE deviceID = '{0}'".format(deviceID))
    skypeAccountIDs = cursor.fetchall() # Retrieve a list of skypeAccountID
    
    skypeAccountIDLists = []
    for skypeAccountID in skypeAccountIDs:
        for data in skypeAccountID:
            skypeAccountIDLists.append(str(data))
            
    if len(skypeAccountIDLists) == 1:
        skypeAccountIDQuery = skypeAccountIDLists[0]
    elif len(skypeAccountIDLists) > 1:
        skypeAccountIDQuery = ','.join(skypeAccountIDLists)
    
    # SkypeContact table
    sheet = book.add_sheet("Skype Contact")
    cursor.execute("SELECT * FROM SkypeContact WHERE skypeAccountID IN ({0})".format(skypeAccountIDQuery))
    dataRows = cursor.fetchall() # Retrieve a list of rows
    dataColumns = list(map(lambda x: x[0], cursor.description)) # Retrieve a list of columns
    exportToXLSDeep(sheet, dataColumns, dataRows)
    
    # SkypeConversation table
    sheet = book.add_sheet("Skype Conversation")
    cursor.execute("SELECT * FROM SkypeConversation WHERE skypeAccountID IN ({0})".format(skypeAccountIDQuery))
    dataRows = cursor.fetchall() # Retrieve a list of rows
    dataColumns = list(map(lambda x: x[0], cursor.description)) # Retrieve a list of columns
    exportToXLSDeep(sheet, dataColumns, dataRows)
    
    # Accounts table
    sheet = book.add_sheet("Accounts")
    cursor.execute("SELECT accountID, name, type FROM Accounts WHERE deviceID = '{0}'".format(deviceID))
    dataRows = cursor.fetchall() # Retrieve a list of rows
    dataColumns = list(map(lambda x: x[0], cursor.description)) # Retrieve a list of columns
    exportToXLSDeep(sheet, dataColumns, dataRows)
    
    cursor.execute("SELECT contactID FROM Contact WHERE deviceID = '{0}'".format(deviceID))
    contactIDs = cursor.fetchall()
    contactIDLists = []
    for contactID in contactIDs:
        for data in contactID:
            contactIDLists.append(str(data))
            
    if len(contactIDLists) == 1:
        contactIDQuery = contactIDLists[0]
    elif len(contactIDLists) > 1:
        contactIDQuery = ','.join(contactIDLists)
    
    # Join the current working directory with the new export filename (timeString)
    dateTime = "Device Details_" + dateTime
    filename = os.path.join(xls_dir, dateTime)
    
    book.save(filename + ".xls")
    aft_log.log("exportDBs: Export of various data successfully!", 2)
    
   
