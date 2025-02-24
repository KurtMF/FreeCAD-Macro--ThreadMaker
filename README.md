 INDEMNITY: By using this software you agree not to sue me for any reason related to the use of this 
 software.

 Copyright (c) 2022 Kurt Funderburg, all rights not explicitly relinquished in LGPL reserved.

   This program is free software; you can redistribute it and/or modify  
   it under the terms of the GNU Lesser General Public License (LGPL)    
   as published by the Free Software Foundation; either version 2 of     
   the License, or (at your option) any later version.                   
                                                                         
   This program is distributed in the hope that it will be useful,       
   but WITHOUT ANY WARRANTY; without even the implied warranty of       
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         
   GNU Library General Public License for more details.                  
                                                                         
   You should have received a copy of the GNU Library General Public     
   License along with this program; if not, write to the Free Software   
   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  
   USA                                                                   

PRE-INSTALLATION INSTRUCTIONS FOR THREADMAKER MACRO:
First, find your FreeCAD Macro directory (https://wiki.freecad.org/How_to_install_macros#Macros_directory).

Second, download or copy the ThreadMaker.zip file into your macro directory, and extract it there.  If you 
already extracted it somewhere else, the move the files (and the ThreadMaker sub-folder) into the FreeCAD 
Macro directory.

Third, confirm that you have files listed below in your macro directory, along with the new folder named
ThreadMaker.  Note: ThreadMaker/TMClasses.py is the underlying class file required by any thread body 
created with this macro.  If you move or delete it, all ThreadMaker solids will fail.

Lastly, read the ThreadMaker User Guide (TMUserGuide.pdf) to quickly learn to generate fasteners for 
ISO 261 standard threads, or generate any other kind of threads based on the ISO 68-1M thread profile.  

TMUserGuide.pdf is here: https://drive.google.com/file/d/1m8EGpg5S-jCm2kR9DDi3Mf0tc6tt2I8Z/view?usp=sharing

CONTENTS ADDED TO FREECAD MACRO DIRECTORY:
06/11/2022  07:48 PM    <DIR>          ThreadMaker
06/01/2022  09:57 PM               309 TMDisableThread.FCMacro
06/01/2022  09:57 PM               305 TMEnableThread.FCMacro
06/11/2022  07:28 PM             2,407 TMMakeInsert.FCMacro
06/11/2022  07:30 PM             9,463 TMMakeShaft.FCMacro
06/10/2022  03:57 PM             3,025 TMREADME.txt
CONTENTS OF ADDED ThreadMaker DIRECTORY:
06/11/2022  06:33 PM            59,078 TMClasses.py
06/10/2022  01:35 PM             1,488 TMIconDisable.png
06/10/2022  01:35 PM             1,413 TMIconEnable.png
06/10/2022  01:34 PM             1,148 TMIconInsert.png
06/10/2022  01:34 PM             1,053 TMIconShaft.png
