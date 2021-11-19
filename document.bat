@echo off
REM run sphinx-apidoc to autogenerate .rst files for robinhood bot
REM runs make html to generate html files according to sphinx parameters and rst files in sphinx-source
REM copies build/html/ to docs/
REM creates a .nojekyll file in docs/
REM removes build/
REM opens docs/index.html file in the default browser.
@echo on

sphinx-apidoc -o sphinx-source src/robinhoodbot -e -f

call make.bat html

Xcopy /E /I .\build\html .\docs /y
fsutil file createnew docs/.nojekyll 0
rmdir /Q /S build

start docs/index.html