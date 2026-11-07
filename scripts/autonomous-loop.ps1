param(
  [string]$InitialTask = "",
  [string]$ContinueTask = "",
  [int]$DelaySeconds = 5,
  [int]$MaxRetries = 3
)

Set-Location "D:\Project NEI"

if ([string]::IsNullOrWhiteSpace($InitialTask)) {
  $InitialTask = @"
Lanjutkan pekerjaan NEI di D:\Project NEI sampai selesai tanpa berhenti atau banyak bertanya.

Baca README.md, PLAN.md, IMPLEMENTATION_GUIDE.md, dan spesifikasi relevan. Kerjakan task berikutnya yang belum selesai. Untuk setiap masalah yang selesai, commit perubahan ke Git dan push ke remote bila tersedia. Lanjut ke task berikutnya sampai seluruh rencana selesai atau ada blocker nyata.

Jangan berhenti hanya untuk laporan progres. Verifikasi pekerjaan dengan test/verification sebelum commit. Berhenti hanya jika semua task selesai, ada blocker nyata, atau manusia menekan Ctrl+C.
"@
}

if ([string]::IsNullOrWhiteSpace($ContinueTask)) {
  $ContinueTask = @"
Lanjutkan NEI sampai selesai.

Ambil task berikutnya dari kondisi repo dan PLAN.md. Selesaikan masalah, jalankan test/verification, commit semua perubahan yang berhasil, push ke remote bila tersedia, update PLAN.md, lalu lanjut ke task berikutnya.

Jangan berhenti atau banyak bertanya. Berhenti hanya jika semua task selesai, ada blocker nyata, atau manusia menekan Ctrl+C.
"@
}

$first = $true
$retryCount = 0
Write-Host "NEI autonomous loop started. Press Ctrl+C to stop." -ForegroundColor Cyan

while ($true) {
  try {
    if ($first) {
      opencode run --auto --format default --title "NEI Autonomous Work" $InitialTask
      $first = $false
    } else {
      opencode run --auto --continue --format default $ContinueTask
    }

    if ($LASTEXITCODE -ne 0) {
      $retryCount++
      Write-Warning "OpenCode exited with code $LASTEXITCODE. Retry $retryCount/$MaxRetries."
      if ($retryCount -ge $MaxRetries) {
        Write-Error "OpenCode failed $MaxRetries times. Loop stopped."
        break
      }
    } else {
      $retryCount = 0
    }
  } catch {
    $retryCount++
    Write-Warning $_.Exception.Message
    if ($retryCount -ge $MaxRetries) { break }
  }
  Start-Sleep -Seconds $DelaySeconds
}
