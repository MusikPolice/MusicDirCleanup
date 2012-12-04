#!/usr/bin/python

import os
import re
import string
from collections import defaultdict
from difflib import SequenceMatcher
from distutils import dir_util
from fuzzywuzzy import fuzz
	
def invalid_input():
	print "Please enter a valid option."
	
def ask_user(prompt_message):
	valid_answer = False
		
	while not valid_answer: 
		result = raw_input(prompt_message + " ([Y]es/[N]o/[A]bort) > ")
		result = result.upper()
		
		# Did we get a valid result?
		if len(result) < 1:
			invalid_input()
			continue
		
		# Interprets user response to a boolean query. Returns boolean flag for y/n/Y/N/yes/no/YES/NO
		# Returns False for any unknown input
		# Returns null if user input is a/A/abort/ABORT		
		
		if result[0] == 'Y':
			return True
		elif result[0] == 'A':
			return None
		elif result[0] == 'N':
			return False
		
		invalid_input()
		continue

# Recursively copies all files/folders from dirToCopy into dirToKeep
# and then removes dirToCopy from the file system.
def CombineDirectoryContents (dirToKeep, dirToCopy):
	if os.path.isdir(dirToKeep) == False or os.path.isdir(dirToCopy) == False:
		print ("One of the specified directories does not exist. Copy fails.")
		return False

	# copy
	dir_util.copy_tree(dirToCopy, dirToKeep)
	print("Copied contents of ")
	print(dirToCopy + " to ")
	print(dirToKeep)

	# clean up
	for root, dirs, files in os.walk(dirToCopy, topdown=False):
		for name in files:
			os.remove(root + os.sep + name)
		for name in dirs:
			os.rmdir(root + os.sep + name)
	os.rmdir(dirToCopy)
	print("Deleted directory %s " % dirToCopy)
	return True

# returns true if string1 is like string2
# utilizes fuzzywuzzy string matching library
# TODO: make acceptance ratio configurable
def like(string1, string2):
	return fuzz.partial_ratio(string1, string2) >= 80


# a new approach that pre-computes the merges
# dirsToCompare - a fully-qualified list of directories that should be compared to one another in a search for duplicates.
def CombineSimilarlyNamedFolders(rootDir, dirsToCompare):
	
	# append trailing slashes to dirs
	# TODO: maybe also check for non-existent dirs here
	for i in range(len(dirsToCompare)):
		if not dirsToCompare[i].endswith(os.sep): 
			dirsToCompare[i] = dirsToCompare[i] + os.sep

	# dictionary of directories to be combined
	matches = defaultdict(list)

	# double loop, bitch
	for i in range(len(dirsToCompare)):
		print('Searching for matches for %s...' % dirsToCompare[i])
		for j in range(len(dirsToCompare)):

			# don't compare a directory to itself, don't compare things that don't exist
			if i == j: continue
			if not os.path.isdir(rootDir + dirsToCompare[i]):
				continue
			if not os.path.isdir(rootDir + dirsToCompare[j]): 
				continue

			tokens1 = os.path.dirname(dirsToCompare[i]).split(os.sep)
			tokens2 = os.path.dirname(dirsToCompare[j]).split(os.sep)
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
					print ('Creating directory %s' % newName)
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
	print ('Searching %s for non-alphanumeric folders...' % rootDir)

	artistDirectories = os.listdir(rootDir)
	artistDirectories.sort()

	for artist in artistDirectories:
		if not os.path.isdir(rootDir + artist): continue
		
		"""
		Detect alphanumeric conditions - ignore the following:
		
		* Whitespace
		* Apostrophes
		* Dashes
		* Commas
		""" 
		artist_test = re.sub(r'\s|\'|-|,', '', artist)
		
		if len(artist_test) > 1 and (not artist_test.isalnum()) and os.path.isdir(rootDir + artist):
			result = ask_user("Would you like to rename <%s>?" % artist)
			if result is None:
				return None
			elif result:

				manual = False

				if re.match('^.*\(\d{4}\)$', artist):
					newName = artist[0:(string.find(artist,'(') - 1)]

					result = ask_user("Rename <%s> to <%s>?" % (artist, newName))
					if result is None:
						return None
					elif result:
						if os.path.isdir(rootDir + newName):
							# folder exists - combine the two
							CombineDirectoryContents(rootDir + newName, rootDir + artist)
						else:
							# folder doesn't exist - rename 
							os.rename(rootDir + artist, rootDir + newName)
							print("Renamed.")
					else:
						# user rejected our suggested name - need to rename manually
						manual = True
				else:
					# didn't match the pattern - need to rename manually
					manual = True


				if manual:
					# rename directory manually
					newName = raw_input("What should we rename it to? ")

					if os.path.isdir(rootDir + newName):
						# if dir exists, combine
						existingFolder = rootDir + newName
						badlyNamedFolder = rootDir + artist + os.sep

						if existingFolder != badlyNamedFolder and os.path.isdir(existingFolder) and os.path.isdir(badlyNamedFolder):
							result = ask_user("Specified directory exists. Combine contents?")
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
	print ('Searching %s for non-alphanumeric folders...' % rootDir)

	# recursively assemble list of subdirs to search
	dirsToSearch = []
	for root, dirs, files in os.walk(rootDir, topdown=False):
		for name in dirs:
			if root not in dirsToSearch:
				if root != startingDir:
					dirsToSearch.append(root)
			if (root + os.sep + name) not in dirsToSearch:
				if (root + os.sep + name) != startingDir:
					dirsToSearch.append(root + os.sep + name)

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
	print ('Searching %s for unwanted file types...' % startingDir)

	ok = []
	bad = []

	for root, dirs, files in os.walk(startingDir, topdown=False):
		for name in files:
			extension = os.path.splitext(root + os.sep + name)[1]
			if extension in bad:
				# delete the file
				print('Deleting file ' + root + os.sep + name)
				os.remove(root + os.sep + name)
			elif extension not in ok:
				# prompt user about this file type
				print('Found new extension *%s' % extension)

				result = ask_user('Delete it?')
				if result is None:
					return
				elif result:
					# delete the file and remember for next time
					os.remove(root + os.sep + name)
					bad.append(extension)
				else:
					# remember for next time
					ok.append(extension)
	print ('Done')


# Deletes empty directories
def DeleteEmptyDirectories():
	print ('Searching %s for empty directories...' % startingDir)

	for root, dirs, files in os.walk(startingDir, topdown=False):
		for name in dirs:
			# returns sub directories and files - if none, it's empty
			# note: this does not consider hidden files - these could be accidentally deleted!
			subdirs = os.listdir(root + os.sep + name)
			if len(subdirs) == 0:
				print('Deleting empty directory ' + root + os.sep + name)
				os.rmdir(root + os.sep + name)

	print ('Done')


# Program Entry
print ('Welcome to MusikPolice\'s Music Directory Cleanup Utility.')
startingDir = raw_input('Enter directory to clean: ')
if not startingDir.endswith(os.sep): 
	startingDir = startingDir + os.sep

while True:
	print('')
	print ('Select an action to perform:')
	print ('1. Combine artist directories (level 1)')
	print ('2. Combine album directories (level 2)')
	print ('3. Rename directories that contain non-standard characters')
	print ('4. Delete unwanted file types')
	print ('5. Delete empty directories')
	print ('6. Quit')
	action = raw_input('>')

	if action == '1':
		if not startingDir.endswith(os.sep): 
			startingDir = startingDir + os.sep
		print ('Searching %s for similarly named artists...' % startingDir)

		artistDirectories = os.listdir(startingDir)
		artistDirectories.sort()
		CombineSimilarlyNamedFolders(startingDir, artistDirectories)

	if action == '2':
		if not startingDir.endswith(os.sep): 
			startingDir += os.sep
		print ('Searching %s for similarly named albums...' % startingDir)
		artistDirectories = os.listdir(startingDir)
		artistDirectories.sort()
		albumDirectories = []
		for a in artistDirectories:
			for sub in os.listdir(startingDir + a):
				albumDirectories.append(a + os.sep + sub + os.sep)
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