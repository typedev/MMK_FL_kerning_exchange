# FLM: KERN Exchange FL/MM
"""

	Exchange classes and kerning between Fontlab and MetricsMachine

	typedev
	Alexander Lubovenko

	www.github.com/typedev

"""
import os
from time import asctime
from robofab.world import CurrentFont
from robofab.ufoLib import UFOWriter, UFOReader
# from robofab.interface.all.dialogs import ProgressBar
from dialogKit import *

VERSION = '0.2.2'

WARNING_TEXT = """The .vfb and UFO must be in the same folder, and the names match fontname.vfb=fontname.ufo

WARNING! I strongly recommended to backup your .vfb and .ufo files before any operation with Import and Export kerning.
"""
HELP_TEXT = """Export to UFO: FontLab will replace all groups, kerning and font.lib from VFB file during export to UFO.

Import from UFO: Only groups and kerning will be replaced during import from UFO.
"""

# IMPORT section =========================================

def get_L_R_ident (kern_L_R_table, n_group):
	l = ''
	r = ''
	if kern_L_R_table.has_key(n_group):
		L, R = kern_L_R_table[n_group]
		if L: l = '*LEFT'
		if R: r = '*RIGHT'
	return l + r


def compareContent (g1, g2):
	a = ''.join(g1)
	b = ''.join(g2)
	if a != b:
		return False
	else:
		return True


def diffGroups (oldTable, newTable, kern_L_R_table):
	newGroups = {}
	delGroups = {}
	chgGroups = {}

	# progress = ProgressBar('Making report: Classes', ticks = len(newTable.items()) + len(oldTable.items()))

	report = '\n\n* * * * * Groups report:'

	for n_group, content in newTable.items():
		# progress.tick()
		if not oldTable.has_key(n_group):
			newGroups[n_group] = content
			report = report + '\n\nNew Group Added: %s%s [%s]' % (
			n_group, get_L_R_ident(kern_L_R_table, n_group), ' '.join(content))
		else:
			if not compareContent(oldTable[n_group], newTable[n_group]):
				chgGroups[n_group] = [oldTable[n_group], newTable[n_group]]
				report = report + '\n\nChanged Group: %s%s' % (n_group, get_L_R_ident(kern_L_R_table, n_group) )
				report = report + '\n\told: [%s]' % (' '.join(oldTable[n_group]))
				report = report + '\n\tnew: [%s]' % (' '.join(newTable[n_group]))
	for o_group, content in oldTable.items():
		# progress.tick()
		if not newTable.has_key(o_group):
			delGroups[o_group] = content
			report = report + '\n\nGroup Deleted: %s [%s]' % (o_group, ' '.join(content))
	report = report + '\n\nGroups TOTAL: Added=%i Deleted=%i Changed=%i' % (
	len(newGroups), len(delGroups), len(chgGroups))
	# progress.close()
	return report#, newGroups, delGroups, chgGroups


def diffKerning (oldTable, newTable):
	newPairs = {}
	delPairs = {}
	chgPairs = {}
	nulPairs = {}
	report = '\n\n* * * * * Kerning report:\n'
	# progress = ProgressBar('Making report: Kerning', ticks = len(newTable.items()) + len(oldTable.items()))

	for (l, r), v in newTable.items():
		# # progress.tick()
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
		# progress.tick()
		if not newTable.has_key((l, r)):
			delPairs[(l, r)] = v
			report = report + '\nPair Deleted: %s %s %i' % (l, r, v)
	report = report + '\n\nPairs TOTAL: Added=%i Deleted=%i Changed=%i Null pairs (ignored)=%i' % (
	len(newPairs), len(delPairs), len(chgPairs), len(nulPairs))
	# progress.close()
	return report#,newPairs, delPairs, chgPairs, nulPairs


def generateClassName (kernClasses, classname):
	for i in range(1, 1000, 1):
		if not kernClasses.has_key(classname + str(i)):
			return classname + str(i)
			break


def importKerningMMK (font, UFOfilepath):
	report = 'Import Kerning Report ' + asctime() + '\nUFO file: ' + UFOfilepath
	kernClasses = {}
	kern_L_R_table = {}
	kernTable = {}
	feaClasses = {}
	dicGroups = {}

	UFO = UFOReader(UFOfilepath)
	kernGroups = UFO.readGroups()
	kernTable = UFO.readKerning()

	# progress = ProgressBar('Converting group names', ticks = len(kernGroups.items()))

	for groupname, content in kernGroups.items():
		# progress.tick()
		if len(content) != 0:
			if content[0] == '':
				content.pop(0)
			if groupname.startswith('@'): #  @MMK_ = MM kern class
				classname = '_' + groupname[7:]

				baseGlyph = content[0]
				content[0] = baseGlyph + '\''
				classcontent = content
				dicGroups[groupname] = baseGlyph

				if kernClasses.has_key(classname):
					if kernClasses[classname] == classcontent:
						kern_L_R_table[classname] = (True, True)
					else:
						classname = generateClassName(kernClasses, classname)
						if groupname[5] == 'L': #  @MMK_L_namegroup
							kern_L_R_table[classname] = (True, False)
						elif groupname[5] == 'R': #  @MMK_R_namegroup
							kern_L_R_table[classname] = (False, True)
						else:
							print "WARNING! Something wrong whith LEFT/RIGHT identification...", groupname
				else:
					if groupname[5] == 'L': #  @MMK_L_namegroup
						kern_L_R_table[classname] = (True, False)
					elif groupname[5] == 'R': #  @MMK_R_namegroup
						kern_L_R_table[classname] = (False, True)
					else:
						print "WARNING! Something wrong whith LEFT/RIGHT identification...", groupname

				kernClasses[classname] = classcontent


			else: # fea class
				feaClasses[groupname] = content#' '.join(content)
		else:
			print 'WARNING! Group with NULL content: %s Ignored.' % groupname
			report = report + '\n\nGroup with NULL content: %s Ignored.' % groupname
	# progress.close()

	# progress = ProgressBar('Merging kerning and fea-classes',ticks = len(kernClasses.items()) + len(feaClasses.items()))

	classes = {}
	for classname, content in kernClasses.items():
		# progress.tick()
		classes[classname] = content#.split(' ')

	for classname, content in feaClasses.items():
		# progress.tick()
		classes[classname] = content#.split(' ')
	# progress.close()

	report = report + diffGroups(font.groups, classes, kern_L_R_table)

	font.groups.clear()
	font.groups = classes
	font.update()

	# progress = ProgressBar('Left/Right identification', ticks = len(font.naked().classes))

	for index, kernClass in enumerate(font.naked().classes):
		# progress.tick()
		if kernClass.startswith('_'):
			nameClass = kernClass.split(':')[0]
			leftBool, rightBool = kern_L_R_table[nameClass]
			font.naked().SetClassFlags(index, leftBool, rightBool)
	font.update()
	print '\nConverting Groups from MetricsMachine to Fontlab Classes: DONE\n'
	# progress.close()

	# progress = ProgressBar('Left pairs converting', ticks = len(kernTable.items()))

	new_kern1 = {}
	for (left, right), value in kernTable.items():
		# progress.tick()
		if dicGroups.has_key(left):
			baseGlyph = dicGroups[left]
			new_kern1[(baseGlyph, right)] = value
		else:
			if left.startswith('@'):
				print "WARNING! Something wrong with pair:", left, right, value, 'Ignored.'
			else:
				new_kern1[(left, right)] = value
	# progress.close()

	# progress = ProgressBar('Right pairs converting', ticks = len(new_kern1.items()))

	new_kern2 = {}
	for (left, right), value in new_kern1.items():
		# progress.tick()
		if dicGroups.has_key(right):
			baseGlyph = dicGroups[right]
			new_kern2[(left, baseGlyph)] = value
		else:
			if right.startswith('@'):
				print "WARNING! Something wrong with pair:", left, right, value, 'Ignored.'
			else:
				new_kern2[(left, right)] = value
	# progress.close()

	report = report + diffKerning(font.kerning, new_kern2)

	font.kerning.clear()
	font.kerning.update(new_kern2)
	font.update()

	reportfile = open(UFOfilepath.replace('.ufo', '.log'), 'w')
	reportfile.write(report)
	reportfile.close()
	print '\nConverting Kerning from MetricsMachine to Fontlab: DONE\n'

# END IMPORT section =====================================

# EXPORT section =========================================

KEY_MMK_Colors = 'com.typesupply.MetricsMachine4.groupColors'

GROUP_COLORS = [(1.0, 0.0, 0.0, 0.25),
                (1.0, 0.5, 0.0, 0.25),
                (1.0, 1.0, 0.0, 0.25),
                (0.0, 1.0, 0.0, 0.25),
                (0.0, 1.0, 1.0, 0.25),
                (0.0, 0.5, 1.0, 0.25),
                (0.0, 0.0, 1.0, 0.25),
                (0.5, 0.0, 1.0, 0.25),
                (1.0, 0.0, 1.0, 0.25),
                (1.0, 0.0, 0.5, 0.25)]


def fixGlyphOrder (font, groupname, baseglyph):
	newcontent = []
	newcontent.append(baseglyph)
	for glyphname in font.groups[groupname]:
		if glyphname != baseglyph:
			newcontent.append(glyphname)
	font.groups[groupname] = newcontent


def checkGlyphOrder (font):
	for group in font.groups.items():
		content = []
		groupname, content = group
		for idx, glyphname in enumerate(content):
			if ('\'' in glyphname) and (idx != 0):
				print 'Group %s has wrong order... fixed.' % groupname
				fixGlyphOrder(font, groupname, glyphname)
				break


def checkContent (content):
	result = []
	for name in content:
		if name != '':
			result.append(name)
	return result


def getKernStrukt (font):
	feaClasses = []
	kernClasses = []
	kern_L_R_table = {}
	for index, glyphClass in enumerate(font.naked().classes):
		if glyphClass.startswith("_"):
			kernClasses.append(glyphClass)
			kern_L_R_table[glyphClass] = (font.naked().GetClassLeft(index), font.naked().GetClassRight(index))
		else:
			feaClasses.append(glyphClass)
	return [kernClasses, kern_L_R_table, feaClasses]


def exportKerningFL (font, UFOfilepath):
	MMK_kernClasses = []
	MMK_baseGlyph_Left = {}
	MMK_baseGlyph_Right = {}

	UFO = UFOWriter(UFOfilepath)

	kernClasses, kern_L_R_table, feaClasses = getKernStrukt(font)

	for glyphClass in kernClasses:
		MMK_glyphClass = glyphClass.replace('\'', '')

		MMK_Name_glyphClass, MMK_Content_glyphClass = MMK_glyphClass.split(':')[0], MMK_glyphClass.split(':')[1]

		MMK_Base_Glyph = MMK_Content_glyphClass.split(' ')[1]
		leftClass, rightClass = kern_L_R_table[glyphClass]

		if (leftClass == 1) and (rightClass == 1):
			MMK_Name_glyphClass_L = '@MMK_L' + MMK_Name_glyphClass
			MMK_kernClasses.append([MMK_Name_glyphClass_L, MMK_Content_glyphClass])
			MMK_baseGlyph_Left[MMK_Base_Glyph] = MMK_Name_glyphClass_L

			MMK_Name_glyphClass_R = '@MMK_R' + MMK_Name_glyphClass
			MMK_kernClasses.append([MMK_Name_glyphClass_R, MMK_Content_glyphClass])
			MMK_baseGlyph_Right[MMK_Base_Glyph] = MMK_Name_glyphClass_R
		else:
			if leftClass == 1:
				MMK_Name_glyphClass = '@MMK_L' + MMK_Name_glyphClass
				MMK_baseGlyph_Left[MMK_Base_Glyph] = MMK_Name_glyphClass
				MMK_kernClasses.append([MMK_Name_glyphClass, MMK_Content_glyphClass])
			if rightClass == 1:
				MMK_Name_glyphClass = '@MMK_R' + MMK_Name_glyphClass
				MMK_baseGlyph_Right[MMK_Base_Glyph] = MMK_Name_glyphClass
				MMK_kernClasses.append([MMK_Name_glyphClass, MMK_Content_glyphClass])

			if (leftClass == 0) and (rightClass == 0):
				print 'WARNING! Wrong Kern group:', MMK_Name_glyphClass, '* NOT Left and NOT Right *. Please fix it.'

	for glyphClass in feaClasses:
		FEA_Name_glyphClass, FEA_Content_glyphClass = glyphClass.split(':')[0], glyphClass.split(':')[1]
		MMK_kernClasses.append([FEA_Name_glyphClass, FEA_Content_glyphClass])

	cycleCountColors = len(GROUP_COLORS)
	dicColors = {}
	groups = {}
	for index, gl in enumerate(MMK_kernClasses):
		content = gl[1].split(' ')
		nameClass = gl[0]
		content = checkContent(content)
		groups[nameClass] = content

		dicColors[nameClass] = GROUP_COLORS[index % cycleCountColors]
	font.lib[KEY_MMK_Colors] = dicColors

	font.update()
	UFO.writeGroups(groups)
	# TODO maybe need to compare UFO and VFB before overwriting font.LIB , and merge LIB if they are not equal
	UFO.writeLib(font.lib)

	kerntabl = font.kerning
	new_kern1 = {}
	new_kern2 = {}
	for (left, right), value in kerntabl.items(): #font.kerning.items():
		if MMK_baseGlyph_Left.has_key(left):
			new_L = MMK_baseGlyph_Left[left]
			new_kern1[(new_L, right)] = value
		else:
			new_kern1[(left, right)] = value

	for (left, right), value in new_kern1.items(): #font.kerning.items():
		if MMK_baseGlyph_Right.has_key(right):
			new_R = MMK_baseGlyph_Right[right]
			new_kern2[(left, new_R)] = value
		else:
			new_kern2[(left, right)] = value

	UFO.writeKerning(new_kern2)

	print 'Converting Classes and Kerning from Fontlab to MetricsMachine: DONE'

# END EXPORT section =====================================

# UI section =============================================

def getUFOpath (font):
	ufoPath = font.path.replace(".vfb", ".ufo")
	if os.path.exists(ufoPath):
		print 'UFO file: ', ufoPath
		return ufoPath
	else:
		print 'UFO file not found...'
		return None


class KERNExchanger(object):
	def __init__ (self):
		self.w = ModalDialog((400, 320), 'Kerning Exchange FontLab<>MetricsMachine. v' + VERSION)
		self.w.btnExport = Button((10, 25, 180, 20), 'Export Kerning to UFO', callback = self.run_exportFLK)

		self.w.btnImport = Button((210, 25, 180, 20), 'Import Kerning from UFO', callback = self.run_importMMK)
		self.w.warninglabel = TextBox((10, 70, -10, 100), WARNING_TEXT)
		self.w.helplabel = TextBox((10, 180, -10, 80), HELP_TEXT)
		self.w.open()

	def run_importMMK (self, sender):
		font = CurrentFont()
		# print 'Import Kerning from:' + font.info.name
		if font != None:
			ufopath = getUFOpath(font)
			if ufopath != None:
				importKerningMMK(font, ufopath)
		else:
			print 'Please, open any .vfb with kerning :)'
		self.w.close()

	def run_exportFLK (self, sender):
		font = CurrentFont()
		if font != None:
			checkGlyphOrder(font)
			ufopath = getUFOpath(font)
			if ufopath != None:
				exportKerningFL(font, ufopath)
		else:
			print 'Please, open any .vfb with kerning :)'
		self.w.close()


if __name__ == "__main__":
	KERNExchanger()



