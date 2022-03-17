@echo off
set project_dir="%cd%"
cd ..
rem dx9_90 is broken
rem python buildshaders.py -shaders "%project_dir%\shader_lists\sm2x_dx90" -game "..\..\..\game\mod_episodic" -source "..\.." -bin_dir "D:\\SteamLibrary\\SteamApps\\common\\Source SDK Base 2013 Singleplayer\\bin\\"
python buildshaders.py -shaders "%project_dir%\shader_lists\sm2x_dx93" -game "..\..\..\game\mod_episodic" -source "..\.." -bin_dir "D:\\SteamLibrary\\SteamApps\\common\\Source SDK Base 2013 Singleplayer\\bin\\" -dx9_30
python buildshaders.py -shaders "%project_dir%\shader_lists\sm30" -game "..\..\..\game\mod_episodic" -source "..\.." -bin_dir "D:\\SteamLibrary\\SteamApps\\common\\Source SDK Base 2013 Singleplayer\\bin\\" -dx9_30 -force30
pause
