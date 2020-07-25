#!/usr/bin/python
##------------------------------------------
##--- Author: Alexander Predl - https://github.com/harveyhase68/caller_id_pi
##--- Date: 25th July 2020
##--- Derived from Author: Pradeep Singh - https://github.com/pradeesi/pass_dtmf_digits
##--- Date: 29th June 2018
##--- Version: 1.1
##--- Python Ver: 2.7
##--- Description: Caller id detection, write to PHP script
##--- Hardware: Raspberry Pi/2/3/4 and USRobotics USR5637 USB Modem
##------------------------------------------

import serial
import time
import threading
import sys
from datetime import datetime
from datetime import timedelta
import os
import fcntl
import subprocess
import requests

MODEM_RESPONSE_READ_TIMEOUT = 5   # Time in Seconds (Default 120 Seconds)
MODEM_NAME = 'U.S. Robotics'      # Modem Manufacturer, For Ex: 'U.S. Robotics' if the 'lsusb' cmd output is similar to "Bus 001 Device 004: ID 0baf:0303 U.S. Robotics"
MODEM_CALL_TIMEOUT = 2            # Time in Seconds until another call id fetched

# Used in global event listener
disable_modem_event_listener = True

# Global Modem Object
analog_modem = serial.Serial()

#=================================================================
# Set COM Port settings
#=================================================================
def set_COM_port_settings(com_port):
	analog_modem.port         = com_port
	analog_modem.baudrate     = 57600 #9600 #115200
	analog_modem.bytesize     = serial.EIGHTBITS #number of bits per bytes
	analog_modem.parity       = serial.PARITY_NONE #set parity check: no parity
	analog_modem.stopbits     = serial.STOPBITS_ONE #number of stop bits
	analog_modem.timeout      = 2          # non-block read
	analog_modem.xonxoff      = False      # disable software flow control
	analog_modem.rtscts       = False       # disable hardware (RTS/CTS) flow control
	analog_modem.dsrdtr       = False       # disable hardware (DSR/DTR) flow control
	analog_modem.writeTimeout = 2     # timeout for write
#=================================================================

#=================================================================
# Detect Com Port
#=================================================================
def detect_COM_port():

	# List all the Serial COM Ports on Raspberry Pi
	proc = subprocess.Popen(['ls /dev/tty[A-Za-z]*'], shell=True, stdout=subprocess.PIPE)
	com_ports = proc.communicate()[0].encode("utf-8","replace")
	com_ports_list = com_ports.split('\n')
	
	# Find the right port associated with the Voice Modem
	for com_port in com_ports_list:
		if 'tty' in com_port:
			#Try to open the COM Port and execute AT Command
			try:
				# Set the COM Port Settings
				set_COM_port_settings(com_port)
				analog_modem.open()
			except:
				print("Unable to open COM Port: " + com_port)
				pass
			else:
				#Try to put Modem in Voice Mode
				if not exec_AT_cmd("AT+FCLASS=8", "OK"):
					print("Error: Failed to put modem into voice mode.")
					if analog_modem.isOpen():
						analog_modem.close()
				else:
					# Found the COM Port exit the loop
					print("Modem COM Port is: " + com_port)
					analog_modem.flushInput()
					analog_modem.flushOutput()
					break
#=================================================================



#=================================================================
# Initialize Modem
#=================================================================
def init_modem_settings():
	
	# Detect and Open the Modem Serial COM Port
	try:
		detect_COM_port()
	except:
		print("Error: Unable to open the Serial Port.")
		sys.exit()

	# Initialize the Modem
	try:
		# Flush any existing input outout data from the buffers
		analog_modem.flushInput()
		analog_modem.flushOutput()

		# Test Modem connection, using basic AT command.
		if not exec_AT_cmd("AT"):
			print("Error: Unable to access the Modem")

		# reset to factory default.
		if not exec_AT_cmd("ATZ3"):
			print("Error: Unable reset to factory default")
			
		# Display result codes in verbose form 	
		if not exec_AT_cmd("ATV1"):
			print("Error: Unable set response in verbose form")

		# Enable Command Echo Mode.
		if not exec_AT_cmd("ATE1"):
			print("Error: Failed to enable Command Echo Mode")

		# Enable formatted caller report.
		if not exec_AT_cmd("AT+VCID=1"):
			print("Error: Failed to enable formatted caller report.")
			
		# Flush any existing input outout data from the buffers
		analog_modem.flushInput()
		analog_modem.flushOutput()

	except:
		print("Error: unable to Initialize the Modem")
		sys.exit()
#=================================================================



#=================================================================
# Execute AT Commands at the Modem
#=================================================================
def exec_AT_cmd(modem_AT_cmd, expected_response="OK"):
	
	global disable_modem_event_listener
	disable_modem_event_listener = True
	
	try:
		# Send command to the Modem
		analog_modem.write((modem_AT_cmd + "\r").encode())

		# Read Modem response
		execution_status = read_AT_cmd_response(expected_response)
		
		disable_modem_event_listener = False

		# Return command execution status
		return execution_status

	except:
		disable_modem_event_listener = False
		print("Error: Failed to execute the command")
		return False		
#=================================================================



#=================================================================
# Read AT Command Response from the Modem
#=================================================================
def read_AT_cmd_response(expected_response="OK"):
	
	# Set the auto timeout interval
	start_time = datetime.now()

	try:
		while 1:
			# Read Modem Data on Serial Rx Pin
			modem_response = analog_modem.readline()
			# print modem_response
			# Recieved expected Response
			if expected_response in modem_response.strip(' \t\n\r' + chr(16)):
				return True
			# Failed to execute the command successfully
			elif "ERROR" in modem_response.strip(' \t\n\r' + chr(16)):
				return False
			elif "NO ANSWER" in modem_response.strip(' \t\n\r' + chr(16)):
				return False
			# Timeout
			elif (datetime.now()-start_time).seconds > MODEM_RESPONSE_READ_TIMEOUT:
				return False


	except:
		print("Error in read_modem_response function...")
		return False
#=================================================================

# Main Function
init_modem_settings()
start_time = datetime.now()
bEnableModem = False

while True:
	modem_response = analog_modem.readline()
	if "RING" in modem_response.strip(' \t\n\r' + chr(16)):
		bEnableModem = True
		sDate = ""
		sTime = ""
		sNumber = ""
		# Set the auto timeout interval
		start_time = datetime.now()
	if bEnableModem:
		if ((datetime.now()-start_time).seconds > MODEM_CALL_TIMEOUT):
			bEnableModem = False
		if "DATE=" in modem_response.strip(' \t\n\r' + chr(16)):
			sDate = "2020-" + modem_response[5:7]+ "-"+modem_response[7:9]
			# print("sDate=" + sDate)
		if "TIME=" in modem_response.strip(' \t\n\r' + chr(16)):
			sTime = modem_response[5:7]+ ":"+modem_response[7:9]+":"+datetime.now().strftime("%S")
			# print("sTime=" + sTime)
		if "NMBR=" in modem_response.strip(' \t\n\r' + chr(16)):
			sNumber = modem_response.strip(' \t\n\r' + chr(16))[5:]
			print("CALL: " + sNumber + " Datum: "+sDate+ " Uhrzeit: "+sTime)
			r = requests.post('http://localhost/set.php', data = {'datum':sDate,'uhrzeit':sTime,'telefon':sNumber})
			# print(r.url)
			# print(r.text)
			if r.text[0:]=="0":
				#something went wrong!!!
				print(r.text)
#done