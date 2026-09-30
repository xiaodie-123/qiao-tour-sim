# 打包安装包:复制 exe 目录 + 使用说明 + (可选)桌面快捷方式 + 压缩包
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$src = Join-Path $root 'dist\QiaoSim'
$name = '运筹三晋-v1.1'
$dst = Join-Path $root ('dist\' + $name)
if (-not (Test-Path $src)) { throw '请先运行 PyInstaller 构建 dist\QiaoSim' }
if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }
Copy-Item -Recurse $src $dst
Copy-Item (Join-Path $root '使用说明.txt') $dst -Force

try {
    $ws = New-Object -ComObject WScript.Shell
    $desktop = [Environment]::GetFolderPath('Desktop')
    $lnk = $ws.CreateShortcut((Join-Path $desktop ('运筹三晋' + '.lnk')))
    $lnk.TargetPath = Join-Path $dst 'QiaoSim.exe'
    $lnk.WorkingDirectory = $dst
    $lnk.Save()
    Write-Output 'OK-SHORTCUT'
} catch {
    Write-Output 'WARN-SHORTCUT-SKIPPED'
}

$zip = Join-Path $root ('dist\运筹三晋-v1.1-win64.zip')
if (Test-Path $zip) { Remove-Item -Force $zip }
Compress-Archive -Path $dst -DestinationPath $zip
Write-Output ('OK-INSTALLER: ' + $zip)
