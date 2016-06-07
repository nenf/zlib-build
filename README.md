Build zlib for windows
====================================
Python script for build zlib with static runtime 

Build steps:
----------

1. Open Visual Studio Command Prompt or call vcvars
```bash
call "C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\bin\amd64\vcvars64.bat"
```
2. Run build.py script
```bash
python build.py --out out_folder --revision master
```
