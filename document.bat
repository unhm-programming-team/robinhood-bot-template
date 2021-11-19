REM runs make html to generate docs according to sphinx parameters
REM copies build/html/ to docs/
REM creates a .nojekyll file in docs/
REM removes build/
REM opens docs/index.html file in the default browser.

call make.bat html

Xcopy /E /I .\build\html .\docs /y
fsutil file createnew docs/.nojekyll 0
rmdir /Q /S build

start docs/index.html