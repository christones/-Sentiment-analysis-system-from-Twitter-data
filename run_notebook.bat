@echo off
cd /d "%~dp0"
set LOG=run_log.txt
echo Started %date% %time% > %LOG%
set PY=python
where python >/dev/null 2>&1 || set PY=py
echo Using: >> %LOG%
where %PY% >> %LOG% 2>&1
%PY% --version >> %LOG% 2>&1
echo Installing Jupyter tools... >> %LOG%
%PY% -m pip install -q jupyter nbconvert ipykernel >> %LOG% 2>&1
echo Executing notebook (this can take 10-30 minutes on 1.6M tweets)... >> %LOG%
%PY% -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 Sentiment_Analysis_Pipeline.ipynb >> %LOG% 2>&1
echo EXIT CODE %errorlevel% >> %LOG%
echo Finished %date% %time% >> %LOG%
