from sgMaya import sgCmds
import pymel.core

sels = pymel.core.ls( sl=1 )

if not len( sels ) < 3: 
    first = sels[0]
    second = sels[1]
    third = sels[2]
    sgCmds.replaceConnection( first, second, third )