@echo off
setlocal

echo ============================================
echo  Controle de Pedidos - Gerador de .exe
echo ============================================
echo.

set PYCMD=

python --version >pycheck.tmp 2>&1
findstr /C:"Python" pycheck.tmp >nul
if not errorlevel 1 (
    set PYCMD=python
    goto PYTHON_OK
)

py -3 --version >pycheck.tmp 2>&1
findstr /C:"Python" pycheck.tmp >nul
if not errorlevel 1 (
    set PYCMD=py -3
    goto PYTHON_OK
)

del pycheck.tmp >nul 2>nul
goto SEM_PYTHON

:PYTHON_OK
del pycheck.tmp >nul 2>nul
echo Python encontrado - usando o comando: %PYCMD%
%PYCMD% --version
echo.

if exist venv_build goto TEM_VENV

echo Criando ambiente de build - isso so acontece na primeira vez...
%PYCMD% -m venv venv_build
if errorlevel 1 goto ERRO_VENV

:TEM_VENV
call venv_build\Scripts\activate.bat
if errorlevel 1 goto ERRO_ATIVAR

echo.
echo Instalando/atualizando o PyInstaller - precisa de internet...
python -m pip install --upgrade pip >nul
python -m pip install --upgrade pyinstaller
if errorlevel 1 goto ERRO_PIP

echo.
echo Gerando o executavel - pode levar um a dois minutos...
python -m PyInstaller --noconfirm --onefile --windowed --name ControleDePedidos --hidden-import tkinter main.py
if errorlevel 1 goto ERRO_PYINSTALLER

if not exist dist\ControleDePedidos.exe goto ERRO_SEM_EXE

copy /Y dist\ControleDePedidos.exe ControleDePedidos.exe >nul
rmdir /S /Q build >nul 2>nul
rmdir /S /Q dist >nul 2>nul
del /Q ControleDePedidos.spec >nul 2>nul

echo.
echo ============================================
echo  SUCESSO!
echo  O arquivo ControleDePedidos.exe foi criado
echo  nesta mesma pasta.
echo  Copie esse arquivo para qualquer outro
echo  computador Windows para usar o programa.
echo ============================================
goto FIM

:SEM_PYTHON
echo [ERRO] Nao encontrei uma instalacao valida do Python neste computador.
echo.
echo Isso pode acontecer mesmo quando o comando "python" existe, se o
echo Windows estiver so abrindo a Microsoft Store no lugar do Python real
echo - isso e um comportamento padrao do Windows quando o Python nao foi
echo instalado corretamente.
echo.
echo Instale o Python em https://www.python.org/downloads/
echo IMPORTANTE - na tela de instalacao, marque a caixinha
echo "Add python.exe to PATH" antes de clicar em Install.
echo Depois de instalar, feche esta janela e de dois cliques no build.bat de novo.
goto FIM

:ERRO_VENV
echo [ERRO] Nao consegui criar o ambiente virtual Python.
goto FIM

:ERRO_ATIVAR
echo [ERRO] Nao consegui ativar o ambiente virtual.
goto FIM

:ERRO_PIP
echo [ERRO] Falha ao instalar o PyInstaller. Verifique sua conexao com a internet.
goto FIM

:ERRO_PYINSTALLER
echo [ERRO] O PyInstaller encontrou um problema ao gerar o .exe. Veja as mensagens acima.
goto FIM

:ERRO_SEM_EXE
echo [ERRO] O processo terminou mas nao encontrei o executavel gerado em dist\
goto FIM

:FIM
echo.
pause
