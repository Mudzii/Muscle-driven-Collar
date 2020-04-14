# ======================================================================================= #
# ================================= IMPORTS ============================================= #
# ======================================================================================= #
import pymel.core as pm
import maya.cmds as cmds
import os
from os.path import dirname
from glob import glob
from maya import OpenMayaUI as omui

# Qt
try:
    import PySide2
    from PySide2 import QtWidgets, QtCore, QtGui
    from PySide2.QtUiTools import *
    from shiboken2 import wrapInstance
    
except ImportError:
    import PySide2
    from PySide import QtCore, QtGui
    from PySide2.QtUiTools import *
    from shiboken2 import wrapInstance 
    QtWidgets = QtGui

# Logger & muscle plugin
import logging

if not cmds.pluginInfo('MayaMuscle.mll', q=True, l=True):
    cmds.loadPlugin( 'MayaMuscle.mll' )


logging.basicConfig()
logger = logging.getLogger('DrivenNurb')
logger.setLevel(logging.INFO)
# ======================================================================================= #
# ======================================================================================= #

clusters = []
del clusters[:]

clusterGrps = []
del clusterGrps[:]

KeepOutList = []
del KeepOutList[:]

KeepOutNames = []
del KeepOutNames[:]


# ================================ #   
def CleanObj(obj):
    pm.delete(obj , ch = 1)
    pm.makeIdentity(obj, apply = True )
    
# ================================ #   
def CreateClusters(curveCVList, prntGrp):
          
     global clusters
     global clusterGrps
     
     i = 0
     baseName = str(NURB) + '_cluster_'
     
     for cv in curveCVList:
        #print 'Creating {0}'.format(cv)
        
        #create cluster 
        cstr = pm.cluster(cv)
        pm.rename(cstr[1], baseName + str(i))       
        
        # create cluster grp. Center on cluster
        temp = pm.group( em = True, name = baseName + str(i) + '_GRP' )    
        cmds.matchTransform(str(temp),str(cstr[1]))
        
        #parent cluster to group
        pm.parent( str(cstr[1]), str(temp))
        pm.parent( str(temp), str(prntGrp))
        
        # append to lists
        clusters.append(cstr)        
        clusterGrps.append(temp)
        i = i + 1
        
        
# ================================ #   
def ClusterToKeepOut(clusterList):
          
    global clusterGrps
    global KeepOutList   
    global KeepOutNames 
        
    i = 0
    for grp in clusterGrps:
        
        # select cluster grp and create keep out
        pm.select(grp)
        temp = mel.eval('cMuscle_rigKeepOutSel();') 
        #CleanObj(temp)
        
        # append info to lists
        KeepOutList.append(clusterList[i])    
        KeepOutNames.append(temp[0])
        i = i + 1
        

# ================================ #   
def ConnectKeepOut():
     
    global KeepOutNames
    global collision_mesh
      
    pm.select(KeepOutNames)
    pm.select(collision_mesh, add = True)
    mel.eval('cMuscle_keepOutAddRemMuscle(1);') 
    
    
    
# ================================ # 
def JointSetup(prntGrp, nrCVs, curveCVList):
    print "jtn setup"
    global NURB
    
    shapes = cmds.listRelatives(str(NURB)) 
    shape = shapes[0]
    
    offset = [0.0, 0.13, 0.25, 0.37, 0.5, 0.63, 0.75, 0.88]
    
    for i in range(nrCVs):
        
        # create grp, LOC and JNT
        tempName = str(NURB) + "_" + str(i)
        tempGrp = pm.group( em = True, name = tempName + '_offset_GRP' )
        tempLoc = pm.spaceLocator(n = tempName + "_loc")
        tempJnt = pm.joint(n = tempName + "_jnt")
        
        # fix hierarchy
        pm.parent( str(tempJnt), str(tempLoc))
        pm.parent( str(tempLoc), str(tempGrp))
        pm.parent( str(tempGrp), str(prntGrp))
        
       
        # create POC node and connect 
        pocNode = cmds.createNode("pointOnCurveInfo", name = tempName + "_POC")
        cmds.setAttr(pocNode + ".turnOnPercentage", 1)
        
        cmds.connectAttr(shape + ".worldSpace[0]", pocNode + ".inputCurve")
        cmds.connectAttr(pocNode + ".result.position", tempGrp + ".translate")
        cmds.setAttr(pocNode + ".parameter", offset[i])

        

    
    

# ======================================================================================= #
# ======================================================================================= #

class DrivenNurb(QtWidgets.QMainWindow):
    
    # ================================ #
    def __init__(self):
        super(DrivenNurb, self).__init__()
        windowName = 'DrivenNurb'
        
        # Delete if exists
        if cmds.window(windowName, exists=True):
            cmds.deleteUI(windowName)
            logger.debug('Deleted previous UI')
        else:
            logger.debug('No previous UI exists')
            pass
            
        # Get Maya window and parent the controller to it
        mayaMainWindow = {o.objectName(): o for o in QtWidgets.qApp.topLevelWidgets()}["MayaWindow"]
        self.setParent(mayaMainWindow)
        self.setWindowFlags(QtCore.Qt.Window)

        self.setWindowTitle('MuscleDrivenNurb')
        self.setObjectName(windowName)
        self.resize(400, 200)

        self.BuildUI()
        
    # ================================ #   
    def BuildUI(self):
        #Main widget
        widget = QtWidgets.QWidget(self)
        self.setCentralWidget(widget)
        
        ##Layout
        lot = QtWidgets.QGridLayout()
        widget.setLayout(lot)
        
        # collision mesh viewer
        col_mesh_view = self.currentDirTxt = QtWidgets.QLineEdit()
        col_mesh_view.setStyleSheet("border: 1px groove black; border-radius: 4px;")
        col_mesh_view.returnPressed.connect(lambda: self.LoadMesh(col_mesh_view.text()))
        lot.addWidget(self.currentDirTxt,0,0,0,1)
        
         # load mesh button  
        loadMeshButton = QtWidgets.QPushButton()
        loadMeshButton.setText("Load Mesh")
        loadMeshButton.clicked.connect(lambda: self.LoadMesh(col_mesh_view.text()))
        lot.addWidget(loadMeshButton,0,1,0,9)   
        
        # nurb mesh viewer
        nurb_mesh_view = self.currentDirTxt = QtWidgets.QLineEdit()
        nurb_mesh_view.setStyleSheet("border: 1px groove black; border-radius: 4px;")
        nurb_mesh_view.returnPressed.connect(lambda: self.LoadNurb(nurb_mesh_view.text()))
        lot.addWidget(self.currentDirTxt,4,0,5,1)
        
         # load nurb button  
        loadMeshButton = QtWidgets.QPushButton()
        loadMeshButton.setText("Load Nurb")
        loadMeshButton.clicked.connect(lambda: self.LoadNurb(nurb_mesh_view.text()))
        lot.addWidget(loadMeshButton,4,1,5,9) 
        
        # create button  
        createButton = QtWidgets.QPushButton()
        createButton.setText("Create muscle Driven curve")
        createButton.clicked.connect(lambda: self.CreateCurve())
        lot.addWidget(createButton,8,0,1,10) 
        
    # ================================ #
    def LoadMesh(self, meshName):
        
        if len(meshName) > 0:
            pm.select(meshName)
            
            #check if added shape is a mesh
            shapes = cmds.listRelatives(str(meshName))            
            if pm.objectType(shapes, isType='mesh'):
            
                global collision_mesh
                collision_mesh = pm.ls( selection=True )[0] 
                print "loading mesh " + str(collision_mesh)
                
            else:
                pm.warning('Please select a mesh instead')  
        
    # ================================ #        
    def LoadNurb(self, nurbName):
        
        if len(nurbName) > 0:
            pm.select(nurbName)
            
            #check if added shape is a NURB
            shapes = cmds.listRelatives(str(nurbName))        
            if pm.objectType(shapes, isType='nurbsCurve'):
            
                global NURB
                NURB = pm.ls( selection=True )[0] 
                print "load nurb " + str(NURB)
                
            else:
                pm.warning('Please select a nurb curve instead')    
    
    # ================================ # 
    def CreateCurve(self):
        
        global NURB        
        global clusters        
        global collision_mesh   
                    
        if NURB and collision_mesh:

            #make mesh muscle object
            pm.select(collision_mesh )
            mel.eval('cMuscle_makeMuscle(0);')
            
            # del history and freeze transforms
            CleanObj(NURB)
            CleanObj(collision_mesh)
            
            # get points on NURB curve
            numCVs = NURB.numCVs()
            curveCVs = cmds.ls('{0}.cv[:]'.format(NURB), fl = True)
            
            # if points found, create stuff
            if curveCVs:
                
                # create clusters and keepout                     
                CLSTRgrp = pm.group( em = True, name = str(NURB) + '_cluster_GRP' )
                CreateClusters(curveCVs, CLSTRgrp)
                ClusterToKeepOut(clusters)
                ConnectKeepOut()
                
                # create joint setup
                JNTgrp = pm.group( em = True, name = str(NURB) + '_rig_GRP' )
                JointSetup(JNTgrp, numCVs, curveCVs)
            
            
 
    

# ======================================================================================= # 
win = DrivenNurb()
win.show() 

