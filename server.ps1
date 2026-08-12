# AI 면접 시스템 - Windows 내장 서버 (설치 불필요)
# start_windows.bat 이 자동으로 실행합니다.

$port = 8000
$root = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "deploy"

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://localhost:$port/")

try {
    $listener.Start()
} catch {
    Write-Host ""
    Write-Host "  서버를 시작하지 못했습니다. 8000번 포트를 다른 프로그램이 쓰고 있을 수 있습니다."
    Write-Host "  실행 중인 다른 서버를 끄고 다시 시도해 주세요."
    Write-Host ""
    Read-Host "  엔터를 누르면 닫힙니다"
    exit
}

Write-Host ""
Write-Host "  서버 실행 중 ...  http://localhost:$port"
Write-Host "  이 창을 닫으면 면접 프로그램이 중단됩니다."
Write-Host "  종료하려면 Ctrl + C 를 누르세요."
Write-Host ""

Start-Process "http://localhost:$port/"

$mime = @{
    ".html" = "text/html; charset=utf-8"
    ".js"   = "text/javascript; charset=utf-8"
    ".css"  = "text/css; charset=utf-8"
    ".mp4"  = "video/mp4"
    ".webm" = "video/webm"
    ".mp3"  = "audio/mpeg"
    ".png"  = "image/png"
    ".jpg"  = "image/jpeg"
    ".jpeg" = "image/jpeg"
    ".svg"  = "image/svg+xml"
    ".md"   = "text/plain; charset=utf-8"
}

while ($listener.IsListening) {
    try {
        $ctx = $listener.GetContext()
        $rel = [System.Uri]::UnescapeDataString($ctx.Request.Url.AbsolutePath)
        if ($rel -eq "/") { $rel = "/index.html" }
        $file = Join-Path $root ($rel.TrimStart("/") -replace "/", "\")

        if (Test-Path -LiteralPath $file -PathType Leaf) {
            $ext = [System.IO.Path]::GetExtension($file).ToLower()
            if ($mime.ContainsKey($ext)) {
                $ctx.Response.ContentType = $mime[$ext]
            } else {
                $ctx.Response.ContentType = "application/octet-stream"
            }
            $bytes = [System.IO.File]::ReadAllBytes($file)
            $ctx.Response.ContentLength64 = $bytes.Length
            $ctx.Response.OutputStream.Write($bytes, 0, $bytes.Length)
        } else {
            $ctx.Response.StatusCode = 404
        }
        $ctx.Response.Close()
    } catch {
        # 브라우저가 연결을 끊는 경우가 있어 무시하고 계속 대기
    }
}
