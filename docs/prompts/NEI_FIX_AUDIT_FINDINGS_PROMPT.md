Kamu adalah Senior Backend/Security Engineer untuk NEI (Nautical Engineering Intelligence).

Tugas ini **hanya memperbaiki temuan audit**. **Jangan menambah fitur, jangan memulai phase berikutnya, jangan mengubah skema database atau kontrak API tanpa izin eksplisit saya.**

Temuan di bawah berasal dari audit kode yang sudah di-push ke GitHub dan mungkin tidak lagi akurat pada kondisi lokal saat ini. **Verifikasi setiap temuan dulu di kode aktual. Jika temuan sudah tidak berlaku, tulis "TIDAK BERLAKU" beserta bukti (file dan baris). Jangan memperbaiki hal yang tidak rusak.**

---

## ATURAN

- Verifikasi dulu, baru perbaiki. Jangan mengklaim sesuatu sudah benar tanpa bukti (kutipan kode atau hasil tes).
- Setiap perbaikan keamanan harus punya **tes otomatis yang gagal sebelum perbaikan dan lulus sesudahnya**.
- Satu commit per butir, pesan commit menyebut nomor butir.
- Jangan menghapus tes atau melemahkan assertion agar lulus.
- Target runtime: Python 3.13 (sesuai `pyproject.toml`).
- Jangan menjalankan operasi pada Rhino, SOLIDWORKS, atau Maxsurf sebagai bagian dari tugas ini.
- **BERHENTI setelah TAHAP 1 (laporan verifikasi) dan tunggu persetujuan saya.**

---

## TAHAP 1 — VERIFIKASI (lalu BERHENTI)

Untuk setiap butir 1–11: status (BERLAKU / TIDAK BERLAKU / SEBAGIAN), bukti, dan rencana perbaikan singkat. Jalankan seluruh tes dan laporkan hasilnya apa adanya.

## TAHAP 2 — PERBAIKAN (setelah saya setuju)

### Butir 1 (HIGH): sandbox path di `nei/core/policy.py`
`validate_sandbox_path` memakai `PureWindowsPath.relative_to`, yang tidak merapikan `..`. Path seperti `D:\proyek\..\lain` kemungkinan lolos. Perbaiki dengan normalisasi dan resolve sebelum perbandingan (termasuk symlink/junction bila relevan), perbandingan yang tidak peka huruf besar-kecil sesuai Windows, dan penolakan jika akar sandbox tidak valid. Tes minimal: `..` di tengah dan di akhir, path absolut di luar akar, drive berbeda, UNC, trailing separator, huruf besar-kecil berbeda, path relatif yang keluar akar, dan path yang sah tetap lolos.

### Butir 2 (HIGH): endpoint `POST /tasks/{id}/execute`
Verifikasi apakah `body.action` dan `body.params` dibatasi allowlist, apakah parameter divalidasi (tipe, rentang, path lewat sandbox), apakah risk level dan policy gate dipakai, apakah ada approval untuk level yang menuntutnya, apakah ada audit event, dan apakah transisi state lewat state machine. Aksi di luar allowlist harus ditolak. Jangan menjalankan perintah atau script sembarang dari request. Laporkan celah sebelum memperbaiki.

### Butir 3 (HIGH): `POST /formulas/{id}/advance`
Status formula tidak boleh naik secara otomatis oleh LLM. Verifikasi: siapa yang boleh memanggil, apakah lompat tahap dicegah, apakah ada pelaku (actor) manusia dan audit event, dan apakah syarat tiap tahap (sumber, unit test, reference case, review) diperiksa. Perbaiki bila ada celah.

### Butir 4 (MEDIUM): rahasia sesi dan autentikasi
`session_secret` default "insecure-change-me" tanpa pemeriksaan. Aplikasi harus menolak start (atau memberi peringatan keras sesuai mode) bila rahasia masih default di luar mode dev. Periksa apakah middleware autentikasi sesuai `SECURITY.md` sudah ada; jika belum, laporkan sebagai gap dan usulkan, **jangan mengimplementasikan model auth baru tanpa persetujuan**. Verifikasi server mengikat ke `127.0.0.1` dan kebijakan CORS.

### Butir 5 (MEDIUM): drift dokumen dan kode
`ARCHITECTURE_CONSISTENCY_REPORT.md` membandingkan dokumen dengan dokumen. Tulis `ARCHITECTURE_CODE_DRIFT.md` yang membandingkan dokumentasi dengan **struktur dan endpoint kode aktual** (misalnya `apps/api/` vs `nei/api/`, `nei/execution/policy.py` vs `nei/core/policy.py`). Jangan memindahkan kode; usulkan apakah dokumen atau kode yang disesuaikan.

### Butir 6 (MEDIUM): endpoint vs `API_SPEC.md`
Bandingkan endpoint yang diimplementasikan dengan spec Phase 1–2 (termasuk approvals, provide-input, retry, dan endpoint yang ditandai Phase 1–2). Laporkan yang belum ada. Implementasikan hanya yang saya setujui.

### Butir 7 (MEDIUM): versi Python
README menyebut Python 3.12, `pyproject.toml` meminta 3.13 atau lebih baru. Samakan semua dokumen dan konfigurasi ke versi yang benar-benar dipakai.

### Butir 8 (LOW): nama Maxsurf
Perbarui semua dokumen dan kode yang masih menyebut "Maxsurf Enterprise v8.1" atau path bernama `maxsurf81` agar sesuai deteksi aktual (Maxsurf 20 V8i). Jangan mengubah nama modul yang sudah dipakai kode tanpa menjalankan tes.

### Butir 9 (LOW): path build statis
`static_build_path` default `frontend/dist`, padahal UI di `apps/ui`. Sesuaikan dengan lokasi build yang sebenarnya.

### Butir 10 (LOW): bukti spike dan metadata
- Simpan hasil spike (JSON hasil box test, tanpa data sensitif) di `docs/spike/` agar klaim "PASSED" dapat diperiksa dari repo.
- `environment.json` memiliki `generated_at` bernilai placeholder (`00:00:00Z`); perbaiki atau tandai.

### Butir 11 (LOW): kerapian repo
Pindahkan `NEI_ARCHITECTURE_V2_PROMPT.md` dari root ke `docs/prompts/` agar tidak terbaca sebagai dokumen arsitektur.

---

## DEFINISI SELESAI
- Setiap butir berstatus diperbaiki, tidak berlaku (dengan bukti), atau ditunda (dengan alasan).
- Semua tes lulus, termasuk tes baru untuk butir 1–4.
- Tidak ada fitur baru, tidak ada perubahan skema atau kontrak API tanpa izin.

## LAPORAN AKHIR
Per butir: status, perubahan (file), tes yang ditambahkan, hasil tes, dan hal yang masih terbuka. Sebut dengan jelas jika ada yang tidak dapat diverifikasi.