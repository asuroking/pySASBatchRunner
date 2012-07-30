#-------------------------------------------------------------------------------
# Name:        setup
# Purpose:     setup for Batch Run SAS programs, package as binary distribution
#
# Author:      Jwang19
#
# Created:     26/07/2012
# Copyright:   (c) Jwang19 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python


from distutils.core import setup
import py2exe


options = {"py2exe":{"compressed":1,
                     "optimize":2,
                     "bundle_files":1
                     }
           }


setup(name = "pySASBatchRunner",
      version = "0.1",
      description = "SAS Batch Runner",
      author = "John Wang",
      author_email = "wangjun.sh@gmail.com",
      url = "",
      packages = ["SASBatchRunner"],
      options = options,
      zipfile = None,
      data_files = ["SASBatchRunner/icon-sas.ico"],
      windows=[{"script":"SASBatchRunner/pySASBatchRunner.py",
                "icon_resources":[(1,"SASBatchRunner/icon-sas.ico")]
                }
               ]
      )

