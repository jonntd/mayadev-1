from maya import OpenMaya
from maya import cmds, mel
import pymel.core
from sgMaya import sgCmds, sgModel
import random
import math
from sgMaya.sgCmds import makeController



def createXLookAtJointLine( inputTargets ):
    
    targets = []
    for inputTarget in inputTargets:
        targets.append( pymel.core.ls( inputTarget )[0] )
    
    beforeJnt = None
    baseMatrix = None
    joints = []
    for i in range( len( targets )-1 ):
        if not baseMatrix:
            baseMatrix = sgCmds.listToMatrix( cmds.getAttr( targets[i].wm.name() ) )
        else:
            baseMatrixList = sgCmds.matrixToList( baseMatrix )
            targetPos = pymel.core.xform( targets[i], q=1, ws=1, t=1 )
            baseMatrixList[12] = targetPos[0]
            baseMatrixList[13] = targetPos[1]
            baseMatrixList[14] = targetPos[2]
            baseMatrix = sgCmds.listToMatrix( baseMatrixList )

        targetPos = OpenMaya.MPoint( *pymel.core.xform( targets[i+1], q=1, ws=1, t=1 ) )
        localPos = targetPos * baseMatrix.inverse()
        
        angleValues = pymel.core.angleBetween( v1=[1,0,0], v2=[localPos.x, localPos.y, localPos.z], er=1 )
        rotMtx = sgCmds.rotateToMatrix( angleValues )
        
        jointMatrix = sgCmds.matrixToList( rotMtx * baseMatrix )
        if beforeJnt:
            pymel.core.select( beforeJnt )
        else:
            pymel.core.select( d=1 )
        cuJoint = pymel.core.joint()
        pymel.core.xform( cuJoint, ws=1, matrix=jointMatrix )
        baseMatrix = sgCmds.listToMatrix( jointMatrix )
        joints.append( cuJoint )
        beforeJnt = cuJoint
    
    pymel.core.select( beforeJnt )
    endJnt = pymel.core.joint()
    pymel.core.xform( endJnt, ws=1, matrix= targets[-1].wm.get() )
    endJnt.r.set( 0,0,0 )
    joints.append( endJnt )
    
    return joints
    


def makeWaveJoint( inputTopJoint ): 
    
    topJoint = pymel.core.ls( inputTopJoint )[0]
    children = topJoint.listRelatives( c=1, type='transform' )
    joints = [topJoint]
    
    while children:
        joints.append( children[0] )
        children = children[0].listRelatives( c=1, type='transform' )
    
    joints = list( filter( lambda x : x.nodeType() == 'joint', joints ) )
    
    methodList = ['Sine', 'Rand', 'RandBig']
    axisList   = ['X', 'Y', 'Z']
    
    firstJnt = joints[0]
    sgCmds.addOptionAttribute( firstJnt, 'All' )
    sgCmds.addAttr( firstJnt, ln='move', k=1 )
    sgCmds.addAttr( firstJnt, ln='allWeight', min=0, dv=1, k=1 )
    sgCmds.addAttr( firstJnt, ln='allSpeed', min=0, dv=1, k=1 )
    for method in methodList:
        sgCmds.addOptionAttribute( firstJnt, '%s' % method )
        sgCmds.addAttr( firstJnt, ln='all%sWeight' % method, min=0, dv=1, k=1 )
        sgCmds.addAttr( firstJnt, ln='all%sSpeed' % method, min=0, dv=1, k=1 )
    sgCmds.addOptionAttribute( firstJnt, 'intervalValueAdd' )
    sgCmds.addAttr( firstJnt, ln='intervalValueAdd', min=0, dv=15, k=1 )
    
    for joint in joints:
        try:sgCmds.freezeJoint( joint )
        except:pass
    
    for method in methodList:
        dvOffset = 0
        dvInterval = -2
        
        sgCmds.addOptionAttribute( firstJnt, 'control%s' % method )
        sgCmds.addAttr( firstJnt, ln='interval%s' %(method), k=1, dv=dvInterval )
        sgCmds.addAttr( firstJnt, ln='offset%s' %(method), k=1, dv=dvOffset )
        for axis in axisList:    
            dvValue = 5
            sgCmds.addAttr( firstJnt, ln='value%s%s' %(method,axis), min=-90, max=90, k=1, dv = dvValue )
        for axis in axisList:
            if axis == 'Y':
                dvSpeed = 1.2
            else:
                dvSpeed = 0.8
            sgCmds.addAttr( firstJnt, ln='speed%s%s' %(method,axis), k=1, dv=dvSpeed )
            
    
    for axis in axisList:  
        randValues = []
        for j in range( 100 ):
            randValue = random.uniform( -1, 1 )
            randValues.append( randValue )
        
        for i in range( 1, len(joints)-1 ):
            methodAdd = pymel.core.createNode( 'plusMinusAverage' )
            globalAllMult = pymel.core.createNode( 'multDoubleLinear' )
            firstJnt.attr( 'allWeight' ) >> globalAllMult.input1
            methodAdd.output1D >> globalAllMult.input2
            
            joint = joints[i]
            methodIndex = 0
            
            for method in methodList:
                globalAllSpeedMult = pymel.core.createNode( 'multDoubleLinear' )
                firstJnt.attr( 'allSpeed' ) >> globalAllSpeedMult.input1
                globalSpeedMult = pymel.core.createNode( 'multDoubleLinear' )
                firstJnt.attr( 'all%sSpeed' % method ) >> globalSpeedMult.input1
                globalSpeedMult.output >> globalAllSpeedMult.input2
                
                animCurve = pymel.core.createNode( 'animCurveUU' )
                animCurve.preInfinity.set( 3 )
                animCurve.postInfinity.set( 3 )
                if method in ['Rand','RandBig']:
                    for j in range( len( randValues ) ):
                        randValue = randValues[j]
                        if j == 0 or j == 99:
                            pymel.core.setKeyframe( animCurve, f=j*10, v=0 )
                        else:
                            pymel.core.setKeyframe( animCurve, f=j*10, v=randValue )
                elif method == 'Sine':
                    pymel.core.setKeyframe( animCurve, f=0,  v= 1 )
                    pymel.core.setKeyframe( animCurve, f=5, v=-1 )
                    pymel.core.setKeyframe( animCurve, f=10, v= 1 )
                
                valueMult = pymel.core.createNode( 'multDoubleLinear' )
                speedMult = pymel.core.createNode( 'multDoubleLinear' )
                intervalMult = pymel.core.createNode( 'multDoubleLinear' )
                inputSum = pymel.core.createNode( 'plusMinusAverage' )
                firstJnt.attr( 'offset%s' %( method ) ) >> inputSum.input1D[0]
                firstJnt.attr( 'move' ) >> speedMult.input1
                firstJnt.attr( 'speed%s%s' %( method, axis ) ) >> speedMult.input2
                speedMult.output >> globalSpeedMult.input2
                globalAllSpeedMult.output >> inputSum.input1D[1]
                intervalMult.input1.set( i )
                firstJnt.attr( 'interval%s' %( method ) ) >> intervalMult.input2
                intervalMult.output >> inputSum.input1D[2]
                inputSum.output1D >> animCurve.input
                animCurve.output >> valueMult.input1
                firstJnt.attr( 'value%s%s' %(method,axis) ) >> valueMult.input2
                
                globalWeightMult = pymel.core.createNode( 'multDoubleLinear' )
                firstJnt.attr( 'all%sWeight' % method ) >> globalWeightMult.input1
                valueMult.output >> globalWeightMult.input2
                globalWeightMult.output >> methodAdd.input1D[methodIndex]
                methodIndex+=1
            
            intervalValueAddPercent = pymel.core.createNode( 'multDoubleLinear' )
            intervalValueAddMult = pymel.core.createNode( 'multDoubleLinear' )
            intervalValueAddAdd  = pymel.core.createNode( 'addDoubleLinear' )
            
            intervalValueAddPercent.input1.set( 0.01 * i )
            firstJnt.attr('intervalValueAdd') >> intervalValueAddPercent.input2
            intervalValueAddPercent.output >> intervalValueAddMult.input1
            globalAllMult.output >> intervalValueAddMult.input2
            globalAllMult.output >>intervalValueAddAdd.input1
            intervalValueAddMult.output >> intervalValueAddAdd.input2
            
            intervalValueAddAdd.output >> joint.attr( 'rotate%s' % axis )
            
            
                


def makeWaveGlobal( inputTopJoints, inputCtl ):
    
    topJoints = []
    for inputTopJoint in inputTopJoints:
        topJoints.append( pymel.core.ls( inputTopJoint )[0] )

    ctl = pymel.core.ls( inputCtl )[0]

    sgCmds.addOptionAttribute( ctl, 'control_offset' )
    sgCmds.addAttr( ctl, ln='offsetGlobalInterval', k=1, dv=1 )
    sgCmds.addAttr( ctl, ln='offsetGlobalRand', k=1, dv=1 )

    attrs = topJoints[0].listAttr( ud=1 )
    sgCmds.addOptionAttribute( ctl, 'wave' )
    for attr in attrs:
        sgCmds.copyAttribute( topJoints[0], ctl, attr.longName() )
    
    circleAttrs = ctl.listAttr( ud=1, k=1 )
    
    for topJoint in topJoints:
        for circleAttr in circleAttrs:
            if not pymel.core.attributeQuery( circleAttr.longName(), node=topJoint, ex=1 ): continue
            circleAttr >> topJoint.attr( circleAttr.longName() )
    
    index = 0
    for topJoint in topJoints:
        offsetRand = pymel.core.createNode( 'multDoubleLinear' )
        offsetInterval = pymel.core.createNode( 'multDoubleLinear' )
        offsetAll = pymel.core.createNode( 'addDoubleLinear' )
        offsetRand.input1.set( random.uniform( -5, 5 ) )
        ctl.attr( 'offsetGlobalRand' ) >> offsetRand.input2
        offsetInterval.input1.set( index )
        ctl.attr( 'offsetGlobalInterval' ) >> offsetInterval.input2
        offsetRand.output >> offsetAll.input1
        offsetInterval.output >> offsetAll.input2
        offsetAll.output >> topJoint.attr( 'offsetSine' )
        index += 1
        allWeightPlug = topJoint.allWeight.listConnections( s=1, d=0, p=1 )[0]
        sgCmds.addAttr( topJoint, ln='globalWeight', min=0, max=1, k=1, dv=1 )
        multGlobal = pymel.core.createNode( 'multDoubleLinear' )
        topJoint.globalWeight >> multGlobal.input1
        allWeightPlug >> multGlobal.input2
        multGlobal.output >> topJoint.allWeight



def createRandomTranslate( inputCtl, inputTarget ):
    
    ctl    = pymel.core.ls( inputCtl )[0]
    target = pymel.core.ls( inputTarget )[0]
    
    sgCmds.addOptionAttribute( ctl, 'translateRandom' )
    sgCmds.addAttr( ctl, ln='move', k=1 )
    sgCmds.addAttr( ctl, ln='speed', k=1, min=0, dv=1 )
    multMove = pymel.core.createNode( 'multDoubleLinear' )
    ctl.attr( 'move' )  >> multMove.input1
    ctl.attr( 'speed' ) >> multMove.input2
    
    for axis in ['X', 'Y', 'Z']:
        animCurve = pymel.core.createNode( 'animCurveUU' )
        animCurve.preInfinity.set( 3 )
        animCurve.postInfinity.set( 3 )
        for j in range( 100 ):
            randValue = random.uniform( -1, 1 )
            if j == 0 or j == 99:
                pymel.core.setKeyframe( animCurve, f=j*10, v=0 )
            else:
                pymel.core.setKeyframe( animCurve, f=j*10, v=randValue )
                print "set rand value : %f" % randValue

        multMove.output >> animCurve.input
        sgCmds.addAttr( ctl, ln='weight_%s' % axis, min=0, dv=0.5, k=1 )
        multWeight = pymel.core.createNode( 'multDoubleLinear' )
        ctl.attr( 'weight_%s' % axis ) >> multWeight.input1
        animCurve.output >> multWeight.input2
        multWeight.output >> target.attr( 'translate%s' % axis )



def makeUdAttrGlobal( inputTargets, inputCtl ):

    targets = []
    for inputTarget in inputTargets:
        targets.append( pymel.core.ls( inputTarget )[0] )

    ctl = pymel.core.ls( inputCtl )[0]

    attrs = targets[0].listAttr( ud=1 )
    for attr in attrs:
        sgCmds.copyAttribute( targets[0], ctl, attr.longName() )
    
    circleAttrs = ctl.listAttr( ud=1, k=1 )
    
    for target in targets:
        for circleAttr in circleAttrs:
            if not pymel.core.attributeQuery( circleAttr.longName(), node=target, ex=1 ): continue
            circleAttr >> target.attr( circleAttr.longName() )



def buildJointLineByVtxNum( mesh, vtxList, numJoints ):
    
    points = OpenMaya.MPointArray()
    
    for vtxIndex in vtxList:
        vtxPos = OpenMaya.MPoint( *cmds.xform( mesh + '.vtx[%d]' % vtxIndex, q=1, ws=1, t=1 )[:3] )
        points.append( vtxPos )
        #print "vtx pos[%d] : %5.3f, %5.3f, %5.3f " %( vtxIndex, vtxPos.x, vtxPos.y, vtxPos.z )
    
    curveData = OpenMaya.MFnNurbsCurveData()
    oData = curveData.create()
    fnCurve = OpenMaya.MFnNurbsCurve()
    
    fnCurve.createWithEditPoints( points, 3, fnCurve.kOpen, False, True, True, oData )
    
    newFnCurve = OpenMaya.MFnNurbsCurve( oData )
    
    eachLength = newFnCurve.length()/numJoints
    parentObj = None
    joints = []
    for i in range( numJoints+1 ):
        paramValue = newFnCurve.findParamFromLength( eachLength * i )
        point = OpenMaya.MPoint()
        newFnCurve.getPointAtParam( paramValue, point )
        
        if not parentObj:
            pymel.core.select( d=1 )
        else:
            pymel.core.select( parentObj )

        joint = pymel.core.joint()
        joints.append( joint )
        pymel.core.move( point.x, point.y, point.z, joint, ws=1 )
        parentObj = joint
    return joints[0]



class ParentedMove:
    
    offsetMatrixAttrName = 'parentedMove_offsetMatrix'
    parentTargetAttrName = 'parentedMove_parentTarget'
    expressionName       = 'ex_ParentedMove'
    
    @staticmethod
    def set( inputChildTarget, inputParentTarget ):
        
        childTarget  = pymel.core.ls( inputChildTarget )[0]
        parentTarget = pymel.core.ls( inputParentTarget )[0]
        
        sgCmds.addAttr( childTarget, ln=ParentedMove.offsetMatrixAttrName, at='matrix' )
        sgCmds.addAttr( childTarget, ln=ParentedMove.parentTargetAttrName, at='message' )
        
        try:parentTarget.message >> childTarget.attr( ParentedMove.parentTargetAttrName )
        except:pass
        
        localMatrix = sgCmds.getMMatrix( childTarget.wm ) * sgCmds.getMMatrix( parentTarget.wim )
        childTarget.attr( ParentedMove.offsetMatrixAttrName ).set( sgCmds.matrixToList( localMatrix ) )
    
    
    @staticmethod
    def reset( inputChildTarget ):
        
        childTarget = pymel.core.ls( inputChildTarget )[0]
        if not pymel.core.attributeQuery( ParentedMove.offsetMatrixAttrName, node=childTarget, ex=1 ) or\
           not pymel.core.attributeQuery( ParentedMove.parentTargetAttrName, node=childTarget, ex=1 ):
            pymel.core.error( "%s is not Parenting Move Object" % childTarget.name() )
        
        parentTargets = childTarget.attr( ParentedMove.parentTargetAttrName ).listConnections( s=1, d=0 )
        if not parentTargets:
            pymel.core.error( "%s is not Parenting Move Object" % childTarget.name() )
        
        localMatrix = sgCmds.getMMatrix( childTarget.wm ) * sgCmds.getMMatrix( parentTargets[0].wim )
        childTarget.attr( ParentedMove.offsetMatrixAttrName ).set( sgCmds.matrixToList( localMatrix ) )

    
    
    @staticmethod
    def run():
        attrs = pymel.core.ls( '*.' + ParentedMove.parentTargetAttrName )
        for attr in attrs:
            node = attr.node()
            parentTarget = attr.listConnections( s=1, d=0 )[0]
            parentMtx = sgCmds.getMMatrix( parentTarget.wm )
            localMtx = sgCmds.getMMatrix( node.attr( ParentedMove.offsetMatrixAttrName ) )
            worldMtxList = sgCmds.matrixToList( localMtx * parentMtx )
            pymel.core.xform( node, ws=1, matrix=worldMtxList )
    
    
    @staticmethod
    def createExpression():
        if pymel.core.ls( ParentedMove.expressionName + '*', type='expression' ): return None
        pymel.core.expression( s="python( \"from sgMaya import sgAnim;sgAnim.ParentedMove.run()\" )",  o="", ae=1, uc='all', n = ParentedMove.expressionName )
    
    
    @staticmethod
    def deleteExpression():
    
        if pymel.core.ls( ParentedMove.expressionName + '*', type='expression' ):
            pymel.core.delete( pymel.core.ls( ParentedMove.expressionName + '*', type='expression' ) )



class NetControlRig:
    
    groupAttrName = 'netControlGroup'
    rowAttrName   = 'netControlRow'
    columnAttrName = 'netControlColumn'
    bigControlAttrName = 'netControlBigTarget'


    def __init__(self, netGroupName ):
        
        self.baseName = netGroupName
        self.numRows = 0
        self.numColumns = 0
        self.targets = []


    def setRows( self, *inputOrderedTargets ):
        
        orderedTargets = [ pymel.core.ls( inputOrderedTarget )[0] for inputOrderedTarget in inputOrderedTargets ]
        for i in range( len( orderedTargets ) ):
            orderedTargets[i].rename( self.baseName + '_%02d' % i )
            sgCmds.addAttr( orderedTargets[i], ln=NetControlRig.groupAttrName, dt='string' )
            orderedTargets[i].attr( NetControlRig.groupAttrName ).set( self.baseName )
            sgCmds.addAttr( orderedTargets[i], ln=NetControlRig.rowAttrName, at='long' )
            orderedTargets[i].attr( NetControlRig.rowAttrName ).set( i )
            self.numRows += 1
            self.targets.append( orderedTargets[i] )


    def setBigConnect( self, *inputBigTargets ):
        
        bigTargets = [ pymel.core.ls( inputBigControl )[0] for inputBigControl in inputBigTargets ]
        
        for i in range( len( bigTargets ) ):
            closeTarget = sgCmds.getClosestTransform( bigTargets[i], self.targets )
            sgCmds.addAttr( closeTarget, ln=NetControlRig.bigControlAttrName, at='message' )
            bigTargets[i].message >> closeTarget.attr( NetControlRig.bigControlAttrName )
    
    
    def setParentContraint(self, circle=False, toParent=False ):
        
        def getBigControl( target ):
            return target.attr( NetControlRig.bigControlAttrName ).listConnections( s=1, d=0 )[0]
        
        if not self.numColumns:
            bigControlIndices = []
            
            for i in range( len( self.targets ) ):
                if not pymel.core.attributeQuery( NetControlRig.bigControlAttrName,
                                                  node = self.targets[i], ex=1 ):
                    continue
                bigControlIndices.append( i )

            for i in range( len( self.targets ) ):
                if toParent:
                    parentTarget = self.targets[i].getParent()
                else:
                    parentTarget = self.targets[i]

                if i in bigControlIndices:
                    bigControl = getBigControl(self.targets[i])
                    pymel.core.parentConstraint( bigControl, parentTarget, mo=1 )
                else:
                    twoSideBigControlsIndices = [None, None]
                    for j in range( len( bigControlIndices ) ):
                        if i < bigControlIndices[j]:
                            if j == 0:
                                if circle:
                                    twoSideBigControlsIndices = [ bigControlIndices[0], bigControlIndices[-1]]
                                else:
                                    twoSideBigControlsIndices = [ bigControlIndices[0], bigControlIndices[0]]
                            else:
                                twoSideBigControlsIndices = [bigControlIndices[j-1],bigControlIndices[j]]
                            break
                    
                    if twoSideBigControlsIndices[0] == None:
                        if circle:
                            twoSideBigControlsIndices = [bigControlIndices[-1], bigControlIndices[0]]
                        else:
                            twoSideBigControlsIndices = [bigControlIndices[-1], bigControlIndices[-1]]
                    
                    twoSideControls = [ getBigControl( self.targets[k] ) for k in twoSideBigControlsIndices ]
                    
                    first  = sgCmds.getMVector( twoSideControls[0] )
                    second = sgCmds.getMVector( twoSideControls[1] )
                    target = sgCmds.getMVector( self.targets[i] )
                    
                    baseVector = second - first
                    targetVector = target - first
                    
                    if baseVector.length() < 0.00001:
                        pymel.core.parentConstraint( twoSideControls[0], parentTarget, mo=1 )
                        continue
                    
                    projTargetToBase = baseVector * ( ( targetVector * baseVector )/baseVector.length()**2 )
                    
                    secondWeight = projTargetToBase.length() / baseVector.length()
                    if secondWeight > 1:
                        secondWeight = 1
                    firstWeight = 1.0 - secondWeight
                    
                    print firstWeight, secondWeight
                    
                    if firstWeight == 0:
                        constraint = pymel.core.parentConstraint( twoSideControls[1], parentTarget, mo=1 )
                    elif secondWeight == 0:
                        constraint = pymel.core.parentConstraint( twoSideControls[0], parentTarget, mo=1 )
                    else:
                        constraint = pymel.core.parentConstraint( twoSideControls[0], twoSideControls[1], parentTarget, mo=1 )
                        constraint.w0.set( firstWeight )
                        constraint.w1.set( secondWeight )
                    
                    
                    
class SplineRig:
    
    def __init__(self, topJoint ):
        
        self.topJoint = pymel.core.ls( topJoint )[0]
        self.jointH = self.topJoint.listRelatives( c=1, ad=1, type='joint' )
        self.jointH.append( self.topJoint )
        self.jointH.reverse()
    
    
    def createSplineCurve(self):
        
        poses = []
        for jnt in self.jointH:
            pos = pymel.core.xform( jnt, q=1, ws=1, t=1 )
            poses.append( pos )
        
        curve = pymel.core.curve( ep=poses, d=3 )
        return curve
    
    
    def assignToCurve(self, inputCurve ):
        
        curve = pymel.core.ls( inputCurve )[0]
        return pymel.core.ikHandle( sj=self.topJoint, ee=self.jointH[-1], sol="ikSplineSolver", ccv=False, pcv=False, curve=curve )[0]
        
        
        


class IkDetailJoint:

    def __init__( self, baseJoint, targetJoint ):
        
        self.baseJoint   = pymel.core.ls( baseJoint )[0]
        self.targetJoint = pymel.core.ls( targetJoint )[0]
        self.joints = []
    
        localMtx = sgCmds.getLocalMatrix( self.targetJoint.wm, self.baseJoint.wim )
        upVectorStart = pymel.core.createNode( 'vectorProduct' ); upVectorStart.op.set( 3 )
        upVectorEnd   = pymel.core.createNode( 'vectorProduct' ); upVectorEnd.op.set( 3 )
        directionIndex = sgCmds.getDirectionIndex( [localMtx.o.get().a30, localMtx.o.get().a31, localMtx.o.get().a32] )
        upVector = sgCmds.getVectorList()[(directionIndex+1)%6]
        upVectorStart.input1.set( upVector )
        upVectorEnd.input1.set( upVector )
        localMtx.o >> upVectorEnd.matrix
        
        self.aimIndex = ( directionIndex ) % 3
        self.upIndex  = ( directionIndex + 1 ) % 3
        self.crossIndex = ( directionIndex + 2 ) % 3
        self.upVectorStart = upVectorStart
        self.upVectorEnd   = upVectorEnd
        self.reverseVector = False
        if directionIndex >= 3:
            self.reverseVector = True


    def makeCurve(self):
        
        crvGrp = pymel.core.createNode( 'transform', n='CrvGrp_'+self.baseJoint )
        crv = pymel.core.curve( p=[[0,0,0],[0,0,0]], n='Crv_'+self.baseJoint, d=1 )
        crv.setParent( crvGrp )
        dcmp = sgCmds.getLocalDecomposeMatrix( self.targetJoint.wm, self.baseJoint.wim )
        dcmp.ot >> crv.getShape().controlPoints[1]
        sgCmds.constrain_all( self.baseJoint, crvGrp )
        self.baseGrp = crvGrp
        self.curve = crv



    def addJointAtParam(self, paramValue ):
        
        pointOnCurveInfo = pymel.core.createNode( 'pointOnCurveInfo' )
        self.curve.getShape().local >> pointOnCurveInfo.inputCurve
        pointOnCurveInfo.top.set( 1 )
        pymel.core.select( self.baseGrp )
        newJoint = pymel.core.joint()
        sgCmds.addAttr( newJoint, ln='param', min=0, max=1, dv=paramValue, k=1 )
        newJoint.attr( 'param' ) >> pointOnCurveInfo.parameter
        
        fbfMtx = pymel.core.createNode( 'fourByFourMatrix' )
        
        def getMultVector( outputAttr, reverse ):
            multVector = pymel.core.createNode( 'multiplyDivide' )
            outputAttr >> multVector.input1
            if reverse:
                multVector.input2.set( -1, -1, -1 )
            else:
                multVector.input2.set( 1,1,1 )
            return multVector
        
        aimMultVector = getMultVector( pointOnCurveInfo.tangent, self.reverseVector )
        
        aimMultVector.outputX >> fbfMtx.attr( 'in%d0' % self.aimIndex )
        aimMultVector.outputY >> fbfMtx.attr( 'in%d1' % self.aimIndex )
        aimMultVector.outputZ >> fbfMtx.attr( 'in%d2' % self.aimIndex )   
        
        blendColor = pymel.core.createNode( 'blendColors' )
        self.upVectorEnd.output >> blendColor.color1
        self.upVectorStart.output >> blendColor.color2
        newJoint.param >> blendColor.blender
        
        upMultVector = getMultVector( blendColor.output, self.reverseVector )
        
        upMultVector.outputX >> fbfMtx.attr( 'in%d0' % self.upIndex )
        upMultVector.outputY >> fbfMtx.attr( 'in%d1' % self.upIndex )
        upMultVector.outputZ >> fbfMtx.attr( 'in%d2' % self.upIndex )
        
        print self.aimIndex, self.upIndex, self.crossIndex
        
        crossVector = sgCmds.getCrossVectorNode( aimMultVector.output, upMultVector.output )
        
        crossVector.outputX >> fbfMtx.attr( 'in%d0' % self.crossIndex )
        crossVector.outputY >> fbfMtx.attr( 'in%d1' % self.crossIndex )
        crossVector.outputZ >> fbfMtx.attr( 'in%d2' % self.crossIndex )
        
        pointOnCurveInfo.positionX >> fbfMtx.in30
        pointOnCurveInfo.positionY >> fbfMtx.in31
        pointOnCurveInfo.positionZ >> fbfMtx.in32
        
        dcmp = sgCmds.getDecomposeMatrix( fbfMtx.output )
        dcmp.ot >> newJoint.t
        dcmp.outputRotate >> newJoint.r
        
        self.joints.append( newJoint )
    
    
    def renameJoints(self, name ):
        
        for i in range( len( self.joints ) ):
            self.joints[i].rename( name + '_%02d' % i )
            
            
        
        

def chainRig( mesh, curve, upObject, upVector, percentOfSpaceOfBlock=0.0, randomOffsetPercent=0 ):
    
    from maya import mel
    
    pymel.core.select( mesh )
    mel.eval( 'CenterPivot' )
    
    pivotMatrix = sgCmds.getPivotWorldMatrix( mesh )
    sgCmds.setPivotZero( mesh )
    sgCmds.setMatrixToTarget( pivotMatrix, mesh, pcp=1 )
    
    def getMeshStartAndEndPoint( mesh, curve ):
        param = sgCmds.getClosestParamAtPoint( mesh, curve )
        direction = sgCmds.getTangentAtParam( curve, param )
        localDirection = sgCmds.getMVector(direction) * sgCmds.listToMatrix( mesh.wim.get() )
        directionIndex = sgCmds.getDirectionIndex( localDirection )
        
        meshChildren = mesh.listRelatives( c=1 )
        bbmin = [10000000,10000000,1000000]
        bbmax = [-10000000,-10000000,-10000000]
        for child in meshChildren:
            cbbmin = child.attr( 'boundingBoxMin' ).get()
            cbbmax = child.attr( 'boundingBoxMax' ).get()
            for i in range( 3 ):
                bbmin[i] = min( bbmin[i], cbbmin[i] )
                bbmax[i] = max( bbmax[i], cbbmax[i] )
            
        meshStartPoint = [ 0,0,0 ]
        meshEndPoint = [ 0,0,0 ]
        meshStartPoint[ directionIndex%3 ] = bbmin[directionIndex%3]
        meshEndPoint[ directionIndex%3 ] = bbmax[directionIndex%3]
        meshStartPoint = sgCmds.getMPoint(meshStartPoint) * sgCmds.listToMatrix( mesh.wm.get() )
        meshEndPoint = sgCmds.getMPoint(meshEndPoint) * sgCmds.listToMatrix( mesh.wm.get() )
        return meshStartPoint, meshEndPoint, directionIndex
    
    paramMinValue = curve.getShape().minValue.get()
    paramMaxValue = curve.getShape().maxValue.get()
    
    startPoint, endPoint,  dirIndex = getMeshStartAndEndPoint( mesh, curve )
    direction = sgCmds.getVectorList()[dirIndex]
    param   = sgCmds.getClosestParamAtPoint( mesh, curve )
    closePoint = sgCmds.getPointAtParam( curve, param )
    tangent = sgCmds.getTangentAtParam( curve, param )
    
    startTr = pymel.core.createNode( 'transform' )
    rot = pymel.core.angleBetween( v1=direction, v2=[tangent.x, tangent.y, tangent.z], euler=1 )
    startTr.t.set( closePoint )
    startTr.r.set( rot )
    
    if mesh.getShape():
        sgCmds.setGeometryMatrixToTarget( mesh, startTr )
    else:
        sgCmds.setMatrixToTarget( startTr.wm.get(), mesh, pcp=1 )
    pymel.core.delete( startTr )
    
    curveLength = sgCmds.getCurveLength( curve )
    
    sizeOfBlock = startPoint.distanceTo( endPoint )
    spaceOfBlock = sizeOfBlock * percentOfSpaceOfBlock
    
    numBlock = int( curveLength/(sizeOfBlock + spaceOfBlock) )
    elseSpace = curveLength - ( sizeOfBlock + spaceOfBlock ) * numBlock
    
    spaceOfBlock += elseSpace / numBlock
    
    blockLength = ( spaceOfBlock + sizeOfBlock )
    eachParamLengthOfBlock = blockLength / curveLength * (paramMaxValue-paramMinValue)
    
    mainGrp = pymel.core.createNode( 'transform' )
    sgCmds.addAttr( mainGrp, ln='param', k=1 )
    
    duMeshPointers = []
    duMeshs = []
    
    for i in range( numBlock ):
        duMesh = pymel.core.duplicate( mesh )[0]
        if mesh.getShape():
            mesh.getShape().outMesh >> duMesh.getShape().inMesh
            sgCmds.copyShader( mesh, duMesh )
        randomOffset = random.uniform( -randomOffsetPercent*blockLength/2, randomOffsetPercent*blockLength/2 )
        duMesh.addAttr( 'offset', k=1, dv= randomOffset )
        
        duMeshPointer = pymel.core.createNode( 'transform' )
        pymel.core.xform( duMeshPointer, ws=1, matrix= duMesh.wm.get() )
        
        animCurve = pymel.core.createNode( 'animCurveUU' )
        animCurve.attr( 'preInfinity' ).set( 3 )
        animCurve.attr( 'postInfinity').set( 3 )

        offsetAdd = pymel.core.createNode( 'addDoubleLinear' )
        paramAdd = pymel.core.createNode( 'addDoubleLinear' )
        paramMult = pymel.core.createNode( 'multDoubleLinear' )
        mainGrp.attr( 'param' ) >> offsetAdd.input1
        duMesh.attr( 'offset' ) >> offsetAdd.input2
        offsetAdd.output >> paramMult.input1
        paramMult.input2.set( (paramMaxValue-paramMinValue)/curveLength )
        paramMult.output >> paramAdd.input1
        paramAdd.input2.set( eachParamLengthOfBlock * i + paramMinValue )
        paramAdd.output >> animCurve.input

        pymel.core.setKeyframe( animCurve, f=paramMinValue, v = paramMinValue )
        pymel.core.setKeyframe( animCurve, f=paramMaxValue, v = paramMaxValue )
        pymel.core.keyTangent( animCurve, itt='linear', ott='linear' )
        
        sgCmds.attachToCurve( duMeshPointer, curve )
        animCurve.output >> duMeshPointer.param
        sgCmds.constrain_parent( duMeshPointer, duMesh )
        duMeshPointers.append( duMeshPointer )
        duMeshs.append( duMesh )
        
        pymel.core.tangentConstraint( curve, duMeshPointer, aim=direction, u=upVector, wu=upVector, wut='objectrotation', wuo=upObject)
    
    pointersGrp   = pymel.core.group( duMeshPointers, n='conveyer_pointersGrp' )
    duMeshsGrp    = pymel.core.group( duMeshs, n='conveyer_duMeshsGrp' )
    mesh.v.set( 0 ); upObject.v.set( 0 ); pointersGrp.v.set( 0 );curve.v.set( 0 )
    pymel.core.parent( mesh, curve, upObject, pointersGrp, duMeshsGrp, mainGrp )
    pymel.core.select( mainGrp )
    
    


def conveyerBeltRig( mesh, curve, percentOfSpaceOfBlock=0.0 ):
    
    def getMeshStartAndEndPoint( mesh, curve ):
        param = sgCmds.getClosestParamAtPoint( mesh, curve )
        direction = sgCmds.getTangentAtParam( curve, param )
        localDirection = sgCmds.getMVector(direction) * sgCmds.listToMatrix( mesh.wim.get() )
        directionIndex = sgCmds.getDirectionIndex( localDirection )
        meshShape = sgCmds.getShape( mesh )
        bbmin = meshShape.attr( 'boundingBoxMin' ).get()
        bbmax = meshShape.attr( 'boundingBoxMax' ).get()
        meshStartPoint = [ 0,0,0 ]
        meshEndPoint = [ 0,0,0 ]
        meshStartPoint[ directionIndex%3 ] = bbmin[directionIndex%3]
        meshEndPoint[ directionIndex%3 ] = bbmax[directionIndex%3]
        meshStartPoint = sgCmds.getMPoint(meshStartPoint) * sgCmds.listToMatrix( mesh.wm.get() )
        meshEndPoint = sgCmds.getMPoint(meshEndPoint) * sgCmds.listToMatrix( mesh.wm.get() )
        return meshStartPoint, meshEndPoint, sgCmds.getVectorList()[directionIndex]
    
    paramMinValue = curve.getShape().minValue.get()
    paramMaxValue = curve.getShape().maxValue.get()
    
    startPoint, endPoint, direction = getMeshStartAndEndPoint( mesh, curve )
    param   = sgCmds.getClosestParamAtPoint( mesh, curve )
    tangent = sgCmds.getTangentAtParam( curve, param )    
    
    paramStartPoint = sgCmds.getClosestParamAtPoint( startPoint, curve )
    paramEndPoint   = sgCmds.getClosestParamAtPoint( endPoint, curve )
    sp = sgCmds.getPointAtParam( curve, paramStartPoint )
    ep = sgCmds.getPointAtParam( curve, paramEndPoint )
    startTr = pymel.core.createNode( 'transform', n='startTr' ); startTr.t.set( sp )
    endTr   = pymel.core.createNode( 'transform', n='endTr' ); endTr.t.set( ep )
    sgCmds.lookAt( endTr, startTr, direction )
    
    if mesh.getShape():
        sgCmds.setGeometryMatrixToTarget( mesh, startTr )
    else:
        sgCmds.setMatrixToTarget( mesh, startTr, pcp=1 )
    curveLength = sgCmds.getCurveLength( curve )
    
    sizeOfBlock = OpenMaya.MPoint( *pymel.core.xform( endTr, q=1, ws=1, t=1 ) ).distanceTo( OpenMaya.MPoint( *pymel.core.xform( startTr, q=1, ws=1, t=1 ) ) )
    spaceOfBlock = sizeOfBlock * percentOfSpaceOfBlock 
    
    numBlock = int( curveLength/(sizeOfBlock + spaceOfBlock) )
    elseSpace = curveLength - ( sizeOfBlock + spaceOfBlock ) * numBlock
    
    spaceOfBlock += elseSpace / numBlock
    
    eachParamLengthOfBlock = ( spaceOfBlock + sizeOfBlock ) / curveLength * (paramMaxValue-paramMinValue)
    
    mainGrp = pymel.core.createNode( 'transform' )
    sgCmds.addAttr( mainGrp, ln='param', k=1 )
    
    duMeshPointers = []
    duMeshs = []
    
    for i in range( numBlock+1 ):
        duMesh = pymel.core.duplicate( mesh )[0]
        mesh.getShape().outMesh >> duMesh.getShape().inMesh
        sgCmds.copyShader( mesh, duMesh )
        
        duMeshPointer = pymel.core.createNode( 'transform' )
        pymel.core.xform( duMeshPointer, ws=1, matrix= duMesh.wm.get() )
        
        animCurve = pymel.core.createNode( 'animCurveUU' )
        animCurve.attr( 'preInfinity' ).set( 3 )
        animCurve.attr( 'postInfinity').set( 3 )

        offsetAdd = pymel.core.createNode( 'addDoubleLinear' )
        offsetMult = pymel.core.createNode( 'multDoubleLinear' )
        mainGrp.attr( 'param' ) >> offsetMult.input1
        offsetMult.input2.set( (paramMaxValue-paramMinValue)/curveLength )
        offsetMult.output >> offsetAdd.input1
        offsetAdd.input2.set( eachParamLengthOfBlock * i + paramMinValue )
        offsetAdd.output >> animCurve.input

        pymel.core.setKeyframe( animCurve, f=paramMinValue, v = paramMinValue )
        pymel.core.setKeyframe( animCurve, f=paramMaxValue, v = paramMaxValue )
        pymel.core.keyTangent( animCurve, itt='linear', ott='linear' )
        
        sgCmds.attachToCurve( duMeshPointer, curve )
        animCurve.output >> duMeshPointer.param
        
        sgCmds.makeParent( duMeshPointer )
        sgCmds.constrain_parent( duMeshPointer, duMesh )
        duMeshPointers.append( duMeshPointer )
        duMeshs.append( duMesh )
    
    for i in range( numBlock ):
        sgCmds.lookAtConnect( duMeshPointers[(i+1)%(numBlock+1)], duMeshPointers[i], direction=tangent )
    pymel.core.delete( duMeshs[-1] )
    
    duMeshGrp    = pymel.core.group( duMeshs, n='conveyer_meshs' )
    duPointerGrp = pymel.core.group( duMeshPointers, n='conveyer_pointers' )




def conveyerBeltRig_deform( mesh, curve, upObject, upVector, numDetail=4 ):
    
    if numDetail < 3: numDetail = 3
    
    def editGeometryTransform( mesh, curve ):
        meshMtx = sgCmds.getPivotWorldMatrix( mesh )
        sgCmds.setGeometryMatrixToTarget( mesh, meshMtx )
        newTr = sgCmds.createNearestPointOnCurveObject( mesh, curve )
        newTrPos = newTr.t.get()
        pymel.core.delete( newTr )
        setMtx = sgCmds.matrixToList( meshMtx )
        setMtx = setMtx[:-4] + [newTrPos[0],newTrPos[1],newTrPos[2]] + [1]
        sgCmds.setGeometryMatrixToTarget( mesh, setMtx ) 
    
    editGeometryTransform( mesh, curve )
    
    curveLength = sgCmds.getCurveLength( curve )
    meshBB = pymel.core.exactWorldBoundingBox( mesh )
    bbmin = meshBB[:3]
    bbmax = meshBB[3:]
    
    sizeX = bbmax[0]-bbmin[0]
    sizeY = bbmax[1]-bbmin[1]
    sizeZ = bbmax[2]-bbmin[2]
    
    size = [ sizeX, sizeY, sizeZ ]
    
    closeParam = sgCmds.getClosestParamAtPoint( mesh, curve )
    paramMinValue = curve.getShape().minValue.get()
    paramMaxValue = curve.getShape().maxValue.get()
    
    tangent = sgCmds.getTangentAtParam( curve, closeParam )
    directionIndex = sgCmds.getDirectionIndex( tangent )
    
    sizeOfBlock = size[ directionIndex%3 ]
    spaceOfEachBlock = sizeOfBlock * 0.02
    
    numBlock = int( curveLength/(sizeOfBlock + spaceOfEachBlock) )
    elseSpace = curveLength - ( sizeOfBlock + spaceOfEachBlock ) * numBlock
    
    spaceOfEachBlock += elseSpace / numBlock
    
    eachParamLengthOfBlock = ( spaceOfEachBlock + sizeOfBlock ) / curveLength * (paramMaxValue-paramMinValue)
    
    mainGrp = pymel.core.createNode( 'transform', n='conveyer_allGrp' )
    sgCmds.addAttr( mainGrp, ln='param', k=1 )
    
    eachCurves = []
    baseCurves = []
    pointers = []
    duMeshs = []
    localMeshs = []
    for i in range( numBlock ):
        duMesh = pymel.core.duplicate( mesh )[0]
        mesh.getShape().outMesh >> duMesh.getShape().inMesh
        localOutMesh = pymel.core.duplicate( mesh )[0]
        duMesh.getShape().outMesh >> localOutMesh.inMesh
        
        offsetMin = -eachParamLengthOfBlock/2
        offsetMax =  eachParamLengthOfBlock/2
        
        eachPointers = []
        for j in range( numDetail ):
            addOffsetValue = ((offsetMax - offsetMin) / (numDetail-1)) * j + offsetMin
            
            animCurve = pymel.core.createNode( 'animCurveUU' )
            animCurve.attr( 'preInfinity' ).set( 3 )
            animCurve.attr( 'postInfinity').set( 3 )
    
            offsetAdd = pymel.core.createNode( 'addDoubleLinear' )
            offsetMult = pymel.core.createNode( 'multDoubleLinear' )
            mainGrp.attr( 'param' ) >> offsetMult.input1
            offsetMult.input2.set( (paramMaxValue-paramMinValue)/curveLength )
            offsetMult.output >> offsetAdd.input1
            offsetAdd.input2.set( eachParamLengthOfBlock * i + addOffsetValue + paramMinValue )
            offsetAdd.output >> animCurve.input
    
            pymel.core.setKeyframe( animCurve, f=paramMinValue, v = paramMinValue )
            pymel.core.setKeyframe( animCurve, f=paramMaxValue, v = paramMaxValue )
            pymel.core.keyTangent( animCurve, itt='linear', ott='linear' )
        
            pointer = pymel.core.createNode( 'transform' )
            sgCmds.attachToCurve( pointer, curve )
            animCurve.output >> pointer.param
            eachPointers.append( pointer )
        pointers += eachPointers

        eachCurve = sgCmds.makeCurveFromSelection( *eachPointers, d=2 )
        mainGrp.attr( 'param' ).set( (closeParam - eachParamLengthOfBlock * i + paramMinValue) * curveLength )
        wireNode = pymel.core.wire( duMesh, gw=False, en=1, ce=0, li=0, w=eachCurve, dds=[0,100000] )[0]
        baseCurve = wireNode.attr( 'baseWire' ).listConnections( s=1, d=0 )[0]
        
        eachCurves.append( eachCurve )
        baseCurves.append( baseCurve )
        duMeshs.append( duMesh )
        localMeshs.append( localOutMesh )
        
        pymel.core.refresh()
    
    eachCurveGrp  = pymel.core.group( eachCurves, n='conveyer_eachCurvesGrp' )
    baseCurveGrp  = pymel.core.group( baseCurves, n='conveyer_baseCurvesGrp' )
    pointersGrp   = pymel.core.group( pointers, n='conveyer_pointersGrp' )
    duMeshsGrp    = pymel.core.group( duMeshs, n='conveyer_duMeshsGrp' )
    localMeshsGrp = pymel.core.group( localMeshs, n='conveyer_localMeshsGrp' )
    mesh.v.set( 0 ); upObject.v.set( 0 ); eachCurveGrp.v.set( 0 ); baseCurveGrp.v.set( 0 ); pointersGrp.v.set( 0 ); duMeshsGrp.v.set( 0 );curve.v.set( 0 )
    pymel.core.parent( mesh, curve, upObject, eachCurveGrp, baseCurveGrp, pointersGrp, duMeshsGrp, localMeshsGrp, mainGrp )
    pymel.core.select( mainGrp )
    
    


def createDefaultPropRig( propGrp ):
    
    propGrp = pymel.core.ls( propGrp )[0]
    
    def makeParent( target ):
        targetP = pymel.core.createNode( 'transform' )
        pymel.core.xform( targetP, ws=1, matrix= target.wm.get() )
        pymel.core.parent( target, targetP )
        targetP.rename( 'P' + target.shortName() )
        return targetP
    
    worldCtl = pymel.core.ls( sgCmds.makeController( sgModel.Controller.circlePoints ).name() )[0]
    moveCtl  = pymel.core.ls( sgCmds.makeController( sgModel.Controller.crossPoints ).name() )[0]
    rootCtl  = pymel.core.ls( sgCmds.makeController( sgModel.Controller.circlePoints ).name() )[0]
    
    bb = cmds.exactWorldBoundingBox(propGrp.name())
    bbmin = bb[:3]
    bbmax = bb[3:]
    
    bbsize = max( bbmax[0] - bbmin[0], bbmax[2] - bbmin[2] )/2
    
    center     = ( ( bbmin[0] + bbmax[0] )/2, ( bbmin[1] + bbmax[1] )/2, ( bbmin[2] + bbmax[2] )/2 )
    floorPoint = ( ( bbmin[0] + bbmax[0] )/2, bbmin[1], ( bbmin[2] + bbmax[2] )/2 )
    
    worldCtl.t.set( *floorPoint )
    moveCtl.t.set( *floorPoint )
    rootCtl.t.set( *center )
    
    rootCtl.shape_sx.set( bbsize*1.2 )
    rootCtl.shape_sy.set( bbsize*1.2 )
    rootCtl.shape_sz.set( bbsize*1.2 )

    moveCtl.shape_sx.set( bbsize*1.3 )
    moveCtl.shape_sy.set( bbsize*1.3 )
    moveCtl.shape_sz.set( bbsize*1.3 )
    
    worldCtl.shape_sx.set( bbsize*1.5 )
    worldCtl.shape_sy.set( bbsize*1.5 )
    worldCtl.shape_sz.set( bbsize*1.5 )
    
    rootCtl.getShape().setAttr( 'overrideEnabled', 1 )
    rootCtl.getShape().setAttr( 'overrideColor', 29 )
    moveCtl.getShape().setAttr( 'overrideEnabled', 1 )
    moveCtl.getShape().setAttr( 'overrideColor', 20 )
    worldCtl.getShape().setAttr( 'overrideEnabled', 1 )
    worldCtl.getShape().setAttr( 'overrideColor', 17 )
    
    shortName = propGrp.shortName().split( '|' )[-1]
    rootCtl.rename( 'Ctl_%s_Root' % shortName )
    moveCtl.rename( 'Ctl_%s_Move' % shortName )
    worldCtl.rename( 'Ctl_%s_World' % shortName )
    
    pRootCtl  = makeParent( rootCtl )
    pMoveCtl  = makeParent( moveCtl )
    pWorldCtl = makeParent( worldCtl )
    
    pymel.core.parent( pRootCtl, moveCtl )
    pymel.core.parent( pMoveCtl, worldCtl )

    sgCmds.setMatrixToGeoGroup( rootCtl.wm.get(), propGrp.name() )
    sgCmds.constrain_all( rootCtl, propGrp )


    

def createSimplePlaneControl( inputTarget ):
    
    target = pymel.core.ls( inputTarget )[0]
    worldCtl = sgCmds.makeController( sgModel.Controller.cubePoints, makeParent=1 )
    
    bb = cmds.exactWorldBoundingBox(target.name())
    bbmin = bb[:3]
    bbmax = bb[3:]
    
    bbsize = max( bbmax[0] - bbmin[0], bbmax[2] - bbmin[2] )/2
    
    center     = ( ( bbmin[0] + bbmax[0] )/2, ( bbmin[1] + bbmax[1] )/2, ( bbmin[2] + bbmax[2] )/2 )
    floorPoint = ( ( bbmin[0] + bbmax[0] )/2, bbmin[1], ( bbmin[2] + bbmax[2] )/2 )
    
    worldCtl.t.set( *floorPoint )
    worldCtlShape = worldCtl.getShape()
    worldCtlShape.shape_sx.set( bbsize*1.2*2 )
    worldCtlShape.shape_sy.set( max((bbmax[1] - bbmin[1]), bbsize * 0.02 )*1.2*2 )
    worldCtlShape.shape_sz.set( bbsize*1.2*2 )
    
    worldCtlShape.setAttr( 'overrideEnabled', 1 )
    worldCtlShape.setAttr( 'overrideColor', 17 )
    
    worldCtl.rename( 'Ctl_World' )
    targetChildren = pymel.core.listRelatives( target, c=1, ad=1, type='transform' )
    if not targetChildren: targetChildren = []
    targetChildren += [target]
    for targetChild in targetChildren:
        if not targetChild.getShape(): continue
        sgCmds.optimizeMesh( targetChild )
    sgCmds.setMatrixToTarget( worldCtl.wm.get(), target, pcp=1  )
    sgCmds.setPivotZero( target )
    sgCmds.constrain_all( worldCtl, target )




def makeLookAtSquashTransform( lookObject, baseObject, lookParentObject=None, baseParentObject=None, size=1 ):

    if not lookParentObject:
        lookParentObject = pymel.core.ls( lookObject )[0].getParent()
    if not baseParentObject:
        baseParentObject = pymel.core.ls( baseObject )[0].getParent()
        if not baseParentObject:
            baseParentObject = baseObject

    dcmpBase   = sgCmds.getDecomposeMatrix( sgCmds.getMultMatrix( lookParentObject + '.wm', baseParentObject + '.wim' ).o )
    dcmpSquash = sgCmds.getDecomposeMatrix( sgCmds.getMultMatrix( lookObject + '.wm', baseObject + '.wim' ).o )
    directionIndex = sgCmds.getDirectionIndex( dcmpBase.ot.get() )

    lookAtChild = sgCmds.makeLookAtChild( lookObject, baseObject )
    lookAtChild.rename( 'lookAtChild_' + baseObject )
    squashTransform = sgCmds.makeChild( lookAtChild, 'null' )
    squashTransform.rename( 'squashTr_' + baseObject )
    squashCenter = sgCmds.makeChild( squashTransform )
    sgCmds.addAttr( squashCenter, ln='positionParam', min=0, max=1, dv=0.5, k=1 )
    
    sgCmds.createControllerShape( sgModel.Controller.diamondPoints,squashCenter, size )
    centerTrMult = pymel.core.createNode( 'multiplyDivide' )
    dcmpBase.attr( ['otx', 'oty', 'otz'][ (directionIndex) % 3 ] ) >> centerTrMult.attr( ['input1X', 'input1Y', 'input1Z'][ (directionIndex) % 3 ] )
    squashCenter.attr( 'positionParam' ) >> centerTrMult.input2X
    squashCenter.attr( 'positionParam' ) >> centerTrMult.input2Y
    squashCenter.attr( 'positionParam' ) >> centerTrMult.input2Z
    centerTrMult.output >> squashCenter.t
    
    distBase   = sgCmds.getDistance( dcmpBase )
    distSquash = sgCmds.getDistance( dcmpSquash )
    
    scaleNode = pymel.core.createNode( 'multiplyDivide' )
    distSquash.distance >> scaleNode.input1X
    distBase.distance   >> scaleNode.input2X
    scaleNode.op.set( 2 )
    
    
    scaleNode.outputX >> squashTransform.attr( ['sx', 'sy', 'sz'][ directionIndex % 3 ] )
    
    sgCmds.addOptionAttribute( lookObject )
    sgCmds.addAttr( lookObject, ln='squash', k=1, dv=1 )
    
    squashAttr = sgCmds.createSquashAttr( scaleNode.outputX, lookObject + '.squash' )
    squashAttr >> squashTransform.attr( ['sx', 'sy', 'sz'][ (directionIndex+1) % 3 ] )
    squashAttr >> squashTransform.attr( ['sx', 'sy', 'sz'][ (directionIndex+2) % 3 ] )
    
    return squashCenter




def makeLookAtSquashBendTransform( lookObject, baseObject, lookParentObject=None, size=1 ):

    if not lookParentObject:
        lookParentObject = pymel.core.ls( lookObject )[0].getParent()

    dcmpBase   = sgCmds.getDecomposeMatrix( sgCmds.getMultMatrix( lookParentObject + '.wm', baseObject + '.wim' ).o )
    dcmpSquash = sgCmds.getDecomposeMatrix( sgCmds.getMultMatrix( lookObject + '.wm', baseObject + '.wim' ).o )
    directionIndex = sgCmds.getDirectionIndex( dcmpBase.ot.get() )

    centerBaseObject = sgCmds.makeChild( baseObject )
    centerBaseObject.rename( 'centerBase_' + baseObject )
    sgCmds.addAttr( centerBaseObject, ln='positionParam', min=0, max=1, dv=0.5, k=1 )
    multCenterNode = pymel.core.createNode( 'multiplyDivide' )
    dcmpSquash.attr( ['otx', 'oty', 'otz'][ (directionIndex) % 3 ] ) >> multCenterNode.attr( ['input1X', 'input1Y', 'input1Z'][ (directionIndex) % 3 ] )
    centerBaseObject.attr( 'positionParam' ) >> multCenterNode.attr('input2X')
    centerBaseObject.attr( 'positionParam' ) >> multCenterNode.attr('input2Y')
    centerBaseObject.attr( 'positionParam' ) >> multCenterNode.attr('input2Z')
    multCenterNode.output >> centerBaseObject.t

    lookAtChild = sgCmds.makeLookAtChild( lookObject, centerBaseObject )
    lookAtChild.rename( 'lookAtChild_' + centerBaseObject )
    squashTransform = sgCmds.makeChild( lookAtChild, 'null' )
    squashTransform.rename( 'squashTr_' + centerBaseObject )
    
    sgCmds.createControllerShape( sgModel.Controller.diamondPoints,squashTransform, size )
    
    distBase   = sgCmds.getDistance( dcmpBase )
    distSquash = sgCmds.getDistance( dcmpSquash )
    
    scaleNode = pymel.core.createNode( 'multiplyDivide' )
    distSquash.distance >> scaleNode.input1X
    distBase.distance   >> scaleNode.input2X
    scaleNode.op.set( 2 )
    
    scaleNode.outputX >> squashTransform.attr( ['sx', 'sy', 'sz'][ directionIndex % 3 ] )
    
    sgCmds.addOptionAttribute( lookObject )
    sgCmds.addAttr( lookObject, ln='squash', k=1, dv=1 )
    
    squashAttr = sgCmds.createSquashAttr( scaleNode.outputX, lookObject + '.squash' )
    squashAttr >> squashTransform.attr( ['sx', 'sy', 'sz'][ (directionIndex+1) % 3 ] )
    squashAttr >> squashTransform.attr( ['sx', 'sy', 'sz'][ (directionIndex+2) % 3 ] )
    
    return centerBaseObject
    
    
    
    
def createMatrixObjectFromGeo( target, directionBasedGeo=False ):
    
    targetShapes = pymel.core.listRelatives( target, c=1, ad=1, type='mesh' )
    
    if directionBasedGeo:
        vectorDicts = {}
        xBaseVector = OpenMaya.MVector( 1,0,0 )
        yBaseVector = OpenMaya.MVector( 0,1,0 )
        zBaseVector = OpenMaya.MVector( 0,0,1 )
        
        for targetShape in targetShapes:
            dagPathMesh = sgCmds.getDagPath(targetShape)
            fnMesh = OpenMaya.MFnMesh( dagPathMesh )
            
            points = OpenMaya.MPointArray()
            fnMesh.getPoints( points, OpenMaya.MSpace.kWorld )
            
            for i in range( fnMesh.numEdges() ):
                util = OpenMaya.MScriptUtil()
                util.createFromList([0,0],2)
                int2Ptr = util.asInt2Ptr()
                fnMesh.getEdgeVertices( i, int2Ptr )
                index1 = util.getInt2ArrayItem( int2Ptr, 0, 0 )
                index2 = util.getInt2ArrayItem( int2Ptr, 0, 1 )
                
                point1 = points[ index1 ]
                point2 = points[ index2 ]
                
                vector = point2 - point1
                
                dotX = math.fabs( xBaseVector * vector )
                dotY = math.fabs( yBaseVector * vector )
                dotZ = math.fabs( zBaseVector * vector )
                
                if dotY == max( [ dotX, dotY, dotZ ] ):
                    continue
                
                if dotX > dotZ:
                    convertedVector = vector if xBaseVector * vector > 0 else -vector
                elif dotZ >= dotX:
                    convertedVector = vector if zBaseVector * vector > 0 else -vector
                
                key = "%.2f,%.2f,%.2f" %( convertedVector.x, convertedVector.y, convertedVector.z )
                if not vectorDicts.has_key( key ):
                    vectorDicts[ key ] = { "value":[convertedVector.x, 0, convertedVector.z], "length":convertedVector.length()}
                else:
                    vectorDicts[ key ]['length'] += convertedVector.length()
                    vectorDicts[ key ]['value'][0] +=  convertedVector.x
                    vectorDicts[ key ]['value'][1] +=  0
                    vectorDicts[ key ]['value'][2] +=  convertedVector.z
            
        maxLength = 0.0
        maxLengthKey = None
        for key in vectorDicts.keys():
            if maxLength < vectorDicts[ key ]['length']:
                maxLength = vectorDicts[ key ]['length']
                maxLengthKey = key
        
        horizonVector = OpenMaya.MVector( *vectorDicts[ maxLengthKey ][ 'value' ] ).normal()
        upVector      = OpenMaya.MVector( 0,1,0 )
        
        dotX = math.fabs( xBaseVector * horizonVector )
        dotZ = math.fabs( zBaseVector * horizonVector )
        
        if dotX > dotZ:
            xVector = horizonVector
            yVector = upVector
            zVector = horizonVector ^ upVector
        else:
            xVector = horizonVector
            yVector = upVector
            zVector = upVector ^ horizonVector
    else:
        xVector = OpenMaya.MVector( 1,0,0 )
        yVector = OpenMaya.MVector( 0,1,0 )
        zVector = OpenMaya.MVector( 0,0,1 )
    
    worldPivot = pymel.core.xform( target, q=1, ws=1, rotatePivot=1 )
    mtxList = [xVector.x, xVector.y, xVector.z,0, yVector.x, yVector.y, yVector.z,0, zVector.x, zVector.y, zVector.z,0, worldPivot[0],worldPivot[1],worldPivot[2],1]
    mtx = sgCmds.listToMatrix( mtxList )
    invMtx = mtx.inverse()
    
    bb = OpenMaya.MBoundingBox()
    
    pointsList = []
    for targetShape in targetShapes:
        dagPathMesh = sgCmds.getDagPath(targetShape)
        fnMesh = OpenMaya.MFnMesh( dagPathMesh )
        
        points = OpenMaya.MPointArray()
        fnMesh.getPoints( points, OpenMaya.MSpace.kWorld )
        pointsList.append( points )
    
    for points in pointsList:
        for i in range( points.length() ):
            bb.expand( points[i] * invMtx )
        
    bbCenter = bb.center() * mtx
    mtxList[12] = bbCenter.x;mtxList[13] = bbCenter.y;mtxList[14] = bbCenter.z
    
    tr = pymel.core.createNode( 'transform' )
    tr.dh.set( 1 )
    pymel.core.xform( tr, ws=1, matrix= mtxList )
    xSize = bb.max().x-bb.min().x
    ySize = bb.max().y-bb.min().y
    zSize = bb.max().z-bb.min().z
    tr.s.set( xSize, ySize, zSize )
    return tr




def setMatrixToCenterPoint( target, directionBasedGeo=False ):
    
    trObject = createMatrixObjectFromGeo( target )
    trObjectMtxList = trObject.wm.get()
    trObjectMtx = sgCmds.listToMatrix( trObjectMtxList )
    pymel.core.delete( trObject )
    point = OpenMaya.MPoint( 0, 0, 0 ) * trObjectMtx
    defaultMtx = sgCmds.getDefaultMatrix()
    defaultMtx[12] = point.x
    defaultMtx[13] = point.y
    defaultMtx[14] = point.z
    sgCmds.setMatrixToTarget( defaultMtx, target, pcp=1 )




def setMatrixToButtomPoint( target, directionBasedGeo=False ):
    
    trObject = createMatrixObjectFromGeo( target )
    trObjectMtxList = trObject.wm.get()
    trObjectMtx = sgCmds.listToMatrix( trObjectMtxList )
    pymel.core.delete( trObject )
    point = OpenMaya.MPoint( 0, -0.5, 0 ) * trObjectMtx
    defaultMtx = sgCmds.getDefaultMatrix()
    defaultMtx[12] = point.x
    defaultMtx[13] = point.y
    defaultMtx[14] = point.z
    sgCmds.setMatrixToTarget( defaultMtx, target, pcp=1 )


        
    
def createPlaneController( target, directionBasedGeo=False ):
    
    trObject = createMatrixObjectFromGeo( target )
    trObjectMtxList = trObject.wm.get()
    trObjectMtx = sgCmds.listToMatrix( trObjectMtxList )
    pymel.core.delete( trObject )
    
    vectorX = OpenMaya.MVector( trObjectMtx[0] )
    vectorY = OpenMaya.MVector( trObjectMtx[1] )
    vectorZ = OpenMaya.MVector( trObjectMtx[2] )
    point = OpenMaya.MPoint( 0, -0.5, 0 ) * trObjectMtx
    
    ctl = sgCmds.makeController( sgModel.Controller.planePoints, 1, makeParent=1 )
    ctlP = ctl.getParent()
    ctlShape = ctl.getShape()
    ctlShape.shape_sx.set( vectorX.length() )
    ctlShape.shape_sy.set( vectorY.length() )
    ctlShape.shape_sz.set( vectorZ.length() )
    ctlShape.scaleMult.set( 0.5 )
    
    pymel.core.xform( ctlP, ws=1, ro=sgCmds.getRotateFromMatrix( trObjectMtxList ) )
    pymel.core.xform( ctlP, ws=1, t=[point.x,point.y,point.z] )
    
    targetP = target.getParent()
    targetGrp = pymel.core.createNode( 'transform' )
    if targetP: targetGrp.setParent( targetP )
    sgCmds.constrain_all( ctl, targetGrp )
    target.setParent( targetGrp )
    pymel.core.select( ctl )
    sgCmds.setIndexColor( ctl, 22 )
    return ctl
    
    
    
def createCubeController_toCenter( target, directionBasedGeo=False ):
    
    trObject = createMatrixObjectFromGeo( target )
    trObjectMtxList = trObject.wm.get()
    trObjectMtx = sgCmds.listToMatrix( trObjectMtxList )
    pymel.core.delete( trObject )
    
    vectorX = OpenMaya.MVector( trObjectMtx[0] )
    vectorY = OpenMaya.MVector( trObjectMtx[1] )
    vectorZ = OpenMaya.MVector( trObjectMtx[2] )
    point = OpenMaya.MPoint( 0, 0, 0 ) * trObjectMtx
    
    ctl = sgCmds.makeController( sgModel.Controller.cubePoints, 1, makeParent=1 )
    ctlP = ctl.getParent()
    ctlShape = ctl.getShape()
    ctlShape.shape_sx.set( vectorX.length() )
    ctlShape.shape_sy.set( vectorY.length() )
    ctlShape.shape_sz.set( vectorZ.length() )
    
    pymel.core.xform( ctlP, ws=1, ro=sgCmds.getRotateFromMatrix( trObjectMtxList ) )
    pymel.core.xform( ctlP, ws=1, t=[point.x,point.y,point.z] )
    
    targetP = target.getParent()
    targetGrp = pymel.core.createNode( 'transform' )
    if targetP: targetGrp.setParent( targetP )
    sgCmds.constrain_all( ctl, targetGrp )
    target.setParent( targetGrp )
    pymel.core.select( ctl )
    sgCmds.setIndexColor( ctl, 22 )
    return ctl



def createCubeController_toButtom( target, directionBasedGeo=False ):
    
    trObject = createMatrixObjectFromGeo( target )
    trObjectMtxList = trObject.wm.get()
    trObjectMtx = sgCmds.listToMatrix( trObjectMtxList )
    pymel.core.delete( trObject )
    
    vectorX = OpenMaya.MVector( trObjectMtx[0] )
    vectorY = OpenMaya.MVector( trObjectMtx[1] )
    vectorZ = OpenMaya.MVector( trObjectMtx[2] )
    point = OpenMaya.MPoint( 0, -0.5, 0 ) * trObjectMtx
    
    ctl = sgCmds.makeController( sgModel.Controller.cubePoints, 1, makeParent=1 )
    ctlP = ctl.getParent()
    ctlShape = ctl.getShape()
    ctlShape.shape_sx.set( vectorX.length() )
    ctlShape.shape_sy.set( vectorY.length() )
    ctlShape.shape_sz.set( vectorZ.length() )
    ctlShape.shape_ty.set( vectorY.length() * 0.5 )
    
    pymel.core.xform( ctlP, ws=1, ro=sgCmds.getRotateFromMatrix( trObjectMtxList ) )
    pymel.core.xform( ctlP, ws=1, t=[point.x,point.y,point.z] )
    
    targetP = target.getParent()
    targetGrp = pymel.core.createNode( 'transform' )
    if targetP: targetGrp.setParent( targetP )
    sgCmds.constrain_all( ctl, targetGrp )
    target.setParent( targetGrp )
    pymel.core.select( ctl )
    sgCmds.setIndexColor( ctl, 22 )
    return ctl
    
    
    

def shadowEffect( lightTransform, projectTargets, projectBase ):
    
    children = pymel.core.listRelatives( projectTargets, c=1, ad=1, type='mesh' )
    projectTargets = [ child.getParent() for child in children if sgCmds.isVisible( child ) ]
    
    def getLocalGeometry( geometry, parentObject ):
        geometryShape = geometry.getShape()
        mm = pymel.core.createNode( 'multMatrix' )
        trGeo = pymel.core.createNode( 'transformGeometry' )
        newMeshShape = pymel.core.createNode( 'mesh' )
        
        geometry.wm >> mm.i[0]
        parentObject.wim >> mm.i[1]
        
        geometryShape.attr( 'outMesh' ) >> trGeo.inputGeometry
        mm.matrixSum >> trGeo.transform
        trGeo.outputGeometry >> newMeshShape.attr( 'inMesh' )
        return newMeshShape.getParent()
    
    def projectMesh( projTarget, projBase ):
        projTargetShape = projTarget.getShape()
        projBaseShape   = projBase.getShape()
        shrinkWrap = pymel.core.deformer( projTargetShape, type='shrinkWrap' )[0]
        shrinkWrap.attr( 'reverse' ).set( 1 )
        shrinkWrap.attr( 'projection' ).set( 2 )
        attrList = ['keepMapBorders','continuity','smoothUVs','keepBorder',
                    'boundaryRule','keepHardEdge','propagateEdgeHardness']
        for attr in attrList:
            projTargetShape.attr( attr ) >> shrinkWrap.attr( attr )
        projBaseShape.attr( 'worldMesh' ) >> shrinkWrap.attr( 'targetGeom' )
        return shrinkWrap

    def getOutMesh( targetMesh ):
        targetMeshShape = targetMesh.getShape()
        newMesh = pymel.core.createNode( 'mesh' )
        targetMeshShape.outMesh >> newMesh.inMesh
        return newMesh.getParent()

    
    def getProjectionTypeOutput( lightTransform ):
        sgCmds.addAttr( lightTransform, ln='projectionType', at='enum', en=':point:directionX:directionY:directionZ', k=1 )
        pmaNode = pymel.core.createNode( 'plusMinusAverage' )
        for i, outputValues in [ (0,[0,0,0]),(1,[1,0,0]),(2,[0,1,0]),(3,[0,0,1]) ]:
            condition = pymel.core.createNode( 'condition' )
            lightTransform.attr( 'projectionType' ) >> condition.firstTerm
            condition.attr( 'secondTerm' ).set( i )
            condition.colorIfTrue.set( *outputValues )
            condition.colorIfFalse.set( 0,0,0 )
            condition.outColor >> pmaNode.input3D[i]
        return pmaNode.attr( 'output3Dx' ), pmaNode.attr( 'output3Dy' ), pmaNode.attr( 'output3Dz' )
    
    def addOffsetAttribute( lightTransform, shrinkWrapNode ):
        sgCmds.addAttr( lightTransform, ln='offset', min=0, k=1 )
        lightTransform.attr( 'offset' ) >> shrinkWrapNode.attr( 'targetInflation' )

    constrainGrp = pymel.core.createNode( 'transform', n=lightTransform.nodeName() + '_shadowCoreGrp' )
    resultGrp    = pymel.core.createNode( 'transform', n=lightTransform.nodeName() + '_shadowResultGrp' )
    localProjBase = getLocalGeometry( projectBase, lightTransform )
    localProjBase.setParent( constrainGrp )
    localProjBase.attr( 'inheritsTransform' ).set( 0 )
    localProjBase.v.set( 0 )
    
    xOutput, yOutput, zOutput = getProjectionTypeOutput( lightTransform )
    
    localGeometrys = []
    resultObjects = []
    for projectTarget in projectTargets:
        localProjTarget = getLocalGeometry( projectTarget, lightTransform )
        localProjTarget.attr( 'inheritsTransform' ).set( 0 )
        localProjTarget.v.set( 0 )
        
        shrinkWrap = projectMesh( localProjTarget, localProjBase )
        resultObject = getOutMesh( localProjTarget )
        sgCmds.copyShader( projectTarget, resultObject )
        xOutput >> shrinkWrap.attr( 'alongX' )
        yOutput >> shrinkWrap.attr( 'alongY' )
        zOutput >> shrinkWrap.attr( 'alongZ' )
        addOffsetAttribute( lightTransform, shrinkWrap )
        
        pymel.core.parent( localProjTarget, resultObject, constrainGrp )
        localGeometrys.append( localProjTarget )
        resultObjects.append( resultObject )
    
    pymel.core.group( localGeometrys, n='LocalObjects' )
    pymel.core.parent( resultObjects, resultGrp )
    
    if not cmds.objExists( 'shadowEffectSurfaceShader' ):
        surfaceShader = cmds.shadingNode( 'surfaceShader', asShader=1, n='shadowEffectSurfaceShader' )
    else:
        surfaceShader = 'shadowEffectSurfaceShader'
    if not cmds.objExists( 'shadowEffectSurfaceShaderSG' ):
        surfaceShaderSG = cmds.sets( renderable=True, noSurfaceShader=True, empty=1, name=surfaceShader + 'SG' )
    else:
        surfaceShaderSG = 'shadowEffectSurfaceShaderSG'

    if not cmds.isConnected( surfaceShader + '.outColor', surfaceShaderSG + '.surfaceShader' ):
        cmds.connectAttr( surfaceShader + '.outColor', surfaceShaderSG + '.surfaceShader' )  
    cmds.sets( resultGrp.name(), forceElement=surfaceShaderSG )
    
    sgCmds.constrain_all( lightTransform, constrainGrp )
    sgCmds.constrain_all( lightTransform, resultGrp )




def createLatticeController( targets, numController=0 ):

    numController = max([numController,2])
    deformer, lattice, latticeBase = pymel.core.lattice(  divisions=[2,numController,2], objectCentered=False,  ldv=[2,numController+1,2] )
    mtxObject = createMatrixObjectFromGeo( targets )
    pymel.core.parent( lattice, latticeBase, mtxObject )
    lattice.t.set( 0,0,0 ), lattice.r.set( 0,0,0 ), lattice.s.set( 1,1,1 )
    latticeBase.t.set( 0,0,0 ), latticeBase.r.set( 0,0,0 ), latticeBase.s.set( 1,1,1 )
    
    mtxObjectSize = mtxObject.sx.get() + mtxObject.sy.get() + mtxObject.sz.get()
    minSize = mtxObjectSize / 20.0
    mtxObject.sx.set( max( [minSize,mtxObject.sx.get()] ) )
    mtxObject.sy.set( max( [minSize,mtxObject.sy.get()] ) )
    mtxObject.sz.set( max( [minSize,mtxObject.sz.get()] ) )
    mtxObject.v.set( 0 )

    mainCtl = sgCmds.makeController( sgModel.Controller.cubePoints, 1, makeParent=1 );sgCmds.setIndexColor( mainCtl, 22 )
    pymel.core.xform( mainCtl, ws=1, matrix=mtxObject.wm.get() )

    sgCmds.constrain_all( mainCtl, mtxObject )

    dtCtlBase = pymel.core.createNode( 'transform' )
    sgCmds.constrain_parent( mainCtl, dtCtlBase )

    pointers = []
    for i in range( numController ):
        position = float(i)/(numController-1) - 0.5
        pointer = pymel.core.createNode( 'transform' )
        pointer.setParent( mainCtl )
        sgCmds.setTransformDefault( pointer )
        pointer.ty.set( position )
        pointers.append( pointer )
        sgCmds.constrain_scale( dtCtlBase, pointer )
    
    conditionNode = pymel.core.createNode( 'condition' )
    conditionNode.op.set( 4 )
    mtxObject.sx >> conditionNode.firstTerm
    mtxObject.sz >> conditionNode.secondTerm
    mtxObject.sx >> conditionNode.colorIfTrueR
    mtxObject.sz >> conditionNode.colorIfFalseR
    
    joints = []
    bindPres = []
    planeCtls = []
    
    beforeParent = dtCtlBase
    for pointer in pointers:
        moveCtl = makeController( sgModel.Controller.movePoints, 1, makeParent=1 );sgCmds.setIndexColor( moveCtl, 20 )
        conditionNode.outColorR >> moveCtl.scaleMult
        
        dcmp = sgCmds.getLocalDecomposeMatrix( pointer.wm, beforeParent.wim )
        planeCtl = sgCmds.makeController( sgModel.Controller.circlePoints, 0.5, makeParent=1 );sgCmds.setIndexColor( planeCtl, 18 )
        moveCtl.getParent().setParent( planeCtl )
        ctlShape = planeCtl.getShape()
        pPlaneCtl = planeCtl.getParent()
        pPlaneCtl.setParent( beforeParent )
        dcmp.ot >> pPlaneCtl.t
        dcmp.outputRotate >> pPlaneCtl.r
        mainCtl.sx >> ctlShape.shape_sx
        mainCtl.sy >> ctlShape.shape_sy
        mainCtl.sz >> ctlShape.shape_sz
        
        multSxMinus = pymel.core.createNode( 'multDoubleLinear' )
        multSxPlus = pymel.core.createNode( 'multDoubleLinear' )
        multSzMinus = pymel.core.createNode( 'multDoubleLinear' )
        multSzPlus = pymel.core.createNode( 'multDoubleLinear' )
        
        mainCtl.sx >> multSxMinus.input1; multSxMinus.input2.set( -0.5 )
        mainCtl.sx >> multSxPlus.input1; multSxPlus.input2.set( 0.5 )
        mainCtl.sz >> multSzMinus.input1; multSzMinus.input2.set( -0.5 )
        mainCtl.sz >> multSzMinus.input1; multSzMinus.input2.set( 0.5 )
        
        for i, position in [ (0,[multSxMinus,multSzMinus]), (1,[multSxMinus,multSzPlus]), 
                             (2,[multSxPlus,multSzMinus]), (3,[multSxPlus,multSzPlus]) ]:
            pymel.core.select( moveCtl )
            joint   = pymel.core.joint(); joint.drawStyle.set( 2 )
            bindPre = pymel.core.createNode( 'transform' )
            bindPre.setParent( pointer )
            sgCmds.setTransformDefault( bindPre )
            joints.append( joint )
            bindPres.append( bindPre )
            position[0].output >> joint.tx; position[1].output >> joint.tz
            position[0].output >> bindPre.tx; position[1].output >> bindPre.tz
        planeCtls.append( planeCtl )
        beforeParent = pointer
    
    for i in range( len( planeCtls )-1 ):
        planeCtls[i+1].getParent().setParent( planeCtls[i] )

    skinCluster = pymel.core.skinCluster( joints, lattice, dr=1000 )
    for i in range( len( joints ) ):
        sgCmds.setBindPreMatrix( joints[i], bindPres[i] )
    lattice.wm >> skinCluster.geomMatrix

    allGrp = pymel.core.createNode( 'transform' )
    pymel.core.parent( mainCtl.getParent(), mtxObject, dtCtlBase, allGrp )

    return mainCtl
    

def createPointConstrainedCam( targetObject ):
    
    targetObject = pymel.core.ls( targetObject )[0].name()
    
    cam = sgCmds.getCurrentCam().name()
    panel = cmds.getPanel( wf=1 )
    if not cam:
        cam = 'persp'
    duCam = cmds.duplicate( cam )[0]
    
    camGrp = cmds.group( em=1 )
    cmds.pointConstraint( targetObject, camGrp )
    
    cmds.parent( duCam, camGrp )
    
    if cmds.getPanel( to=panel ):
        print 'lookThroughModelPanel %s %s;' %( duCam, panel )
        mel.eval( 'lookThroughModelPanel %s %s;' %( duCam, panel ) )
    
    
    