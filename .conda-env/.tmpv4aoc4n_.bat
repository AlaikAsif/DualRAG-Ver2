@ECHO OFF
@SET PYTHONIOENCODING=utf-8
@SET PYTHONUTF8=1
@FOR /F "tokens=2 delims=:." %%A in ('chcp') do for %%B in (%%A) do set "_CONDA_OLD_CHCP=%%B"
@chcp 65001 > NUL
@CALL "C:\ProgramData\anaconda3\condabin\conda.bat" activate "C:\Users\Alaik\Documents\work\chatbot-revamp\.conda-env"
@IF %ERRORLEVEL% NEQ 0 EXIT /b %ERRORLEVEL%
@C:\Users\Alaik\Documents\work\chatbot-revamp\.conda-env\python.exe -Wi -m compileall -q -l -i C:\Users\Alaik\AppData\Local\Temp\tmp81yj1hdm -j 0
@IF %ERRORLEVEL% NEQ 0 EXIT /b %ERRORLEVEL%
@chcp %_CONDA_OLD_CHCP%>NUL
