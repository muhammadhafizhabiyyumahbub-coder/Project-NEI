# TASK: IMPLEMENT NEI FRONTEND — PHASE 2

Kamu bertindak sebagai Senior Frontend Engineer sekaligus UI/UX Designer untuk project **NEI (Nautical Engineering Intelligence)**.

Tugasmu adalah mengimplementasikan frontend NEI secara nyata ke dalam repository yang sudah ada.

Jangan hanya membuat mockup, screenshot, atau dokumentasi. Implementasikan kode yang dapat dijalankan.

## 1. LANGKAH PERTAMA: AUDIT PROJECT

Sebelum mengubah kode:

1. Baca `README.md`.
2. Baca `PLAN.md`.
3. Baca `ARCHITECTURE.md`.
4. Baca `FRONTEND_SPEC.md`.
5. Baca `API_SPEC.md`.
6. Periksa struktur folder `apps/ui/`.
7. Periksa seluruh komponen frontend yang sudah tersedia.
8. Periksa backend API dan endpoint aktual.
9. Periksa `package.json` dan dependencies yang sudah terpasang.

Buat pemetaan singkat:
- Komponen yang sudah tersedia.
- Komponen yang perlu dibuat.
- Endpoint backend yang benar-benar tersedia.
- Endpoint yang belum tersedia.
- Ketidaksesuaian antara dokumentasi dan implementasi.

**Jangan mengasumsikan API tersedia hanya karena tercantum dalam dokumentasi.**

Jangan menghapus atau mengganti implementasi yang sudah berfungsi tanpa alasan teknis.

## 2. TUJUAN DESAIN

NEI harus terlihat seperti professional naval engineering workstation, bukan dashboard template biasa.

Konsep desain:

- Dark-first interface.
- Professional engineering software aesthetic.
- Modern, minimalis, presisi, dan informatif.
- High information density tetapi tetap mudah dibaca.
- Warna aksen biru untuk interaksi utama.
- Status sistem menggunakan warna yang konsisten.
- Sidebar permanen.
- Layout responsif.
- Typography profesional.
- Konsistensi desain pada seluruh halaman.

Inspirasi visual:
- Professional CAD software.
- Engineering monitoring workstation.
- Modern developer tools.
- Scientific computing dashboards.

Hindari:
- Tampilan seperti website marketing.
- Gradient berlebihan.
- Terlalu banyak rounded cards.
- Animasi dekoratif yang tidak diperlukan.
- Emoji sebagai pengganti icon.
- Data statistik palsu yang terlihat seperti data aktual.

Gunakan Lucide icons jika dependency tersedia atau tambahkan secara terkontrol.

## 3. DESIGN SYSTEM

Buat design system terpusat.

Contoh palet warna awal:

Background:
- Main: #0B1120
- Sidebar: #0F172A
- Panel: #111C2E
- Elevated: #172338

Border:
- Default: #263449

Text:
- Primary: #E5EDF7
- Secondary: #94A3B8
- Muted: #64748B

Accent:
- Primary blue: #3B82F6
- Hover blue: #2563EB

Status:
- Success: #22C55E
- Warning: #F59E0B
- Error: #EF4444
- Info: #38BDF8

Buat reusable design tokens untuk:
- Colors.
- Typography.
- Spacing.
- Border radius.
- Shadows.
- Component states.

Jangan mendefinisikan warna secara acak di setiap komponen.

## 4. APPLICATION LAYOUT

Buat layout utama NEI dengan:

### A. Sidebar

Bagian atas:
- Logo NEI.
- Nautical Engineering Intelligence.
- Status koneksi backend.

Navigasi:
1. Dashboard
2. AI Workspace
3. Projects
4. Engineering Knowledge
5. Calculation Center
6. Software Control
7. Verification & Reports
8. Settings

Untuk tahap implementasi ini, prioritaskan halaman:
- Dashboard.
- Projects.
- Connectors.
- Settings.

Halaman lain boleh dibuat sebagai placeholder yang konsisten dengan design system, tetapi jangan berpura-pura memiliki fungsi yang belum diimplementasikan.

Bagian bawah:
- Backend status.
- Application version jika tersedia.
- User/system status jika tersedia.

### B. Topbar

Isi:
- Nama halaman.
- Breadcrumb.
- Backend connection indicator.
- Notification indicator jika sistem notifikasi tersedia.
- Refresh action jika relevan.

### C. Main Content

Gunakan layout yang fleksibel dan konsisten pada seluruh halaman.

## 5. HALAMAN DASHBOARD

Buat dashboard engineering workstation.

Bagian utama:

### System Overview
Tampilkan:
- Backend status.
- Database status jika tersedia.
- AI provider status jika tersedia.
- Active tasks.
- Completed tasks.
- Failed tasks.

Semua status harus berasal dari API aktual.

Jika data tidak tersedia:
- Tampilkan `UNKNOWN` atau `UNAVAILABLE`.
- Jangan membuat angka palsu.
- Berikan penjelasan bahwa data belum tersedia.

### Recent Tasks
Tampilkan:
- Task ID.
- Task name.
- Status.
- Created time.
- Updated time.

Tambahkan:
- Status badges.
- Empty state.
- Loading state.
- Error state.

### Engineering Software
Tampilkan konektor:
- Rhino 6.
- SOLIDWORKS 2022.
- Maxsurf Enterprise v8.1.
- ANSYS: NOT CONFIGURED / DEFERRED.

Status konektor harus berasal dari backend jika tersedia.

Jangan menampilkan konektor sebagai CONNECTED tanpa bukti dari sistem.

### Recent Activity
Tampilkan aktivitas terbaru apabila endpoint tersedia.

## 6. HALAMAN PROJECTS

Buat halaman pengelolaan project engineering.

Fitur:
- Project list.
- Search.
- Filter.
- Sort.
- Project detail entry.
- Create project jika backend mendukungnya.
- Empty state.
- Loading state.
- Error state.

Informasi project:
- Project name.
- Project ID.
- Description.
- Created date.
- Updated date.
- Project status jika tersedia.

Jangan menyimpan data permanen hanya di frontend apabila backend belum mendukung penyimpanan tersebut.

## 7. HALAMAN CONNECTORS

Buat halaman Software Control / Connectors.

Tampilkan kartu atau tabel untuk:

1. Rhino 6.
2. SOLIDWORKS 2022.
3. Maxsurf Enterprise v8.1.
4. ANSYS.

Setiap konektor mempunyai:
- Software name.
- Version.
- Connection status.
- Capability status.
- Last health check.
- Available actions.
- Error information jika tersedia.

Capability status harus mendukung:
- SUPPORTED.
- UNSUPPORTED.
- UNKNOWN.
- UNAVAILABLE.

Tombol:
- Detect.
- Health Check.
- Inspect Capabilities.

Hanya aktifkan tombol apabila endpoint backend benar-benar tersedia.

Jangan membuat simulasi koneksi software yang terlihat seperti koneksi nyata.

ANSYS tetap deferred dan tidak boleh diimplementasikan sebagai konektor aktif.

## 8. HALAMAN SETTINGS

Buat pengaturan aplikasi:

- Backend connection information.
- Application information.
- Theme preference.
- API configuration display.
- Local storage information jika tersedia.
- Version information.

Jangan pernah menampilkan API key, password, token, atau secret dari backend.

Jangan menyimpan secret dalam localStorage.

## 9. FRONTEND ARCHITECTURE

Gunakan struktur yang sesuai dengan repository saat ini.

Jika belum tersedia, struktur yang disarankan:

apps/ui/src/
├── api/
│   ├── client.ts
│   ├── endpoints.ts
│   └── types.ts
├── assets/
├── components/
│   ├── layout/
│   ├── navigation/
│   ├── dashboard/
│   ├── projects/
│   ├── connectors/
│   └── ui/
├── hooks/
├── layouts/
├── pages/
│   ├── Dashboard.tsx
│   ├── Projects.tsx
│   ├── Connectors.tsx
│   ├── Settings.tsx
│   └── PlaceholderPage.tsx
├── routes/
├── styles/
├── types/
├── utils/
├── App.tsx
└── main.tsx

Jangan memaksakan struktur ini jika repository sudah memiliki struktur yang lebih baik.

Gunakan:
- React.
- TypeScript.
- Vite.
- Tailwind CSS jika sudah digunakan.
- React Router jika diperlukan.
- TanStack Query jika sudah digunakan.
- Lucide React untuk icons jika tersedia.

Gunakan reusable components.

Hindari satu file besar yang berisi seluruh halaman.

## 10. API INTEGRATION

Periksa implementasi backend sebelum membuat API client.

Buat satu API client terpusat.

Persyaratan:
- Base URL melalui konfigurasi environment.
- Request timeout.
- Error handling.
- Response validation jika sesuai.
- Loading state.
- Network failure handling.
- TypeScript types.
- Tidak ada API request langsung yang tersebar di setiap komponen.

Penting:

Dokumentasi API dan implementasi aktual mungkin berbeda.

Ikuti endpoint aktual yang sudah tersedia. Catat perbedaan dengan dokumentasi, tetapi jangan mengubah backend dalam task ini.

Jangan menggunakan mock data sebagai pengganti backend tanpa penanda yang jelas.

Jika endpoint belum tersedia, tampilkan status `NOT IMPLEMENTED` atau `UNAVAILABLE`.

## 11. UX REQUIREMENTS

Semua halaman harus memiliki:

- Loading state.
- Empty state.
- Error state.
- Responsive layout.
- Accessible labels.
- Keyboard navigation.
- Tooltip pada icon-only buttons.
- Konsistensi spacing.
- Konsistensi typography.
- Feedback saat user melakukan action.

Jangan membuat tombol yang tidak mempunyai fungsi.

Untuk aksi yang belum didukung backend, tampilkan disabled state beserta alasan yang jelas.

## 12. SECURITY

Frontend harus mengikuti prinsip keamanan NEI:

- Local-first.
- Tidak mengekspos API secrets.
- Tidak menyimpan password atau token sensitif di browser storage.
- Tidak menganggap frontend sebagai security boundary.
- Validasi input di frontend dan tetap mengandalkan validasi backend.
- Tidak menjalankan arbitrary commands dari browser.
- Tidak melakukan operasi destruktif terhadap file engineering.
- Tidak mengirim data ke layanan eksternal tanpa kebutuhan yang jelas.

## 13. TESTING DAN VALIDATION

Setelah implementasi:

1. Jalankan TypeScript check.
2. Jalankan lint jika tersedia.
3. Jalankan frontend tests jika tersedia.
4. Jalankan production build.
5. Perbaiki error yang muncul.
6. Periksa seluruh routing.
7. Periksa tampilan setiap halaman.
8. Pastikan tidak ada tombol yang menyesatkan.
9. Pastikan frontend dapat berkomunikasi dengan backend yang tersedia.
10. Pastikan frontend tetap menampilkan error state ketika backend mati.

Jangan mengklaim berhasil jika build atau test belum dijalankan.

## 14. DEFINITION OF DONE

Implementasi dinyatakan selesai apabila:

- Dashboard sudah berfungsi.
- Projects page sudah berfungsi sesuai API yang tersedia.
- Connectors page sudah berfungsi sesuai kemampuan backend.
- Settings page sudah tersedia.
- Sidebar dan routing berjalan.
- Design system konsisten.
- API client terpusat.
- Loading, empty, dan error states tersedia.
- Tidak ada fake connection status.
- Tidak ada secret yang terekspos.
- TypeScript check berhasil.
- Production build berhasil.
- Dokumentasi frontend diperbarui sesuai implementasi aktual.

## 15. EXECUTION RULES

Kerjakan secara bertahap:

PHASE A — Audit existing frontend dan backend API.

PHASE B — Implement design system dan application layout.

PHASE C — Implement Dashboard.

PHASE D — Implement Projects.

PHASE E — Implement Connectors.

PHASE F — Implement Settings.

PHASE G — Integrasi API.

PHASE H — Testing, debugging, dan final review.

Setelah setiap fase:
- Periksa hasil implementasi.
- Jalankan test yang relevan.
- Catat file yang berubah.
- Catat kendala.
- Jangan lanjut dengan asumsi jika ada masalah arsitektur.

Jangan:
- Menghapus dokumentasi penting.
- Mengubah backend tanpa izin.
- Mengubah database schema tanpa izin.
- Mengganti teknologi utama tanpa alasan.
- Mengimplementasikan ANSYS.
- Mengklaim fitur sudah bekerja tanpa pengujian.
- Menggunakan fake data untuk menyamarkan fitur yang belum tersedia.

## FINAL REPORT

Setelah selesai, berikan laporan:

1. Fitur yang berhasil dibuat.
2. Daftar file baru.
3. Daftar file yang diubah.
4. API yang berhasil diintegrasikan.
5. API yang belum tersedia.
6. Test yang dijalankan dan hasilnya.
7. Build result.
8. Known issues.
9. Rekomendasi tahap berikutnya.

Mulai dengan PHASE A. Audit repository terlebih dahulu, lalu lanjutkan implementasi secara bertahap.