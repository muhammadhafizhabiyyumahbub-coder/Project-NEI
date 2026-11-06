param(
  [string]$InitialTask = "",
  [string]$ContinueTask = "",
  [int]$DelaySeconds = 5,
  [int]$MaxRetries = 3
)

Set-Location "D:\Project NEI"

if ([string]::IsNullOrWhiteSpace($InitialTask)) {
  $InitialTask = @"
Kamu bekerja sebagai autonomous coding agent untuk project NEI di D:\Project NEI.

Tujuan: kerjakan project sampai selesai tanpa meminta konfirmasi rutin.

Aturan kerja:
1. Baca README.md, PLAN.md, IMPLEMENTATION_GUIDE.md, dan spesifikasi yang relevan.
2. Pilih task berikutnya yang belum selesai dari PLAN.md berdasarkan dependency dan prioritas.
3. Implementasikan task tersebut, bukan hanya membuat rencana.
4. Jalankan test, lint, type check, atau verification yang relevan.
5. Jika gagal, diagnosis dan perbaiki lalu jalankan ulang.
6. Update PLAN.md dan dokumentasi setelah task selesai.
7. Buat checkpoint Git setelah perubahan stabil.
8. Lanjutkan langsung ke task berikutnya tanpa menunggu instruksi manusia.
9. Jangan berhenti hanya untuk memberikan laporan progres.
10. Jangan mengarang hasil test atau menyatakan selesai tanpa verifikasi.

Berhenti hanya jika semua task yang dapat dikerjakan selesai, ada blocker nyata yang membutuhkan keputusan/credential/perangkat manusia, provider error berulang, atau manusia menekan Ctrl+C.
"@
}

if ([string]::IsNullOrWhiteSpace($ContinueTask)) {
  $ContinueTask = @"
Lanjutkan autonomous work pada D:\Project NEI.

Baca kondisi repo saat ini dan PLAN.md. Ambil task berikutnya yang belum selesai. Implementasikan, jalankan test/verification, perbaiki kegagalan, update PLAN.md, buat checkpoint Git, lalu lanjutkan ke task berikutnya.

Jangan hanya melaporkan hasil dan jangan meminta konfirmasi rutin. Berhenti hanya untuk blocker nyata, provider error berulang, semua task selesai, atau Ctrl+C.
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
