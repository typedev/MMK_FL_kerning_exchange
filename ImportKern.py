# copy kern class information from source
from robofab.world import CurrentFont
import os
import pickle

font = CurrentFont()

kernDumpPath = os.path.splitext(font.path)[0] + ".kernToMMK"


# kern_strukt = None
filekern = open(kernDumpPath, 'r')
# kern_strukt = pickle.load(filekern)
filekern.close()

# kernClasses, kernClassesToBooleans, feaClasses = kern_strukt
kernClasses, kernClassesToBooleans, feaClasses = pickle.load(filekern)

KEY_MMK_Colors = 'com.typesupply.MetricsMachine4.groupColors'

groupColors = [ (1.0, 0.0, 0.0, 0.25),
				(1.0, 0.5, 0.0, 0.25),
				(1.0, 1.0, 0.0, 0.25),
				(0.0, 1.0, 0.0, 0.25),
				(0.0, 1.0, 1.0, 0.25),
				(0.0, 0.5, 1.0, 0.25),
				(0.0, 0.0, 1.0, 0.25),
				(0.5, 0.0, 1.0, 0.25),
				(1.0, 0.0, 1.0, 0.25),
				(1.0, 0.0, 0.5, 0.25)  ]

MMK_kernClasses = []
MMK_baseGlyph_Left = {}
MMK_baseGlyph_Right = {}

def checkContent(content):
	result = []
	for name in content:
		if name!='':
			result.append(name)
	return result


for glyphClass in kernClasses:
	MMK_glyphClass = glyphClass.replace('\'','')

	MMK_Name_glyphClass, MMK_Content_glyphClass = MMK_glyphClass.split(':')[0] , MMK_glyphClass.split(':')[1]

	MMK_Base_Glyph = MMK_Content_glyphClass.split(' ')[1]
	leftClass, rightClass = kernClassesToBooleans[glyphClass]

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

		# MMK_kernClasses.append([MMK_Name_glyphClass, MMK_Content_glyphClass])

for glyphClass in feaClasses:
	FEA_Name_glyphClass, FEA_Content_glyphClass = glyphClass.split(':')[0] , glyphClass.split(':')[1]
	MMK_kernClasses.append([FEA_Name_glyphClass, FEA_Content_glyphClass])

font.groups.clear()# []
font.update()


cycleCountColors = len(groupColors)
dicColors = {}
groups = font.groups
for index, gl in enumerate(MMK_kernClasses):
	content = gl[1].split(' ')
	nameClass = gl[0]
	content = checkContent(content)
	groups[nameClass] = content

	dicColors[nameClass] = groupColors[index % cycleCountColors]
font.lib[KEY_MMK_Colors] = dicColors
font.update()

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

font.kerning.clear()
font.kerning.update(new_kern2)
font.update()

print 'Converting Classes and Kerning from Fontlab to MetricsMachine: DONE'

