#!/usr/bin/env python

import os, glob
import shutil
import stat
from PIL import ExifTags
from PIL import Image
import pysftp
import credentials
import json
import sys

if len(sys.argv) < 2:
	print "Pass in the config file"
	sys.exit()

configFile = sys.argv[1]

fp = open(configFile)
configDb = json.load(fp);
fp.close()

# TODO, validate the configDB

inputPath = configDb['pathToInputDirs'] #input
webDir = configDb['pathToLocalOutputDir'] #TopLevel output
subWebDir = configDb['subOutputDir'] 
finalOutTopLevelDir = webDir + "/" + subWebDir;

imgCompressQual = configDb['imgCompressQual']
thumbCompressQual = configDb['thumbCompressQual']

maxImageSize = (configDb['maxImageSize'], configDb['maxImageSize'])
thumbSize = (configDb['thumbSize'], configDb['thumbSize'])

domainName = configDb['domainName']
httpDomainName = 'http://'+ domainName

generatedHtmlDir = configDb['generatedHtmlDir_server']
basePhotoImageDir = configDb['basePhotoImageDir_server']

webReqGenHtmlDir = configDb['webRequestGeneratedHtmlDir']
webReqImageDir = configDb['webRequestImageDir']

webGeneratedHtmlDir = str(httpDomainName + '/' + webReqGenHtmlDir)
webBasePhotoImageDir = str(httpDomainName + '/'+ webReqImageDir)

webServerRootDir = configDb["webServerRootDir"]

pushFilesToServer = True



print "outputDir: " + str(finalOutTopLevelDir)
# ToDo Check that the web directory doesn't already exist!

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


# Ok, so we have the structure of dirs and filenames to make some web versions.

# Start by verifying that our final output dir exists:

if not os.path.exists(finalOutTopLevelDir):
	print "Creating directory"
	os.makedirs(finalOutTopLevelDir)


#print(paths)
#sys.exit()

# This is here so I can ignore all files when we copy the dir tree below
def ignore(folder, contents): 
	return set(n for n in contents if not os.path.isdir(os.path.join(folder, n))) 


# Copy our directories into the web directory. Safety?
#for dir in paths['./'][0]:
#	shutil.copytree(dir, webDir+"/"+subWebDir+"/"+dir, ignore=ignore)


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

	# if we have at least one file
	if(files):
		imgDir = path
		lastDir = imgDir.split('/')[-1]
		print "lastDir = " + lastDir
		imgSaveDir = os.path.join(webDir, subWebDir, lastDir)
		thumbsSaveDir = os.path.join( imgSaveDir, 'thumbs' )

		if not os.path.exists(imgSaveDir):
			print "Creating directory"
			os.makedirs(imgSaveDir)

		for file in files:
			imgPath = os.path.join( imgDir, file )
			imgSavePath = os.path.join( imgSaveDir, file )
			thumbSavePath = os.path.join( thumbsSaveDir, str('thumb_'+file) )
			print 'imgPath = ' + imgPath + ' imgSavePath = ' + imgSavePath + ' thumbSavePath = ' + thumbSavePath
			try:
				if ( file.endswith('.jpg') or file.endswith('.jpeg') or file.endswith('.JPG') or file.endswith('.JPEG') ): 
					image = Image.open( imgPath )
					maxsize = maxImageSize
					
					try :
						for orientation in ExifTags.TAGS.keys() : 
							if ExifTags.TAGS[orientation]=='Orientation' : break 
						exif=dict(image._getexif().items())

						if   exif[orientation] == 3 : 
							print "rotating image 180"
							image=image.rotate(180, expand=True)
						elif exif[orientation] == 6 : 
							print "rotating image 270"
							image=image.rotate(270, expand=True)
						elif exif[orientation] == 8 : 
							print "rotating image 90"
							image=image.rotate(90, expand=True)

						image.thumbnail(maxsize, Image.ANTIALIAS)
						image.save(imgSavePath, "JPEG", quality=imgCompressQual)

					except:
						traceback.print_exc()

					

					# Create thumbnail dir (if it doesn't already exist)
					if not os.path.isdir(thumbsSaveDir):
						os.mkdir(thumbsSaveDir)

					# Generate thumbnail
					# First cut down the file quickly and roughly
					#img = image.resize( (thumbSize[0]*2, thumbSize[1]*2) )
					# Then perform final reduction with more care
					#img = img.resize( thumbSize, Image.ANTIALIAS)
					image.thumbnail(thumbSize, Image.ANTIALIAS)
					image.save(thumbSavePath, "JPEG", quality=thumbCompressQual)

					# Add image to filelist in dict indexed by path
					# If key doesn't already exist, create it with an empty list.
					# Append the file to the correct list
					pathsImageDict.setdefault(path, []).append(file)

			except Exception as e:
				print e


def getRidOfExtension(name):
	return str( name.split('.')[0] )


print ""
print ""
print "##################################################################"
print " Generating HTML..."
print "##################################################################"
print ""

# Generate the html files for the gallery
for path, images in pathsImageDict.iteritems():

	imgDir = path
	lastDir = imgDir.split('/')[-1]

	# File name is the name of the indexx
	generatedHtmlOutFile = os.path.join(finalOutTopLevelDir, lastDir+'.html')
	print 'generated html file path: ' + generatedHtmlOutFile
	fp = open( generatedHtmlOutFile, 'w' )
	for imgFile in images:
		fp.write('<a href="'+ webBasePhotoImageDir+'/'+subWebDir+'/'+lastDir+'/'+imgFile+'" data-gallery="" class="hoverZoomLink" title="'+getRidOfExtension(imgFile).title()+'">\n')
		fp.write('\t<img src="'+webBasePhotoImageDir+'/'+subWebDir+'/'+lastDir+'/'+'thumbs/thumb_'+imgFile+'" alt="">\n')
		fp.write('</a>\n')
	fp.close()

#for path, dirsAndFiles in paths.iteritems():
#	print path + " : " + '('+str(dirsAndFiles[0])+') ' + ' ('+str(dirsAndFiles[1])+')'



if pushFilesToServer:
	print ""
	print ""
	print "##################################################################"
	print " Pushing Files to the server..."
	print "##################################################################"
	print ""
	# Get ready to push files to the server!!!
	with pysftp.Connection(domainName, username=credentials.username, password=credentials.password) as sftp:

		# Create (potentially) new directories
		ftpNewGeneratedHtmlDir = webServerRootDir + '/' + generatedHtmlDir + '/' + subWebDir
		ftpNewImageDir = webServerRootDir + '/' + basePhotoImageDir + '/' + subWebDir 

		print "ftpNewDir = " + ftpNewImageDir
		try:
			sftp.makedirs(ftpNewImageDir)
			sftp.makedirs(ftpNewGeneratedHtmlDir)
		except IOError:
			print "Couldn't create dir, " + ftpNewImageDir + " on Server"


		# Push html files to 'generated' folder on the server. (that is their final home)
		with sftp.cd(ftpNewGeneratedHtmlDir):
			for file in glob.glob(finalOutTopLevelDir+'/*.html'):
				print('Uploading: '+ file + ' to ' + ftpNewGeneratedHtmlDir + ' ...')
				sftp.put(file)  # upload file to public/ on remote
	    

	    # Now push all directories of images to the 'img/photography' dir on the server. (That is their final home)
		with sftp.cd(ftpNewImageDir):
			print glob.glob(finalOutTopLevelDir+'/*')
			contents = [ item for item in glob.glob(finalOutTopLevelDir+'/*') if os.path.isdir(item) ]
			for item in contents:
				currentDir = ftpNewImageDir+'/'+item.split('/')[-1]
				print 'currentDir = ' + currentDir


				# if( sftp.isdir(currentDir) ):
				# 	try:
				# 		sftp.put_r()
				try:
					sftp.makedirs(currentDir, mode=755)
				except IOError:
					print "Couldn't create dir, or uploading failed"

				print('Uploading: '+ item + ' to '+ currentDir + ' ...')
				sftp.put_r(item, currentDir)  # upload file to publicon remote

			
    





