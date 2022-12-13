#!/usr/bin/python3
#
# Frigidaire/Electrolux Modular Appliance Control System (MACS) bus logger
# Copyright (C) Josh Currier (doitaljosh@gmail.com)
# GitHub Repo: https://github.com/doitaljosh/macs-logger
#

import os
import sys
import traceback
import struct
import codecs
import serial
import time
import argparse

# Parse run-time arguments
parseArgs = argparse.ArgumentParser()
parseArgs.add_argument("-d", "--device", help = "TTY device")
parseArgs.add_argument("-l", "--logfmt", help = "Log format: csv, text")
parseArgs.add_argument("-lf", "--logfile", help = "Log file location")
parseArgs.add_argument("-q", "--quiet", help = "Quietly log to a file")
args = parseArgs.parse_args()

# Process arguments
if not args.device:
	sys.exit("Please specify the TTY device.")
if args.logfmt:
	if not args.logfile:
		sys.exit("A log format was specified without a file location.")
	print("Logging to {} file at {}".format(args.logfmt, args.logfile))
	if (os.path.exists(args.logfile)):
		os.remove(args.logfile)
	if (args.logfmt == "csv"):
		with open(args.logfile, "a") as logFile:
			logFile.write("Type,SourceAddr,Length,Command,Payload\n")
if args.quiet:
	if not args.logfmt and args.logfile:
		sys.exit("Quiet mode requires a log format and location to be specified.")
	print("Quiet mode enabled")

# Definitions for node and command names for verbose logging
nodeNames = {
	'0x45': ' OVC1',
	'0x65': ' OVC2',
	'0x25': ' OUI',
	'0xa5': ' GPU',
	'0xff': ' BCST'
}
	
commandNames = {
	'0x6c': ' heartbeat',
	'0x2e': ' tempMonitor',
	'0x2c': ' reportOpenRTD',
	'0x24': ' ovenLightState'
}

# Serial port instance
# Baud rate is fixed at 9600 for all MACS applications
instance = serial.Serial(args.device,9600,timeout=5)

# MACS start-of-frame sequences
macsSofNormal = b'\xc9\x2d'
macsSofDiag = b'\xc9\x3a'

# Refresh period for data retrieval
refreshRate = 0.001

# Formatting variables
msgType = "Unknown"
commandName = "Unknown"
sourceName = "Unknown"

# Returns the node name given a byte
def getNodeName(node):
	global nodeNames
		
	if node in nodeNames.keys():
		return node + nodeNames[node]
	else:
		return node + ' UNK '

# Returns the command name given a byte
def getCommandName(command):
	global commandNames
		
	if command in commandNames.keys():
		return command + commandNames[command]
	else:
		return command + ' Unknown'

# Parses the MACS packet and logs it in readable form
def logMessage():
	
	header = instance.read(3)

	# Get the packet header from the packet buffer
	command = hex(header[2]) # MACS command
	length = int(header[1]) # Message length excluding header
	source = hex(header[0]) # Should be the OVC addresses

	# Log each message if a length is known
	if length not in commandNames:
	
		global nodeName
		global commandName
	
		nodeName = getNodeName(source)
		commandName = getCommandName(command)
			
		payload = instance.read(int(header[1]))
		
		payloadFmt = " ".join("{:02x}".format(byte) for byte in payload)
		
		if (args.logfmt == 'csv'):
			logFmtCsv = '"{}","{}","{}","{}","{}"'.format(msgType, nodeName, length, commandName, payloadFmt)
			with open(args.logfile, 'a') as logFile:
				logFile.write(logFmtCsv)
				logFile.write("\n")
			if not args.quiet: print(logFmtCsv)
		elif (args.logfmt == 'text'):
			logFmtText = "type: {}, src: {}, length: {}, cmd: {}, payload: {}".format(msgType, nodeName, length, commandName, payloadFmt)
			with open(args.logfile, 'a') as logFile:
				logFile.write(logFmtText)
				logFile.write("\n")	
			if not args.quiet: print(logFmt)
		else:
			logFmtConsole = "MACS message: type: {}, src: {}, length: {}, cmd: {}, payload: {}".format(msgType, nodeName, length, commandName, payloadFmt)
			print(logFmtConsole)

# Simple function to convert hexadecimal to integer.
def hexToInt(data):
	return int.from_bytes(data, byteorder='little', signed=False) # MACS data types are little-endian

# Main while loop.
try:
	while True:
		sof = instance.read(2)
		if (sof == macsSofNormal):
			msgType = "Normal"
			instance.flushInput()
			instance.flushOutput()
			logMessage()
			time.sleep(refreshRate)
		if (sof == macsSofDiag):
			msgType = "Diag"
			instance.flushInput()
			instance.flushOutput()
			logMessage()
			time.sleep(refreshRate)
except:
	traceback.print_exc()
