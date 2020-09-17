import sys
import shutil
import os
import time
import re
from enum import Enum

class State(Enum):
	ERROR = 0 
	VALID = 1

class Error(Enum):
	ERR_IMG = 0
	ERR_CREDIT = 1
	ERR_EXPLANATION = 2

class DirInfo(object):
	def __init__(self, program, src):
		self.p = program
		self.src = src
		self.fInfos = []
		self.dInfos = []
		self.vFiles = []
		self.nbFiles = 0
		self.nbValidFiles = 0
		self.nbErrors = 0

	def printLogStats(self):
		print("\nTotal:\t{0}".format(self.nbFiles))
		print("Errors:\t{0}".format(self.nbErrors))
		self.log.write("Total: {0} files ".format(self.nbFiles))
		self.log.write("\nValid: {0} files".format(self.nbValidFiles))

	def createLogFile(self):
		self.log = open('log.txt', 'w')

	def closeLogFile(self):
		self.log.close()

	def logImgData(self, fInfo):
		sep = "------------------------------------\n"
		if(fInfo.state is State.VALID):
			self.log.write("{0}\n".format(fInfo.img))
			self.log.write("\n{0}".format(fInfo.credit))
			self.log.write("\n{0}".format(sep))

	def printError(self, fInfo):
		if(fInfo.state is State.ERROR):
			print("File \"{0}{1}\"".format(fInfo.filename, fInfo.extension), end='')
			if(Error.ERR_IMG in fInfo.err):
				print("\t{0}".format(self.p.parser.errorMsg[Error.ERR_IMG.value]))
			if(Error.ERR_CREDIT in fInfo.err):
				print("\t{0}".format(self.p.parser.errorMsg[Error.ERR_CREDIT.value]))
			if(Error.ERR_EXPLANATION in fInfo.err):
				print("\t{0}".format(self.p.parser.errorMsg[Error.ERR_EXPLANATION.value]))

class FileInfo(object):
	def __init__(self, fileFullname , filepath, filename, extension, size):
		self.fileFullname = fileFullname
		self.filepath = filepath
		self.filename = filename
		self.extension = extension
		self.size = size
		self.state = None
		self.err = []
		self.img = ""
		self.credit = ""

class util(object):
	def getInfos(src):
		filesInfo = []
		dirInfo = []
		for dirpath, dirnames, fnames in os.walk(src):
			for f in fnames:
				fileFullname = os.path.join(dirpath, f)
				filename, ext = os.path.splitext(f)
				size = os.path.getsize(fileFullname)
				filesInfo.append(FileInfo(fileFullname, dirpath, filename, ext, size))
				dirInfo.append(fileFullname)
		
		return filesInfo, dirInfo

	def extractTextData(ch):
		f = open(ch, 'r', errors='ignore')
		l = f.readlines()
		f.close()
		return l

	def makeDir(src):
		shutil.rmtree(src, ignore_errors=True)
		os.mkdir(src)

	def copyFiles(src, dest):
		filesname = copy_tree(src, dest, 1, 1, 1, 1)

	def getCurrentDirectory():
		cd = os.getcwd()
		return cd
	
class Parser(object):
	def __init__(self, program):
		self.p = program
		self.imgPattern = re.compile("<a href=\"image/")
		self.creditStartPattern = re.compile("(Credit|Courtesy)")
		self.creditEndPattern = re.compile("(Explanation)")
		self.imgCleaningPattern = re.compile("([a-zA-Z]|[0-9]|_|-)+\.[a-zA-Z]+")

		self.errorMsg = [ "Error_IMG: Couldn't find appropriate image info.",
						 "Error_CREDIT: Couldn't find start of credit info.",
						 "Error_EXPLANATION: Couldn't find end of credit info." ]

	def cleanImgData(self, data):
		imgDataClean = re.search(self.imgCleaningPattern, data)

		if(imgDataClean):
			return imgDataClean[0]
		else:
			return ""

	def parseData(self, text, fInfo):
		imgData = ""
		self.creditData = ""
		self.continueTofetchCreditInfo = 0
		imgValidation = creditValidation = endCreditValidation = 0
		
		for line in text:
			if(not imgValidation):
				if(re.search(self.imgPattern, line)):
					imgData += line;
					imgValidation = 1

			if(not creditValidation):
				if(re.search(self.creditStartPattern, line)):
					self.continueTofetchCreditInfo = 1
					creditValidation = 1

			if(creditValidation and not endCreditValidation):
				if(re.search(self.creditEndPattern, line)):
					self.continueTofetchCreditInfo = 0
					endCreditValidation = 1

			if(self.continueTofetchCreditInfo == 1):
				self.creditData += line

		if(not imgValidation):
			fInfo.err.append(Error.ERR_IMG)
		if(not creditValidation):
			fInfo.err.append(Error.ERR_CREDIT)
		if(not endCreditValidation):
			fInfo.err.append(Error.ERR_EXPLANATION)

		if(fInfo.err):
			fInfo.state = State.ERROR
			self.p.Info.nbErrors += 1
		else:
			fInfo.state = State.VALID

			fInfo.img = self.cleanImgData(imgData)
			fInfo.credit = self.creditData
			if(fInfo.img and fInfo.credit):
				self.p.Info.vFiles.append(fInfo)

class Program(object):
	def __init__(self):
		self.src = sys.argv[1]
		self.html_dest = "bibliotheque/"
		self.credit_dest = "credit/"
		self.setup()
		self.parse()
		#self.create_credit()
		self.copy_html()

	def setup(self):
		self.startProgram = time.time()
		self.Info = DirInfo(self, self.src)
		self.Info.fInfos, self.Info.dInfos = util.getInfos(self.src)
		self.Info.nbFiles = len(self.Info.dInfos)
		self.Info.createLogFile()

	def parse(self):
		self.parser = Parser(self)
		for f in self.Info.fInfos:
			text = util.extractTextData(f.fileFullname)
			self.parser.parseData(text, f)
			self.Info.printError(f)
			self.Info.logImgData(f)

		self.Info.nbValidFiles = len(self.Info.vFiles)
		self.Info.printLogStats()

		self.Info.closeLogFile()

	def copy_html(self):
		var = input("\nDo you want to copy all ({0}) valid files to \"{1}\"? (Y/n) ".format(self.Info.nbValidFiles, self.html_dest))
		if(var == 'Y'):
			util.makeDir(util.getCurrentDirectory()+"/"+self.html_dest)
			print("\n Starting copy ##")
			for f in self.Info.vFiles:
				shutil.copy2(f.fileFullname, self.html_dest + f.filename + f.extension)

			endProgram = time.time()
			print("\nTemps Total: %f" % (endProgram - self.startProgram))
		else:
			sys.exit()

	"""
	def create_credit(self):
		util.makeDir(util.getCurrentDirectory()+self.credit_dest)
		for vFile in self.Info.vFiles:
			f = open(self.credit_dest + vFile.img + ".txt", 'w')
			f.write(vFile.credit)
			f.close()
	"""

if __name__ == '__main__':
	program = Program()