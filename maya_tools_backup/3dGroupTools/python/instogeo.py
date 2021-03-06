{\rtf1\ansi\ansicpg949\deff0\deflang1033\deflangfe1042{\fonttbl{\f0\fnil\fcharset129 \'b8\'bc\'c0\'ba \'b0\'ed\'b5\'f1;}}
{\*\generator Msftedit 5.41.21.2510;}\viewkind4\uc1\pard\sa200\sl276\slmult1\lang18\f0\fs20\par
#-*- coding: utf-8 -*-\par
\par
def insttogeo(evt=0):\par
    #=======================================================================  \par
    import maya.cmds as cmds\par
    import maya.mel as mel\par
    \par
    \par
    insName_= cmds.ls(sl=1)\par
    \par
    nPart_ = cmds.listConnections(insName_, type= 'nParticle')\par
    instList_ = cmds.listConnections(insName_, type= 'transform')\par
    len(instList_)\par
    \par
      \par
        \par
    #=======================================================================  \par
    \par
    #=======================================================================  \par
    start = cmds.playbackOptions(q=1,min=1)\par
    end = cmds.playbackOptions(q=1,max=1)\par
    cmds.currentTime(end, e=1)\par
    #last particle id \'c3\'a3\'b1\'e2#\par
    parid_= cmds.getAttr(nPart_[0]+'.id')\par
    parid_.sort()\par
    len(parid_)\par
    lastPid_ = parid_[len(parid_)-1]\par
    \par
    #obj \'b8\'b8\'b5\'e9\'b1\'e2#\par
    allobj_= []\par
    for i in range(int(lastPid_)+1):\par
        obj_= cmds.duplicate(instList_[i%len(instList_)])\par
        allobj_.append(obj_[0])\par
    \par
        cmds.setAttr( obj_[0]+'.visibility', 0)\par
        cmds.setKeyframe( obj_[0], at='visibility')\par
    \par
        \par
    #=======================================================================  \par
        \par
    start = cmds.playbackOptions(q=1,min=1)\par
    end = cmds.playbackOptions(q=1,max=1)\par
    \par
    for f in range(int(start) , int(end + 1)):\par
        cmds.currentTime(f, e=1)\par
        if cmds.getAttr(nPart_[0]+'.id')>0:\par
            parid_= cmds.getAttr(nPart_[0]+'.id')\par
            for i in range(int(lastPid_)+1):\par
                if float(i) in parid_:\par
                    posat_= mel.eval("particleInstancer -name %s -q -position %s;" %(insName_[0], nPart_[0])) \par
                    rotat_= mel.eval("particleInstancer -name %s -q -rotation %s;" %(insName_[0], nPart_[0]))\par
                    radat_= mel.eval("particleInstancer -name %s -q -scale %s;" %(insName_[0], nPart_[0]))\par
                    pos_ = cmds.nParticle(nPart_, id= int(i), q=1, at= posat_)\par
                    rot_ = cmds.nParticle(nPart_, id= int(i), q=1, at= rotat_)\par
                    rad_ = cmds.nParticle(nPart_, id= int(i), q=1, at= radat_)\par
                    cmds.setAttr(allobj_[int(i)]+'.translate', pos_[0], pos_[1], pos_[2], type="double3")\par
                    cmds.setAttr(allobj_[int(i)]+'.rotate', rot_[0], rot_[1], rot_[2], type="double3")\par
                    cmds.setAttr(allobj_[int(i)]+'.scale', rad_[0], rad_[0], rad_[0], type="double3")\par
                    cmds.setAttr(allobj_[int(i)]+'.visibility', 1)\par
                    cmds.setKeyframe(allobj_[int(i)])\par
                else:\par
                    cmds.setAttr(allobj_[int(i)]+'.visibility', 0)\par
                    cmds.setKeyframe(allobj_[int(i)])\par
                \par
                \par
                \par
                \par
                \par
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++\par
def insttogeoGUI():\par
    import maya.cmds as cmds\par
    \par
    win = 'Instancer_to_Geo'\par
    if cmds.window(win, exists=1):\par
        cmds.deleteUI(win)\par
    cmds.window(win, width=400, height=200)\par
    cmds.columnLayout(adjustableColumn=True)\par
    cmds.button(label='instancer to geo',h=100, command= insttogeo)\par
    cmds.columnLayout()\par
\par
    cmds.showWindow(win)\par
    \par
insttogeoGUI()\par
\par
\par
\par
\par
\par
\par
}
 