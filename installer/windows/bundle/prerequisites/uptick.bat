SET python36=%LocalAppData%\Programs\Python\Python36\python.exe
SET python36_32=%LocalAppData%\Programs\Python\Python36-32\python.exe
if exist %python36% %python36% -m pip install uptick
if exist %python36_32% %python36_32% -m pip install uptick
rem If both paths are not found try to use pip to install uptick
if not exist %python36_32% & %python36% pip install uptick