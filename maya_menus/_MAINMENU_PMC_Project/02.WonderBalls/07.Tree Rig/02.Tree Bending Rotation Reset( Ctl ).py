from sgProject import wonderBalls
import pymel.core

sels = pymel.core.ls( sl=1 )
wonderBalls.treeBendingLookAtConnectReset( sels[0] )