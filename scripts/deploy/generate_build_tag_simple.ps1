# Simple Build Tag Generator
param([string]$OutputFile = "")

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$tag = "20$($timestamp.Substring(2,6))-$($timestamp.Substring(9,6))"

Write-Host "Generated tag: $tag"

if ($OutputFile -ne "") {
    $dir = Split-Path $OutputFile -Parent
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    $tag | Out-File -FilePath $OutputFile -Encoding UTF8 -NoNewline
    Write-Host "Tag saved to: $OutputFile"
}

Write-Output $tag
