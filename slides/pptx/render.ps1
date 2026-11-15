# Export every slide of the deck to PNG with the local PowerPoint (visual QA). Usage: powershell -File slides/pptx/render.ps1
$deck = Join-Path $PSScriptRoot 'open_llm_clinical_ie_review.pptx'
$out = Join-Path $PSScriptRoot 'qa'
if (Test-Path $out) { Remove-Item -Recurse -Force $out }
New-Item -ItemType Directory -Force $out | Out-Null
$app = New-Object -ComObject PowerPoint.Application
try {
  $p = $app.Presentations.Open($deck, $true, $false, $false)
  $p.Export($out, 'PNG', 1600, 900)
  $p.Close()
} finally { $app.Quit() }
Get-ChildItem $out | Select-Object -ExpandProperty Name
