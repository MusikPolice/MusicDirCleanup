#!/usr/bin/python

from distutils import dir_util
import os
import re
from collections import defaultdict
from difflib import SequenceMatcher
from fuzzywuzzy import fuzz


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
	if os.path.isdir(dirToKeep) == False or os.path.isdir(dirToCopy) == False:
		print ("One of the specified directories does not exist. Copy fails.")
		return False

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
# utilizes fuzzywuzzy string matching library
# TODO: make acceptance ratio configurable
def like(string1, string2):
	return fuzz.partial_ratio(string1, string2) >= 75


# a new approach that pre-computes the merges
# dirsToCompare - a fully-qualified list of directories that should be compared to one another in a search for duplicates.
def CombineSimilarlyNamedFolders(rootDir, dirsToCompare):
	
	# append trailing slashes to dirs
	# TODO: maybe also check for non-existent dirs here
	for i in range(len(dirsToCompare)):
		if not dirsToCompare[i].endswith('/'): dirsToCompare[i] = dirsToCompare[i] + '/'

	# dictionary of directories to be combined
	matches = defaultdict(list)

	# double loop, bitch
	for i in range(len(dirsToCompare)):
		print('Searching for matches for ' + dirsToCompare[i] + '... ')
		for j in range(len(dirsToCompare)):

			# don't compare a directory to itself, don't compare things that don't exist
			if i == j: continue
			if not os.path.isdir(rootDir + dirsToCompare[i]): continue
			if not os.path.isdir(rootDir + dirsToCompare[j]): continue

			tokens1 = os.path.dirname(dirsToCompare[i]).split('/')
			tokens2 = os.path.dirname(dirsToCompare[j]).split('/')
			folder1 = tokens1[len(tokens1) - 1]
			folder2 = tokens2[len(tokens2) - 1]

			# if directory names are similar, mark for combination
			if (like(folder1, folder2)):
				matches[dirsToCompare[i]].append(dirsToCompare[j])

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
				indexstr = raw_input('Enter the indices of the directories to combine. Return to combine all of the above, ''s'' to skip, or ''a'' to abort: ')
				if indexstr == '':
					# all
					combineDirs.append(rootDir + d)
					for d3 in matches[d]:
						combineDirs.append(rootDir + d3)
				elif indexstr == 'a':
					print ('User chose to abort')
					return None
				elif indexstr == 's':
					print ('User chose to skip')
					continue
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

		#clear matches
		matches.clear()

	

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
	print ('1. Combine Artist Folders (level 1)')
	print ('2. Combine Album Folders (level 2)')
	print ('3. Rename Folders That Contain Non-Alphanumeric Characters')
	print ('4. Delete Unwanted File Types')
	print ('5. Delete Empty Directories')
	print ('6. Quit')
	action = raw_input('>')

	if action == '1':
		if not startingDir.endswith('/'): startingDir = startingDir + '/'
		print ('Searching ' + startingDir + ' for similarly named artists...')

		artistDirectories = os.listdir(startingDir)
		artistDirectories.sort()
		CombineSimilarlyNamedFolders(startingDir, artistDirectories)

	if action == '2':
		if not startingDir.endswith('/'): startingDir = startingDir + '/'
		print ('Searching ' + startingDir + ' for similarly named albums...')
		artistDirectories = os.listdir(startingDir)
		artistDirectories.sort()
		albumDirectories = []
		for a in artistDirectories:
			for sub in os.listdir(startingDir + a):
				albumDirectories.append(a + '/' + sub + '/')
		albumDirectories.sort()
		CombineSimilarlyNamedFolders(startingDir, albumDirectories)

	elif action == '3':
		RenameFoldersNonAlphanumericRecursive(startingDir)
	elif action == '4':
		DeleteUnwantedFileTypes()
	elif action == '5':
		DeleteEmptyDirectories()
	elif action == '6':
		break