#!/usr/bin/env python

import os, glob
import shutil
import stat
from PIL import ExifTags
from PIL import Image
import sys
import traceback

# if len(sys.argv) < 2:
# 	print "Pass in min filesize to consider file for reduction"
# 	sys.exit()


imgCompressQual=80
thumbCompressQual=50
maxImageSize=2048,2048
thumbSize=600,400 # (width, height)
crop_thumbs=False




def resize_and_crop(img, savePath, size, crop_type='middle'):
	"""
	Resize and crop an image to fit the specified size.

	args:
	    img_path: path for the image to resize.
	    modified_path: path to store the modified image.
	    size: `(width, height)` tuple.
	    crop_type: can be 'top', 'middle' or 'bottom', depending on this
	        value, the image will cropped getting the 'top/left', 'middle' or
	        'bottom/right' of the image to fit the size.
	raises:
	    Exception: if can not open the file in img_path of there is problems
	        to save the image.
	    ValueError: if an invalid `crop_type` is provided.
	"""
	# If height is higher we resize vertically, if not we resize horizontally

	# Get current and desired ratio for the images
	img_ratio = img.size[0] / float(img.size[1])
	ratio = size[0] / float(size[1])
	print "img_ratio = " + str(img_ratio) + ". ratio = " + str(ratio)
	#The image is scaled/cropped vertically or horizontally depending on the ratio
	if ratio > img_ratio:
		img = img.resize((size[0], int(round(size[0] * img.size[1] / img.size[0]))),
		        Image.ANTIALIAS)
		# Crop in the top, middle or bottom
		if crop_type == 'top':
			box = (0, 0, img.size[0], size[1])
		elif crop_type == 'middle':
			box = (0, int(round((img.size[1] - size[1]) / 2)), img.size[0],
		           int(round((img.size[1] + size[1]) / 2)))
		elif crop_type == 'bottom':
			box = (0, img.size[1] - size[1], img.size[0], img.size[1])
		else :
			raise ValueError('ERROR: invalid value for crop_type')
		print "ratio > img_ratio. Cropping box: "
		print box
		img = img.crop(box)
	elif ratio < img_ratio:
		img = img.resize((int(round(size[1] * img.size[0] / img.size[1])), size[1]),
		        Image.ANTIALIAS)
		# Crop in the top, middle or bottom
		if crop_type == 'top':
			box = (0, 0, size[0], img.size[1])
		elif crop_type == 'middle':
			box = (int(round((img.size[0] - size[0]) / 2)), 0,
		           int(round((img.size[0] + size[0]) / 2)), img.size[1])
		elif crop_type == 'bottom':
			box = (img.size[0] - size[0], 0, img.size[0], img.size[1])
		else :
			raise ValueError('ERROR: invalid value for crop_type')

		print "ratio < img_ratio. Cropping box: "
		print box
		img = img.crop(box)
	else :
		print "so i guess the ratios are the same?"
		img = img.resize((size[0], size[1]),
	            Image.ANTIALIAS)
	    # If the scale is the same, we do not need to crop
	print "Saving thumb to " + savePath
	img.save(savePath, "JPEG", quality=thumbCompressQual)



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


# Ok, so we have the structure of dirs and filenames to make some web versions.



print(paths)
#sys.exit()


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
		imgSaveDir = os.path.join(imgDir, "reduced")
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

						# I am using thumbnail() to compress the image
						print "maxsize = " + str(maxsize)
						image.thumbnail(maxsize, Image.ANTIALIAS)
						image.save(imgSavePath, "JPEG", quality=imgCompressQual)

					except:
						traceback.print_exc()
						sys.exit()

					

					# Create thumbnail dir (if it doesn't already exist)
					if not os.path.isdir(thumbsSaveDir):
						os.mkdir(thumbsSaveDir)

					# Generate thumbnail
					if crop_thumbs:
						resize_and_crop(image, thumbSavePath, thumbSize)
					else:
						image.thumbnail(thumbSize, Image.ANTIALIAS)
						image.save(thumbSavePath, "JPEG", quality=thumbCompressQual)

					# First cut down the file quickly and roughly
					#img = image.resize( (thumbSize[0]*2, thumbSize[1]*2) )
					# Then perform final reduction with more care
					#img = img.resize( thumbSize, Image.ANTIALIAS)
					

					# Add image to filelist in dict indexed by path
					# If key doesn't already exist, create it with an empty list.
					# Append the file to the correct list
					#pathsImageDict.setdefault(path, []).append(file)

			except Exception as e:
				print e
	
    





