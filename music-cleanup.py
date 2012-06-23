#!/usr/bin/python

from distutils import dir_util
import os
import re
from sys import exit
from collections import defaultdict


# Interprets user response to a boolean query. Returns boolean flag for y/n/Y/N/yes/no/YES/NO
# Returns False for any unknown input
# Returns null if user input is a/A/abort/ABORT
def InterpretYesNoAbort(ans):
	if ans.upper() == 'A' or ans.upper() == 'ABORT':
		return None
	elif ans.upper() == 'Y' or ans.upper() == 'YES':
		return True
	else:
		return False

# Recursively copies all files/folders from dirToCopy into dirToKeep
# and then removes dirToCopy from the file system.
def CombineDirectoryContents (dirToKeep, dirToCopy):

	# copy
	dir_util.copy_tree(dirToCopy, dirToKeep)
	print("Copied contents of " + dirToCopy + " to " + dirToKeep)

	# clean up
	for root, dirs, files in os.walk(dirToCopy, topdown=False):
		for name in files:
			os.remove(root + '/' + name)
		for name in dirs:
			os.rmdir(root + '/' + name)
	os.rmdir(dirToCopy)
	print("Deleted directory " + dirToCopy)
	return True

# returns true if string1 is like string2
# TODO: check if string1 contains string2, visa versa, and edit-distance comparisons
def like(string1, string2):
	return True


# a new approach that pre-computes the merges
# TODO: this is better, but the ultimate would be to pass in a list of other folders at the same level as the root
# 	so that we can first combine artists, then albums, etc.
# 	also need a keyword ignore list so things like 'greatest hits' can be filtered out 
def CombineSimilarlyNamedFolders2(rootDir):
	if not rootDir.endswith('/'): rootDir = rootDir + '/'
	print ('Searching ' + rootDir + ' for similarly named folders...')

	# alphabetically sorted list of all dirs under the root
	# TODO: see above
	directories = os.listdir(rootDir)
	directories.sort()

	# dictionary of directories to be combined
	matches = defaultdict(list)

	# list of directories already earmarked for combining
	# skip these so they aren't processed twice
	skipdirs = []

	# double loop, bitch
	for i in range(len(directories)):
		for j in range(len(directories)):

			# don't compare a directory to itself, don't compare things already marked for combination
			if i == j: continue
			if directories[i] in skipdirs: continue

			# if directory names are similar, mark for combination
			if (like(directories[i], directories[j])):
				matches[directories[i]].append(directories[j])
				skipdirs.append(directories[j])

	# do the combination in a (sort of) user-friendly manner
	for d in matches:
		if len(matches[d]) > 0:
			# show the user what we might combine
			print ('The following directories have similar names:')
			print ('1. ' + d)
			for d2 in range(len(matches[d])):
				print (str(d2 + 2) + '. ' + matches[d][d2])

			combineDirs = []

			# ask the user what we should actually combine
			indexstr = raw_input('Enter the indices of the directories to combine. Enter an empty string to combine all of the above directories, or ''a'' to abort: ')
			if (indexstr == ''):
				# all
				combineDirs.append(rootDir + d)
				for d3 in matches[d]:
					combineDirs.append(rootDir + d3)
			elif (indexstr == 'a'):
				print ('User chose to abort')
				return None
			else:
				# some
				indices = indexstr.split(',')
				for i in indices:
					if (int(i) == 1):
						combineDirs.append(rootDir + d)
					else:
						combineDirs.append(rootDir + matches[d][int(i) - 2])

			# show what we're actually combining
			print ('You chose to combine the following directories:')
			count = 1
			for d4 in combineDirs:
				print (str(count) + '. ' + d4)
				count += 1

			inputStr = raw_input('Enter the index of the directory that will contain all combined directories. Enter a non-numeric string to specify a different name, or ''a'' to abort: ')
			if (inputStr == 'a'):
				print ('User chose to abort')
				return None

			try:
				temp = int(inputStr)
				if temp > 0 and temp <= len(combineDirs):
					newName = combineDirs[temp - 1]
				else:
					newName = rootDir + str(inputStr)
			except:
				# user entered a textual name
				newName = rootDir + str(inputStr)

			if not os.path.isdir(newName):
				print ('Creating directory ' + newName)
				os.makedirs(newName)

			# combine all dirs
			for i in combineDirs:
				if i == newName: continue
				CombineDirectoryContents (newName, i)


# Searches for and prompts user to combine folders that have similar names.
# Similarity is determined by removing whitespace and non alpha/non alphanumeric characters
# and comparing to other folder names. 
# Returns None if user aborts operation, True otherwise
def CombineSimilarlyNamedFolders(rootDir):
	if not rootDir.endswith('/'): rootDir = rootDir + '/'
	print ('Searching ' + rootDir + ' for similarly named folders...')

	artistDirectories = os.listdir(rootDir)
	artistDirectories.sort()

	# a dictionary of directory names to cleaned names
	artists = {}

	for artist in artistDirectories:
		if not os.path.isdir(rootDir + artist): continue

		# strips all non-alphabetical characters and upper cases
		artistAlphaOnly = ''.join(ch for ch in artist if ch.isalpha()).upper()
		if len(artistAlphaOnly) > 1 and artistAlphaOnly in artists:
			# move the contents of duplicateFolder/ into existingFolder/ and delete duplicateFolder/
			existingFolder = rootDir + artists[artistAlphaOnly]
			duplicateFolder = rootDir + artist

			if existingFolder != duplicateFolder and os.path.isdir(existingFolder) and os.path.isdir(duplicateFolder):
				result = InterpretYesNoAbort(raw_input("Move contents of " + duplicateFolder + " into " + existingFolder + "? (yes/no/abort) >"))
				if result is None:
					return None
				elif result:
					# combine the two directories
					CombineDirectoryContents(existingFolder, duplicateFolder)
		else:
			# if not a match, add to the collection so future matches can be made
			artists[artistAlphaOnly] = artist


		# strips all non alpha characters and upper cases
		artistAlphaNumericOnly = ''.join(ch for ch in artist if ch.isalnum()).upper()
		if len(artistAlphaNumericOnly) > 1 and artistAlphaNumericOnly in artists:
			# move the contents of duplicateFolder/ into existingFolder/ and delete duplicateFolder/
			existingFolder = rootDir + artists[artistAlphaNumericOnly]
			duplicateFolder = rootDir + artist

			if existingFolder != duplicateFolder and os.path.isdir(existingFolder) and os.path.isdir(duplicateFolder):
				result = InterpretYesNoAbort(raw_input("Move contents of " + artist + " into " + artists[artistAlphaNumericOnly] + "? (yes/no/abort) >"))
				if result is None:
					return None
				elif result:
					# combine the two directories
					CombineDirectoryContents(existingFolder, duplicateFolder)
		else:
			# if not a match, add to the collection so future matches can be made
			artists[artistAlphaNumericOnly] = artist


		# if another directory exists that starts or ends with the clean artist name, combine?
		for otherArtistName in artistDirectories:
			otherArtistAlphaOnly = ''.join(ch for ch in otherArtistName if ch.isalpha()).upper()
			otherArtistAlphaNumericOnly = ''.join(ch for ch in otherArtistName if ch.isalnum()).upper()

			# dump out if anything evaluated to empty string - these are incomparable
			if len(artistAlphaOnly) < 2: continue
			if len(otherArtistAlphaOnly) < 2: continue
			if len(artistAlphaNumericOnly) < 2: continue
			if len(otherArtistAlphaNumericOnly) < 2: continue

			# alpha only
			if otherArtistAlphaOnly != artistAlphaOnly and (otherArtistAlphaOnly.startswith(artistAlphaOnly) or otherArtistAlphaOnly.endswith(artistAlphaOnly)):
				# move the contents of duplicateFolder/ into existingFolder/ and delete duplicateFolder/
				existingFolder = rootDir + artist
				duplicateFolder = rootDir + otherArtistName

				if existingFolder != duplicateFolder and os.path.isdir(existingFolder) and os.path.isdir(duplicateFolder):
					result = InterpretYesNoAbort(raw_input("Move contents of " + otherArtistName + " into " + artist + "? (yes/no/abort) >"))
					if result is None:
						return None
					elif result:
						# combine the two directories
						CombineDirectoryContents(existingFolder, duplicateFolder)

			# alphanumeric only
			if otherArtistAlphaNumericOnly != artistAlphaNumericOnly and (otherArtistAlphaNumericOnly.startswith(artistAlphaNumericOnly) or otherArtistAlphaNumericOnly.endswith(artistAlphaNumericOnly)):
				# move the contents of duplicateFolder/ into existingFolder/ and delete duplicateFolder/
				existingFolder = rootDir + artist
				duplicateFolder = rootDir + otherArtistName

				if existingFolder != duplicateFolder and os.path.isdir(existingFolder) and os.path.isdir(duplicateFolder):
					result = InterpretYesNoAbort(raw_input("Move contents of " + otherArtistName + " into " + artist + "? (yes/no/abort) >"))
					if result is None:
						return None
					elif result:
						# combine the two directories
						CombineDirectoryContents(existingFolder, duplicateFolder)
	print('Done')
	return True


# Does the above, but searches the entire subtree of rootDir
def CombineSimilarlyNamedFoldersRecursive(rootDir):
	print ('Searching ' + rootDir + ' for similarly named folders...')

	dirsToSearch = []

	# recursively assemble list of sub dirs
	for root, dirs, files in os.walk(rootDir, topdown=False):
		for name in dirs:
			if root not in dirsToSearch:
				if root != startingDir:
					dirsToSearch.append(root)
			if (root + '/' + name) not in dirsToSearch:
				if (root + '/' + name) != startingDir:
					dirsToSearch.append(root + '/' + name)

	# process them in alphabetical order
	dirsToSearch.sort()
	for search in dirsToSearch:
		if not os.path.isdir(search): continue

		# if user hits abort, respect it
		if CombineSimilarlyNamedFolders(search) is None:
			break
	

# Searches for and prompts user to rename folders that contain non-alphanumeric characters.
# If user specifies a new folder name that already exists, folder contents are combined.
# Returns None if user aborts, True otherwise
def RenameFoldersNonAlphanumeric(rootDir):
	if not rootDir.endswith('/'): rootDir = rootDir + '/'
	print ('Searching ' + rootDir + ' for non-alphanumeric folders...')

	artistDirectories = os.listdir(rootDir)
	artistDirectories.sort()

	for artist in artistDirectories:
		if not os.path.isdir(rootDir + artist): continue

		# if artist contains non-alphanumeric characters, optionally rename the folder
		if len(re.sub(r'\s', '', artist)) > 1 and (not re.sub(r'\s', '', artist).isalnum()) and os.path.isdir(rootDir + artist):
			result = InterpretYesNoAbort(raw_input("Would you like to rename " + artist + "? (yes/no/abort) >"))
			if result is None:
				return None
			elif result:
				# rename directory
				newName = raw_input("What should we rename it to? ")

				if os.path.isdir(rootDir + newName):
					# if dir exists, combine
					existingFolder = rootDir + newName
					badlyNamedFolder = rootDir + artist

					if existingFolder != badlyNamedFolder and os.path.isdir(existingFolder) and os.path.isdir(badlyNamedFolder):
						result = InterpretYesNoAbort(raw_input("Specified Directory exists. Combine contents? (yes/no/abort) >"))
						if result is None:
							return None
						elif result:
							CombineDirectoryContents(existingFolder, badlyNamedFolder)
				else:	
					# if not, just rename as requested
					os.rename(rootDir + artist, rootDir + newName)

				print('Renamed')
	print('Done')
	return True


# Does the above, but searches the entire subtree of rootDir
def RenameFoldersNonAlphanumericRecursive(rootDir):
	print ('Searching ' + rootDir + ' for non-alphanumeric folders...')

	# recursively assemble list of subdirs to search
	dirsToSearch = []
	for root, dirs, files in os.walk(rootDir, topdown=False):
		for name in dirs:
			if root not in dirsToSearch:
				if root != startingDir:
					dirsToSearch.append(root)
			if (root + '/' + name) not in dirsToSearch:
				if (root + '/' + name) != startingDir:
					dirsToSearch.append(root + '/' + name)

	# process them in alphabetical order
	dirsToSearch.sort()
	for search in dirsToSearch:
		if not os.path.isdir(search): continue

		# respect user abort
		if RenameFoldersNonAlphanumeric(search) is None:
			break


# Searches for folders that have some name x where another folder with the name The x also exists.
# User is prompted to combine the folders
def CombineFoldersIgnorePrefix():
	print ('Searching ' + startingDir + ' for folders to combine...')

	artistDirectories = os.listdir(startingDir)
	artistDirectories.sort()

	for artist in artistDirectories:
		if not os.path.isdir(startingDir + artist): continue

		if not artist.upper().startswith('THE '):
			if os.path.isdir(startingDir + 'The ' + artist):
				result = InterpretYesNoAbort(raw_input('Would you like to combine ' + artist + ' with The ' + artist + '? (yes/no/abort) >'))
				if result is None:
					return
				elif result:
					CombineDirectoryContents(startingDir + 'The ' + artist, startingDir + artist)
		if not artist.upper().startswith('A '):
			if os.path.isdir(startingDir + 'A ' + artist):
				result = InterpretYesNoAbort(raw_input('Would you like to combine ' + artist + ' with A ' + artist + '? (yes/no/abort) >'))
				if result is None:
					return
				elif result:
					CombineDirectoryContents(startingDir + 'A ' + artist, startingDir + artist)
	print ('Done')


# Iterates through the folder structure looking for files with unwanted extensions and deleting them.
# Prompts user for each new file type that is encountered and remembers selection
def DeleteUnwantedFileTypes():
	print ('Searching ' + startingDir + ' for unwanted file types...')

	ok = []
	bad = []

	for root, dirs, files in os.walk(startingDir, topdown=False):
		for name in files:
			extension = os.path.splitext(root + '/' + name)[1]
			if extension in bad:
				# delete the file
				print('Deleting file ' + root + '/' + name)
				os.remove(root + '/' + name)
			elif extension not in ok:
				# prompt user about this file type
				print('Found new extension *' + extension)

				result = InterpretYesNoAbort(raw_input('Delete it? (yes/no/abort) >'))
				if result is None:
					return
				elif result:
					# delete the file and remember for next time
					os.remove(root + '/' + name)
					bad.append(extension)
				else:
					# remember for next time
					ok.append(extension)
	print ('Done')


# Deletes empty directories
def DeleteEmptyDirectories():
	print ('Searching ' + startingDir + ' for empty directories...')

	for root, dirs, files in os.walk(startingDir, topdown=False):
		for name in dirs:
			# returns sub directories and files - if none, it's empty
			# note: this does not consider hidden files - these could be accidentally deleted!
			subdirs = os.listdir(root + '/' + name)
			if len(subdirs) == 0:
				print('Deleting empty directory ' + root + '/' + name)
				os.rmdir(root + '/' + name)

	print ('Done')


# Program Entry
print ('Welcome to MusikPolice\'s Music Directory Cleanup Utility.')
startingDir = raw_input('Enter directory to clean: ')
if not startingDir.endswith('/'): startingDir = startingDir + '/'

while True:
	print('')
	print ('Select an action to perform:')
	print ('1. Combine Similarly Named Folders')
	print ('2. Rename Folders That Contain Non-Alphanumeric Characters')
	print ('3. Rename Folders That Contain Non-Alphanumeric Characters (Recursive)')
	print ('4. Combine Folders By Ignoring Prefixes The and A')
	print ('5. Delete Unwanted File Types (Recursive)')
	print ('6. Delete Empty Directories (Recursive)')
	print ('7. Quit')
	action = raw_input('>')

	if action == '1':
		CombineSimilarlyNamedFolders2(startingDir)
	elif action == '2':
		RenameFoldersNonAlphanumeric(startingDir)
	elif action == '3':
		RenameFoldersNonAlphanumericRecursive(startingDir)
	elif action == '4':
		CombineFoldersIgnorePrefix()
	elif action == '5':
		DeleteUnwantedFileTypes()
	elif action == '6':
		DeleteEmptyDirectories()
	elif action == '7':
		break
