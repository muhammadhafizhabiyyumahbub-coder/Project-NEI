# TASK: NEI ARCHITECTURE V2 — AUDIT DAN KOREKSI ARSITEKTUR (BERTAHAP, DENGAN GERBANG PERSETUJUAN)

Bertindaklah sebagai **Principal Software Architect, Systems Engineer, dan Engineering Software Integration Architect**.

Proyek: **NEI (Nautical Engineering Intelligence)**, local-first AI engineering assistant untuk Naval Architecture dan Marine Engineering. Pengembang tunggal: mahasiswa; semua berjalan di satu laptop.

Tugas ini adalah **audit dan dokumentasi arsitektur**. Jangan menulis kode aplikasi.

---

## 0. ATURAN KERJA DAN GERBANG PERSETUJUAN (WAJIB)

Pekerjaan dibagi empat tahap. **Berhenti di akhir Tahap 1 dan Tahap 2, lalu tunggu persetujuan eksplisit saya.** Jangan lanjut ke tahap berikutnya sebelum saya menulis "lanjut".

- Tahap 1: audit repository dan laporan temuan. **STOP.**
- Tahap 2: usulan keputusan arsitektur beserta alasan dan konsekuensi. **STOP.**
- Tahap 3: tulis semua dokumen (setelah persetujuan).
- Tahap 4: consistency audit dan laporan akhir.

Aturan tambahan:
- Satu commit per dokumen, dengan pesan commit yang menjelaskan isi.
- Jangan menghapus atau menimpa file lama sebelum memeriksa apakah masih dipakai. Dokumen yang diganti dipindahkan ke `docs/archive/` dan perubahan penting dicatat.
- Jika repository ternyata hampir kosong, katakan apa adanya; jangan mengisi laporan audit dengan temuan buatan.

---

## 1. KONTEKS

Lingkungan target:
- Windows 11, satu komputer, semua software lokal.
- Rhino 6, SOLIDWORKS 2022, Bentley Maxsurf 20 V8i.
- ANSYS: belum dikonfirmasi terpasang. **Status DEFERRED. Jangan buat connector ANSYS** sampai saya mengonfirmasi.
- Spesifikasi perangkat keras: **jangan ditebak dari dokumen lama; ukur** (lihat Phase 0). Sebagai peringatan awal, mesin pengembangan adalah laptop kelas menengah-bawah (Core i3 gen 8, RAM 8 GB, GPU MX230) sehingga anggaran sumber daya adalah kendala desain nyata.

NEI harus mampu: memahami instruksi engineering, membuat execution plan, mencari referensi teknis (jurnal, buku, standar, IMO, BKI, IACS), menghitung lewat deterministic calculation engine, mengontrol software lewat connector, memverifikasi hasil, menyimpan riwayat/sumber/perhitungan/file/audit log, dan menghasilkan laporan dengan provenance.

AI berperan sebagai planner, orchestrator, dan interpreter. AI **bukan** kalkulator yang menjadi sumber kebenaran numerik, bukan pengganti CAD/CAE, bukan lembaga klasifikasi, dan bukan otoritas pernyataan kepatuhan regulasi.

### Keputusan yang SUDAH saya tetapkan (jangan diubah tanpa alasan teknis tertulis)
- Backend: Python, FastAPI, Pydantic v2, SQLite, modular monolith.
- Frontend: React, TypeScript, Vite, Tailwind CSS, shadcn/ui, Lucide icons, TanStack Query, Recharts bila dibutuhkan.
- Desain: Hybrid AI Workspace + Engineering Workstation, profesional dan padat informasi, dark-first.
- Tipe TypeScript diusahakan dihasilkan dari OpenAPI backend.
- ANSYS ditunda.

---

## 2. KEDALAMAN SPESIFIKASI (PENTING)

Dokumen yang ditulis tanpa kode cepat menjadi basi. Karena itu:

- **Phase 0–2: spesifikasi PENUH dan konkret** (field, endpoint, tabel, komponen, state). Agen coding tidak boleh perlu menebak.
- **Phase 3 dan seterusnya: tingkat KEPUTUSAN.** Tulis keputusan, alasan, dependensi, daftar tabel/endpoint/halaman yang ditunda, dan **pertanyaan terbuka**. Jangan mengarang detail field untuk fase yang jauh.
- Setiap fakta hanya boleh didefinisikan di **satu** dokumen sumber; dokumen lain menautkan, bukan menyalin. Nyatakan di `ARCHITECTURE.md` dokumen mana yang menjadi sumber kebenaran untuk apa. Nyatakan juga bahwa setelah Phase 1, schema Pydantic dan migrasi database di kode menjadi sumber kebenaran, dan dokumen mencatat keputusan serta alasan.

---

## 3. ATURAN UTAMA

- Jangan mengarang kemampuan API software, spesifikasi, versi, atau kompatibilitas library.
- Versi library (Vite, Tailwind, shadcn/ui, TanStack Query, FastAPI, Pydantic, dll.) harus diverifikasi dari dokumentasi resmi atau registry paket sebelum dituliskan, **bukan dari ingatan model**. Jika tidak bisa diverifikasi, tulis `UNVERIFIED`.
- Jangan mengklaim connector berhasil sebelum ada pengujian nyata di mesin ini.
- Jangan membuat referensi jurnal, standar, klausul BKI, atau IMO fiktif. Dokumen protokol tidak boleh berisi daftar sumber yang diisi dari ingatan.
- Pisahkan secara eksplisit: **FAKTA TERVERIFIKASI**, **ASUMSI**, **KEPUTUSAN DESAIN**, dan **UNVERIFIED**.
- Jangan membuat microservices berlebihan. Jangan mengganti teknologi tanpa alasan teknis.
- Jangan bypass lisensi, aktivasi, proteksi, atau access control.
- Software yang terdeteksi tidak berarti API atau fiturnya tersedia.
- Jangan merekomendasikan satu metode integrasi sebelum ada bukti teknis atau eksperimen; jika belum pasti, tulis sebagai keputusan yang diselesaikan oleh spike.
- Setiap keputusan penting disertai alasan teknis dan konsekuensinya.

---

## 4. TAHAP 1 — AUDIT REPOSITORY

Sebelum mengubah apa pun:
1. Periksa seluruh struktur repository dan baca semua dokumentasi dan kode yang ada.
2. Identifikasi file kosong, duplikat, kontradiktif, tidak relevan (termasuk `Arsitektur.py` dan `FrontEnd.py` bila ada).
3. Identifikasi keputusan yang belum dibuat.
4. Tulis `ARCHITECTURE_AUDIT.md` dengan kategori CRITICAL, HIGH, MEDIUM, LOW, INFORMATIONAL.

### Temuan awal yang sudah diketahui (verifikasi masing-masing di repository)
1. Frontend belum punya spesifikasi (`FrontEnd.py` kosong).
2. Kontradiksi: dashboard wajib di Alpha milestone, tetapi `apps/ui` ditulis "optional later".
3. Urutan Alpha milestone tidak konsisten dengan roadmap (Alpha hanya butuh Rhino, roadmap menaruh Evidence Engine dan Engineering Core di depannya).
4. Kontrak API belum ada.
5. Skema database dan relasi belum ada.
6. State machine belum punya tabel transisi; "active state" belum didefinisikan.
7. Transport integrasi Rhino 6 belum diputuskan.
8. Verification Engine ada di diagram tetapi tidak punya modul dan kontrak di struktur repo (hanya `engineering/validation/`).
9. PLAN.md, IMPLEMENTATION_GUIDE.md, SECURITY.md, DATA_GOVERNANCE.md belum ada.
10. `Arsitektur.py` memakai path Linux (`/mnt/data/ARCHITECTURE.md`) yang tidak cocok untuk Windows.
11. `Arsitektur.py` memakai konversi Markdown-ke-Markdown lewat pypandoc yang tidak perlu dan menambah ketergantungan pada pandoc. Dokumen sebaiknya ditulis langsung sebagai `.md`.

### Audit tambahan WAJIB (belum ada di daftar di atas)
Periksa dan laporkan setidaknya:
- **Model proses dan sesi.** Aplikasi GUI seperti Rhino dan SOLIDWORKS umumnya hanya dapat diotomasi dari sesi desktop interaktif pengguna, bukan dari Windows service. Tentukan dan tandai `UNVERIFIED` sampai diuji: di mana backend berjalan, bagaimana COM/IPC dipanggil, thread/apartment, kunci per-aplikasi (satu operasi pada satu waktu), job panjang, dan pemulihan jika software hang atau menampilkan dialog modal.
- **Edisi dan lisensi.** Apakah edisi terpasang (misalnya akademik/student) mengizinkan otomasi atau API? Jangan diasumsikan; catat sebagai `UNVERIFIED` dan sebutkan dokumentasi vendor yang harus dicek. Tanpa bypass apa pun.
- **Anggaran sumber daya.** Apakah Rhino, SOLIDWORKS, Maxsurf, backend, dev server Vite, dan browser dapat berjalan bersamaan di mesin ini? Rancang `resource_manager` dan kebijakan "satu software berat per waktu" bila tidak. Tentukan strategi LLM: LLM lokal kemungkinan tidak praktis, jadi tentukan provider eksternal, data apa yang boleh dikirim, dan mode privasi.
- Risiko drift antar dokumen (lihat bagian 2) dan duplikasi isi antara ARCHITECTURE.md lama dengan dokumen baru (misalnya EEP).
- Keamanan server lokal: binding localhost, DNS rebinding, CSRF, origin check.
- Konkurensi SQLite (mode WAL, penulis tunggal), integritas file artifact, backup.
- Setiap masalah lain yang kamu temukan. Jangan membatasi diri pada daftar ini.

**Akhiri Tahap 1 dengan laporan ringkas, lalu BERHENTI.**

---

## 5. TAHAP 2 — USULAN KEPUTUSAN ARSITEKTUR

Untuk setiap keputusan: opsi yang dipertimbangkan, rekomendasi, alasan teknis, konsekuensi, dan status (FAKTA / ASUMSI / KEPUTUSAN / UNVERIFIED). Cakup minimal:
- Batas sistem, arah dependensi modul, dan lokasi repository tiap modul di diagram.
- Model proses dan sesi, locking, dan recovery.
- Auth lokal, CORS, CSRF, SSE atau WebSocket, envelope respons, error schema, pagination, idempotency, timeout, retry, versioning API.
- ID (UUID atau integer), konvensi timestamp, strategi kolom JSON, migrasi, manifest artifact, hash file, backup/restore, retensi.
- Roadmap yang diusulkan (bagian 7) dan definisi Alpha 0.1.
- Daftar spike dan kriteria lulus tiap spike.

**Akhiri dengan usulan dan pertanyaan terbuka, lalu BERHENTI menunggu "lanjut".**

---

## 6. TAHAP 3 — DOKUMEN YANG DITULIS

Hasilkan dokumen berikut (kedalaman mengikuti bagian 2). Jangan membuat file kosong atau placeholder yang seolah selesai; bagian yang ditunda ditulis sebagai "DEFERRED" beserta alasan.

1. `ARCHITECTURE_AUDIT.md` (dari Tahap 1, diperbarui)
2. `ARCHITECTURE.md`: visi produk, batas sistem, prinsip, arsitektur tingkat tinggi, tanggung jawab dan lokasi tiap modul, arah dependensi, alur data dan eksekusi, penanganan error, recovery, batas keamanan, audit dan observability, deployment local-first, keputusan teknologi, fitur ditunda, dan peta "dokumen sumber kebenaran".
3. `FRONTEND_SPEC.md`:
   - **Spesifikasi penuh** untuk: application shell, navigasi, Dashboard, koneksi health API, design tokens, library komponen, state loading/empty/error/offline, integrasi API (TanStack Query, tipe dari OpenAPI), event streaming, dialog approval, aksesibilitas, struktur folder, dan milestone UI.
   - **Tingkat keputusan** untuk: AI Workspace, Project Manager, Engineering Knowledge, Calculation Center, Software Control, Verification & Reports, Settings. Jelaskan tujuan, komponen utama, dan state kunci, serta tandai detail lanjutan sebagai DEFERRED.
   - Responsive behavior secukupnya untuk desktop dan laptop; mobile bukan prioritas (nyatakan sebagai keputusan).
4. `API_SPEC.md`: keputusan eksplisit (REST, SSE/WebSocket, auth lokal, CORS, CSRF, validasi, envelope, error schema, pagination, idempotency, timeout, retry, versioning). Endpoint untuk Phase 1–2 lengkap dengan method, path, tujuan, schema request/response, error cases, dan risk level. Endpoint fase lanjut hanya daftar plus fase target.
5. `DATABASE_SCHEMA.md`: SQLite. Tabel Phase 1–2 lengkap (kolom, PK, FK, indeks, constraint). Tabel fase lanjut hanya daftar, kebutuhan, dan relasi. Untuk setiap tabel, jelaskan kenapa ada; jangan membuat tabel hanya karena namanya ada di daftar kandidat (projects, project_files, tasks, task_steps, task_events, approvals, connectors, connector_probes, evidence_sources, evidence_chunks, formulas, methods, calculation_runs, calculation_inputs, calculation_results, artifacts, audit_events, model_usage, settings).
6. `STATE_MACHINE_SPEC.md`: tabel transisi (state saat ini, event, guard, state berikut, side effect, perilaku gagal) untuk PENDING, PLANNING, NEEDS_INPUT, VALIDATING, WAITING_APPROVAL, QUEUED, RUNNING, VERIFYING, COMPLETED, FAILED, CANCELLED, NEEDS_REVIEW, RECOVERING. Jelaskan status aktif dan terminal, jalur kembali dari NEEDS_INPUT, jalur dari RECOVERING, kapan NEEDS_REVIEW dipakai, timeout, retry dan execution attempt, cancellation, idempotency, audit tiap transisi. Script yang sukses tidak otomatis COMPLETED; harus ada verifikasi postcondition.
7. `RHINO6_INTEGRATION_SPIKE.md`: bandingkan (1) RhinoCommon/plugin .NET, (2) RhinoPython, (3) command-based automation, (4) IPC lokal, (5) GUI automation sebagai fallback. Per metode: kompatibilitas Rhino 6, runtime, kelebihan/kekurangan, keamanan, stabilitas, pengiriman parameter, penerimaan hasil, deteksi kegagalan, verifikasi geometri, biaya. Klaim kompatibilitas yang tidak bisa dibuktikan dari dokumentasi resmi atau eksperimen ditulis `UNVERIFIED`. **Jangan merekomendasikan satu metode sebelum eksperimen berjalan.** Rancang eksperimen aman: detect Rhino, buka dokumen disposable, buat box 10 x 3 x 1, baca bounding box, verifikasi dimensi dan unit, simpan sebagai file baru, jangan sentuh file produksi. Tulis kriteria lulus dan gagal untuk tiap metode.
8. `CONNECTOR_SPEC.md`: kontrak umum connector; SOLIDWORKS 2022 (COM/API terdokumentasi, probe versi dan kemampuan, read-only dahulu, part disposable bila didukung, jangan asumsikan pywin32 atau COM bekerja sebelum diuji); Maxsurf v8.1 (berdasarkan dokumentasi resmi dan instalasi aktual, file exchange, GUI fallback, jangan klaim public API tanpa bukti); ANSYS DEFERRED. Capability registry dengan status `SUPPORTED`, `UNSUPPORTED`, `UNKNOWN`, `UNAVAILABLE` (default `UNKNOWN`).
9. `VERIFICATION_SPEC.md`: pisahkan verifikasi eksekusi script, operasi connector, geometri, kalkulasi, sumber/evidence, dan validasi hasil engineering. Setiap verification record memuat: target, kondisi yang diharapkan, observasi aktual, toleransi, metode, hasil, evidence, timestamp, software/versi, status. Tentukan modul dan lokasinya di repository.
10. `ENGINEERING_EVIDENCE_PROTOCOL.md`: protokol, bukan daftar sumber. Metadata sumber, validasi sumber, status evidence, record formula (ID, versi, persamaan, variabel dan satuan, asumsi, applicability, referensi sumber, halaman/bagian/klausul, implementasi, unit test, reference case, review status), lifecycle `DRAFT -> SOURCE_ATTACHED -> IMPLEMENTED -> UNIT_TESTED -> REFERENCE_CASE_TESTED -> TECHNICAL_REVIEW -> APPROVED_FOR_USE`. LLM tidak boleh menaikkan status formula. Hasil hitung tidak berarti memenuhi regulasi.
11. `SECURITY.md`: local-only binding, auth, batas akses file dan direktori, pembatasan eksekusi script, secret management, pengungkapan data ke LLM eksternal, audit log, approval policy, recovery.
12. `DATA_GOVERNANCE.md`: integritas file, hash, backup, restore, retensi, hak atas dokumen sumber (hanya simpan yang berhak dipakai).
13. `PLAN.md`: roadmap dengan dependensi (bagian 7).
14. `IMPLEMENTATION_GUIDE.md`: panduan untuk OpenCode, hanya konkret untuk Phase 0–2 (urutan kerja, struktur folder, perintah, tes yang harus lulus, definisi selesai), dan aturan "berhenti dan lapor" setiap akhir fase.

Perbarui `README.md` (proyek dan dokumen utama). Pada `Arsitektur.py`: jangan dihapus dulu; periksa apakah masih dipakai, dan jika diganti, pindahkan ke `docs/archive/` dan catat.

---

## 7. ROADMAP YANG DIUSULKAN (evaluasi, ubah bila dependensi mengharuskan, jelaskan alasannya)

Prinsip urutan: **risiko tertinggi dibuktikan lebih awal; fitur terlihat tidak boleh mengorbankan dependensi.**

- **Phase 0 — Audit repository, environment, dan spike risiko.**
  - Laporan environment (Python, versi dan jalur software, ukuran hardware) dan pengukuran sumber daya saat software dijalankan bersamaan.
  - **Spike Rhino 6** (mandiri, tanpa backend) sesuai `RHINO6_INTEGRATION_SPIKE.md`.
  - **Probe saja** untuk SOLIDWORKS dan Maxsurf: terdeteksi? versi? apakah ada antarmuka otomasi terdokumentasi? Tanpa operasi pada dokumen.
  - Cek kebijakan edisi/lisensi terhadap otomasi (dokumen vendor).
- **Phase 1 — Backend foundation:** FastAPI, SQLite, kontrak Pydantic, state machine, audit logging, artifact storage, health endpoint.
- **Phase 2 — Frontend foundation:** React + TypeScript, shell, Dashboard, integrasi health, navigasi dasar, tipe dari OpenAPI.
- **Phase 3 — Kerangka verifikasi minimal dan connector Rhino 6** (memakai hasil spike) = **Alpha 0.1** (definisi di bawah).
- **Phase 4 — Evidence engine dan EEP.**
- **Phase 5 — Engineering core deterministik (satuan, formula lifecycle, reference case) dan verifikasi kalkulasi.**
- **Phase 6 — Connector SOLIDWORKS 2022.**
- **Phase 7 — Connector Maxsurf v8.1.**
- **Phase 8 — Workflow lintas software.**
- **Phase 9 — Domain engineering lanjutan.**

### Definisi Alpha 0.1 (harus ditulis eksplisit di PLAN.md)
Pengguna membuka dashboard, membuat project, meminta box uji 10 x 3 x 1 di Rhino 6; planner terstruktur (template, bukan LLM menulis kode bebas); policy gate memeriksa aksi dan path; connector membuat objek di dokumen disposable; verifikasi memeriksa bounding box, jumlah objek, dan unit dari **hasil Rhino, bukan stdout script**; artifact `.3dm` baru dan manifest tersimpan; dashboard menampilkan hasil, hash script, dan log eksekusi; tidak ada file asli yang ditimpa. Alpha 0.1 **tidak** membutuhkan evidence engine atau engineering core.

Untuk setiap fase tulis: dependensi, deliverable, kriteria diterima, risiko, dan apa yang secara sengaja belum termasuk.

---

## 8. TAHAP 4 — VALIDASI KONSISTENSI

Periksa dan laporkan dalam `ARCHITECTURE_CONSISTENCY_REPORT.md`:
1. Nama modul dan folder konsisten di semua dokumen.
2. Setiap modul di diagram punya lokasi dan tanggung jawab di repository.
3. Endpoint cocok dengan kebutuhan frontend.
4. Schema request/response cocok dengan model Pydantic yang direncanakan.
5. State machine cocok dengan task API.
6. Database mendukung task, audit, dan verifikasi.
7. Approval policy konsisten dengan risk level L0–L3.
8. Capability connector cocok dengan tool router.
9. Verification engine cocok dengan task lifecycle.
10. Roadmap sesuai dependensi dan Alpha 0.1 konsisten dengan fase.
11. ANSYS tetap DEFERRED.
12. Tidak ada klaim API atau versi library yang belum dibuktikan.
13. Tidak ada fakta yang didefinisikan ulang di lebih dari satu dokumen sumber.

Jangan menyatakan semuanya konsisten jika masih ada konflik; daftarkan konflik yang belum selesai.

---

## 9. FORMAT LAPORAN AKHIR

Laporkan: dokumen dibuat, dokumen diperbarui, keputusan arsitektur yang ditetapkan, kontradiksi yang diselesaikan, hal yang masih `UNVERIFIED`, risiko teknis tertinggi, hasil consistency audit, dan rekomendasi langkah berikutnya untuk OpenCode.

**Standar keberhasilan:** dengan dokumen ini, OpenCode dapat mengerjakan Phase 0–2 tanpa menebak keputusan arsitektur apa pun. Untuk fase berikutnya, dokumen menyatakan dengan jelas keputusan yang sudah diambil, keputusan yang menunggu hasil spike, dan pertanyaan yang masih terbuka.
