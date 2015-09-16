#!/usr/bin/env python

import os, datetime
import stat

# Get a list of all our files
files = os.listdir('./')

# Remove this script from that list
try:
	files.remove( os.path.basename(__file__) )
except:
	pass # This is ok. If the script isn't in the list, that's what we want!

# Dictionary to hold all the times
times = {}

for file in files:

	t = os.path.getmtime(file)
	dateModified = datetime.datetime.fromtimestamp(t)

	fileMode= os.stat(file).st_mode

	# Ignore directories and special files
	if stat.S_ISREG(fileMode):
		# Categorize lists of files into dates
		key = dateModified.strftime("%m-%d-%y")
		# If key doesn't already exist, create it with an empty list.
		# Append the file to the correct list
		times.setdefault(key, []).append(file)

# Iterate over keys in the 'times' dictionary
for lastModTime, fileList in times.iteritems():
	print "Creating directory: " + lastModTime
	numFiles = len(fileList)
	try:
		os.mkdir(lastModTime)
	except:
		print "Couldn't create directory " +lastModTime+" , does it already exist?"
		response = raw_input("\tShould we continue?, We will attempt to move " + str(numFiles) +" files into " + lastModTime + " (y or n) ")
		
		if( (response == 'n') or (response == 'N') or (response == 'no') or (response == 'No') ):
			# Don't move anything!
			continue

	print "\t-- Moving " + str(numFiles) + " files into " + lastModTime
	# Go through all files corresponding to time
	for file in fileList:
		# move files to new home
		os.rename(file, str(lastModTime)+"/"+file)


