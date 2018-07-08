#!/usr/bin/env python

import os, glob
import shutil
import stat
from PIL import ExifTags
from PIL import Image
import sys
import traceback


inputPath = './'
paths = {}
for path, dirs, files in os.walk(inputPath):
	# check that the path itself is not a hidden folder
	if not path.startswith('./.') or not path.startswith('.'):

		# Iterate through list of dirs and remove hidden dirs
		nonHiddenDirs = [ d for d in dirs if not (d.startswith('.') or d.startswith('./.')) ]

		# Iterate through list of files and remove of hidden files
		nonHiddenfiles = [ f for f in files if not (f.startswith('.') or f.startswith('./.')) ]

		paths[path] = (nonHiddenDirs, nonHiddenfiles)



# Remove this script from that list
try:
	paths[ './' ][1].remove( os.path.basename(__file__) )
except:
	pass # This is ok. If the script isn't in the list, that's what we want!


print ""
print ""
print "##################################################################"
print " Resizing Images, Generating Thumbnails, Rotating if necessary..."
print "##################################################################"
print ""

pathsImageDict = {}

# Reduce the files
for path, dirsAndFiles in paths.iteritems():
	dirs = dirsAndFiles[0]
	files = dirsAndFiles[1]

	if(files):
		imgDir = path
		lastDir = imgDir.split('/')[-1]

		for file in files:
			imgPath = os.path.join( imgDir, file )
			print 'imgPath = ' + imgPath
			try:
				if ( file.endswith('.jpg') or file.endswith('.jpeg') or file.endswith('.JPG') or file.endswith('.JPEG') ):
					image = Image.open( imgPath )
					print(file + ": Width = " + str(image.size[0]) + ", Height = " + str(image.size[1]));

			except Exception as e:
				print e
