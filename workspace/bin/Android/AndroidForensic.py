# Imports
import argparse
import os
import subprocess
import sys
import shutil
import datetime

import aft_log
import analyze_databases
import extract_files
import database_connector

# Variables
adbPath = ""
curr_dir = ""

# DATE & TIME
DATE = str(datetime.datetime.today()).split(' ')[0]
TIME = str(datetime.datetime.today()).split(' ')[1].split('.')[0].split(':')

def backupProcess():
    curr_dir = os.getcwd()
    adbPath = os.path.join(curr_dir, "tools", "adb.exe")
    # Check if there is a smartphone or emulator connected
    if len(subprocess.Popen([adbPath, 'devices'], stdout=subprocess.PIPE).communicate(0)[0].split()) > 4:
        # Create backup directory
        try:
            device_name = subprocess.Popen([adbPath, 'devices'], stdout=subprocess.PIPE).communicate(0)[0].split()[4]
        except:
            print "Error! No Android smartphone connected! Check if the relevant drivers is installed."
            print "Terminating Android Forensic Tool"
            sys.exit(3) # indicates that no smartphone or emulator was connected to the PC
            
        # Get Android OS version which is running on the connected device
        try:
            os_version = subprocess.Popen([adbPath, 'shell', 'getprop', 'ro.build.version.release'], stdout=subprocess.PIPE).communicate(0)[0].split()[0]
        except:
            os_version = subprocess.Popen([adbPath, 'shell', 'getprop', 'ro.build.version.release'], stdout=subprocess.PIPE).communicate(0)[0]
        os_version2 = os_version.replace(".", "")
        if len(os_version2) < 3:
            os_version2 = os_version2.join("0")
            
        if (os.path.exists(os.path.join(curr_dir, "Cases"))):
            pass
        else:
            os.mkdir("Cases")
            
        backup_dir = os.path.join(curr_dir, "Cases", DATE + "__" + TIME[0] + "-" + TIME[1] + "-" + TIME[2] + "__" + device_name + "__Backup")
        os.mkdir(backup_dir)
        
        aft_log.LOG_LEVEL_GLOBAL = 4
        log_file = backup_dir + "/log/aft.log"
        os.mkdir(backup_dir + "/log")
        aft_log.FILE_HANDLE = open(log_file, "a+")
        aft_log.log("==============================================", 2)
        aft_log.log("| Android Forensic Tool v1.0 by Team Blazers |", 2)
        aft_log.log("==============================================", 2)
        
        print "\nConnecting to device: " + device_name
        # Collect and display device information
        aft_log.log("====== Forensic Examination Information ======", 2)
        print "Begin extraction of data, please wait..."
        examination_time = DATE + "  " + TIME[0] + ":" + TIME[1] + ":" + TIME[2]
        aft_log.log("Device Serial Number: " + device_name + "\nDate of Examination: "  + examination_time + "\nDevice is running: Android OS v" + os_version, 2)
        
        # Get Device manufacturer
        try:
            device_manufacturer = subprocess.Popen([adbPath, 'shell', 'getprop', 'ro.product.manufacturer'], stdout=subprocess.PIPE).communicate(0)[0].split()[0]
        except:
            device_manufacturer = subprocess.Popen([adbPath, 'shell', 'getprop', 'ro.product.manufacturer'], stdout=subprocess.PIPE).communicate(0)[0]
        aft_log.log("Device Manufacturer: " + device_manufacturer, 2)
        # Get Device model
        s = subprocess.Popen([adbPath, 'shell', 'getprop', 'ro.product.model'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        device_model,err = s.communicate()
        device_model = device_model.replace('\n', '')
        aft_log.log("Device Model: " + device_model, 2)
        # Get Device IMEI
        temp_string = subprocess.Popen([adbPath, 'shell', 'dumpsys', 'iphonesubinfo'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(0)[0]
        device_IMEI = temp_string.split("Device ID = ", 1)[1]
        device_IMEI = device_IMEI.replace('\n', '')
        aft_log.log("Device IMEI Number: " + device_IMEI, 2)
        print ""
        
        # Dump system info
        print "Collecting system dump"
        command = adbPath + ' shell dumpsys'
        s = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out,err = s.communicate()
        with open("sysdump.txt", "w+") as text_file:
            text_file.write(out)
        # move file
        shutil.move('sysdump.txt',os.path.join(backup_dir, "sysdump.txt"))
        aft_log.log("System dump collected\n", 2)
        extractorPath = os.path.join(curr_dir, "tools", "extractor")
        
        # Start the extraction of information
        #command = adbPath + ' pull /data/data/com.android.providers.contacts/databases/contacts2.db C:\\'
        aft_log.log("=========== Conducting Full Backup ===========", 2)
        print "Please unlock device and approve the backup procedure without any password indicated"
        command = adbPath + ' backup -f backup.ab -apk -shared -all -system'
        subprocess.Popen(command, stdout=subprocess.PIPE).communicate(0)[0]
        
        # Copy the backup file into the java directory
        shutil.move("backup.ab", os.path.join(extractorPath, "backup.ab"))
        print "Converting backup to tar version..."
        
        # Change the current working directory for java to work
        save_dir = curr_dir
        os.chdir(extractorPath)
        
        # Convert the backup file to a tar file
        command = 'java -jar abe.jar unpack backup.ab backup.tar'
        s = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out,err = s.communicate()
        print out
        
        # Copy the various file into the case directory
        shutil.move("backup.ab", os.path.join(backup_dir, "backup.ab"))
        extractorPath = os.path.join(save_dir, "tools", "7z")
        shutil.move("backup.tar", os.path.join(extractorPath, "backup.tar"))
        
        # Change back to the original directory
        os.chdir(save_dir)
        extracted_dir = os.path.join(backup_dir, "backup")
        
        # Change the current working directory for 7z to extract the file
        os.chdir(extractorPath)
        print "Extracting tar file..."
        command = '7z.exe x backup.tar -o*'
        subprocess.Popen(command, stdout=subprocess.PIPE).communicate(0)[0]
        
        # Copy the various file into the case directory
        shutil.move("backup.tar", os.path.join(backup_dir, "backup.tar"))
        shutil.move(os.path.join(curr_dir, "tools", "7z","backup"), extracted_dir)
        
        aft_log.log("Backup successfully created\n", 2)
        os.chdir(save_dir)
        endingMessage(backup_dir)
        
        # Closing Log File
        aft_log.FILE_HANDLE.close()
    
    else:
        print "Error! No Android smartphone connected! "
        print "Check if the relevant drivers is installed"
        print "Terminating Android Forensic Tool..."
        sys.exit(3) # indicates that no smartphone or emulator was connected to the PC
    
def extractionProcess():
    curr_dir = os.getcwd()
    adbPath = os.path.join(curr_dir, "tools", "adb.exe")
    # Check if there is a smartphone or emulator connected
    if len(subprocess.Popen([adbPath, 'devices'], stdout=subprocess.PIPE).communicate(0)[0].split()) > 4:
        # Create backup directory
        try:
            device_name = subprocess.Popen([adbPath, 'devices'], stdout=subprocess.PIPE).communicate(0)[0].split()[4]
        except:
            print "Error! No Android smartphone connected! Check if the relevant drivers is installed."
            print "Terminating Android Forensic Tool"
            sys.exit(3) # indicates that no smartphone or emulator was connected to the PC
        
        # Starting the daemon with root privileges
        try:
            subprocess.Popen([adbPath, 'root']).wait()
        except:
            print ""
        # Get Android OS version which is running on the connected device
        try:
            os_version = subprocess.Popen([adbPath, 'shell', 'getprop', 'ro.build.version.release'], stdout=subprocess.PIPE).communicate(0)[0].split()[0]
        except:
            os_version = subprocess.Popen([adbPath, 'shell', 'getprop', 'ro.build.version.release'], stdout=subprocess.PIPE).communicate(0)[0]
        os_version2 = os_version.replace(".", "")
        if len(os_version2) < 3:
            os_version2 = os_version2.join("0")
            
        if (os.path.exists(os.path.join(curr_dir, "Cases"))):
            print ""
        else:
            os.mkdir("Cases")
        backup_dir = os.path.join(curr_dir, "Cases", DATE + "__" + TIME[0] + "-" + TIME[1] + "-" + TIME[2] + "__" + device_name + "__" + "Extraction")
        os.mkdir(backup_dir)
        
        aft_log.LOG_LEVEL_GLOBAL = 4
        log_file = backup_dir + "/log/aft.log"
        os.mkdir(backup_dir + "/log")
        aft_log.FILE_HANDLE = open(log_file, "a+")
        aft_log.log("==============================================", 2)
        aft_log.log("| Android Forensic Tool v1.0 by Team Blazers |", 2)
        aft_log.log("==============================================", 2)
        
        print "\nConnecting to device: " + device_name
        serialExist = True
        try:
            getDeviceSerial = database_connector.get_device_id(curr_dir, device_name)
            if getDeviceSerial > 0:
                serialExist = True
            else:
                serialExist = False
        except:
            serialExist = False
        
        if serialExist == False:
            # Collect and display device information
            aft_log.log("====== Forensic Examination Information ======", 2)
            print "Begin extraction of data, please wait..."
            examination_time = DATE + "  " + TIME[0] + ":" + TIME[1] + ":" + TIME[2]
            aft_log.log("Device Serial Number: " + device_name + "\nDate of Examination: "  + examination_time + "\nDevice is running: Android OS v" + os_version, 2)
            
            # Get Device manufacturer
            try:
                device_manufacturer = subprocess.Popen([adbPath, 'shell', 'getprop', 'ro.product.manufacturer'], stdout=subprocess.PIPE).communicate(0)[0].split()[0]
            except:
                device_manufacturer = subprocess.Popen([adbPath, 'shell', 'getprop', 'ro.product.manufacturer'], stdout=subprocess.PIPE).communicate(0)[0]
            aft_log.log("Device Manufacturer: " + device_manufacturer, 2)
            # Get Device model
            s = subprocess.Popen([adbPath, 'shell', 'getprop', 'ro.product.model'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            device_model,err = s.communicate()
            device_model = device_model.replace('\n', '')
            aft_log.log("Device Model: " + device_model, 2)
            # Get Device IMEI
            temp_string = subprocess.Popen([adbPath, 'shell', 'dumpsys', 'iphonesubinfo'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(0)[0]
            device_IMEI = temp_string.split("Device ID = ", 1)[1]
            device_IMEI = device_IMEI.replace('\n', '')
            aft_log.log("Device IMEI Number: " + device_IMEI, 2)
            print ""
            
            # Dump system info
            print "Collecting system dump"
            command = adbPath + ' shell dumpsys'
            s = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out,err = s.communicate()
            with open("sysdump.txt", "w+") as text_file:
                text_file.write(out)
            # move file
            shutil.move('sysdump.txt',os.path.join(backup_dir, "sysdump.txt"))
            aft_log.log("System dump collected\n", 2)
            
            # Begin the extraction of data
            file_dir = os.path.join(backup_dir, 'databases')
            os.mkdir(file_dir)
            # Pictures
            picture_dir = os.path.join(backup_dir, 'pictures')
            os.mkdir(picture_dir)
            # Extract databases
            extractDatabases(curr_dir, file_dir, picture_dir, os_version, device_name)
            xls_dir = os.path.join(backup_dir, 'xls')
            os.mkdir(xls_dir)
            
            print ""
            print "Obtaining application list..."
            cmd = adbPath + ' shell pm list packages'
            s = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out,err = s.communicate()
            s = out.replace("package:","")
            application_list = s.split('\r\n')
            print "Application list obtained"
            
            # Analyze Databases
            # analyzes the dumped databases and convert it into a xls format
            aft_log.log("\n============= Database Analysis ==============\n", 2)
            aft_log.log("analyzeDBs: -> starting to analyze the databases....", 0)
            # Obtain phone details  
            analyze_databases.analyze_phone_details(curr_dir, file_dir, os_version, device_manufacturer, device_model, device_name, device_IMEI, examination_time)
            # Obtain the applications list
            analyze_databases.obtain_applications_list(curr_dir, application_list, device_name)
            # Analyze the contacts database
            analyze_databases.analyze_contacts_database(curr_dir, file_dir)
            # Analyze the call logs
            analyze_databases.analyze_call_logs(curr_dir, file_dir)
            # Analyze the browser            
            analyze_databases.analyze_browser_bookmark(curr_dir, file_dir)
            analyze_databases.analyze_browser_history(curr_dir, file_dir)
            analyze_databases.analyze_browser_search(curr_dir, file_dir)
            # Analyze SMS
            analyze_databases.analyze_sms(curr_dir, file_dir)
            # Analyze Skype
            analyze_databases.analyze_skype(curr_dir, file_dir)
            # Analyze Accounts
            analyze_databases.analyze_account(curr_dir, file_dir)
            # Analyze Mail
            #analyze_databases.analyze_mail(curr_dir, file_dir)
            
            # Analyze the 
            dateTime = DATE + "__" + TIME[0] + "-" + TIME[1] + "-" + TIME[2]
            analyze_databases.export_to_xls(curr_dir, xls_dir, dateTime)
            
            aft_log.log("\nExtraction successfully completed\n", 2)
            endingMessage(backup_dir)
        elif serialExist == True:
            aft_log.log("This device data have already been extracted", 2)
            aft_log.log("Closing Android Forensic Tool", 2)
        
        # Closing Log File
        aft_log.FILE_HANDLE.close()
    
    else:
        print "Error! No Android smartphone connected! "
        print "Check if the relevant drivers is installed"
        print "Terminating Android Forensic Tool..."
        sys.exit(3) # indicates that no smartphone or emulator was connected to the PC

# Extract important sqlite databases from an android device
def extractDatabases(currdir, file_dir, picture_dir, os_version, device_name):
    aft_log.log("========== Extract SQLite Databases ==========", 0)
    extract_files.extract_SQLite_Files(currdir, file_dir, picture_dir, os_version, device_name)
    aft_log.log("All SQLite databases extracted", 0)
    aft_log.log("", 3)    
    
def endingMessage(curr_dir):
    print ""
    print "Visit the splunk web to view the extracted data."
    print "View the collected files at " + curr_dir
    print "Thank you for using Android Forensic Tool!"
    sys.exit()

def cloneDevice():
    curr_dir = os.getcwd()
    adbPath = os.path.join(curr_dir, "tools", "adb.exe")
    # Check if there is a smartphone or emulator connected
    if len(subprocess.Popen([adbPath, 'devices'], stdout=subprocess.PIPE).communicate(0)[0].split()) > 4:
        # Create backup directory
        try:
            device_name = subprocess.Popen([adbPath, 'devices'], stdout=subprocess.PIPE).communicate(0)[0].split()[4]
        except:
            print "Error! No Android smartphone connected! Check if the relevant drivers is installed."
            print "Terminating Android Forensic Tool"
            sys.exit(3) # indicates that no smartphone or emulator was connected to the PC
            
        # Get Android OS version which is running on the connected device
        try:
            os_version = subprocess.Popen([adbPath, 'shell', 'getprop', 'ro.build.version.release'], stdout=subprocess.PIPE).communicate(0)[0].split()[0]
        except:
            os_version = subprocess.Popen([adbPath, 'shell', 'getprop', 'ro.build.version.release'], stdout=subprocess.PIPE).communicate(0)[0]
        os_version2 = os_version.replace(".", "")
        if len(os_version2) < 3:
            os_version2 = os_version2.join("0")
            
        if (os.path.exists(os.path.join(curr_dir, "Cases"))):
            print ""
        else:
            os.mkdir("Cases")
        backup_dir = os.path.join(curr_dir, "Cases", DATE + "__" + TIME[0] + "-" + TIME[1] + "-" + TIME[2] + "__" + device_name + "__Clone")
        os.mkdir(backup_dir)
        
        aft_log.LOG_LEVEL_GLOBAL = 4
        log_file = backup_dir + "/log/aft.log"
        os.mkdir(backup_dir + "/log")
        aft_log.FILE_HANDLE = open(log_file, "a+")
        aft_log.log("==============================================", 2)
        aft_log.log("| Android Forensic Tool v1.0 by Team Blazers |", 2)
        aft_log.log("==============================================", 2)
        
        print "\nConnecting to device: " + device_name
        # Collect and display device information
        aft_log.log("====== Forensic Examination Information ======", 2)
        print "Begin extraction of data, please wait..."
        examination_time = DATE + "  " + TIME[0] + ":" + TIME[1] + ":" + TIME[2]
        aft_log.log("Device Serial Number: " + device_name + "\nDate of Examination: "  + examination_time + "\nDevice is running: Android OS v" + os_version, 2)
        
        # Get Device manufacturer
        try:
            device_manufacturer = subprocess.Popen([adbPath, 'shell', 'getprop', 'ro.product.manufacturer'], stdout=subprocess.PIPE).communicate(0)[0].split()[0]
        except:
            device_manufacturer = subprocess.Popen([adbPath, 'shell', 'getprop', 'ro.product.manufacturer'], stdout=subprocess.PIPE).communicate(0)[0]
        aft_log.log("Device Manufacturer: " + device_manufacturer, 2)
        # Get Device model
        s = subprocess.Popen([adbPath, 'shell', 'getprop', 'ro.product.model'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        device_model,err = s.communicate()
        device_model = device_model.replace('\n', '')
        aft_log.log("Device Model: " + device_model, 2)
        # Get Device IMEI
        temp_string = subprocess.Popen([adbPath, 'shell', 'dumpsys', 'iphonesubinfo'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate(0)[0]
        device_IMEI = temp_string.split("Device ID = ", 1)[1]
        device_IMEI = device_IMEI.replace('\n', '')
        aft_log.log("Device IMEI Number: " + device_IMEI, 2)
        print ""
        
        # Begin the extraction of data
        file_dir = backup_dir + "/C"
        os.mkdir(file_dir)
        
        # Start the extraction of information
        #command = adbPath + ' pull /data/data/com.android.providers.contacts/databases/contacts2.db C:\\'
        aft_log.log("=========== Cloning Device ===========", 2)
        print "Please wait while we attempt to extract everything."
        try:
            contactsdb = subprocess.Popen([adbPath, 'pull', '/', file_dir], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out = contactsdb.communicate()
            aft_log.log("Device successfully cloned!", 2)
        except:
            aft_log.log("Extractor: -> Device does not appear to be rooted!", 2)
        
        endingMessage(backup_dir)
        
        # Closing Log File
        aft_log.FILE_HANDLE.close()
    
    else:
        print "Error! No Android smartphone connected! "
        print "Check if the relevant drivers is installed"
        print "Terminating Android Forensic Tool..."
        sys.exit(3) # indicates that no smartphone or emulator was connected to the PC

# The main function
def run(argv):
    parser = argparse.ArgumentParser(description='Do note that these commands listed below can only be used once at a time')
    parser.add_argument("-g", "--guide", help="Short guide on using Android Forensic Tool", action="store_true")
    parser.add_argument("-a", "--about", help="Android Forensic Tool information", action="store_true")
    parser.add_argument("-v", "--view", help="View connected devices", action="store_true")
    parser.add_argument("-t", "--test", help="Test all variables required to conduct Android forensic", action="store_true")
    parser.add_argument("-u", "--unlock", help="Unlock a locked android device (root required)", action="store_true")
    parser.add_argument("-b", "--backup", help="Conduct a backup of the connected device to do analysis on", action="store_true")
    parser.add_argument("-e", "--extract", help="Begin extracting information from connected device", action="store_true")
    parser.add_argument("-c", "--clone", help="Create a complete copy of the android device (root required)", action="store_true")
    args = parser.parse_args()
    
    #Variables
    curr_dir = os.getcwd()
    adbPath = os.path.join(curr_dir, "tools", "adb.exe")
    command = None
    
    if args.guide:
        print "Guide on using Android Forensic Tool"
        print "-> Test all variables (using -t) required for the Android Forensic process before extracting data"
        print "-> If all conditions are met, Android Forensic extraction can begin by issuing a -e command"
        print "-Note-"
        print "-> -e command will only work on a rooted device, therefore Android Forensic Tool will attempt to do a temporary root on the device"
        print "-> If you do not wish to temporary root the device, a -b command can be issued to conduct a full backup of the device to do analysis on"
        print "-Other Information-"
        print "-> Temporary root of the deive will immediately be revoked upon reboot of the device"
        print "-> Usage of the command line on AndroidForensics.py can be done if you would like to access it programmically"
    elif args.about:
        print "Android Forensic Tool created by Team Blazers"
        print "Using:"
        command = adbPath + ' version'
        s = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = s.communicate()
        print out
    elif args.view:
        try:
            device_name = subprocess.Popen([adbPath, 'devices'], stdout=subprocess.PIPE).communicate(0)[0].split()[4]
        except:
            print "No Android smartphone connected! Check if the relevant drivers is installed."
            sys.exit(3) # indicates that no smartphone or emulator was connected to the PC
        print "Detected Device:" + device_name
    elif args.test:
        print "Checking all required conditions"
        print "-------------------------------------"
        try:
            device_name = subprocess.Popen([adbPath, 'devices'], stdout=subprocess.PIPE).communicate(0)[0].split()[4]
        except:
            print "Error! No Android smartphone connected! Check if the relevant drivers is installed."
            print "Terminating Android Forensic Tool"
            sys.exit(3) # indicates that no smartphone or emulator was connected to the PC
        print "Device chosen :" + device_name
        print "Attempting to connect to database..."
        print "Connection established"
    elif args.unlock:
        command = adbPath + ' shell rm /data/system/gesture.key'
        s = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = s.communicate()
        if not "Permission denied" in out: 
            print "Phone unlocked. Use any gesture to unlock device."
            print "Please remember to set remove password upon accessing device"
        else:
            print "Your device don't appear to be rooted."
    elif args.backup:
        backupProcess()
    elif args.extract:
        extractionProcess()
    elif args.clone:
        cloneDevice()
    else:
        print "Please input a valid command! Use -h for a list of commands"
        print "For example, 'AndroidForensic.py -h'"
 
if __name__ == '__main__':
    run(sys.argv)
    
# Commands guide

# for list
#s = subprocess.check_output(cmd.split())
#print s.split('\r\n')
        
#Write file
#with open("DeviceInfo.txt", "w+") as text_file:
    #text_file.write(device_info)
# move file
#shutil.move('DeviceInfo.txt',os.path.join(backup_dir, "DeviceInfo.txt"))
        
