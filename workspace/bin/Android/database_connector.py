# Imports
import aft_log
import sqlite3
import os
import subprocess
import StringIO

def export_phone_details(curr_dir, os_version, device_manufacturer, device_model, device_name, device_IMEI, examination_time):
    os.chdir('..')
    print "Sending phone details..."
    try:
        # Establish database connection and create a cursor
        tempConn = sqlite3.connect('SMDF.sqlite')
        tempCurr = tempConn.cursor()

        # Insert data into Device table
        tempCurr.execute("INSERT INTO Device VALUES (NULL,'{0}','{1}','{2}','{3}','{4}','{5}')"
                    .format(os_version, device_manufacturer, device_model, device_name, device_IMEI, examination_time))
        
        # Commit to database (Update)
        tempConn.commit()

        # Close database connection
        tempConn.close()
        aft_log.log("ExportDB: -> Phone details successfully exported!", 2)
    except:
        aft_log.log("ExportDB: -> Connection to DB failed!", 2)
    os.chdir(curr_dir)

def get_device_id(curr_dir, device_name):
    os.chdir('..')
    try:
        # Establish database connection and create a cursor
        tempConn = sqlite3.connect('SMDF.sqlite')
        tempCurr = tempConn.cursor()

        tempCurr.execute("SELECT deviceID FROM Device WHERE serialNumber = '{0}' ORDER BY deviceID DESC".format(device_name))
        deviceID = tempCurr.fetchone()[0]

        # Close database connection
        tempConn.close()
    except:
        print ""
    os.chdir(curr_dir)
    return deviceID

def export_contact(curr_dir, deviceID, contactName):
    os.chdir('..')
    contactID = 0
    try:
        # Establish database connection and create a cursor
        tempConn = sqlite3.connect('SMDF.sqlite')
        tempCurr = tempConn.cursor()

        # Insert data into Contact table
        tempCurr.execute("INSERT INTO Contact VALUES (NULL,{0},'{1}')".format(deviceID, contactName))
        # Commit to database (Update)
        tempConn.commit()
        
        tempCurr.execute("SELECT contactID FROM Contact WHERE contactName = '{0}' ORDER BY contactID DESC".format(contactName))
        contactID = tempCurr.fetchone()[0]

        # Close database connection
        tempConn.close()
    except:
        aft_log.log("ExportDB: -> Error in creating contact!", 2)
    os.chdir(curr_dir)
    return contactID

def export_contact_email(curr_dir, contactID, emailType, email):
    os.chdir('..')
    try:
        # Establish database connection and create a cursor
        tempConn = sqlite3.connect('SMDF.sqlite')
        tempCurr = tempConn.cursor()

        # Insert data into Contact table
        tempCurr.execute("INSERT INTO ContactEmail VALUES (NULL,{0},'{1}','{2}')".format(contactID, emailType, email))
        # Commit to database (Update)
        tempConn.commit()

        # Close database connection
        tempConn.close()
    except:
        aft_log.log("ExportDB: -> Error in exporting contact email!", 2)
    os.chdir(curr_dir)
    
def export_contact_details(curr_dir, contactID, detailType, detail):
    os.chdir('..')
    try:
        # Establish database connection and create a cursor
        tempConn = sqlite3.connect('SMDF.sqlite')
        tempCurr = tempConn.cursor()

        # Insert data into Contact table
        tempCurr.execute("INSERT INTO ContactDetails VALUES (NULL,{0},'{1}','{2}')".format(contactID, detailType, detail))
        # Commit to database (Update)
        tempConn.commit()

        # Close database connection
        tempConn.close()
    except:
        aft_log.log("ExportDB: -> Error in exporting contact details!", 2)
    os.chdir(curr_dir)
    
def export_contact_number(curr_dir, contactID, numberType, number):
    os.chdir('..')
    try:
        # Establish database connection and create a cursor
        tempConn = sqlite3.connect('SMDF.sqlite')
        tempCurr = tempConn.cursor()

        # Insert data into Contact table
        tempCurr.execute("INSERT INTO ContactNumber VALUES (NULL,{0},'{1}','{2}')".format(contactID, numberType, number))
        # Commit to database (Update)
        tempConn.commit()

        # Close database connection
        tempConn.close()
    except:
        aft_log.log("ExportDB: -> Error in exporting contact number!", 2)
    os.chdir(curr_dir)
    
def export_call_logs(curr_dir, deviceID, number, duration, timeCalled, status):
    os.chdir('..')
    try:
        # Establish database connection and create a cursor
        tempConn = sqlite3.connect('SMDF.sqlite')
        tempCurr = tempConn.cursor()

        # Insert data into Contact table
        tempCurr.execute("INSERT INTO CallLogs VALUES (NULL,{0},'{1}', '{2}', '{3}', '{4}')".format(deviceID, number, duration, timeCalled, status))
        # Commit to database (Update)
        tempConn.commit()

        # Close database connection
        tempConn.close()
    except:
        aft_log.log("ExportDB: -> Error in exporting call logs!", 2)
    os.chdir(curr_dir)
    
def export_browser_history(curr_dir, deviceID, browserType, title, url, lastVisited, visitCount):
    os.chdir('..')
    try:
        # Establish database connection and create a cursor
        tempConn = sqlite3.connect('SMDF.sqlite')
        tempCurr = tempConn.cursor()

        # Insert data into BrowserHistory table
        tempCurr.execute("INSERT INTO BrowserHistory VALUES (NULL, {0},'{1}', '{2}', '{3}', '{4}', '{5}', NULL)".format(deviceID, browserType, title, url, lastVisited, visitCount))
        # Commit to database (Update)
        tempConn.commit()

        # Close database connection
        tempConn.close()
    except:
        aft_log.log("ExportDB: -> Error in exporting browser History!", 2)
    os.chdir(curr_dir)
    
def export_browser_bookmarks(curr_dir, deviceID, browserType, title, url, dateCreated):
    os.chdir('..')
    try:
        # Establish database connection and create a cursor
        tempConn = sqlite3.connect('SMDF.sqlite')
        tempCurr = tempConn.cursor()

        # Insert data into BrowserHistory table
        tempCurr.execute("INSERT INTO BrowserBookmark VALUES (NULL, {0}, '{1}', '{2}', '{3}', '{4}')".format(deviceID, browserType, title, url, dateCreated))
        # Commit to database (Update)
        tempConn.commit()

        # Close database connection
        tempConn.close()
    except:
        aft_log.log("ExportDB: -> Error in exporting browser bookmarks!", 2)
    os.chdir(curr_dir)

def export_browser_search(curr_dir, deviceID, browserType, search, date):
    os.chdir('..')
    try:
        # Establish database connection and create a cursor
        tempConn = sqlite3.connect('SMDF.sqlite')
        tempCurr = tempConn.cursor()

        # Insert data into BrowserSearch table
        tempCurr.execute("INSERT INTO BrowserSearch VALUES (NULL, {0},'{1}', '{2}', '{3}')".format(deviceID, browserType, search, date))
        # Commit to database (Update)
        tempConn.commit()

        # Close database connection
        tempConn.close()
    except:
        aft_log.log("ExportDB: -> Error in exporting browser search!", 2)
    os.chdir(curr_dir)

def export_sms(curr_dir, deviceID, address, messageType, message, dateTime):
    os.chdir('..')
    try:
        # Establish database connection and create a cursor
        tempConn = sqlite3.connect('SMDF.sqlite')
        tempCurr = tempConn.cursor()

        # Insert data into Contact table
        tempCurr.execute("INSERT INTO SMSHistory VALUES (NULL, {0}, '{1}', '{2}', '{3}', '{4}')".format(deviceID, address, messageType, message, dateTime))
        # Commit to database (Update)
        tempConn.commit()

        # Close database connection
        tempConn.close()
    except:
        aft_log.log("ExportDB: -> Error in exporting sms history!", 2)
    os.chdir(curr_dir)
    
def export_skype_account(curr_dir, deviceID, skypeName, fullName, liveid_membername, birthday, gender, language, country, province, city, phone_home, phone_office, phone_mobile, aboutMe, emails, lastUpdatedProfile, moodText, lastUpdatedMood):
    os.chdir('..')
    try:
        # Establish database connection and create a cursor
        tempConn = sqlite3.connect('SMDF.sqlite')
        tempCurr = tempConn.cursor()

        # Insert data into Contact table
        tempCurr.execute("INSERT INTO SkypeAccount VALUES (NULL, {0}, '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}', '{8}', '{9}', '{10}', '{11}', '{12}', '{13}', '{14}', '{15}', '{16}', '{17}')".format(deviceID, skypeName, fullName, liveid_membername, birthday, gender, language, country, province, city, phone_home, phone_office, phone_mobile, aboutMe, emails, lastUpdatedProfile, moodText, lastUpdatedMood))
        # Commit to database (Update)
        tempConn.commit()

        # Close database connection
        tempConn.close()
    except:
        aft_log.log("ExportDB: -> Error in exporting skype accounts!", 2)
    os.chdir(curr_dir)

def get_skype_account_id(curr_dir, deviceID, skypeName):
    os.chdir('..')
    try:
        # Establish database connection and create a cursor
        tempConn = sqlite3.connect('SMDF.sqlite')
        tempCurr = tempConn.cursor()

        tempCurr.execute("SELECT skypeAccountID FROM SkypeAccount WHERE deviceID = '{0}' AND skypename = '{1}'".format(deviceID, skypeName))
        skypeAccountID = tempCurr.fetchone()[0]

        # Close database connection
        tempConn.close()
    except:
        print ""
    os.chdir(curr_dir)
    return skypeAccountID

def export_skype_contact(curr_dir, skypeAccountID, skypeName, displayName, lastOnlineTimestamp, birthday, gender, language, country, province, city, phone_home, phone_office, phone_mobile, aboutMe, emails, lastUpdatedProfile, moodText):
    os.chdir('..')
    try:
        # Establish database connection and create a cursor
        tempConn = sqlite3.connect('SMDF.sqlite')
        tempCurr = tempConn.cursor()

        # Insert data into Contact table
        tempCurr.execute("INSERT INTO SkypeContact VALUES (NULL, {0}, '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}', '{8}', '{9}', '{10}', '{11}', '{12}', '{13}', '{14}', '{15}', '{16}')".format(skypeAccountID, skypeName, displayName, lastOnlineTimestamp, birthday, gender, language, country, province, city, phone_home, phone_office, phone_mobile, aboutMe, emails, lastUpdatedProfile, moodText))
        # Commit to database (Update)
        tempConn.commit()

        # Close database connection
        tempConn.close()
    except:
        aft_log.log("ExportDB: -> Error in exporting skype accounts!", 2)
    os.chdir(curr_dir)
    
def export_skype_conversation(curr_dir, skypeAccountID, author, author_Fullname, dialog_Partner, conversationType, message, callDuration, timestamp):
    os.chdir('..')
    try:
        # Establish database connection and create a cursor
        tempConn = sqlite3.connect('SMDF.sqlite')
        tempCurr = tempConn.cursor()

        # Insert data into Contact table
        tempCurr.execute("INSERT INTO SkypeConversation VALUES (NULL, {0}, '{1}', '{2}', '{3}', '{4}', '{5}', {6}, '{7}')".format(skypeAccountID, author, author_Fullname, dialog_Partner, conversationType, message, callDuration, timestamp))
        # Commit to database (Update)
        tempConn.commit()

        # Close database connection
        tempConn.close()
    except:
        aft_log.log("ExportDB: -> Error in exporting skype accounts!", 2)
    os.chdir(curr_dir)    

def export_application(curr_dir, device_id, application):
    os.chdir('..')
    try:
        # Establish database connection and create a cursor
        tempConn = sqlite3.connect('SMDF.sqlite')
        tempCurr = tempConn.cursor()

        # Insert data into Application table
        tempCurr.execute("INSERT INTO Application VALUES (NULL, {0}, '{1}')".format(device_id, application))
        # Commit to database (Update)
        tempConn.commit()

        # Close database connection
        tempConn.close()
    except:
        aft_log.log("ExportDB: -> Error in exporting application list!", 2)
    os.chdir(curr_dir) 
    
def export_accounts(curr_dir, deviceID, name, accountType):
    os.chdir('..')
    try:
        # Establish database connection and create a cursor
        tempConn = sqlite3.connect('SMDF.sqlite')
        tempCurr = tempConn.cursor()

        # Insert data into Application table
        tempCurr.execute("INSERT INTO Accounts VALUES (NULL, {0}, '{1}', '{2}')".format(deviceID, name, accountType))
        # Commit to database (Update)
        tempConn.commit()

        # Close database connection
        tempConn.close()
    except:
        aft_log.log("ExportDB: -> Error in exporting accounts!", 2)
    os.chdir(curr_dir) 
    
def get_account_id(curr_dir, name):
    os.chdir('..')
    accountID = 0
    try:
        # Establish database connection and create a cursor
        tempConn = sqlite3.connect('SMDF.sqlite')
        tempCurr = tempConn.cursor()

        tempCurr.execute("SELECT accountID FROM Accounts WHERE name = '{0}' ORDER BY deviceID DESC".format(name))
        accountID = tempCurr.fetchone()[0]

        # Close database connection
        tempConn.close()
    except:
        print ""
    os.chdir(curr_dir)
    if accountID:
        return accountID
    else:
        return 0
    
def export_email(curr_dir, accountID, fromAddress, toAddresses, timestamp, subject, message):
    os.chdir('..')
    try:
        # Establish database connection and create a cursor
        tempConn = sqlite3.connect('SMDF.sqlite')
        tempCurr = tempConn.cursor()

        # Insert data into Application table
        tempCurr.execute("INSERT INTO Mail VALUES (NULL, {0}, '{1}', '{2}', '{3}', '{4}', '{5}')".format(accountID, fromAddress, toAddresses, timestamp, subject, message))
        # Commit to database (Update)
        tempConn.commit()

        # Close database connection
        tempConn.close()
    except:
        aft_log.log("ExportDB: -> Error in exporting accounts!", 2)
    os.chdir(curr_dir) 

def read_sqlite(sqlite_path, sql):
    command = ['sqlite3.exe', '-line', sqlite_path, sql]
    p =subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if err:
        return []
    events = ''
    for line in StringIO.StringIO(out).readlines():
        if line == '\r\n' or line == '\n':
            continue
        events += line
    events_arr = events.split('\r\n')
    events_arr.pop()
    return events_arr