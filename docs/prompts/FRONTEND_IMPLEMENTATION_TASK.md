# TASK: IMPLEMENT NEI FRONTEND — PHASE 2 (REVISI)

Kamu bertindak sebagai Senior Frontend Engineer sekaligus UI/UX Designer untuk project NEI (Nautical Engineering Intelligence).

Implementasikan frontend NEI sebagai kode yang dapat dijalankan di repository yang sudah ada. Jangan membuat hanya mockup, screenshot, atau dokumentasi.

---

## 0. ATURAN TAMBAHAN (mengesampingkan bagian lain yang bertentangan)

- **Maxsurf yang terpasang adalah Maxsurf 20 V8i** (versi 20.00.01.59 menurut `environment.json`), bukan "Maxsurf Enterprise v8.1". Gunakan nama dan versi dari data backend jika tersedia; jika tidak, tampilkan "Maxsurf 20 V8i".
- **FRONTEND_SPEC.md adalah sumber kebenaran design tokens dan perilaku halaman.** Palet di bagian 3 hanyalah usulan awal. Jika berbeda dengan FRONTEND_SPEC.md, laporkan perbedaannya pada akhir Phase A dan tunggu keputusan; jangan memilih diam-diam.
- **Stack:** React, TypeScript, Vite, Tailwind CSS, shadcn/ui, Lucide, TanStack Query, React Router. shadcn/ui belum terpasang; pasang secara terkontrol hanya komponen yang dipakai. Periksa apakah `tailwind.config.js` masih relevan karena `package.json` memakai Tailwind v4 lewat `@tailwindcss/vite`; laporkan temuannya.
- **Tipe API harus berasal dari OpenAPI** (`apps/ui/openapi.json` melalui `generate-types.mjs`), bukan ditulis tangan. Jika tipe hasil generate tidak cocok dengan respons backend aktual, laporkan sebagai ketidaksesuaian; jangan diam-diam diubah.
- **Versi dependency:** verifikasi dari registry npm atau dokumentasi resmi sebelum menambah atau mengubah versi. Jangan menebak versi.
- **Dashboard:** backend saat ini hanya punya daftar task per project dan belum tentu punya endpoint ringkasan. **Jangan menghitung Active/Completed/Failed lewat banyak request tersembunyi.** Tampilkan UNAVAILABLE dengan penjelasan, dan catat endpoint yang dibutuhkan di `docs/FRONTEND_API_GAPS.md`.
- **Backend tidak boleh diubah** di task ini. Semua kebutuhan backend dicatat di `docs/FRONTEND_API_GAPS.md`.
- Kondisi awal: `apps/ui/src/App.tsx` masih template bawaan Vite. Anggap frontend Phase 2 **belum selesai** meskipun scaffold, hooks, dan API client sudah ada. Jangan menghapus yang berfungsi (hooks, `api/client.ts`) tanpa alasan teknis tertulis.
- **BERHENTI setelah PHASE A** dan tunggu persetujuan saya sebelum PHASE B.

---

## 1. LANGKAH PERTAMA: AUDIT PROJECT (PHASE A)

Sebelum mengubah kode:

1. Baca README.md, PLAN.md, ARCHITECTURE.md, FRONTEND_SPEC.md, API_SPEC.md, IMPLEMENTATION_GUIDE.md.
2. Periksa `apps/ui/` (struktur, komponen, hooks, API client, package.json, konfigurasi Vite dan Tailwind).
3. Periksa backend dan endpoint aktual (`nei/api/`, `nei/connectors/`). Jangan mengasumsikan endpoint ada hanya karena tercantum di dokumentasi.
4. Jalankan `npm ci` (atau `npm install`), TypeScript check, dan build pada kondisi awal. Catat hasilnya apa adanya.

Buat pemetaan singkat:
- Komponen yang sudah ada dan yang perlu dibuat.
- Endpoint yang benar-benar tersedia dan yang belum.
- Ketidaksesuaian antara dokumentasi dan implementasi (termasuk palet vs FRONTEND_SPEC, tailwind config, tipe OpenAPI vs respons aktual).
- Rencana implementasi per fase, dan pertanyaan terbuka.

**STOP. Tunggu persetujuan sebelum PHASE B.**

---

## 2. TUJUAN DESAIN

NEI harus terlihat seperti professional naval engineering workstation, bukan template dashboard.

- Dark-first, estetika software engineering profesional, modern, minimalis, presisi, informatif.
- Kepadatan informasi tinggi tetapi mudah dibaca.
- Aksen biru untuk interaksi utama; warna status konsisten.
- Sidebar permanen, layout responsif untuk desktop dan laptop (mobile bukan prioritas).
- Tipografi dan spacing konsisten di semua halaman.

Hindari: tampilan marketing, gradient berlebihan, terlalu banyak kartu membulat, animasi dekoratif, emoji sebagai icon, dan data statistik palsu yang tampak seperti data aktual.

Gunakan Lucide icons yang sudah terpasang.

## 3. DESIGN SYSTEM

Buat design system terpusat (tokens), bukan warna acak per komponen. Usulan awal (tunduk pada FRONTEND_SPEC.md):

- Background: main `#0B1120`, sidebar `#0F172A`, panel `#111C2E`, elevated `#172338`.
- Border: `#263449`.
- Teks: primary `#E5EDF7`, secondary `#94A3B8`, muted `#64748B`.
- Aksen: blue `#3B82F6`, hover `#2563EB`.
- Status: success `#22C55E`, warning `#F59E0B`, error `#EF4444`, info `#38BDF8`.

Tokens untuk: warna, tipografi, spacing, radius, shadow, dan state komponen. Pastikan kontras teks memadai (aksesibilitas).

## 4. APPLICATION LAYOUT

**Sidebar:** logo NEI dan "Nautical Engineering Intelligence"; indikator koneksi backend; navigasi (Dashboard, AI Workspace, Projects, Engineering Knowledge, Calculation Center, Software Control, Verification & Reports, Settings); di bagian bawah status backend dan versi aplikasi bila tersedia.

Prioritas implementasi: **Dashboard, Projects, Connectors (Software Control), Settings.** Halaman lain berupa placeholder konsisten yang **jelas menyatakan belum tersedia**, tanpa berpura-pura punya fungsi.

**Topbar:** nama halaman, breadcrumb, indikator koneksi backend, tombol refresh bila relevan, indikator notifikasi hanya jika sistemnya ada.

**Main content:** layout fleksibel dan konsisten.

## 5. DASHBOARD

Semua status harus berasal dari API aktual. Jika data tidak ada, tampilkan UNKNOWN atau UNAVAILABLE beserta alasannya. Jangan membuat angka palsu.

- **System Overview:** status backend (dari `/health`), status database dan AI provider bila tersedia, ringkasan task sesuai aturan di bagian 0.
- **Recent Tasks:** ID, nama, status, waktu dibuat dan diperbarui; status badge; state loading, empty, dan error. Gunakan hanya endpoint yang benar-benar ada.
- **Engineering Software:** Rhino 6, SOLIDWORKS 2022, Maxsurf 20 V8i, ANSYS (DEFERRED / NOT CONFIGURED). Jangan tampilkan CONNECTED tanpa bukti dari sistem.
- **Recent Activity:** hanya bila endpoint tersedia.

## 6. PROJECTS

Daftar project, pencarian, filter, urutan, entri ke detail project, buat project (hanya bila backend mendukung), serta state empty, loading, dan error. Informasi: nama, ID, deskripsi, tanggal dibuat dan diperbarui, status bila tersedia. Jangan menyimpan data permanen hanya di frontend bila backend belum mendukungnya.

## 7. CONNECTORS (SOFTWARE CONTROL)

Kartu atau tabel untuk Rhino 6, SOLIDWORKS 2022, Maxsurf 20 V8i, ANSYS. Tiap konektor menampilkan: nama, versi, status koneksi, status kapabilitas (`SUPPORTED`, `UNSUPPORTED`, `UNKNOWN`, `UNAVAILABLE`), waktu health check terakhir, aksi yang tersedia, dan informasi error bila ada.

Tombol Detect, Health Check, dan Inspect Capabilities hanya aktif jika endpoint backend benar-benar ada; selain itu disabled dengan alasan yang jelas. Jangan membuat simulasi koneksi. ANSYS tetap deferred dan tidak diimplementasikan sebagai konektor aktif.

## 8. SETTINGS

Informasi koneksi backend, informasi aplikasi dan versi, preferensi tema, tampilan konfigurasi API (read-only), informasi penyimpanan lokal bila tersedia. **Jangan pernah menampilkan API key, password, token, atau secret, dan jangan menyimpannya di localStorage.**

## 9. ARSITEKTUR FRONTEND

Gunakan struktur yang sesuai dengan repository dan FRONTEND_SPEC.md (bagian "Folder structure"). Saran bila belum ada: `api/`, `components/{layout,navigation,dashboard,projects,connectors,ui}`, `hooks/`, `layouts/`, `pages/`, `routes/`, `styles/`, `types/`, `utils/`. Jangan memaksakan struktur ini bila repository sudah punya yang lebih baik. Gunakan komponen yang dapat dipakai ulang; hindari satu file besar berisi seluruh halaman.

## 10. INTEGRASI API

Satu API client terpusat: base URL dari environment, timeout, penanganan error dan kegagalan jaringan, tipe dari OpenAPI, tanpa request langsung yang tersebar di komponen. Ikuti endpoint aktual dan catat perbedaannya dengan dokumentasi. Jangan memakai mock data sebagai pengganti backend; bila endpoint belum ada, tampilkan NOT IMPLEMENTED atau UNAVAILABLE.

## 11. UX

Semua halaman: loading, empty, dan error state; layout responsif; label aksesibel; navigasi keyboard; tooltip pada tombol icon-only; spacing dan tipografi konsisten; umpan balik setelah aksi. Jangan buat tombol tanpa fungsi; aksi yang belum didukung diberi disabled state dengan alasan.

## 12. KEAMANAN

Local-first; tidak mengekspos secret; tidak menyimpan token atau password di browser storage; frontend bukan security boundary; validasi input di frontend tetapi backend tetap otoritas; tidak menjalankan perintah sembarang dari browser; tidak melakukan operasi destruktif terhadap file engineering; tidak mengirim data ke layanan eksternal tanpa kebutuhan jelas.

## 13. TESTING DAN VALIDASI

1. TypeScript check, lint, dan test frontend bila ada.
2. Production build.
3. Periksa semua routing.
4. Uji frontend terhadap backend yang berjalan, dan uji tampilan error state saat backend dimatikan.
5. Periksa tampilan halaman dengan screenshot otomatis (misalnya Playwright) bila bisa dipasang; jika tidak, tulis jelas bahwa pemeriksaan visual harus dilakukan manual oleh saya. Jangan mengklaim sudah memeriksa tampilan tanpa bukti.
6. Pastikan tidak ada tombol yang menyesatkan dan tidak ada status koneksi palsu.

Jangan mengklaim berhasil jika build atau test belum dijalankan.

## 14. DEFINITION OF DONE

- Dashboard, Projects, Connectors, dan Settings berfungsi sesuai kemampuan backend aktual.
- Sidebar dan routing berjalan; halaman lain berupa placeholder jujur.
- Design system konsisten dan terpusat; API client terpusat; tipe dari OpenAPI.
- Loading, empty, dan error state tersedia; tidak ada fake status; tidak ada secret terekspos.
- TypeScript check dan production build berhasil (dengan bukti keluaran perintah).
- `docs/FRONTEND_API_GAPS.md` ditulis; FRONTEND_SPEC.md diperbarui sesuai implementasi aktual (perubahan dicatat, tidak menghapus isi penting).

## 15. ATURAN EKSEKUSI

Kerjakan bertahap: **A** audit (lalu BERHENTI) → **B** design system dan layout → **C** Dashboard → **D** Projects → **E** Connectors → **F** Settings → **G** integrasi API → **H** testing dan review akhir.

Setelah setiap fase: periksa hasil, jalankan test relevan, catat file yang berubah dan kendala, dan **satu commit per fase** dengan pesan yang jelas. Jangan lanjut dengan asumsi bila ada masalah arsitektur; berhenti dan laporkan.

Jangan: menghapus dokumentasi penting, mengubah backend atau skema database, mengganti teknologi utama tanpa alasan, mengimplementasikan ANSYS, mengklaim fitur bekerja tanpa pengujian, atau memakai data palsu untuk menyamarkan fitur yang belum ada.

## LAPORAN AKHIR

1. Fitur yang dibuat. 2. File baru. 3. File diubah. 4. API yang berhasil diintegrasikan. 5. API yang belum tersedia (rujuk `docs/FRONTEND_API_GAPS.md`). 6. Test dan hasilnya. 7. Hasil build. 8. Known issues. 9. Rekomendasi tahap berikutnya.

**Mulai dengan PHASE A. Audit dulu, laporkan, lalu BERHENTI.**