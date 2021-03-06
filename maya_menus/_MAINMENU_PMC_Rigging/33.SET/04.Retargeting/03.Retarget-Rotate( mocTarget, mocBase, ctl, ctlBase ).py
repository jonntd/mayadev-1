import pymel.core
sels = pymel.core.ls( sl=1 )

target = sels[0]
targetBase = sels[1]
ctl = sels[2]
ctlBase = sels[3]

multMtx = pymel.core.createNode( 'multMatrix' )
target.wm >> multMtx.i[0]
targetBase.wim >> multMtx.i[1]
ctlBase.wm >> multMtx.i[2]
ctl.pim >> multMtx.i[3]
dcmp = pymel.core.createNode( 'decomposeMatrix' )
multMtx.matrixSum >> dcmp.imat
dcmp.outputRotate >> ctl.r