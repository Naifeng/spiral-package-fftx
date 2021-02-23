#! python

##  Copyright (c) 2018-2021, Carnegie Mellon University
##  See LICENSE for details

##  This script will compile and run a test program acting as a harness to test
##  and time spiral generated code.  It takes as arguments the spiral script
##  file, from which problem size and other relevant information is extracted
##  and put into a simple header file.  The CUDA harness code is compiled (using
##  the sizes extracted) and then runs to exrcise the spiral generated code.
##
##  This script constructs a command line for cmake and uses defines to inform
##  cmake of the script name(s) (from which code must be generated by spiral).
##
##  The spiral script identifies parameters needed for the harness as follows:
##
##  n := 80;        ##  PICKME #define cubeN 80
##
##  The variable n used in the spiral script must be reflected in the harness,
##  after 'PICKME' write an equivalent definition for the C code.  This script
##  extracts all lines from the spiral script matching 'PICKME' and echoes the
##  portion after 'PICKME' to the file testsizes.h

import sys
import subprocess
import os
import re

incl_cpu_code = False

if len(sys.argv) < 2:
    print ( 'Usage: ' + sys.argv[0] + ' spiral_script [ CPU_spiral_script ]' )
    sys.exit ( 'missing argument(s)' )

gap_script = sys.argv[1]
_cmakeGapScript   = '-D_gpuGapScript=' + gap_script
_cmakeGpuFileName = ''

_harnessName = 'HarnessWarpxCuda'                       ##  driver program name
_cmakeHarnessName = '-D_harnessName=' + _harnessName   ##  becomes project name in cmake

##  create the sizes header file - testsizes.h

testsizes = open ( 'testsizes.h.tmp', 'w' )

with open ( gap_script, 'r' ) as fil:
    for line in fil.readlines():
        if 'PICKME' in line:
            defl = re.sub('.* PICKME ', '', line)
            testsizes.write ( defl )
        if 'CODEFILE' in line:
            _gpuFileName = re.sub ( '.*CODEFILE', '', defl )
            _gpuFileName = re.sub ( '[ "\n]', '', _gpuFileName )
            _cmakeGpuFileName = '-D_gpuFileName=' + _gpuFileName

testsizes.close()
fil.close()

if len(sys.argv) >= 3:
    incl_cpu_code = True

_buildCPU = ''
_cmakeCpuGapScript = ''
_cmakeCpuFileName  = ''

if incl_cpu_code:
    ##  Next argument is required, must be CPU gap script
    if len(sys.argv) < 3:
        print ( 'Usage: ' + sys.argv[0] + ' ' + gap_script + ' ' + ' CPU_spiral_script' )
        sys.exit ( 'missing argument(s)' )
        
    cpu_gap_script = sys.argv[2]
    _cmakeCpuGapScript = '-D_cpuGapScript=' + cpu_gap_script

    ##  Add the CPU sizes to the header file
    testsizes = open ( 'testsizes.h.tmp', 'a' )
    with open ( cpu_gap_script, 'r' ) as fil:
        for line in fil.readlines():
            if 'PICKME' in line:
                defl = re.sub('.* PICKME ', '', line)
                testsizes.write ( defl )
            if 'PSATDCODE' in line:
                _cpuFileName = re.sub ( '.*PSATDCODE', '', defl )
                _cpuFileName = re.sub ( '[ "\n]', '', _cpuFileName )
                _cmakeCpuFileName = '-D_cpuFileName=' + _cpuFileName

    testsizes.close()
    fil.close()
    _buildCPU = '-D_buildCpuCode=True'

##  Cleanup the testsizes.h file (protect against multiple times included & duplicate lines)

testsizes = open ( 'testsizes.h', 'w')
testsizes.write ( '#ifndef _testsizes_h\n' )
testsizes.write ( '#define _testsizes_h\n\n' )
testsizes.close ()

cmdstr = 'sort -u testsizes.h.tmp >> testsizes.h && rm testsizes.h.tmp'
result = subprocess.run ( cmdstr, shell=True, check=True )
res = result.returncode

testsizes = open ( 'testsizes.h', 'a')
testsizes.write ( '\n#endif\n' )
testsizes.close ()

##  Create the build directory (if it doesn't exist)

build_dir = 'build'
isdir = os.path.isdir ( build_dir )
if not isdir:
    os.mkdir ( build_dir )

##  Run cmake and build to build the code

cmdstr = 'rm -rf * && cmake ' + _cmakeHarnessName + ' ' + _cmakeGapScript + ' ' + _cmakeGpuFileName + ' '
cmdstr = cmdstr + _buildCPU + ' ' + _cmakeCpuGapScript + ' ' + _cmakeCpuFileName

os.chdir ( build_dir )
##  print ( cmdstr )                ## testing script, stop here
##  sys.exit (0)                    ## testing script, stop here

if sys.platform == 'win32':
    cmdstr = cmdstr + ' .. && cmake --build . --config Release --target install'
else:
    cmdstr = cmdstr + ' .. && make install'

result = subprocess.run ( cmdstr, shell=True, check=True )
res = result.returncode

if (res != 0):
    print ( result )
    sys.exit ( res )

os.chdir ( '..' )

if sys.platform == 'win32':
    cmdstr = './HarnessWarpxCuda.exe'
else:
    cmdstr = './HarnessWarpxCuda'
    
result = subprocess.run ( cmdstr )
res = result.returncode

if (res != 0):
    print ( result )
    sys.exit ( res )

sys.exit (0)
