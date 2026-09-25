$ErrorActionPreference = 'SilentlyContinue'
$uninstallRoots = @(
  'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
  'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
  'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*'
)
$app = Get-ItemProperty $uninstallRoots | Where-Object { $_.DisplayName -match '剪映|Jianying' } | Select-Object -First 1
if ($app.DisplayIcon) {
  $iconPath = [string]$app.DisplayIcon
  $iconPath = $iconPath.Trim('"') -replace ',\d+$',''
  $exe = Join-Path (Split-Path $iconPath -Parent) 'JianyingPro.exe'
  if (Test-Path -LiteralPath $exe) {
    Start-Process -FilePath $exe
  }
}
