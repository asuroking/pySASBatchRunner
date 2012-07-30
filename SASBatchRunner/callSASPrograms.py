#-------------------------------------------------------------------------------
# Name:        callSASPrograms
# Purpose:     Call SAS programs using subprocess
#
# Author:      Jwang19
#
# Created:     29/07/2012
# Copyright:   (c) Jwang19 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import os
import subprocess

def callSASPrograms(SASProgramList):
    """
    execute SAS programs from given DICT:: SASProgramList.
    Module subprocess is used for call external program.
    """

    sascmd = u'C:\Program Files\SAS\SASFoundation\9.2\sas.exe'
    cfg = u'C:\Program Files\SAS\SASFoundation\9.2\nls\en\SASV9.CFG'

    for SASProgram in SASProgramList:
        if os.path.exists(SASProgram[0]):

            fullcmd = sascmd + u' -sysin "' + SASProgram[0] + u'"' + u' -log "' + SASProgram[1] + u'"' + \
                      u' -print "' + SASProgram[2] + u'"' + u' -config "' + cfg + u'"'

            subprocess.call(fullcmd)
