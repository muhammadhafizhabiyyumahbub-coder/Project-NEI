# TASK: DIAGNOSIS DAN PERBAIKAN PEMANGGILAN RHINO 6 (OTONOM, DENGAN PENGAMAN)

Kamu adalah Senior Integration Engineer untuk NEI. Kerjakan tugas ini **sampai selesai tanpa menunggu persetujuan**, tetapi patuhi semua pengaman di bawah. Saya hanya akan membaca laporan akhirnya.

## MASALAH

`nei/connectors/rhino6/connector.py`, fungsi `_run_rhino_script`, memanggil:

    Rhino.exe -1 -r <script.py>

Efeknya di komputer saya: Rhino 6 membuka jendela GUI dan menampilkan dialog **"Unable to load nei_rhino_<id>.py.rhp plug-in: initialization failed"**. Rhino memperlakukan file script `.py` sebagai plug-in, bukan sebagai script yang dijalankan. Setiap pemanggilan menghasilkan dialog baru. Switch `-1` dan `-r` **tidak terverifikasi** sebagai switch command line Rhino 6. Klaim "Method 2 PASSED" di `environment.json` dan `docs/rhino_spike_report.md` hanya berlaku untuk eksekusi manual di dalam Rhino, bukan untuk pemanggilan command line connector.

Tujuan: temukan **pemanggilan yang terbukti bekerja** (dengan bukti file hasil), perbaiki connector, dan tambahkan pengaman serta tes.

## PENGAMAN WAJIB (TIDAK BOLEH DILANGGAR)

1. **Jangan pernah mematikan proses Rhino yang sudah berjalan sebelum kamu mulai.** Sebelum pengujian apa pun, cek `tasklist /FI "IMAGENAME eq Rhino.exe"`. Jika Rhino sudah berjalan, **jangan uji live**; lewati ke bagian "Jika uji live tidak dapat dilakukan" dan minta saya menutupnya di laporan akhir.
2. Hanya matikan proses Rhino yang **kamu sendiri mulai**, berdasarkan PID dari `Popen` (gunakan `taskkill /PID <pid> /T /F`). Jangan pernah `taskkill /IM Rhino.exe`.
3. Semua file uji hanya di folder temp khusus yang kamu buat (misalnya `%TEMP%\nei_rhino_cli_test\`). **Jangan menyentuh file produksi, folder proyek saya, atau file `.3dm` milik saya.**
4. Jangan mengedit registry Windows, file pengaturan Rhino, atau folder plug-in Rhino. Jika ada sisa plug-in palsu `nei_rhino_*` terdaftar, **laporkan** cara menghapusnya secara manual; jangan hapus sendiri.
5. Maksimal **10 percobaan live**, masing-masing timeout 60 detik. Hentikan percobaan jika muncul dialog yang tidak dikenal berulang kali.
6. Jangan menebak lalu menyatakan berhasil. "Berhasil" berarti file hasil JSON ditulis oleh script **di dalam Rhino** dan isinya benar (lihat kriteria di bawah).
7. Jangan mengubah backend di luar `nei/connectors/rhino6/`, tes terkait, dan dokumen yang disebut di bawah. Jangan mengubah skema database atau kontrak API.
8. Satu commit per butir kerja, pesan commit jelas. Jangan `git add -A`; tambahkan file secara spesifik.

## LANGKAH 1: KUMPULKAN KANDIDAT (tanpa menjalankan Rhino)

1. Baca `connector.py`, `docs/rhino_spike_report.md`, `environment.json`, dan tes yang ada.
2. Cari dokumentasi **resmi McNeel** untuk command line Rhino 6 (jika punya akses web), atau berkas bantuan Rhino 6 yang terpasang. Catat sumbernya. Jika tidak bisa mengakses dokumentasi, tandai semua kandidat **UNVERIFIED** dan gunakan percobaan berurutan dengan pengaman di atas.
3. Susun daftar kandidat pemanggilan (urut dari yang paling mungkin), misalnya variasi dari bentuk `Rhino.exe /nosplash /runscript="-_RunPythonScript ""<path>"""` dengan dan tanpa `/notemplate`, dan cara menutup Rhino setelah script selesai (script menutup Rhino sendiri, atau command `_Exit` pada runscript). Jangan menganggap bentuk ini benar; ini hanya kandidat yang harus diuji. Perhatikan penanganan tanda kutip pada path yang mengandung spasi.
4. Tulis skrip uji **disposable** (RhinoPython 2.7-compatible, tanpa f-string) yang hanya: membuat box 10 x 3 x 1 di dokumen kosong, membaca bounding box dan satuan, lalu menulis satu file JSON hasil ke folder uji. Script tidak menyimpan atau membuka file lain.

## LANGKAH 2: UJI LIVE BERURUTAN (jika pengaman 1 terpenuhi)

Untuk setiap kandidat, urut:
1. Pastikan tidak ada Rhino yang berjalan (kecuali yang kamu mulai).
2. Jalankan dengan `Popen`, catat PID, tunggu hingga file hasil muncul atau timeout 60 detik.
3. Catat: perintah persis, apakah dialog plug-in error muncul (jika bisa dideteksi), apakah file hasil ditulis, isi file hasil, kode keluar, dan lama waktu.
4. Pastikan proses Rhino yang kamu mulai sudah berakhir; jika belum, matikan berdasarkan PID.
5. Hapus file temp uji.

**Kandidat dinyatakan LULUS hanya jika:** file JSON hasil ditulis oleh script di dalam Rhino; `success` bernilai true; bounding box sama dengan 10 x 3 x 1 dalam toleransi 1e-6; satuan terbaca; tidak ada dialog "Unable to load ... plug-in"; dan Rhino berakhir bersih atau dapat diakhiri aman lewat PID. Jalankan kandidat lulus **tiga kali berturut-turut** untuk memastikan stabil.

Hentikan setelah ada kandidat yang lulus tiga kali, atau setelah 10 percobaan.

### Jika uji live tidak dapat dilakukan (Rhino sedang berjalan, atau tidak ada kandidat lulus)
- Jangan mengubah connector menjadi bentuk yang belum terbukti.
- Tulis dokumen dan skrip uji siap pakai (langkah 3 dan 4) supaya saya cukup menjalankannya, dan jelaskan apa yang harus saya lakukan di laporan akhir.
- Tetap kerjakan pengaman dan tes di Langkah 3 yang tidak bergantung pada pemanggilan benar.

## LANGKAH 3: PERBAIKI CONNECTOR (hanya bila ada kandidat LULUS)

1. Ganti pemanggilan di `_run_rhino_script` dengan bentuk yang terbukti. Semua pemanggil (`_create_box`, `_inspect_objects`, docinfo) memakai fungsi ini; pastikan semuanya tetap bekerja.
2. Pengaman runtime: jika proses Rhino yang dimulai connector melebihi timeout, matikan **hanya PID itu** (dengan seluruh pohon prosesnya), dan hapus file script serta file hasil sementara dalam blok `finally`. Jika Rhino sudah berjalan saat connector dipanggil, kembalikan error yang jelas ("Rhino sudah berjalan; tutup dulu atau gunakan mode lain") alih-alih menjalankan atau membunuhnya.
3. Nama file temp tidak boleh bergantung pada `id(self)`; gunakan UUID di folder temp khusus NEI.
4. Kembalikan error yang informatif jika file hasil tidak dibuat (timeout, Rhino gagal start), bukan hanya `None`.
5. Perbarui `docs/rhino_spike_report.md` dan `environment.json`: bedakan dengan tegas **"terbukti via eksekusi manual"** dan **"terbukti via command line connector"**, sertakan perintah yang terbukti, tanggal, dan hasil uji. Simpan log percobaan (tanpa data sensitif) di `docs/spike/rhino_cli_test.md`, termasuk percobaan yang gagal.

## LANGKAH 4: TES

- Tes unit (tanpa Rhino): subprocess di-mock; verifikasi bentuk perintah persis, penanganan path dengan spasi, pembersihan file temp saat timeout dan saat error, penolakan ketika Rhino sudah berjalan, dan hanya PID sendiri yang dimatikan.
- Satu tes integrasi live yang **dilewati secara default** dan hanya berjalan jika variabel lingkungan `NEI_LIVE_RHINO=1` diset; tes ini menjalankan skrip uji box dan memverifikasi hasilnya.
- Jalankan seluruh tes dan laporkan hasilnya apa adanya. Jangan melemahkan tes yang ada.

## DEFINISI SELESAI

- Ada pemanggilan Rhino yang terbukti (lulus tiga kali) dan digunakan oleh connector, **atau** ada penjelasan jujur mengapa belum bisa dibuktikan beserta langkah uji untuk saya.
- Tidak ada lagi dialog "Unable to load ... plug-in" pada pemanggilan connector.
- Pengaman keselamatan proses dan pembersihan file temp ada dan teruji.
- Dokumen spike dan environment.json tidak lagi mengklaim lebih dari yang terbukti.

## LAPORAN AKHIR (WAJIB)

1. Ringkasan satu paragraf: berhasil, sebagian, atau belum.
2. Tabel percobaan: perintah, hasil, bukti.
3. Perubahan file dan hasil tes.
4. Hal yang masih UNVERIFIED.
5. Tindakan yang harus saya lakukan secara manual (misalnya menutup Rhino, atau menghapus entri plug-in palsu `nei_rhino_*` di Tools > Options > Plug-ins), jika ada.
