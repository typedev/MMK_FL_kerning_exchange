"""
	Compare and Update from UFO.
	If the .vfb has a UFO in the same folder, and the names match
		<fontname>.vfb -> <fontname>.ufo
	compare the digests for each glyph in the vfb and the ufo
	update the glyph in the vfb if there is no match
	don't touch groups, kerning, other values.
	
	evb 08

	Import and converting MetricsMachine's groups and kerning

	typedev 14

"""

from robofab.interface.all.dialogs import AskYesNoCancel
from robofab.interface.all.dialogs import Message
from time import asctime
from robofab.world import AllFonts, OpenFont, CurrentFont
from robofab.objects.objectsRF import RFont as _RFont
from robofab.tools.glyphNameSchemes import glyphNameToShortFileName
from robofab.glifLib import GlyphSet
from robofab.objects.objectsFL import RGlyph
from robofab.ufoLib import makeUFOPath, UFOWriter
from robofab.interface.all.dialogs import ProgressBar
from robofab.plistlib import readPlist, writePlist

# from vanilla import Window

from dialogKit import *
from sets import Set

import os

# report = ''

def getLRid(kernClassesToBooleans, n_group):
	l = ''
	r = ''
	if kernClassesToBooleans.has_key(n_group):
		L, R = kernClassesToBooleans[n_group]
		if L: l = '*LEFT'
		if R: r = '*RIGHT'
	return l + r


def compareContent(g1, g2):
	a = ''.join(g1)
	b = ''.join(g2)
	if a != b:
		return False
	else:
		return True


def diffGroups(oldTable, newTable, kernClassesToBooleans):
	newGroups = {}
	delGroups = {}
	chgGroups = {}

	progress = ProgressBar('Making report: Classes', ticks=len(newTable.items()) + len(oldTable.items()))

	report = '\n\n* * * * * Groups report:'

	for n_group, content in newTable.items():
		progress.tick()
		if not oldTable.has_key(n_group):
			newGroups[n_group] = content
			report = report + '\n\nNew Group Added: %s%s [%s]' % (
			n_group, getLRid(kernClassesToBooleans, n_group), ' '.join(content))
		else:
			if not compareContent(oldTable[n_group], newTable[n_group]):
				chgGroups[n_group] = [oldTable[n_group], newTable[n_group]]
				report = report + '\n\nChanged Group: %s%s' % (n_group, getLRid(kernClassesToBooleans, n_group) )
				report = report + '\n\told: [%s]' % (' '.join(oldTable[n_group]))
				report = report + '\n\tnew: [%s]' % (' '.join(newTable[n_group]))
	for o_group, content in oldTable.items():
		progress.tick()
		if not newTable.has_key(o_group):
			delGroups[o_group] = content
			report = report + '\n\nGroup Deleted: %s [%s]' % (o_group, ' '.join(content))
	report = report + '\n\nGroups TOTAL: Added=%i Deleted=%i Changed=%i' % (
	len(newGroups), len(delGroups), len(chgGroups))
	progress.close()
	return report#, newGroups, delGroups, chgGroups


def diffKerning(oldTable, newTable):
	newPairs = {}
	delPairs = {}
	chgPairs = {}
	nulPairs = {}
	report = '\n\n* * * * * Kerning report:\n'
	progress = ProgressBar('Making report: Kerning', ticks=len(newTable.items()) + len(oldTable.items()))

	for (l, r), v in newTable.items():
		progress.tick()
		if v == 0:
			nulPairs[(l, r)] = v
		else:
			if not oldTable.has_key((l, r)):
				newPairs[(l, r)] = v
				report = report + '\nNew Pair: %s %s %i' % (l, r, v)
			else:
				if oldTable[(l, r)] != newTable[(l, r)]:
					chgPairs[(l, r)] = [oldTable[(l, r)], newTable[(l, r)]]
					report = report + '\nChanged Pair: %s %s' % (l, r)
					report = report + '\n\told: %i\tnew: %i' % (oldTable[(l, r)], newTable[(l, r)])
	for (l, r), v in oldTable.items():
		progress.tick()
		if not newTable.has_key((l, r)):
			delPairs[(l, r)] = v
			report = report + '\nPair Deleted: %s %s %i' % (l, r, v)
	report = report + '\n\nPairs TOTAL: Added=%i Deleted=%i Changed=%i Null pairs (ignored)=%i' % (
	len(newPairs), len(delPairs), len(chgPairs), len(nulPairs))
	progress.close()
	return report#,newPairs, delPairs, chgPairs, nulPairs


def generateClassName(kernClasses, classname):
	for i in range(1, 1000, 1):
		if not kernClasses.has_key(classname + str(i)):
			return classname + str(i)
			break


def importKerningMMK(font, UFOfilepath):
	report = 'Import MMKerning Report ' + asctime() + '\nUFO file: ' + UFOfilepath
	kernClasses = {}
	kernClassesToBooleans = {}
	kernTable = {}
	feaClasses = {}
	dicGroups = {}
	UFOpath_kerning = UFOfilepath + '/kerning.plist'
	UFOpath_groups = UFOfilepath + '/groups.plist'

	kernGroups = readPlist(UFOpath_groups)

	progress = ProgressBar('Converting group names', ticks=len(kernGroups.items()))

	for groupname, content in kernGroups.items():
		progress.tick()
		if len(content) != 0:

			if content[0] == '':
				content.pop(0)
			if groupname.startswith('@'): #  @MMK_
				classname = '_' + groupname[7:]

				baseGlyph = content[0]
				content[0] = baseGlyph + '\''
				classcontent = content
				dicGroups[groupname] = baseGlyph

				if kernClasses.has_key(classname):
					if kernClasses[classname] == classcontent:
						kernClassesToBooleans[classname] = (True, True)

					else:
						classname = generateClassName(kernClasses, classname)
						kernClasses[classname] = classcontent

						if groupname[5] == 'L': #  @MMK_L_namegroup
							kernClassesToBooleans[classname] = (True, False)
						elif groupname[5] == 'R': #  @MMK_R_namegroup
							kernClassesToBooleans[classname] = (False, True)
						else:
							print "WARNING! Something wrong whith LEFT/RIGHT identification...", groupname
						# kernClassesToBooleans[classname] = (True, True)
				else:
					if groupname[5] == 'L':
						kernClassesToBooleans[classname] = (True, False)
					elif groupname[5] == 'R':
						kernClassesToBooleans[classname] = (False, True)
					else:
						print "WARNING! Something wrong whith LEFT/RIGHT identification...", groupname
					kernClasses[classname] = classcontent

			else: # fea
				feaClasses[groupname] = content#' '.join(content)
		else:
			print 'WARNING! Group with NULL content:', groupname
	progress.close()

	progress = ProgressBar('Merging kerning and fea-classes', ticks=len(kernClasses.items()) + len(feaClasses.items()))

	classes = {} #= font.groups
	for classname, content in kernClasses.items():
		progress.tick()
		classes[classname] = content#.split(' ')
	# font.naked().classes
	for classname, content in feaClasses.items():
		progress.tick()
		classes[classname] = content#.split(' ')
	progress.close()

	report = report + diffGroups(font.groups, classes, kernClassesToBooleans)

	font.groups.clear()
	font.groups = classes
	font.update()

	progress = ProgressBar('Left/Right identification', ticks=len(font.naked().classes))

	for index, kernClass in enumerate(font.naked().classes):
		progress.tick()
		if kernClass.startswith('_'):
			# print kernClass
			nameClass = kernClass.split(':')[0]
			# print nameClass
			leftBool, rightBool = kernClassesToBooleans[nameClass]
			font.naked().SetClassFlags(index, leftBool, rightBool)
	font.update()
	print '\nConverting Groups from MetricsMachine to Fontlab Classes: DONE\n'
	progress.close()

	pl = readPlist(UFOpath_kerning)
	for left, right in pl.items():
		for key_r, value in right.items():
			kernTable[(left, key_r)] = value

	progress = ProgressBar('Left pairs converting', ticks=len(kernTable.items()))

	new_kern1 = {}
	for (left, right), value in kernTable.items():
		progress.tick()
		if dicGroups.has_key(left):
			baseGlyph = dicGroups[left]
			new_kern1[(baseGlyph, right)] = value
		else:
			if left.startswith('@'):
				print "WARNING! Something wrong with pair:", left, right, value, 'Ignored.'
			else:
				new_kern1[(left, right)] = value
	progress.close()

	progress = ProgressBar('Right pairs converting', ticks=len(new_kern1.items()))

	new_kern2 = {}
	for (left, right), value in new_kern1.items():
		progress.tick()
		if dicGroups.has_key(right):
			baseGlyph = dicGroups[right]
			new_kern2[(left, baseGlyph)] = value
		else:
			if right.startswith('@'):
				print "WARNING! Something wrong with pair:", left, right, value, 'Ignored.'
			else:
				new_kern2[(left, right)] = value
	progress.close()

	report = report + diffKerning(font.kerning, new_kern2)

	font.kerning.clear()
	font.kerning.update(new_kern2)
	font.update()

	reportfile = open(UFOfilepath.replace('.ufo', '.log'), 'w')
	reportfile.write(report)
	reportfile.close()
	print '\nConverting Kerning from MetricsMachine to Fontlab: DONE\n'


class UpdateFromUFODialogDialog(object):
	def __init__(self, ufo, vfb, ufoPath):
		self.ufo = ufo
		self.vfb = vfb
		self.ufoPath = ufoPath
		self.updateNames = []
		self.w = ModalDialog((200, 400), 'Update Font From UFO', okCallback=self.okCallback)
		self.w.list = List((5, 70, -5, -100), ['Comparing VFB',
		                                       "to its UFO.",
		                                       "Click Compare to begin.",
		                                       '',
		                                       'Click Import MMK kerning',
		                                       'to import MetricsMachine\'s',
		                                       'kerning and groups.'
		], callback=self.listHitCallback)

		self.w.importKerningMMKbutton = Button((10, 315, -10, 20), "Import MMK kerning",
		                                       callback=self.importKerningMMKCallback)
		self.w.updateButton = Button((10, 40, 85, 20), 'Update', callback=self.updateCallback)
		self.w.updateAllButton = Button((105, 40, -10, 20), 'Update All', callback=self.updateAllCallback)
		self.w.checkButton = Button((10, 10, -10, 20), 'Compare Glyphs', callback=self.checkCallback)

		self.w.open()

	def okCallback(self, sender):
		print 'this final list contains:', list(self.w.list)

	def importKerningMMKCallback(self, sender):
		self.w.list.set([])
		print 'Importing Kerning', asctime()
		importKerningMMK(self.vfb, self.ufoPath)

	# pass

	def listHitCallback(self, sender):
		selection = sender.getSelection()
		if not selection:
			selectedItem = None
		else:
			selectionIndex = selection[0]
			selectedItem = sender[selectionIndex]
		print 'selection:', selectedItem

	def updateAllCallback(self, sender):
		print "Update all glyphs"
		names = self.updateNames[:]
		progress = ProgressBar('Update all glyphs', ticks=len(names))
		for n in self.updateNames:
			self.updateGlyph(n)
			names.remove(n)
			self.w.list.set(names)
			progress.tick()
		self.w.list.setSelection([-1])
		progress.close()

	# if self.w.MMK_import.get():
	# 	importKerningMMK(self.vfb, self.ufoPath)


	def updateCallback(self, sender):
		print "Update selected glyph"
		names = []
		for index in self.w.list.getSelection():
			names.append(self.updateNames[index])
		progress = ProgressBar('Update selected glyph', ticks=len(names))
		for n in names:
			self.updateGlyph(n)
			self.updateNames.remove(n)
			self.w.list.set(self.updateNames)
			progress.tick()
		self.w.list.setSelection([-1])
		progress.close()

	# if self.w.MMK_import.get():
	# 	importKerningMMK(self.vfb, self.ufoPath)

	def checkCallback(self, sender):
		print "checking fonts"
		self.analyseFonts()

	def analyseFonts(self):
		ufoDigests = {}
		print "calculating UFO digests"
		ufoNames = self.ufo.keys()
		vfbNames = self.vfb.keys()
		self.w.list.set([])
		self.updateNames = []

		progress1 = ProgressBar('Calculating Glyphs Order', ticks=len(ufoNames)) #(5, -100, -5, 10),

		for n in ufoNames:
			if n not in vfbNames:
				# print 'p1:', n
				self.updateNames.append(n)
				self.updateNames.sort()
				self.w.list.set(self.updateNames)
				self.w.list.setSelection([-1])
			progress1.tick()
		progress1.close()

		relevantNames = Set(ufoNames) & Set(vfbNames)
		names = list(relevantNames)
		names.sort()

		progress2 = ProgressBar('Comparing Glyphs', ticks=len(names)) #(5, -120, -5, 10),
		for name in names:
			# print 'p2:',name
			ufoDigest = self.ufo[name]._getDigest()
			vfbDigest = self.vfb[name]._getDigest()
			if ufoDigest != vfbDigest:
				self.updateNames.append(name)
				self.w.list.set(self.updateNames)
				self.w.list.setSelection([-1])
			progress2.tick()
		progress2.close()

	def updateGlyph(self, name):
		print "importing", name
		self.vfb[name].clear()
		self.vfb.insertGlyph(self.ufo[name], name=name)
		self.vfb[name].width = self.ufo[name].width
		self.vfb[name].note = self.ufo[name].note
		self.vfb[name].psHints.update(self.ufo[name].psHints)
		self.vfb[name].mark = 50
		self.vfb[name].update()


if __name__ == "__main__":


	f = CurrentFont()
	ufoPath = f.path.replace(".vfb", ".ufo")
	if os.path.exists(ufoPath):
		print "there is a ufo for this font at", ufoPath
		ufo = _RFont(ufoPath)
		UpdateFromUFODialogDialog(ufo, f, ufoPath)
	f.update()

	print "done"