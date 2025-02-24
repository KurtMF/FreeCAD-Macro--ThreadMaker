# INDEMNITY: By using this software you agree not to sue me for any reason related to the use of this software.
#
# Copyright (c) 2022 Kurt Funderburg, all rights not explicitly relinquished in LGPL reserved.
#
#   This program is free software; you can redistribute it and/or modify  
#   it under the terms of the GNU Lesser General Public License (LGPL)    
#   as published by the Free Software Foundation; either version 2 of     
#   the License, or (at your option) any later version.                   
#                                                                         
#   This program is distributed in the hope that it will be useful,       
#   but WITHOUT ANY WARRANTY; without even the implied warranty of       
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         
#   GNU Library General Public License for more details.                  
#                                                                         
#   You should have received a copy of the GNU Library General Public     
#   License along with this program; if not, write to the Free Software   
#   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  
#   USA                                                                   

import FreeCAD, Part, math, os
from FreeCAD import Base
from PySide import QtGui, QtCore

__title__ = "ThreadMaker: Fully parametric threaded shafts for supported standards or custom user specs."
__author__ = "Kurt Funderburg"

MRUPATH = "User parameter:BaseApp/Macro/ThreadMaker/MRU"		# getParam(MRUPATH) stores last accepted values of dialog
EXTOBJECTNAME = "ThreadExt"			# Thread object name, also object label prefix.  Will also use "ThreadInsert"
INTOBJECTNAME = "ThreadInt"			
SUPPORTEDSTANDARDS = { 			# Dictionary constant of { Name : Taper(float) }
	"Custom" : 0, 								# Unrestricted specification of d, p, t
	"ISO 261 Metric" : 0 }						# Straight metric thread  

# ISO 261 CONSTANTS AND METHODS ########################################################
ISO965EXTPITCHTOL = ('3e', '3f', '3g', '3h', '4e', '4f', '4g', '4h', '5e', '5f', '5g', '5h', '6e', '6f', '6g', '6h', '7e', '7f', '7g', '7h', 
						'8e', '8f', '8g', '8h', '9e', '9f', '9g', '9h')
ISO965EXTCRESTTOL = ('4e', '4f', '4g', '4h', '6e', '6f', '6g', '6h', '8e', '8f', '8g', '8h')
ISO965INTPITCHTOL = ('4G', '4H', '5G', '5H', '6G', '6H', '7G', '7H', '8G', '8H')
ISO965INTCRESTTOL = ('4G', '4H', '5G', '5H', '6G', '6H', '7G', '7H', '8G', '8H')
#ISO261PDTABLE = {  		# ISO 261 Table 2 Pitch-Diameter lookup table as Python dictionary defined at end of this module

def iso965ExtPitchDev(nomdiameter, pitch, pitchtol):		# Compute & return pitch deviation per ISO965 S.13 formulae
	""" (nomdiameter (float), pitch (float), potchtol (str)) """
	fd = 0.0
	td = 0.0
	if  pitchtol[1] == "e":	fd = (50 + 11 * pitch) / 1000	#ese = – (50 + 11 P)  #exceptions for P<=0.45
	if  pitchtol[1] == "f":	fd = (30 + 11 * pitch) / 1000	#esf = – (30 + 11 P)  # not applicable for P<=0.3
	if  pitchtol[1] == "g":	fd = (15 + 11 * pitch) / 1000	#esg = – (15 + 11 P)
	if  pitchtol[1] == "h":	fd = 0						#esh = 0
	td6 = 90 * pitch**0.4 * nomdiameter**0.1 / 1000	#Crest Tol. Deviation (number grade) PTD6 (um) = 90 * P ** 0.4 * D ** 0.1; 
	if  pitchtol[0] == "3":	td = 0.5 * td6
	if  pitchtol[0] == "4":	td = 0.63 * td6	# PTD4 = 0,63 TD6; 
	if  pitchtol[0] == "5":	td = 0.8 * td6		# PTD5 =  0,8 PTD6; 
	if  pitchtol[0] == "6":	td = td6
	if  pitchtol[0] == "7":	td = 1.25 * td6	# PTD7 = 1,25 TD6; 
	if  pitchtol[0] == "8":	td = 1.6 * td6		# PTD8 = 1,6 TD6
	if  pitchtol[0] == "9":	td = 2.0 * td6		# PTD8 = 1,6 TD6
	return fd + td

def iso965IntPitchDev(nomdiameter, pitch, pitchtol):		# Compute & return pitch deviation per ISO965 S.13 formulae
	""" (nomdiameter (float), pitch (float), potchtol (str)) """
	fd = 0.0
	td = 0.0
	if  pitchtol[1] == "G":	fd = (15 + 11 * pitch) / 1000	#esg = – (15 + 11 P)
	if  pitchtol[1] == "H":	fd = 0						#esh = 0
	td6 = 90 * pitch**0.4 * nomdiameter**0.1 / 1000	#Crest Tol. Deviation (number grade) PTD6 (um) = 90 * P ** 0.4 * D ** 0.1; 
	if  pitchtol[0] == "4":	td = 0.85 * td6	# PTD4 = 0,63 TD6; 
	if  pitchtol[0] == "5":	td = 1.06 * td6		# PTD5 =  0,8 PTD6; 
	if  pitchtol[0] == "6":	td = 1.32 * td6
	if  pitchtol[0] == "7":	td = 1.7 * td6	# PTD7 = 1,25 TD6; 
	if  pitchtol[0] == "8":	td = 2.12 * td6		# PTD8 = 1,6 TD6
	return fd + td

def iso965ExtCrestDev(pitch, cresttol):		# Compute & return crest deviation per ISO965 S.13 formulae
	""" (pitch (float), potchtol (str)) """
	fd = 0.0
	td = 0.0
	if  cresttol[1] == "e":	fd = (50 + 11 * pitch) / 1000	#ese = – (50 + 11 P)  #exceptions for P<=0.45
	if  cresttol[1] == "f":	fd = (30 + 11 * pitch) / 1000	#esf = – (30 + 11 P)  # not applicable for P<=0.3
	if  cresttol[1] == "g":	fd = (15 + 11 * pitch) / 1000	#esg = – (15 + 11 P)
	if  cresttol[1] == "h":	fd = 0						#esh = 0
	td6 = (180 * pitch**(2/3) - 3.15/pitch**(1/2)) / 1000	#Crest Tol. Deviation (number grade) CTD6 (um) = 180 * P ** 2/3 - 3.15/sqrt(P); 
	if  cresttol[0] == "4":	td = 0.63 * td6	# PTD4 = 0,63 TD6; 
	if  cresttol[0] == "6":	td = td6
	if  cresttol[0] == "8":	td = 1.6 * td6		# PTD8 = 1,6 TD6
	return fd + td

def iso965IntCrestDev(pitch, cresttol):		# Compute & return crest deviation per ISO965 S.13 formulae
	""" (pitch (float), potchtol (str)) """
	fd = 0.0
	td = 0.0
	if  cresttol[1] == "G":	fd = (15 + 11 * pitch) / 1000	#esg = – (15 + 11 P)
	if  cresttol[1] == "H":	fd = 0						#esh = 0
	if pitch >= 1.0: 	td6 = 230 * pitch**0.7 / 1000
	else: 			td6 = (433 * pitch - 190 * pitch**1.22) / 1000
	if  cresttol[0] == "4":	td = 0.63 * td6	# PTD4 = 0,63 TD6; 
	if  cresttol[0] == "5":	td = 0.8 * td6		# PTD5 =  0,8 PTD6; 
	if  cresttol[0] == "6":	td = td6
	if  cresttol[0] == "7":	td = 1.25 * td6	# PTD7 = 1,25 TD6; 
	if  cresttol[0] == "8":	td = 1.6 * td6		# PTD8 = 1,6 TD6
	return fd + td

def makeProfileExt681M(minordiameter, pitch, roundroot):	
	""" Generated ISO 68.1M cutter (not adder) profile wire anchord to start point of helix: (majordiameter/2, 0, 0) with 
	trangle base line extended outwards to force intersection with shaft during shaft.cut(thread) operation """
	padding = .25		# extra distance trangle base line is extended outwards past shaft wall, without affecting Dmin (for booleans performance)
						# 	ISO standard profile height above shaft wall.
	profheight = pitch * 5/16 * math.sqrt(3)		# ISO 68M
	v1 = Base.Vector(minordiameter/2 + profheight + padding, 0, padding/math.sqrt(3))	
	v2 = Base.Vector(minordiameter/2, 0, -pitch*5/16)
	v3 = Base.Vector(minordiameter/2, 0, -pitch*9/16)	
	v4 = Base.Vector(minordiameter/2 + profheight + padding, 0, -pitch*7/8 - padding/math.sqrt(3))
	l1 = Part.LineSegment(v1,v2)
	l3 = Part.LineSegment(v3,v4)
	l4 = Part.LineSegment(v4,v1)
	if roundroot:
		v5 = Base.Vector(minordiameter/2 - pitch/8/math.sqrt(3), 0, -pitch*7/16)		# ARc center point for roundroot
		a1 = Part.Arc(v2, v5, v3)
		sprofile = Part.Shape([l1, a1, l3, l4])
	else:
		l2 = Part.LineSegment(v2,v3)
		sprofile = Part.Shape([l1, l2, l3, l4])
	return Part.Wire(sprofile.Edges)
# End method makeProfileExt681M()

def makeProfileInt681M(minordiameter, pitch, roundroot):	
	""" Generated ISO 68.1M cutter profile wire anchord to start point of helix: (majordiameter/2, 0, 0) with 
	trangle base line extended inwords to force intersection with insert wall during insert.cut(thread) operation """
	padding = .25		# extra distance trangle base line is extended outwards past shaft wall, without affecting Dmin (for booleans performance)
						# 	ISO standard profile height above shaft wall.
	profheight = pitch * 5/16 * math.sqrt(3)		# ISO 68M
	v1 = Base.Vector(minordiameter/2 - padding, 0, padding/math.sqrt(3)-pitch/16)	
	v2 = Base.Vector(minordiameter/2 + profheight, 0, -pitch*6/16)
	v3 = Base.Vector(minordiameter/2 + profheight, 0, -pitch*8/16)	
	v4 = Base.Vector(minordiameter/2 - padding, 0, -pitch*7/8 - padding/math.sqrt(3)+pitch/16)
	l1 = Part.LineSegment(v1,v2)
	l3 = Part.LineSegment(v3,v4)
	l4 = Part.LineSegment(v4,v1)
	if roundroot:
		v5 = Base.Vector(minordiameter/2 + profheight + pitch/16/math.sqrt(3), 0, -pitch*7/16)		# ARc center point for roundroot
		a1 = Part.Arc(v2, v5, v3)
		sprofile = Part.Shape([l1, a1, l3, l4])
	else:
		l2 = Part.LineSegment(v2,v3)
		sprofile = Part.Shape([l1, l2, l3, l4])
	return Part.Wire(sprofile.Edges)
# End method makeProfileInt681M()

# GENERIC THREAD BODY CLASSES #############################################################		
class TMThreadShaft:		#######################################################
	""" Threaded Shaft Class draws solid threaded shaft from  parameters given in initprops."""
	norebuild=False		# set by onChanged to cause execute to skip solid rebuild for changes like Placement

	def __init__(self,obj, initprops):		# initprops = [standard(txt), size(txt), dia., pitch, length, taper, clearance, chamfer(bool)
									# 	left-handed(bool), thrddisable(bool), roundroot(bool), pitchtol(txt), cresttol(txt)]
		if not initprops:
			raise RuntimeError("ThreadShaft.execute: Can't instantiate with no specs in initprops.\n")

		#Add properties to doc object
		obj.addProperty("App::PropertyEnumeration", "ThrdStandard", "Thread Parameters", "Thread standard or custom specs")
		obj.addProperty("App::PropertyEnumeration", "StdSize", "Thread Parameters", "Standard size")
		obj.addProperty("App::PropertyLength","Diameter","Thread Parameters","Thread diameter")
		if initprops[0] == "Custom":
			obj.addProperty("App::PropertyLength","Pitch","Thread Parameters","Pitch")
		else:
			obj.addProperty("App::PropertyEnumeration","Pitch","Thread Parameters","Standard pitch selection")
		obj.addProperty("App::PropertyLength","Length","Thread Parameters","Thread body length")
		obj.addProperty("App::PropertyAngle","Taper","Thread Parameters","Thread taper Angle")
		obj.addProperty("App::PropertyLength","Clearance","Thread Parameters","Radial clearance shifts thread profile inwards (ext) or outwards (int) for increasing gap between mating threads")
		obj.addProperty("App::PropertyBool","Chamfer","Thread Parameters","Chamfer base (else bevel base)")
		obj.addProperty("App::PropertyBool","Lefty","Thread Parameters","Left-handed thread")
		obj.addProperty("App::PropertyBool","DisableThrd","Thread Parameters","Disable thread generation")
		obj.addProperty("App::PropertyBool","RoundRoot","Thread Parameters","Rounded profile root")
		obj.addProperty("App::PropertyEnumeration", "TolPitch", "Thread Parameters", "Pitch Tolerance")
		obj.addProperty("App::PropertyEnumeration", "TolCrest", "Thread Parameters", "Crest Tolerance")
		obj.addProperty("App::PropertyBool","IsPotato","Thread Parameters","Thread body is potato")
		obj.setEditorMode("IsPotato",2)			# Hidden prop to indicate geometry failure for testing

		# Load initprops from dialog into object props
		obj.ThrdStandard = tuple(SUPPORTEDSTANDARDS)
		if initprops[0] in list(SUPPORTEDSTANDARDS): obj.ThrdStandard = initprops[0]

		obj.StdSize = tuple(ISO261PDTABLE)
		obj.StdSize = initprops[1]
		if initprops[0] == "Custom": obj.setEditorMode("StdSize", 2)

		obj.Diameter = initprops[2]
		if initprops[0] != "Custom": obj.setEditorMode("Diameter", 1)

		if initprops[0] == "Custom":
			obj.Pitch = initprops[3]
		else:
			obj.Pitch = ISO261PDTABLE[obj.StdSize]
			obj.Pitch = str(initprops[3])

		obj.Length = initprops[4]

		obj.Taper = initprops[5]
		if initprops[0] != "Custom": obj.setEditorMode("Taper", 1)

		obj.Clearance = initprops[6]
		obj.Chamfer = initprops[7]
		obj.Lefty = initprops[8]
		obj.DisableThrd = initprops[9]
		obj.RoundRoot = initprops[10]
		
		obj.TolPitch = tuple(ISO965EXTPITCHTOL)
		obj.TolPitch = initprops[11]
		if initprops[0] == "Custom": obj.setEditorMode("TolPitch", 2)

		obj.TolCrest = tuple(ISO965EXTCRESTTOL)
		obj.TolCrest = initprops[12]
		if initprops[0] == "Custom": obj.setEditorMode("TolCrest", 2)

		# Make attachable
		if int(FreeCAD.Version()[1]) >= 19:
			obj.addExtension('Part::AttachExtensionPython')
		else:
			obj.addExtension('Part::AttachExtensionPython', obj)

		self.Type = EXTOBJECTNAME
		obj.Proxy = self
	# end __init__

	def execute(self,fp):
		"""Generates external threaded shaft refined solid. """
		fp.IsPotato=False
		if self.norebuild:		# only true when last onChange call was for placement or other listed prop
			self.norebuild = False
			return

		# Get thread properties
		majordiameter = float(fp.Diameter)		# for ISO this is Dmaj = Dnom-CrestDev
		pitch = float(fp.Pitch)
		length = float(fp.Length)
		taper = float(fp.Taper)
		clearance = float(fp.Clearance)
		chamfer = fp.Chamfer
		left = fp.Lefty
		tdisable = fp.DisableThrd
		roundroot = fp.RoundRoot
		if fp.ThrdStandard == "Custom":
			crestdev = 0.0
			pitchdev = 0.0
		else:
			crestdev = iso965ExtCrestDev(pitch, fp.TolCrest)
			pitchdev = iso965ExtPitchDev(majordiameter + crestdev, pitch, fp.TolPitch)

		# Derived/internal vars
		majordiameter = majordiameter - clearance	# Apply clearance to controlling diameter
		profheight = pitch * 5/16 * math.sqrt(3)		# pre-tolerance truncation
		diameter = majordiameter + crestdev - 2*profheight - pitchdev		# Dmin: ISO minor d with pitch tolerance applied
		tdiameter = majordiameter - length * math.sin(taper*math.pi/180)		# top diamater (taper applied)
		print(fp.Name + " Dmin = " + str(diameter))

		# BUILD SHAFT
		if majordiameter == tdiameter:
			shaft = Part.makeCylinder(majordiameter/2, length)
		else:
			shaft = Part.makeCone(majordiameter/2, tdiameter/2, length)
		shaft.rotate(Base.Vector(0,0,0), Base.Vector(0,0,1), 107)		#Fixes lots of problems doing booleans after thread fuse!

		if not tdisable:			# Top L. corner of profile coincident with bottom R corner of shaft
			# BUILD PROFILE
			wprofile = makeProfileExt681M(diameter, pitch, roundroot)

			# BUILD HELIX
			helixpad = .01				# Extend helix above and below shaft by this amount to clear lines for flaky boolean ops
			wprofile.translate(Base.Vector(0,0,-helixpad))		# Start thread sweep below shaft end for boolean ops
			helix = Part.makeLongHelix(pitch, length+pitch+helixpad*2, majordiameter/2, -taper/2, left)
			helix.translate(Base.Vector(0,0,-helixpad))

			# BUILD THREAD
			thread = Part.BRepOffsetAPI.MakePipeShell(helix)
			thread.setFrenetMode(True)  # Sets a Frenet (true) or a CorrectedFrenet(false) trihedron to perform the sweeping.  False = corkscrew.
			thread.setTransitionMode(1)  # 0=Transformed, *1=right corner transition, 2=Round corner
			thread.add(wprofile, False)	# WithContact = connect to helix.  WithCorrection = orthogonal to helix tangent.
			if not thread.isReady():		
				fp.Shape = shaft
				fp.IsPotato = True
				raise RuntimeError("ThreadShaft.execute: BRepOffsetAPI not ready error sweeping thread profile.\n")
			thread.build()
			if not thread.makeSolid(): 
				fp.Shape = shaft
				fp.IsPotato = True
				raise RuntimeError("ThreadShaft.execute: BRepOffsetAPI faled building swept thread solid.\n")
			sthread = thread.shape()

			# SHAFT.CUT(THREAD)
			threadbody = shaft.cut(sthread)
			if threadbody.childShapes()==[]:
				fp.Shape = shaft
				fp.IsPotato = True
				raise RuntimeError("ThreadShaft.execute: Failed while fusing thread to shaft.  Try changing Diameter or Pitch.\n")

		else:	# TDISABLE=True; Make fast cosmetic thread.  shaft=shaft solid
			threadbody=shaft

		# TRIM THREAD BODY TOP/BOTTOM
		# Best results obtained using padding (not tolerance), and ensuring intersection points aren't too close
		threadbody.rotate(Base.Vector(0,0,0), Base.Vector(0,0,1), 37)

		# BEVEL TOP with THREAD.sub(Part.Face.revolve())
		tmindiameter = tdiameter + crestdev - 2*profheight - pitchdev		#tdiameter, tmindiameter = top diameters after any taper
		v1 = Base.Vector(tmindiameter/2-0.1, 0, length+0.1)
		v2 = Base.Vector(tdiameter/2+0.1, 0, length+0.1)
		v3 = Base.Vector(tdiameter/2+0.1, 0, length - tdiameter/2 + tmindiameter/2 - 0.2)
		l1 = Part.LineSegment(v1,v2)
		l2 = Part.LineSegment(v2,v3)
		l3 = Part.LineSegment(v3,v1)
		topcutter = Part.Shape([l1, l2, l3])
		topcutter = Part.Wire(topcutter.Edges)
		topcutter = Part.Face(topcutter)
		topcutter = topcutter.revolve(Base.Vector(0,0,1), Base.Vector(0,0,360))
		topcutter.rotate(Base.Vector(0,0,0), Base.Vector(0,0,1), 207)
		threadbody = threadbody.cut(topcutter)	

		if chamfer:
			# FUSE BASE TO SHAFT
			pad = pitch/13.856 + 1e-2	#0.15			#shifts upper, inner coner up and in to prevent fuse failures on rounded root
			v1 = Base.Vector(0, 0, 0)		# Profile 45 deg. trangle embedded in shaft deeply enough to fill round root 
			v10 = Base.Vector(0, 0, profheight + pad)
			v2 = Base.Vector(diameter/2-pad, 0, profheight + pad)			# (shifted by pitch/4)
			v3 = Base.Vector(majordiameter/2, 0, 0)
			l1 = Part.LineSegment(v1,v10)
			l10 = Part.LineSegment(v10, v2)
			l2 = Part.LineSegment(v2,v3)
			l3 = Part.LineSegment(v3,v1)
			base = Part.Shape([l1, l10, l2, l3])
			base = Part.Wire(base.Edges)
			base = Part.Face(base)
			base = base.revolve(Base.Vector(0,0,1), Base.Vector(0,0,360))
			base.rotate(Base.Vector(0,0,0), Base.Vector(0,0,1), -107)
			threadbody.translate(Base.Vector(0,0,2e-3))		# just enough to avoid a "splitter line" on bottom, and avoid fuse errors.
			threadbody = threadbody.fuse(base)
			if threadbody.childShapes()==[]:
				fp.Shape = shaft
				fp.IsPotato = True
				raise RuntimeError("ThreadShaft.execute: Failed while fusing base to thread.  Try changing Diameter or Pitch.\n")
#			threadbody = threadbody.removeSplitter()	# removeSplitter increases render time 800% on 100mm thread but enables PD fuse
		else:	# Bevel Base
			# BEVEL BOTTOM with THREAD.sub(Part.Face.revolve())
			v1 = Base.Vector(diameter/2-0.1, 0, -0.1)
			v2 = Base.Vector(majordiameter/2+0.1, 0, -0.1)
			v3 = Base.Vector(majordiameter/2+0.1, 0, majordiameter/2 - diameter/2 + 0.2)
			l1 = Part.LineSegment(v1,v2)
			l2 = Part.LineSegment(v2,v3)
			l3 = Part.LineSegment(v3,v1)
			cutter = Part.Shape([l1, l2, l3])
			cutter = Part.Wire(cutter.Edges)
			cutter = Part.Face(cutter)
			cutter = cutter.revolve(Base.Vector(0,0,0), Base.Vector(0,0,1), 360)
			cutter.rotate(Base.Vector(0,0,0), Base.Vector(0,0,1), -107)
			threadbody = threadbody.cut(cutter)
		
		fp.Shape = threadbody
		fp.positionBySupport()
		print(fp.Name + " Dmaj = " + str(fp.Shape.BoundBox.XLength))
	#end method execute: threadbody created, fused with existing solid if any, stored into document fp object

	def onChanged(self, fp, prop):
		"""If prop in coded list, set flag to prevent execute from rebuilding the thread solid"""
		#To prevent recomputation on transform.
#		print(str(prop))
		if prop in ["Placement"]:
			self.norebuild=True
		else:
			self.norebuild=False
# end class TMThreadShaft:

class TMThreadInsert:		#######################################################
	""" Threaded Insert Class draws solid threaded insert from  parameters given in initprops."""
	norebuild=False		# set by onChanged to cause execute to skip solid rebuild for changes like Placement

	def __init__(self,obj, initprops):		# initprops = [standard(txt), size(txt), dia., pitch, length, taper, clearance, chamfer(bool)
									# 	left-handed(bool), thrddisable(bool), roundroot(bool), pitchtol(txt), cresttol(txt)]
		if not initprops:
			raise RuntimeError("ThreadInsert.execute: Can't instantiate with no specs in initprops.\n")

		#Add properties to doc object
		obj.addProperty("App::PropertyEnumeration", "ThrdStandard", "Thread Parameters", "Thread standard or custom specs")
		obj.addProperty("App::PropertyEnumeration", "StdSize", "Thread Parameters", "Standard size")
		obj.addProperty("App::PropertyLength","Diameter","Thread Parameters","Thread diameter")
		if initprops[0] == "Custom":
			obj.addProperty("App::PropertyLength","Pitch","Thread Parameters","Pitch")
		else:
			obj.addProperty("App::PropertyEnumeration","Pitch","Thread Parameters","Standard pitch selection")
		obj.addProperty("App::PropertyLength","Length","Thread Parameters","Thread body length")
		obj.addProperty("App::PropertyAngle","Taper","Thread Parameters","Thread taper Angle")
		obj.addProperty("App::PropertyLength","Clearance","Thread Parameters","Radial clearance shifts thread profile inwards (ext) or outwards (int) for increasing gap between mating threads")
		obj.addProperty("App::PropertyBool","Chamfer","Thread Parameters","Chamfer base (else bevel base)")
		obj.addProperty("App::PropertyBool","Lefty","Thread Parameters","Left-handed thread")
		obj.addProperty("App::PropertyBool","DisableThrd","Thread Parameters","Disable thread generation")
		obj.addProperty("App::PropertyBool","RoundRoot","Thread Parameters","Rounded profile root")
		obj.addProperty("App::PropertyEnumeration", "TolPitch", "Thread Parameters", "Pitch Tolerance")
		obj.addProperty("App::PropertyEnumeration", "TolCrest", "Thread Parameters", "Crest Tolerance")
		obj.addProperty("App::PropertyBool","IsPotato","Thread Parameters","Thread body is potato")
		obj.setEditorMode("IsPotato",2)			# Hidden prop to indicate geometry failure for testing

		# Load initprops from dialog into object props
		obj.ThrdStandard = tuple(SUPPORTEDSTANDARDS)
		if initprops[0] in list(SUPPORTEDSTANDARDS): obj.ThrdStandard = initprops[0]

		obj.StdSize = tuple(ISO261PDTABLE)
		obj.StdSize = initprops[1]
		if initprops[0] == "Custom": obj.setEditorMode("StdSize", 2)

		obj.Diameter = initprops[2]
		if initprops[0] != "Custom": obj.setEditorMode("Diameter", 1)

		if initprops[0] == "Custom":
			obj.Pitch = initprops[3]
		else:
			obj.Pitch = ISO261PDTABLE[obj.StdSize]
			obj.Pitch = str(initprops[3])

		obj.Length = initprops[4]

		obj.Taper = initprops[5]
		if initprops[0] != "Custom": obj.setEditorMode("Taper", 1)

		obj.Clearance = initprops[6]
		obj.Chamfer = initprops[7]
		obj.Lefty = initprops[8]
		obj.DisableThrd = initprops[9]
		obj.RoundRoot = initprops[10]
		
		obj.TolPitch = tuple(ISO965INTPITCHTOL)
		obj.TolPitch = initprops[11]
		if initprops[0] == "Custom": obj.setEditorMode("TolPitch", 2)

		obj.TolCrest = tuple(ISO965INTCRESTTOL)
		obj.TolCrest = initprops[12]
		if initprops[0] == "Custom": obj.setEditorMode("TolCrest", 2)

		# Make attachable
		if int(FreeCAD.Version()[1]) >= 19:
			obj.addExtension('Part::AttachExtensionPython')
		else:
			obj.addExtension('Part::AttachExtensionPython', obj)

		self.Type = INTOBJECTNAME
		obj.Proxy = self
	# end __init__

	def execute(self,fp):
		"""Generates internal threaded shaft refined solid. """
		fp.IsPotato=False
		if self.norebuild:		# only true when last onChange call was for placement or other listed prop
			self.norebuild = False
			return

		# Get thread properties
		majordiameter = float(fp.Diameter)		# for ISO this is Dmaj = Dnom-CrestDev
		pitch = float(fp.Pitch)
		length = float(fp.Length)
		taper = float(fp.Taper)
		clearance = float(fp.Clearance)
		chamfer = fp.Chamfer
		left = fp.Lefty
		tdisable = fp.DisableThrd
		roundroot = fp.RoundRoot
		if fp.ThrdStandard == "Custom":
			crestdev = 0.0
			pitchdev = 0.0
		else:
			crestdev = iso965IntCrestDev(pitch, fp.TolCrest)
			pitchdev = iso965IntPitchDev(majordiameter + crestdev, pitch, fp.TolPitch)

		# Derived/internal vars
		majordiameter = majordiameter + clearance	# Apply clearance to controlling diameter
		profheight = pitch * 5/16 * math.sqrt(3)		# pre-tolerance truncation
		diameter = majordiameter - crestdev - 2*profheight + pitchdev		# Dmin: ISO minor d with pitch tolerance applied
		tdiameter = majordiameter + length * math.sin(taper*math.pi/180)		# top diamater (taper applied)
		tmindiameter = tdiameter - crestdev - 2*profheight + pitchdev		#tdiameter, tmindiameter = top diameters after any taper
		print(fp.Name + " Dmin = " + str(diameter))

		# BUILD INSERT
		if majordiameter == tdiameter:
			shaft = Part.makeCylinder(diameter/2, length)
		else:
			shaft = Part.makeCone(diameter/2, tmindiameter/2, length)
		insert = Part.makeCylinder(tdiameter/2+0.5, length)
		insert = insert.cut(shaft)
		insert.rotate(Base.Vector(0,0,0), Base.Vector(0,0,1), 107)		#Fixes lots of problems doing booleans after thread fuse!

		if not tdisable:			# Top L. corner of profile coincident with bottom R corner of shaft
			# BUILD PROFILE
			wprofile = makeProfileInt681M(diameter, pitch, roundroot)

			# BUILD HELIX
			helixpad = .01				# Extend helix above and below shaft by this amount to clear lines for flaky boolean ops
			wprofile.translate(Base.Vector(0,0,-helixpad))		# Start thread sweep below shaft end for boolean ops
			helix = Part.makeLongHelix(pitch, length+pitch+helixpad*2, majordiameter/2, taper/2, left)
			helix.translate(Base.Vector(0,0,-helixpad))

			# BUILD THREAD
			thread = Part.BRepOffsetAPI.MakePipeShell(helix)
			thread.setFrenetMode(True)  # Sets a Frenet (true) or a CorrectedFrenet(false) trihedron to perform the sweeping.  False = corkscrew.
			thread.setTransitionMode(1)  # 0=Transformed, *1=right corner transition, 2=Round corner
			thread.add(wprofile, False)	# WithContact = connect to helix.  WithCorrection = orthogonal to helix tangent.
			if not thread.isReady():		
				fp.Shape = shaft
				fp.IsPotato = True
				raise RuntimeError("ThreadInsert.execute: BRepOffsetAPI not ready error sweeping thread profile.\n")
			thread.build()
			if not thread.makeSolid(): 
				fp.Shape = shaft
				fp.IsPotato = True
				raise RuntimeError("ThreadInsert.execute: BRepOffsetAPI faled building swept thread solid.\n")
			sthread = thread.shape()

			# INSERT.CUT(THREAD)
			threadbody = insert.cut(sthread)
			if threadbody.childShapes()==[]:
				fp.Shape = shaft
				fp.IsPotato = True
				raise RuntimeError("ThreadInsert.execute: Failed while fusing thread to insert.  Try changing Diameter or Pitch.\n")

		else:	# TDISABLE=True; Make fast cosmetic thread.  shaft=shaft solid
			threadbody=insert

		# TRIM THREAD BODY TOP/BOTTOM
		# Best results obtained using padding (not tolerance), and ensuring intersection points aren't too close
		threadbody.rotate(Base.Vector(0,0,0), Base.Vector(0,0,1), 37)

		# BEVEL TOP with THREAD.sub(Part.Face.revolve())
		v1 = Base.Vector(tdiameter/2+0.1, 0, length+0.1)
		v2 = Base.Vector(tmindiameter/2-0.1, 0, length+0.1)
		v3 = Base.Vector(tmindiameter/2-0.1, 0, length - tdiameter/2 + tmindiameter/2 - 0.2)
		l1 = Part.LineSegment(v1,v2)
		l2 = Part.LineSegment(v2,v3)
		l3 = Part.LineSegment(v3,v1)
		topcutter = Part.Shape([l1, l2, l3])
		topcutter = Part.Wire(topcutter.Edges)
		topcutter = Part.Face(topcutter)
		topcutter = topcutter.revolve(Base.Vector(0,0,1), Base.Vector(0,0,360))
		topcutter.rotate(Base.Vector(0,0,0), Base.Vector(0,0,1), 207)
		threadbody = threadbody.cut(topcutter)	

		if chamfer:
			# FUSE BASE
			pad = pitch/27.712 + 0.01			# Shifts top corner of bevel triangle up and in (to insert) to clear round root and reduce fuse failures
			v1 = Base.Vector(tdiameter/2 + 0.5, 0, 0)		# Profile 45 deg. trangle embedded in shaft deeply enough to fill round root 
			v2 = Base.Vector(diameter/2, 0, 0)	
			v3 = Base.Vector(majordiameter/2+pad, 0, profheight + pad)
			l1 = Part.LineSegment(v1,v2)
			l2 = Part.LineSegment(v2,v3)
			l3 = Part.LineSegment(v3,v1)
			base = Part.Shape([l1,  l2, l3])
			base = Part.Wire(base.Edges)       
			base = Part.Face(base)
			base = base.revolve(Base.Vector(0,0,1), Base.Vector(0,0,360))
			base.rotate(Base.Vector(0,0,0), Base.Vector(0,0,1), -107)
			vpad = 7e-4 + pitch*3e-4 + majordiameter*5e-5	#<<< Passes 100% test cases on chamfer base & round root
			threadbody.translate(Base.Vector(0,0,vpad))
			threadbody = threadbody.fuse(base)
			if threadbody.childShapes()==[]:
				fp.Shape = shaft
				fp.IsPotato = True
				raise RuntimeError("ThreadInsert.execute: Failed while fusing base to insert.  Try changing Diameter or Pitch.\n")
#			threadbody = threadbody.removeSplitter()	# removeSplitter increases render time 800% on 100mm thread but enables PD fuse
		else:	# Bevel Base
 			# BEVEL BOTTOM with THREAD.sub(Part.Face.revolve())
			v1 = Base.Vector(majordiameter/2+0.1, 0, -0.1)
			v2 = Base.Vector(diameter/2-0.1, 0, -0.1)
			v3 = Base.Vector(diameter/2-0.1, 0, majordiameter/2 - diameter/2 + 0.2)
			l1 = Part.LineSegment(v1,v2)
			l2 = Part.LineSegment(v2,v3)
			l3 = Part.LineSegment(v3,v1)
			cutter = Part.Shape([l1, l2, l3])
			cutter = Part.Wire(cutter.Edges)
			cutter = Part.Face(cutter)
			cutter = cutter.revolve(Base.Vector(0,0,0), Base.Vector(0,0,1), 360)
			cutter.rotate(Base.Vector(0,0,0), Base.Vector(0,0,1), -107)
			threadbody = threadbody.cut(cutter)
		
		fp.Shape = threadbody
		fp.positionBySupport()
		print(fp.Name + " Dmaj = " + str(majordiameter))
	#end method execute: threadbody created, fused with existing solid if any, stored into document fp object

	def onChanged(self, fp, prop):
		"""If prop in coded list, set flag to prevent execute from rebuilding the thread solid"""
		#To prevent recomputation on transform.
#		print(str(prop))
		if prop in ["Placement"]:
			self.norebuild=True
		else:
			self.norebuild=False

# end class TMThreadInsert:


class TMThreadVP:		#######################################################

	OriginalShapeColor = ()		#Store shape color to restore after rendering disabled threads
	OriginalShapeTransparency = 0.0
	ObjectType = ""

	def __init__(self, obj):
		'''Set this object to the proxy object of the actual view provider'''
		self.ObjectType = obj.Object.Proxy.Type		# So getIcon can choose which icon
		obj.Proxy = self

	def attach(self, vobj):
		self.vobj = vobj

	def updateData(self, fp, prop):
		''' Properties validation for updates to Data panel in combo view. '''
		self.ObjectType = fp.Proxy.Type		# So getIcon can choose which icon
		# if thrdstandard != Custom: size, pitch, pitchtol and cresttol recompute maj. diameter
		#CAUTION: don't set props to value which fails validation!
		# Custom dimension validation also applied to standardized inputs
		if prop in ["Diameter", "Pitch", "Length", "Taper"]: 
			# Validation for D, P, and L based on large-pitch-small-diameter combinations which break the boolean ops in ThreadShaft.execute()
			#d now = od.  id = od - p*1.1.  P < (od - 1.1*p - c)/1.1; < (od - c)/1.1 - p; P < (od - c)/2.2; P*2.2 + c < OD
			if prop == "Diameter" and float(fp.Diameter)-float(fp.Clearance) < float(fp.Pitch)  * 2.3: 
				FreeCAD.Console.PrintWarning("TM:  Outer Diameter (less Clearance and Taper) cannot be < (Pitch  * 2.3)\n")
				fp.Diameter = float(fp.Pitch) * 2.3 + float(fp.Clearance)
			#d now = od.  id = od - p*1.1.  P < (od - 1.1*p - c)/1.1; < (od - c)/1.1 - p; P < (od - c)/2.2
			if prop == "Pitch" and fp.ThrdStandard == "Custom" and float(fp.Pitch) > float(fp.Diameter)/2.2 or float(fp.Pitch) < 0.1:
				FreeCAD.Console.PrintWarning("TM:  Pitch cannot be > (Diameter / 2.3) and cannot be < 0.1.\n")
				if float(fp.Pitch) < 0.1:	fp.Pitch = 0.1
				if float(fp.Pitch) > float(fp.Diameter)/2.2:	fp.Pitch = float(fp.Diameter)/2.3
			if prop == "Length" and float(fp.Length) < float(fp.Pitch):
				FreeCAD.Console.PrintWarning("TM:  Length cannot be < Pitch\n")
				fp.Length = fp.Pitch
			if prop in ["Diameter", "Pitch", "Clearance"] and (float(fp.Diameter)-float(fp.Clearance)) < 3.5 and float(fp.Pitch) > 1.0:
				FreeCAD.Console.PrintWarning("TM: Computation may fail if Diameter (less Clearance & Taper) < 3.5 while Pitch > 1.0.\n")
			if prop == "Taper" and abs(float(fp.Taper)) > 5.0:
				FreeCAD.Console.PrintWarning("TM: Computation may fail if |Taper| > 5.0.\n")

		if prop == "DisableThrd":			# toggle shape color for thread disable state
			if fp.DisableThrd:
				self.OriginalShapeColor = fp.ViewObject.ShapeColor
				self.OriginalShapeTransparency = fp.ViewObject.Transparency
				fp.ViewObject.ShapeColor =(0.4, 0.4, 1.0)
				fp.ViewObject.Transparency = 50
			elif self.OriginalShapeColor != ():
				fp.ViewObject.ShapeColor = self.OriginalShapeColor
				fp.ViewObject.Transparency = self.OriginalShapeTransparency

		if prop == "ThrdStandard":		# change prop state for sz, pitch, dia, taper
			if fp.ThrdStandard == "Custom":		# Disable sz, p(popup), ct, pt; enable d, p(textbox), t.
				fp.setEditorMode("StdSize", 2)
				oldpitch = fp.Pitch
				fp.removeProperty("Pitch")
				fp.addProperty("App::PropertyLength","Pitch","Thread Parameters","Pitch")
				fp.Pitch = oldpitch
				fp.setEditorMode("TolPitch", 2)
				fp.setEditorMode("TolCrest", 2)
				fp.setEditorMode("Diameter", 0)
				fp.setEditorMode("Taper", 0)
			else:			# Not Custom
				fp.setEditorMode("StdSize", 0)		# Size enumeration
				if fp.StdSize not in list(ISO261PDTABLE): fp.StdSize = "M10"
				oldpitch = fp.Pitch						# Pitch
				fp.removeProperty("Pitch")
				fp.addProperty("App::PropertyEnumeration","Pitch","Thread Parameters","Standard pitch selection")
				fp.Pitch = ISO261PDTABLE[fp.StdSize]
				if str(oldpitch) in ISO261PDTABLE[fp.StdSize]: fp.Pitch = oldpitch
				fp.setEditorMode("TolPitch", 0)
				fp.setEditorMode("TolCrest", 0)
				fp.setEditorMode("Diameter", 1)
				fp.setEditorMode("Taper", 1)
				fp.Taper = SUPPORTEDSTANDARDS[fp.ThrdStandard]		# Taper

		if prop == "StdSize" and fp.ThrdStandard != "Custom":		# update p(popup2)
			oldpitch = fp.Pitch
			fp.removeProperty("Pitch")
			fp.addProperty("App::PropertyEnumeration","Pitch","Thread Parameters","Standard pitch selection")
			fp.Pitch = ISO261PDTABLE[fp.StdSize]
			if str(oldpitch) in ISO261PDTABLE[fp.StdSize]: fp.Pitch = oldpitch

		if prop in ["StdSize", "Pitch", "TolCrest"] and fp.ThrdStandard != "Custom":		# Update Major Dia.
			if self.ObjectType == EXTOBJECTNAME:
				fp.Diameter = float(fp.StdSize[1:]) - iso965ExtCrestDev(float(fp.Pitch), fp.TolCrest)
			else:
				fp.Diameter = float(fp.StdSize[1:]) + iso965IntCrestDev(float(fp.Pitch), fp.TolCrest)

		if prop in ["StdSize", "Pitch", "TolCrest", "TolPitch"] and fp.ThrdStandard != "Custom":		# Override invalid Tol
			if self.ObjectType == EXTOBJECTNAME:
				if iso965ExtPitchDev(float(fp.StdSize[1:]), float(fp.Pitch), fp.TolPitch) > iso965ExtCrestDev(float(fp.Pitch), fp.TolCrest):
					FreeCAD.Console.PrintWarning("TM:  " + fp.TolPitch + " Ptich Deviation exceeded " + fp.TolCrest + " Crest Deviation.  Pitch Tolerance was set to 3h.\n")
					fp.TolPitch = "3h"
			else: 
				if iso965IntPitchDev(float(fp.StdSize[1:]), float(fp.Pitch), fp.TolPitch) > iso965IntCrestDev(float(fp.Pitch), fp.TolCrest):
					FreeCAD.Console.PrintWarning("TM:  " + fp.TolPitch + " Ptich Deviation exceeded " + fp.TolCrest + " Crest Deviation.  Pitch Tolerance was set to 4H.\n")
					fp.TolPitch = "4H"

		if prop in ["ThrdStandard", "StdSize", "Diameter", "Pitch", "Length", "TolPitch", "TolCrest", "Lefty"]: 
			if fp.ThrdStandard == "Custom":
				self.label = self.ObjectType + " " + str(round(float(fp.Diameter),3)) + " x " + str(round(float(fp.Pitch),3)) + " - " + str(round(float(fp.Length),3)) + " "
			else:
				self.label = self.ObjectType + " " + fp.StdSize + " x " + str(round(float(fp.Pitch),3)) + " - " + fp.TolPitch + fp.TolCrest + " - " + str(round(float(fp.Length),3)) + " "
			if fp.Lefty:	self.label = self.label + "- L "
			fp.Label = self.label
	# end VP updateData

	def getDisplayModes(self,obj):
		'''Return a list of display modes.'''
		modes=[]
		modes.append("Flat Lines")
		modes.append("Shaded")
		modes.append("Wireframe")
		return modes

	def getDefaultDisplayMode(self):
		'''Return the name of the default display mode. It must be defined in getDisplayModes.  Not called!?'''
		return "Flat Lines"

	def setDisplayMode(self,mode):
		'''Map the display mode defined in attach with those defined in getDisplayModes.\
				Since they have the same names nothing needs to be done. This method is optional'''
		return mode

	def onChanged(self, vp, prop):
		'''Here we can do something when a single VP property (ie- Proxy) got changed'''
		pass

	def getIcon(self):
		'''Return the icon in XPM format which will appear in the tree view. This method is\
				optional and if not defined a default icon is shown.'''
		param = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Macro")# macro path in FreeCAD preferences
		path = param.GetString("MacroPath","") + "/ThreadMaker/"
		path = path.replace("\\","/")
		if self.ObjectType == EXTOBJECTNAME:
			return path + "TMIconShaft.png"
		if self.ObjectType == INTOBJECTNAME:
			return path + "TMIconInsert.png"
		else: 
			return

	def __getstate__(self):
		'''When saving the document this object gets stored using Python's json module.\
				Since we have some un-serializable parts here -- the Coin stuff -- we must define this method\
				to return a tuple of all serializable objects or None.'''
		return None

	def __setstate__(self,state):
		'''When restoring the serialized object from document we have the chance to set some internals here.\
				Since no data were serialized nothing needs to be done here.'''
		return None
# end class PDThreadVP

class TMDialog(QtGui.QDialog):
	"""Opens dialog window for ThreadMaker object parameters. Pre-loads values from MRU if present.  Results returned =
	[thrdstandard, stdsize, diameter, pitch, length, taper, clearance, chamfer(bool), left-handed(bool), thrddisable(bool), 
	roundroot(bool), pitchtol, cresttol]"""
	def __init__(self, internal):		
		""" internal(bool) = true if internal thread object, else external thread """
		super(TMDialog, self).__init__()
		self.initUI(internal)

	def initUI(self, internal):			
		""" internal(bool) = true if internal thread object, else external thread """
		# Define box & widgets; load MRU values if present.  Pitch may be popup list (non-custom) or textInput (custom) 
		# but widgets for both are defined here
		self.result = None
		self.internal = internal
		param_grp=FreeCAD.ParamGet(MRUPATH)
		self.ts = param_grp.GetString("thrdstandard")
		self.sz = param_grp.GetString("stdsize")
		self.d = param_grp.GetFloat("diameter")
		self.p = param_grp.GetFloat("pitch")
		self.l = param_grp.GetFloat("length")
		self.t = param_grp.GetFloat("taper")
		self.c = param_grp.GetFloat("clearance")
		self.cb = param_grp.GetBool("chamfer")
		self.lh = param_grp.GetBool("lefty")
		self.td = param_grp.GetBool("tdisable")
		self.rr = param_grp.GetBool("roundroot")
		self.pt = param_grp.GetString("pitchtol")
		self.ct = param_grp.GetString("cresttol")

		if internal: 		# internal thread tol selection lists & crest deviation
			self.ISO965PITCHTOL = ISO965INTPITCHTOL
			self.ISO965CRESTTOL = ISO965INTCRESTTOL
		else:	 		# external thread tol selection lists & crest deviation
			self.ISO965PITCHTOL = ISO965EXTPITCHTOL
			self.ISO965CRESTTOL = ISO965EXTCRESTTOL



		# thrdstandard reconfigures pitch from textInput to popup, size, diameter, taper
		# size reloads pitch popup list
		# if thrdstandard != Custom: size, pitch, pitchtol and cresttol recompute maj. diameter
		# Build dialog window and stuff MRU values in
		line = 15			# first line of text/widgets on dialog box
		lineinc = 25		# added for each new line

		# define window		xLoc,yLoc,xDim,yDim
		self.setGeometry(250, 250, 270, 355)
		self.setWindowTitle("Thread Parameters")
		self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
		self.setMouseTracking(True)

		# Standard selection box- validate mru, set custom if undef. standard
		self.label0 = QtGui.QLabel("Thread Standard", self)
		self.label0.move(20, line)
		# if ts then textInput = listbox with ts prepouplated
		self.popup1 = QtGui.QComboBox(self)
		self.popup1.setStyleSheet("background : #ffffff")
		self.popup1.addItems(list(SUPPORTEDSTANDARDS))
		if self.ts not in list(SUPPORTEDSTANDARDS): self.ts = "Custom"
		self.popup1.setCurrentIndex(list(SUPPORTEDSTANDARDS).index(self.ts))
		self.popup1.activated[str].connect(self.onPopup1)
		self.popup1.setFixedWidth(125)
		self.popup1.move(120, line)

		# Size selection box- if Custom: clear() else: populate SIZES list and set MRU value
		line+=lineinc
		self.label5 = QtGui.QLabel("Standard Size", self)
		self.label5.move(20, line)
		# if sz then prepouplate.  if Custom then clear else 
		self.popup0 = QtGui.QComboBox(self)
		self.popup0.setStyleSheet("background : #ffffff")
		self.popup0.addItems(list(ISO261PDTABLE))
		if self.ts == "Custom":
			self.popup0.setDisabled(True)
			self.label5.setStyleSheet("color : #b0b0b0")
		else:	# ISO261 Standard
			if self.sz not in list(ISO261PDTABLE): self.sz = list(ISO261PDTABLE)[19]
			self.popup0.setCurrentIndex(list(ISO261PDTABLE).index(self.sz))
			self.label5.setStyleSheet("color :")
		self.popup0.activated[str].connect(self.onPopup0)
		self.popup0.setFixedWidth(65)
		self.popup0.move(120, line)
		if self.ts != "Custom": self.popup0.setFocus()

		# Pitch Tol. selection box
		line+=lineinc
		self.label8 = QtGui.QLabel("Pitch Tol.", self)
		self.label8.move(20, line)
		self.popup3 = QtGui.QComboBox(self)
		self.popup3.setStyleSheet("background : #ffffff")
		self.popup3.addItems(self.ISO965PITCHTOL)
		if self.ts == "Custom":
			self.label8.setStyleSheet("color : #b0b0b0")
			self.popup3.setDisabled(True)
		else:	# populate pitch tolerances
			if self.pt not in self.ISO965PITCHTOL: 
				if self.internal: self.pt = "6H"
				else: self.pt = "6g"
			self.popup3.setCurrentIndex(self.ISO965PITCHTOL.index(self.pt))
			self.label8.setStyleSheet("color :")
		self.popup3.activated[str].connect(self.onPopup3)
		self.popup3.setFixedWidth(50)
		self.popup3.move(80, line)

		# Crest Tol. selection box
		self.label9 = QtGui.QLabel("Crest Tol.", self)
		self.label9.move(140, line)
		# if sz then prepouplate.  if Custom then clear else 
		self.popup4 = QtGui.QComboBox(self)
		self.popup4.setStyleSheet("background : #ffffff")
		self.popup4.addItems(self.ISO965CRESTTOL)
		if self.ts == "Custom":
			self.label9.setStyleSheet("color : #b0b0b0")
			self.popup4.setDisabled(True)
		else:	# populate pitch tolerances
			if self.ct not in self.ISO965CRESTTOL:
				if self.internal: self.ct = "6H"
				else: self.ct = "6g"
			self.popup4.setCurrentIndex(self.ISO965CRESTTOL.index(self.ct))
			self.label9.setStyleSheet("color :")
		self.popup4.activated[str].connect(self.onPopup4)
		self.popup4.setFixedWidth(50)
		self.popup4.move(200, line)

		# Diameter input box
		line+=lineinc
		self.label1 = QtGui.QLabel("Major Diameter", self)
		self.label1.move(20, line)
		# if ts then textInput = listbox with sz prepouplated
		self.textInput = QtGui.QLineEdit(self)
		self.textInput.setFixedWidth(50)
		self.textInput.move(120, line)
		self.textInput.setText(str(round(self.d,3)))
		if self.ts == "Custom":
			self.textInput.setFocus()
		else:
			self.textInput.setDisabled(True)

		# Pitch: if Custom: input box else: popup list.  Create both widgets, but show only one
		line+=lineinc
		self.label2 = QtGui.QLabel("Pitch", self)
		self.label2.move(20, line)
		self.textInput1 = QtGui.QLineEdit(self)
		self.textInput1.setFixedWidth(50)
		self.textInput1.move(120, line)
		self.textInput1.setText(str(max(self.p, 0.2)))		# stuff p here even if non custom
		self.popup2 = QtGui.QComboBox(self)
		self.popup2.setStyleSheet("background : #ffffff")
		self.popup2.activated[str].connect(self.onPopup2)
		self.popup2.setFixedWidth(50)
		self.popup2.move(120, line)
		if self.ts == "Custom": 
			self.popup2.hide()
		else:
			self.textInput1.hide()
			self.popup2.addItems(ISO261PDTABLE[self.sz])
			if str(self.p) not in ISO261PDTABLE[self.sz]: 	self.p = float(ISO261PDTABLE[self.sz][0])
			self.popup2.setCurrentIndex(ISO261PDTABLE[self.sz].index(str(self.p)))
			if internal:
				self.d = float(self.sz[1:]) + iso965IntCrestDev(self.p, self.ct)		# Update diameter with crest deviation
			else:
				self.d = float(self.sz[1:]) - iso965ExtCrestDev(self.p, self.ct)		# Update diameter with crest deviation
			self.textInput.setText(str(round(self.d, 3)))

		# Length input box
		line+=lineinc
		self.label3 = QtGui.QLabel("Length", self)
		self.label3.move(20, line)
		self.textInput2 = QtGui.QLineEdit(self)
		self.textInput2.setText(str(self.l))
		self.textInput2.setFixedWidth(50)
		self.textInput2.move(120, line)

		# Taper input box with ISO, NPT setter buttons- if not Custom, grey out/ read-only
		line+=lineinc
		self.label6 = QtGui.QLabel("Taper", self)
		self.label6.move(20, line)
		self.textInput3 = QtGui.QLineEdit(self)
		self.textInput3.setFixedWidth(50)
		self.textInput3.move(120, line)
		self.textInput3.setText(str(self.t))
		if self.ts != "Custom":
			self.textInput3.setDisabled(True)
		# ISO button
		self.pushButton1 = QtGui.QPushButton('ISO', self)
		self.pushButton1.clicked.connect(self.onPushButton1)
		self.pushButton1.setMaximumWidth(30)
		self.pushButton1.move(180, line)
		# NPT button
		self.pushButton2 = QtGui.QPushButton('NPT', self)
		self.pushButton2.clicked.connect(self.onPushButton2)
		self.pushButton2.setMaximumWidth(30)
		self.pushButton2.move(220, line)

		# Radial clearance input box
		line+=lineinc
		self.label7 = QtGui.QLabel("Radial Clearance", self)
		self.label7.move(20, line)
		self.textInput4 = QtGui.QLineEdit(self)
		self.textInput4.setText(str(self.c))
		self.textInput4.setFixedWidth(50)
		self.textInput4.move(120, line)

		# Base selection radio buttons
		line+=(lineinc+5)
		self.radioButton1 = QtGui.QRadioButton("Bevel Base",self)
		self.radioButton1.clicked.connect(self.onRadioButton1)
		self.radioButton1.move(20,line)
		self.radioButton2 = QtGui.QRadioButton("Chamfer Base",self)
		self.radioButton2.clicked.connect(self.onRadioButton2)
		self.radioButton2.move(120,line)
		if self.cb:	#Chamfer base
			self.radioButton2.click()
		else:
			self.radioButton1.click()

		# Rounded Root checkbox
		line+=(lineinc+5)
		self.checkbox3 = QtGui.QCheckBox("Rounded Root", self)
		self.checkbox3.clicked.connect(self.onCheckbox3)
		self.checkbox3.move(20, line)
		if self.rr: self.checkbox3.click()
		# Left Handed checkbox
		self.checkbox1 = QtGui.QCheckBox("Left-Handed", self)
		self.checkbox1.clicked.connect(self.onCheckbox1)
		self.checkbox1.move(130,line)
		if self.lh: self.checkbox1.click()
		# Thread Disable checkbox
		line+=lineinc
		self.checkbox2 = QtGui.QCheckBox("Disable Thread", self)
		self.checkbox2.clicked.connect(self.onCheckbox2)
		self.checkbox2.move(20,line)
		if self.td: self.checkbox2.click()

		# OK button
		line+=(lineinc+10)
		self.okButton = QtGui.QPushButton('OK', self)
		self.okButton.clicked.connect(self.onOk)
		self.okButton.move(40, line)
		# cancel button
		self.cancelButton = QtGui.QPushButton('Cancel', self)
		self.cancelButton.clicked.connect(self.onCancel)
		self.cancelButton.setAutoDefault(True)
		self.cancelButton.move(150, line)

		# Warning message placeholder
		line+=lineinc
		self.warnlabel = QtGui.QLabel("", self)
		self.warnlabel.setMinimumWidth(250)
		self.warnlabel.setStyleSheet("color : #ff0000")
		self.warnlabel.move(10, line)
		# now make the window visible
		self.show()
	# end initUI(self):	

	def onRadioButton1(self):
		"""Bevel base"""
		return

	def onRadioButton2(self):
		"""Chamfer base"""
		return

	def onPushButton1(self):
		"""ISO thread taper override"""
		if self.ts == "Custom": self.textInput3.setText("0.0")

	def onPushButton2(self):
		"""NPT thread taper override"""
		if self.ts == "Custom": self.textInput3.setText("1.7899")

	def onCheckbox1(self):
		"""Left-Handed thread"""
		return

	def onCheckbox2(self):
		"""Disable thread"""
		return

	def onCheckbox3(self):
		"""Rounded root"""
		return

	def onPopup1(self, selection):		# Standard selected- set widdgets for sz, d, p, t
		"""Thread standard popup list """		# size/label5/popup0::tolp/label8/popup3::tolc/lagel9/popup4
		self.ts = selection		
		if self.ts == "Custom": 	# Disable sz, p(popup), ct, pt; enable d, p(textbox), t.
			self.popup0.setDisabled(True)					# popup0 = size 
			self.label5.setStyleSheet("color : #b0b0b0")
			self.popup2.hide()					# popup2 = pitch
			self.popup3.setDisabled(True)		# pitch tol
			self.label8.setStyleSheet("color : #b0b0b0")
			self.popup4.setDisabled(True)		# crest tol
			self.label9.setStyleSheet("color : #b0b0b0")
			self.textInput.setDisabled(False)		# textInput = diameter
			self.textInput1.show()				# textInput1 = pitch
			self.textInput1.setText(self.popup2.currentText())
			self.textInput3.setDisabled(False)	# textInput3 = taper
		else: 	# ISO261	# Enable sz, p(popup), ct, pt; disable d, p(textbox), t
							# load SIZES, PITCHES, diameter; set initial values for sz, p, d, t
			self.popup0.setDisabled(False)					# StdSize
			self.label5.setStyleSheet("color : ")
			self.d = int(self.d)
			self.sz = "M" + str(self.d)
			if self.sz not in list(ISO261PDTABLE): self.sz = list(ISO261PDTABLE)[19]
			self.popup0.setCurrentIndex(list(ISO261PDTABLE).index(self.sz))
			self.popup2.clear()								# pitch
			self.popup2.addItems(ISO261PDTABLE[self.sz])
			if str(self.p) not in ISO261PDTABLE[self.sz]: self.p = float(ISO261PDTABLE[self.sz][0])
			self.popup2.setCurrentIndex(ISO261PDTABLE[self.sz].index(str(self.p)))
			self.popup2.show()			
			self.popup3.setDisabled(False)			# 
			self.label8.setStyleSheet("color : ")
			self.popup4.setDisabled(False)
			self.label9.setStyleSheet("color : ")
			self.textInput.setDisabled(True)				# diameter
			if self.internal:
				self.d = float(self.sz[1:]) + iso965IntCrestDev(self.p, self.ct)
			else:
				self.d = float(self.sz[1:]) - iso965ExtCrestDev(self.p, self.ct)
			self.textInput.setText(str(round(self.d, 3)))
			self.textInput1.hide()
			self.textInput3.setDisabled(True)			# taper
			self.textInput3.setText(str(SUPPORTEDSTANDARDS[self.ts]))
		return
	# End onPopup1

	def onPopup0(self, selection):		#Size popup- store sz selection, update p(popup2), update d
		self.sz = selection		
		self.popup2.clear()
		self.popup2.addItems(ISO261PDTABLE[self.sz])
		if str(self.p) not in ISO261PDTABLE[self.sz]: self.p = float(ISO261PDTABLE[self.sz][0])
		self.popup2.setCurrentIndex(ISO261PDTABLE[self.sz].index(str(self.p)))
		if self.ts != "Custom":
			if self.internal:
				self.d = float(self.sz[1:]) + iso965IntCrestDev(self.p, self.ct)		# diameter	
			else:
				self.d = float(self.sz[1:]) - iso965ExtCrestDev(self.p, self.ct)		# diameter	
			self.textInput.setText(str(round(self.d,3)))
		return

	def onPopup2(self, selection):		# Pitch popup- lookup and set d
		"""Pitch popup list for Custom std"""
		self.p = float(selection)
		if self.ts != "Custom":
			if self.internal:
				self.d = float(self.sz[1:]) + iso965IntCrestDev(self.p, self.ct)		# diameter	
			else:
				self.d = float(self.sz[1:]) - iso965ExtCrestDev(self.p, self.ct)		# diameter	
			self.textInput.setText(str(round(self.d,3)))
		return

	def onPopup3(self, selection):		# Pitch tolerance popup- lookup and set pt
		self.pt = selection
		return

	def onPopup4(self, selection):		# Crest tolerance popup- lookup and set pt
		self.ct = selection
		if self.ts != "Custom":		
			if self.internal:
				self.d = float(self.sz[1:]) + iso965IntCrestDev(self.p, self.ct)		# diameter	
			else:
				self.d = float(self.sz[1:]) - iso965ExtCrestDev(self.p, self.ct)		# diameter	
			self.textInput.setText(str(round(self.d,3)))
		return

	def onCancel(self):
		self.result = None
		self.close()

	def onOk(self):
		"""Validate numeric text inputs, convert to positive if negative"""
		self.ts = self.popup1.currentText()
		self.sz = self.popup0.currentText()
		self.d = self.textInput.text()
		if self.ts == "Custom":
			self.p = self.textInput1.text()
		else:
			self.p = self.popup2.currentText()
		self.l = self.textInput2.text()
		self.t = self.textInput3.text()
		self.c = self.textInput4.text()
		self.cb = self.radioButton2.isChecked()
		self.lh = self.checkbox1.isChecked()
		self.td = self.checkbox2.isChecked()
		self.rr = self.checkbox3.isChecked()
		self.pt = self.popup3.currentText()
		self.ct = self.popup4.currentText()
		self.warnlabel.setText("")

		# Validate numeric input types, convert to float
		try:		# pitch type validation
			self.p = float(self.p)
		except:
			self.warnlabel.setText("Pitch must be a number (you entered " + str(self.p) + ")")
			self.textInput1.setFocus()
			return
		try:		# diameter type validation
			self.d = float(self.d)
		except:
			self.warnlabel.setText("Diameter must be a number (you entered " + str(self.d) + ")")
			self.textInput.setFocus()
			return
		try:		# length validation
			self.l = float(self.l)
		except:
			self.warnlabel.setText("Length must be a number (you entered " + str(self.l) + ")")
			self.textInput2.setFocus()
			return
		try:		# taper angle validation
			self.t = float(self.t)
		except:
			self.warnlabel.setText("Taper angle must be a number (you entered " + str(self.t) + ")")
			self.textInput3.setFocus()
			return
		try:
			self.c = float(self.c)
		except:
			self.warnlabel.setText("Clearance must be a number (you entered " + str(self.c) + ")")
			self.textInput4.setFocus()
			return

		# Validate numeric values pitch, diam., len., clearance
		if self.p < 0: self.p = -self.p
		if self.d < 0: self.d = -self.d		
		if self.l < 0: self.l = -self.l
		#self.d = thread O.D.  id ~ od - p*1.1.     P < (od - 1.1*p - c)/1.1; < (od - c)/1.1 - p;  ***P < (od - c)/2.2***
		if (self.p >= (self.d-self.c)/2.3):
			self.warnlabel.setText("Pitch must be less than (Dia. - Clearance)/ 2.3")
			self.textInput1.setFocus()
			return
		if (self.p < 0.1):
			self.warnlabel.setText("Pitch must be greater than 0.1")
			self.textInput1.setFocus()
			return
		if self.l <= self.p:
			self.warnlabel.setText("Length must be greater than Pitch")
			self.textInput2.setFocus()
			return
		if self.internal and self.ts != "Custom" and iso965IntPitchDev(float(self.sz[1:]), self.p, self.pt) > iso965IntCrestDev(self.p, self.ct):
			self.warnlabel.setText(self.pt + " Pitch Dev. > " + self.ct + " Crest Dev. is not allowed.")
			self.popup4.setFocus()
			return
		if not self.internal and self.ts != "Custom" and iso965ExtPitchDev(float(self.sz[1:]), self.p, self.pt) > iso965ExtCrestDev(self.p, self.ct):
			self.warnlabel.setText(self.pt + " Pitch Dev. > " + self.ct + " Crest Dev. is not allowed.")
			self.popup4.setFocus()
			return
			
		# Stash validated props in MRU list for prepopulation
		param_grp=FreeCAD.ParamGet(MRUPATH)
		param_grp.SetString("thrdstandard", self.ts)
		param_grp.SetString("stdsize", self.sz)
		param_grp.SetFloat("diameter", self.d)
		param_grp.SetFloat("pitch", self.p)
		param_grp.SetFloat("length", self.l)
		param_grp.SetFloat("taper", self.t)
		param_grp.SetFloat("clearance", self.c)
		param_grp.SetBool("chamfer", self.cb)
		param_grp.SetBool("lefty", self.lh)
		param_grp.SetBool("tdisable", self.td)
		param_grp.SetBool("roundroot", self.rr)
		param_grp.SetString("pitchtol", self.pt)
		param_grp.SetString("cresttol", self.ct)

		self.result = [self.ts, self.sz, self.d, self.p, self.l, self.t, self.c, self.cb, self.lh, self.td, self.rr, self.pt, self.ct]
		self.close()

	def keyPressEvent(self, event):
		if event.nativeVirtualKey() == 27:			# Esc pressed
			self.onCancel()
		if event.nativeVirtualKey() == 13:			# Enter pressed
			self.onOk()
# end class ThreadDialog(QtGui.QDialog):

### ISO 261 Table 2: Pitch/Diameter Selection.  Finer pitches were added per Table 1.
#   Generated from PDF --(data entry)--> MS Excel, Excel formulas to format into Python dictonary text strings
ISO261PDTABLE = {  
'M1':['0.25','0.2'],
'M1.1':['0.25','0.2'],
'M1.2':['0.25','0.2'],
'M1.4':['0.3','0.2'],
'M1.6':['0.35','0.2'],
'M1.8':['0.35','0.2'],
'M2':['0.4','0.25','0.2'],
'M2.2':['0.45','0.25','0.2'],
'M2.5':['0.45','0.35','0.25','0.2'],
'M3':['0.5','0.35','0.25','0.2'],
'M3.5':['0.6','0.35','0.25','0.2'],
'M4':['0.7','0.5','0.35','0.25'],
'M4.5':['0.75','0.5','0.35','0.25'],
'M5':['0.8','0.5','0.35','0.25'],
'M5.5':['0.8','0.5','0.35','0.25'],
'M6':['1.0','0.75','0.5','0.35','0.25'],
'M7':['1.0','0.75','0.5','0.35','0.25'],
'M8':['1.25','1.0','0.75','0.5','0.35','0.25'],
'M9':['1.25','1.0','0.75','0.5','0.35','0.25'],
'M10':['1.5','1.25','1.0','0.75','0.5','0.35'],
'M11':['1.5','1.0','0.75','0.5','0.35'],
'M12':['1.75','1.5','1.25','1.0','0.75','0.5'],
'M14':['2.0','1.5','1.25','1.0','0.75','0.5'],
'M15':['2.0','1.5','1.0','0.75','0.5'],
'M16':['2.0','1.5','1.0','0.75','0.5'],
'M17':['2.0','1.5','1.0','0.75','0.5'],
'M18':['2.5','2.0','1.5','1.0','0.75','0.5'],
'M20':['2.5','2.0','1.5','1.0','0.75','0.5'],
'M22':['2.5','2.0','1.5','1.0','0.75','0.5'],
'M24':['3.0','2.0','1.5','1.0','0.75'],
'M25':['3.0','2.0','1.5','1.0','0.75'],
'M26':['3.0','1.5','1.0','0.75'],
'M27':['3.0','2.0','1.5','1.0','0.75'],
'M28':['3.0','2.0','1.5','1.0','0.75'],
'M30':['3.5','3.0','2.0','1.5','1.0','0.75'],
'M32':['3.5','2.0','1.5','1.0','0.75'],
'M33':['3.5','3.0','2.0','1.5','0.75'],
'M35':['3.5','1.5','1.0'],
'M36':['4.0','3.0','2.0','1.5','1.0'],
'M38':['4.0','1.5','1.0'],
'M39':['4.0','3.0','2.0','1.5','1.0'],
'M40':['4.0','3.0','2.0','1.5','1.0'],
'M42':['4.5','4.0','3.0','2.0','1.5','1.0'],
'M45':['4.5','4.0','3.0','2.0','1.5','1.0'],
'M48':['5.0','4.0','3.0','2.0','1.5','1.0'],
'M50':['5.0','4.0','3.0','2.0','1.5','1.0'],
'M52':['5.0','4.0','3.0','2.0','1.5','1.0'],
'M55':['5.0','4.0','3.0','2.0','1.5','1.0'],
'M56':['5.5','4.0','3.0','2.0','1.5','1.0'],
'M58':['5.5','4.0','3.0','2.0','1.5','1.0'],
'M60':['5.5','4.0','3.0','2.0','1.5','1.0'],
'M62':['5.5','4.0','3.0','2.0','1.5','1.0'],
'M64':['6.0','4.0','3.0','2.0','1.5','1.0'],
'M65':['6.0','4.0','3.0','2.0','1.5','1.0'],
'M68':['6.0','4.0','3.0','2.0','1.5','1.0'],
'M70':['6.0','4.0','3.0','2.0','1.5','1.0'],
'M72':['6.0','4.0','3.0','2.0','1.5','1.0'],
'M75':['6.0','4.0','3.0','2.0','1.5','1.0'],
'M76':['6.0','4.0','3.0','2.0','1.5','1.0'],
'M78':['6.0','2.0','1.5','1.0'],
'M80':['6.0','4.0','3.0','2.0','1.5','1.0'],
'M82':['6.0','2.0','1.5'],
'M85':['6.0','4.0','3.0','2.0','1.5'],
'M90':['6.0','4.0','3.0','2.0','1.5'],
'M95':['6.0','4.0','3.0','2.0','1.5'],
'M100':['6.0','4.0','3.0','2.0','1.5'],
'M105':['6.0','4.0','3.0','2.0','1.5'],
'M110':['6.0','4.0','3.0','2.0','1.5'],
'M115':['6.0','4.0','3.0','2.0','1.5'],
'M120':['6.0','4.0','3.0','2.0','1.5'],
'M125':['8.0','6.0','4.0','3.0','2.0','1.5'],
'M130':['8.0','6.0','4.0','3.0','2.0','1.5'],
'M135':['8.0','6.0','4.0','3.0','2.0','1.5'],
'M140':['8.0','6.0','4.0','3.0','2.0','1.5'],
'M145':['8.0','6.0','4.0','3.0','2.0','1.5'],
'M150':['8.0','6.0','4.0','3.0','2.0','1.5'],
'M155':['8.0','6.0','4.0','3.0','2.0'],
'M160':['8.0','6.0','4.0','3.0','2.0'],
'M165':['8.0','6.0','4.0','3.0','2.0'],
'M170':['8.0','6.0','4.0','3.0','2.0'],
'M175':['8.0','6.0','4.0','3.0','2.0'],
'M180':['8.0','6.0','4.0','3.0','2.0'],
'M185':['8.0','6.0','4.0','3.0','2.0'],
'M190':['8.0','6.0','4.0','3.0','2.0'],
'M195':['8.0','6.0','4.0','3.0','2.0'],
'M200':['8.0','6.0','4.0','3.0','2.0'],
'M205':['8.0','6.0','4.0','3.0'],
'M210':['8.0','6.0','4.0','3.0'],
'M215':['8.0','6.0','4.0','3.0'],
'M220':['8.0','6.0','4.0','3.0'],
'M225':['8.0','6.0','4.0','3.0'],
'M230':['8.0','6.0','4.0','3.0'],
'M235':['8.0','6.0','4.0','3.0'],
'M240':['8.0','6.0','4.0','3.0'],
'M245':['8.0','6.0','4.0','3.0'],
'M250':['8.0','6.0','4.0','3.0'],
'M255':['8.0','6.0','4.0','3.0'],
'M260':['8.0','6.0','4.0','3.0'],
'M265':['8.0','6.0','4.0','3.0'],
'M270':['8.0','6.0','4.0','3.0'],
'M275':['8.0','6.0','4.0','3.0'],
'M280':['8.0','6.0','4.0','3.0'],
'M285':['8.0','6.0','4.0','3.0'],
'M290':['8.0','6.0','4.0','3.0'],
'M295':['8.0','6.0','4.0','3.0'],
'M300':['8.0','6.0','4.0','3.0'] }