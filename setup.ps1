# nlm-workspace 한 번에 설치 (Windows PowerShell)
#   실행: powershell -ExecutionPolicy Bypass -File .\setup.ps1
# 하는 일: 파이썬 확인 → 라이브러리 설치 → 작업 폴더 만들기 → nlm 로그인 안내 → Edge(PDF 변환) 확인

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$env:PYTHONIOENCODING = 'utf-8'

# 1) 파이썬: py 런처로 3.11을 먼저 찾고, 없으면 PATH의 python
$py = $null
try { & py -3.11 -c "import sys" 2>$null; if ($LASTEXITCODE -eq 0) { $py = @('py', '-3.11') } } catch {}
if (-not $py) {
    try { & python -c "import sys; assert sys.version_info >= (3, 10)" 2>$null; if ($LASTEXITCODE -eq 0) { $py = @('python') } } catch {}
}
if (-not $py) { Write-Host '파이썬 3.10 이상이 필요합니다. https://www.python.org 또는 Microsoft Store에서 Python 3.11을 설치한 뒤 다시 실행하세요.' -ForegroundColor Red; exit 1 }
$pyExe = $py[0]; $pyArgs = @($py | Select-Object -Skip 1)
Write-Host "파이썬: $(& $pyExe @pyArgs --version)"

# 2) 라이브러리 (pip 대신 python -m pip: PATH에 다른 파이썬이 먼저 잡혀 있어도 같은 파이썬에 설치)
& $pyExe @pyArgs -m pip install --user --upgrade pip | Out-Null
& $pyExe @pyArgs -m pip install --user -r requirements.txt
if ($LASTEXITCODE -ne 0) { Write-Host '라이브러리 설치 실패' -ForegroundColor Red; exit 1 }

# 3) 작업 폴더
foreach ($d in '01_upload', '02_from-lm', '03_work', '04_final', 'inbox') { New-Item -ItemType Directory -Force $d | Out-Null }

# 4) nlm 위치 확인 (사용자 Scripts 폴더가 PATH에 없을 수 있음)
$scripts = & $pyExe @pyArgs -c "import sysconfig; print(sysconfig.get_path('scripts', 'nt_user'))"
if ($env:Path -notlike "*$scripts*") { $env:Path += ";$scripts" }
$nlm = Get-Command nlm -ErrorAction SilentlyContinue
if ($nlm) { Write-Host "nlm: $($nlm.Source)" } else { Write-Host "nlm을 찾지 못했습니다. 이 폴더를 PATH에 추가하세요: $scripts" -ForegroundColor Yellow }

# 5) Edge (tools/to_pdf.py가 HTML → PDF 변환에 사용)
$edge = @("${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe", "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($edge) { Write-Host "Edge: $edge" } else { Write-Host 'Microsoft Edge가 없어서 to_pdf.py는 쓸 수 없습니다.' -ForegroundColor Yellow }

Write-Host ''
Write-Host '설치 완료. 다음 순서로 진행하세요:' -ForegroundColor Green
Write-Host '  1. nlm login                       (브라우저로 Google 로그인, 쿠키 저장)'
Write-Host '  2. python tools/sync.py            (노트북 목록 → notebooks.md, 노트북별 폴더)'
Write-Host '  3. python tools/restore.py --all   (NotebookLM에 올려 둔 소스 텍스트 다시 받기)'
