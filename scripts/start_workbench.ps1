$ErrorActionPreference = 'Stop'

$python = $env:PYTHON_PATH
$pythonPrefix = @()
if (-not $python) {
  $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
  if ($pythonCommand) {
    $python = $pythonCommand.Source
  } else {
    $pyCommand = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCommand) {
      $python = $pyCommand.Source
      $pythonPrefix = @('-3')
    }
  }
}
if (-not $python) {
  Add-Type -AssemblyName PresentationFramework
  [System.Windows.MessageBox]::Show('未找到 Python 3。请安装 Python，或设置 PYTHON_PATH 后重试。', '自媒体剪辑台') | Out-Null
  exit 1
}

$server = Join-Path $PSScriptRoot 'workbench_server.py'
$projectRoot = $env:DOUYIN_EDITOR_PROJECTS
if (-not $projectRoot) {
  $documents = [Environment]::GetFolderPath('MyDocuments')
  $projectRoot = Join-Path $documents 'Codex\自媒体剪辑台项目'
}
$healthUrl = 'http://127.0.0.1:8765/api/health'
$pageUrl = 'http://127.0.0.1:8765/?v=multi-upload-fix-3'

function Test-Workbench {
  try {
    $result = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 2
    return $result.ok -eq $true
  } catch {
    return $false
  }
}

if (-not (Test-Workbench)) {
  $listeners = Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
  foreach ($listener in $listeners) {
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)" -ErrorAction SilentlyContinue
    if ($process.CommandLine -like '*workbench_server.py*') {
      Stop-Process -Id $listener.OwningProcess -Force -ErrorAction SilentlyContinue
    }
  }

  $arguments = @($pythonPrefix) + @($server, '--root', $projectRoot, '--port', '8765')
  Start-Process -FilePath $python -ArgumentList $arguments -WindowStyle Hidden

  $started = $false
  for ($attempt = 0; $attempt -lt 20; $attempt++) {
    Start-Sleep -Milliseconds 300
    if (Test-Workbench) {
      $started = $true
      break
    }
  }
  if (-not $started) {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show('剪辑工作台启动失败，请回到 Codex 告诉我。', '自媒体剪辑台') | Out-Null
    exit 1
  }
}

& (Join-Path $PSScriptRoot 'launch_jianying.ps1')
Start-Process $pageUrl
