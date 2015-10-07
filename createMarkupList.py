#!/usr/bin/env python

import os, glob
import shutil
import stat
from PIL import Image
import pysftp
import credentials


path = './'
webDir = os.path.join( os.path.dirname(__file__), "web" )
imgCompressQual = 80
thumbCompressQual = 80

maxImageSize = 1024, 1024
thumbSize = (75, 75)

htmlMenuListFileName = 'image_submenu.html'

domainName = 'benclouser.com'
httpDomainName = 'http://www.benclouser.com'


generatedHtmlDir = 'generated/photography'
basePhotoImageDir = 'img/photography'
webGeneratedHtmlDir = str(httpDomainName + '/' + generatedHtmlDir)
webBasePhotoImageDir = str(httpDomainName + '/'+ basePhotoImageDir)




# ToDo Check that the web directory doesn't already exist!




paths = {}
for path, dirs, files in os.walk(path):
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

# Start by creating a web directory in the root directory.
os.mkdir( webDir )

# This is here so I can ignore all files when we copy the dir tree below
def ignore(folder, contents): 
	return set(n for n in contents if not os.path.isdir(os.path.join(folder, n))) 

# Copy our directories into the web directory
for dir in paths['./'][0]:
	shutil.copytree(dir, webDir+"/"+dir, ignore=ignore)


pathsImageDict = {}

# Reduce the files
for path, dirsAndFiles in paths.iteritems():
	dirs = dirsAndFiles[0]
	files = dirsAndFiles[1]

	# if we have at least one file
	if(files):
		imgDir = path
		imgSaveDir = os.path.join(webDir, path)
		thumbsSaveDir = os.path.join( imgSaveDir, 'thumbs' )

		for file in files:
			imgPath = os.path.join( imgDir, file )
			imgSavePath = os.path.join( imgSaveDir, file )
			thumbSavePath = os.path.join( thumbsSaveDir, str('thumb_'+file) )
			print 'imgPath = ' + imgPath + ' imgSavePath = ' + imgSavePath + ' thumbSavePath = ' + thumbSavePath
			try:
				if ( file.endswith('.jpg') or file.endswith('.jpeg') or file.endswith('.JPG') or file.endswith('.JPEG') ): 
					image = Image.open( imgPath )
					maxsize = maxImageSize
					image.thumbnail(maxsize, Image.ANTIALIAS)
					image.save(imgSavePath, "JPEG", quality=imgCompressQual)

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


# File structure should be like this

# rootDir/<location or category>/<date>
# ie. rootDir/Seattle/02-12-2015
#          -    -     03-14-2015
#          -    -     03-15-2015
#          -   Reston/06-12-2015
#          -    -     09-13-2015



def getLastDir( path ):
	lastDir = os.path.basename(os.path.normpath(path))
	return str(lastDir)

def getCategory( path ):
	path = os.path.normpath(path)
	individualDirs = path.split('/')
	if len(individualDirs) < 2:
		print 'Warning, couldnt find category, using '+ str(path)
		return path
	
	# category is the 2nd to last folder
	return str( individualDirs[-2] ).lower()




def getRidOfExtension(name):
	return str( name.split('.')[0] )

# Generate menu html based off the directories
if pathsImageDict:
	fp = open(os.path.join(webDir, htmlMenuListFileName), 'w')
	fp.write('<table>\n')
	fp.write('<th>Images</th>\n')
	# keep a list of the one's we have processed
	processedCategory = []
	for path, images in pathsImageDict.iteritems():
		if path not in processedCategory:
			fp.write('<tr>')
			fp.write('<td><a href="'+webGeneratedHtmlDir+'/'+getCategory(path)+'.html">'+getCategory(path).title()+'</a></td>')
			fp.write('</tr>\n')
			processedCategory.append(getCategory(path))

	fp.write('</table>')
	fp.close()


# Generate the html files for the gallery
for path, images in pathsImageDict.iteritems():

	# File name is the name of the indexx
	print 'category index file path: ' + str( os.path.join(webDir, getCategory(path)+'.html') )
	fp = open( os.path.join(webDir, getCategory(path)+'.html'), 'w' )
	for imgFile in images:
		fp.write('<a href="'+ webBasePhotoImageDir+'/'+path+'/'+imgFile+'" data-gallery="" class="hoverZoomLink" title="'+getRidOfExtension(imgFile).title()+'">\n')
		fp.write('\t<img src="'+webBasePhotoImageDir+'/'+path+'/thumbs/thumb_'+imgFile+'" alt="">\n')
		fp.write('</a>\n')
	fp.close()

#for path, dirsAndFiles in paths.iteritems():
#	print path + " : " + '('+str(dirsAndFiles[0])+') ' + ' ('+str(dirsAndFiles[1])+')'


# Get ready to push files to the server!!!
with pysftp.Connection(domainName, username=credentials.username, password=credentials.password) as sftp:

	# Push html files to 'generated' folder on the server. (that is their final home)
	with sftp.cd('/var/www/html/'+generatedHtmlDir):
		for file in glob.glob(webDir+'/*.html'):
			print('Uploading: '+ file + ' to ' + generatedHtmlDir + ' ...')
			sftp.put(file)  # upload file to public/ on remote
        
    # Now push all directories of images to the 'img/photography' dir on the server. (That is their final home)
	with sftp.cd('/var/www/html/'+ basePhotoImageDir):
		print glob.glob(webDir+'/*')
		contents = [ item for item in glob.glob(webDir+'/*') if os.path.isdir(item) ]
		for item in contents:
			currentDir = '/var/www/html/'+ basePhotoImageDir+'/'+item.split('/')[-1]
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

			
    





