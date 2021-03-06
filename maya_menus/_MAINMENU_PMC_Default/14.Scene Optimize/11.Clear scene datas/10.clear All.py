import maya.cmds as cmds

def cleanMeshInScene( *args ):

    def cleanMesh( targetObj ):
    
        targetShapes = cmds.listRelatives( targetObj, s=1, f=1 )
        for targetShape in targetShapes:
            if not cmds.getAttr( targetShape+'.io' ): continue
            if cmds.listConnections( targetShape + '.outMesh', s=0, d=1 ): continue 
            if cmds.listConnections( targetShape + '.worldMesh', s=0, d=1 ): continue 
            cmds.delete( targetShape )
            cmds.warning( "%s is deleted" % targetShape )
    
    meshs = cmds.ls( type='mesh' )
    
    meshObjs = []
    for mesh in meshs:
        if cmds.getAttr( mesh+'.io' ): continue
        meshP = cmds.listRelatives( mesh, p=1, f=1 )[0]
        if meshP in meshObjs: continue
        meshObjs.append( meshP ) 
    
    for meshObj in meshObjs:
        cleanMesh( meshObj )

cleanMeshInScene()


import pymel.core
pymel.core.delete( pymel.core.ls( type='audio' ) )


import pymel.core
sels = pymel.core.ls( type='unknown' )
if sels:
    try:pymel.core.delete( sels )
    except:pass


import pymel.core
displayLayers = pymel.core.ls( type='displayLayer' )
for displayLayer in displayLayers:
    if not displayLayer.v.get(): continue
    if displayLayer.name() == 'defaultLayer': continue
    pymel.core.delete( displayLayer )


import pymel.core
sels = pymel.core.ls( type='renderLayer' )
for sel in sels:
    if sel == 'defaultRenderLayer': continue
    pymel.core.delete( sel )

import maya.mel
maya.mel.eval( 'hyperShadePanelMenuCommand("hyperShadePanel1", "deleteUnusedNodes");' )

try:pymel.core.delete( 'frameCounterUpdate' )
except:pass
try:pymel.core.delete( 'timeCodeUpdate' )
except:pass

from maya import cmds
plugins = cmds.unknownPlugin( q=1, list=1 )
if not plugins: plugins = []
for plugin in plugins:
    try:cmds.unknownPlugin( plugin, remove=1 )
    except:pass