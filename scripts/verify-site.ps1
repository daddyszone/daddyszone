$ErrorActionPreference = 'Stop'

$siteRoot = Join-Path $PSScriptRoot '..\dist'
$requiredFiles = @('index.html', '404.html', 'robots.txt', 'sitemap.xml', 'favicon.svg', 'CNAME')

foreach ($file in $requiredFiles) {
    $path = Join-Path $siteRoot $file
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Missing required site file: $file"
    }
}

$index = Get-Content -Raw -LiteralPath (Join-Path $siteRoot 'index.html')
foreach ($needle in @('<main', 'meta name="description"', 'rel="canonical"', 'og:title', 'prefers-reduced-motion')) {
    if ($index -notmatch [regex]::Escape($needle)) {
        throw "index.html is missing expected markup: $needle"
    }
}

Write-Host 'Static site verification passed.'

