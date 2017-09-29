# Imports
import os

os.chdir('Android')

print "=============================================="
print "|    Android Forensic Tool Commands List     |"
print "=============================================="
print "1) guide    -    Short guide on using Android Forensic Tool"
print "2) about    -    Android Forensic Tool information"
print "3) view     -    View connected device"
print "4) test     -    Check all variables required to conduct Android forensic"
print "5) unlock   -    Unlock a locked android device (root required)"
print "6) backup   -    Begin backup of device (Analysis method for non-rooted device)"
print "7) extract  -    Begin extracting information from connected device\n                (Temporary root of the device have to be done)"
print "8) clone    -    Create a complete copy of the android device (root required)"
print "0) exit     -    Exit Android Forensic Tool"
print "Please key in the number of your chosen option"

exitSequence = False
straightExit = True
inputCommand = ""
while exitSequence == False:
    inputCommand = raw_input(">>")
    if (inputCommand == "1"):
        print ""
        os.system('AndroidForensic.py -g')
    elif (inputCommand == "2"):
        print ""
        os.system('AndroidForensic.py -a')
    elif (inputCommand == "3"):
        print ""
        os.system('AndroidForensic.py -v')
    elif (inputCommand == "4"):
        print ""
        os.system('AndroidForensic.py -t')
    elif (inputCommand == "5"):
        print ""
        os.system('AndroidForensic.py -u')
    elif (inputCommand == "6"):
        print ""
        os.system('AndroidForensic.py -b')
        exitSequence = True
        straightExit = False
    elif (inputCommand == "7"):
        print ""
        os.system('AndroidForensic.py -e')
        exitSequence = True
        straightExit = False
    elif (inputCommand == "8"):
        print ""
        os.system('AndroidForensic.py -c')
        exitSequence = True
        straightExit = False
    elif (inputCommand == "0"):
        exitSequence = True
    else:
        print "Invalid command! Please input a correct command."
    print ""
if (straightExit == False):
    raw_input()
    