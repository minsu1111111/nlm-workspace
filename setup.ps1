# nlm-workspace 설치 (Windows PowerShell) — 이 저장소를 clone한 폴더에서 실행
#   powershell -ExecutionPolicy Bypass -File .\setup.ps1
# 하는 일: 파이썬 확인 → nlmw 설치(검산 라이브러리 포함) → 이 폴더를 작업 폴더로 초기화 → 점검 안내

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$env:PYTHONIOENCODING = 'utf-8'

# 1) 파이썬 3.10+ : py 런처(3.12, 3.11, 3.10 순) → PATH의 python
$py = $null
foreach ($v in '3.13', '3.12', '3.11', '3.10') {
    try { & py "-$v" -c "import sys" 2>$null; if ($LASTEXITCODE -eq 0) { $py = @('py', "-$v"); break } } catch {}
}
if (-not $py) {
    try { & python -c "import sys; assert sys.version_info >= (3, 10)" 2>$null; if ($LASTEXITCODE -eq 0) { $py = @('python') } } catch {}
}
if (-not $py) { Write-Host '파이썬 3.10 이상이 필요합니다 (python.org 또는 Microsoft Store).' -ForegroundColor Red; exit 1 }
$exe = $py[0]; $pa = @($py | Select-Object -Skip 1)
Write-Host "파이썬: $(& $exe @pa --version)"

# 2) 설치 (python -m pip: PATH에 다른 파이썬이 있어도 같은 파이썬에 설치)
& $exe @pa -m pip install --user --upgrade pip | Out-Null
& $exe @pa -m pip install --user -e ".[study]"
if ($LASTEXITCODE -ne 0) { Write-Host '설치 실패' -ForegroundColor Red; exit 1 }

# 3) 사용자 Scripts 폴더를 이번 창 PATH에 추가 (nlm, nlmw)
$scripts = & $exe @pa -c "import sysconfig; print(sysconfig.get_path('scripts', 'nt_user'))"
if ($env:Path -notlike "*$scripts*") { $env:Path += ";$scripts" }
if (-not ([Environment]::GetEnvironmentVariable('Path', 'User') -like "*$scripts*")) {
    Write-Host "참고: 새 창에서도 nlm/nlmw를 쓰려면 이 폴더를 사용자 PATH에 추가하세요:`n  $scripts" -ForegroundColor Yellow
}

# 4) 이 폴더를 작업 폴더로
nlmw init .

Write-Host ''
Write-Host '설치 완료. 다음:' -ForegroundColor Green
Write-Host '  nlm login        (브라우저로 Google 로그인)'
Write-Host '  nlmw doctor      (점검)'
Write-Host '  nlmw sync        (노트북 목록 → notebooks.md)'
