# Use in PowerShell before running nlm directly:  . .\tools\env.ps1
$scripts = Join-Path $env:USERPROFILE 'AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\Scripts'
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
if ($env:Path -notlike "*$scripts*") { $env:Path += ";$scripts" }
$env:PYTHONIOENCODING = 'utf-8'
[Console]::OutputEncoding = [Text.Encoding]::UTF8
