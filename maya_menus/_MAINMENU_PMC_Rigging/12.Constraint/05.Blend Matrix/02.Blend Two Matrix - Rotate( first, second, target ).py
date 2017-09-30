from sgMaya import sgCmds
import pymel.core

sels = pymel.core.ls( sl=1 )

for sel in sels[2:]:
    blendNode = sgCmds.createBlendTwoMatrixNode( sels[0], sels[1] )
    mm = sgCmds.createNode( 'multMatrix' )
    blendNode.matrixOutput() >> mm.i[0]
    sel.pim >> mm.i[1]
    dcmp = sgCmds.getDecomposeMatrix( mm.matrixSum )
    dcmp.outputRotate >> sel.r
    
    sgCmds.addAttr( sel, ln='blend', min=0, max=1, k=1, dv=0.5 )
    print sel.blend.name(), " >> ", blendNode.blend.name()
    sel.blend >> blendNode.blend