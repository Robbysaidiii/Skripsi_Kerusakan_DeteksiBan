# Deteksi Ban — Django + SVM (LBP+GLCM+Gabor+Wavelet+Canny+HuMoments)

Web app Django untuk mendeteksi kondisi ban dari foto (Kamera / Upload)
menjadi 3 kelas: **Normal**, **Retak** (`cracked`), **Robek** (`Tear`).
Desain mengikuti mockup yang diberikan (sidebar biru, kartu "Pilih Sumber
Gambar" & "Hasil Deteksi").

Model ML yang dipakai adalah SVM + PCA + StandardScaler hasil training kamu
sendiri (skrip `v5 parallel`: LBP multi-scale + GLCM + Gabor + Wavelet +
Canny grid + Hu Moments → StandardScaler → PCA(95%) → SVC RBF).

## 1. Install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Pasang file model hasil training

Salin 5 file berikut ke folder `deteksi/ml_models/` (folder ini sudah
disiapkan, saat ini kosong):

```
deteksi/ml_models/
├── svm_best.pkl
├── scaler.pkl
├── pca.pkl
├── label_encoder.pkl
└── metadata.json
```

File-file ini persis yang dihasilkan skrip training kamu di tahap
"SIMPAN MODEL FINAL" (`04_model/`). **Jangan diubah namanya.**

Selama file-file ini belum ada, halaman utama akan menampilkan peringatan
"Model belum siap" dan endpoint prediksi akan mengembalikan pesan error
yang jelas — bukan crash.

## 3. Jalankan migrasi & server

```bash
python manage.py migrate
python manage.py runserver
```

Buka `http://127.0.0.1:8000/` di browser.

## Struktur penting

```
deteksi/
├── ml/
│   ├── feature_extraction.py   # HARUS identik dgn pipeline training
│   └── inference.py            # load pkl + jalankan prediksi
├── ml_models/                  # taruh 5 file .pkl/.json di sini
├── templates/deteksi/
│   ├── base.html                # layout sidebar + header
│   └── beranda.html             # halaman deteksi (kamera/upload)
├── static/deteksi/
│   ├── css/style.css
│   └── js/app.js                # logic kamera, upload, fetch API, render hasil
├── views.py                     # beranda() + predict_view() (API JSON)
└── urls.py
```

## Halaman yang tersedia

- **Beranda** (`/`) — kartu ringkas: pilih Kamera/Upload, hasil deteksi
  singkat ditampilkan langsung di sebelah kanan (sesuai mockup pertama).
- **Deteksi** (`/deteksi/`) — halaman "Hasil Deteksi" lengkap: gambar yang
  dianalisis, detail deteksi (nama file, ukuran gambar, metode, waktu),
  dan ringkasan hasil per kelas (sesuai mockup kedua).

## Catatan penting soal mockup "Hasil Deteksi" (halaman Deteksi)

Mockup kedua yang kamu berikan menampilkan beberapa elemen yang **tidak
bisa dihasilkan oleh model SVM klasifikasi ini** karena model hanya
mengklasifikasikan satu gambar utuh ke 3 kelas (Normal/Retak/Robek) +
probabilitas — bukan model deteksi objek/segmentasi. Elemen yang saya
sesuaikan (tidak saya buat palsu/hardcode):

- **Kotak deteksi berwarna di atas gambar ban** (bounding box per area
  cacat) — dihapus, karena butuh model object detection terpisah untuk
  menentukan lokasi cacat di gambar. Sebagai gantinya, gambar diberi
  bingkai warna sesuai hasil klasifikasi keseluruhan (hijau/kuning/merah).
- **Tipe Ban & Ukuran Ban** (mis. "Bridgestone Turanza T005", "205/55 R16")
  — dihapus dari "Detail Deteksi", diganti dengan info yang benar-benar
  ada: Nama File & Ukuran Gambar (piksel).
- **Keausan Tapak (%), Kedalaman Alur (mm), Benjolan** — dihapus, karena
  model ini tidak mengukur ketebalan tapak/kedalaman alur/benjolan. Diganti
  dengan **probabilitas per kelas** (Normal/Retak/Robek) dari `predict_proba`
  SVM, ditampilkan dengan gaya visual yang mirip (kartu ikon + nilai +
  status).

Kalau ke depannya kamu ingin fitur bounding box / pengukuran tapak yang
sesungguhnya, itu butuh model tambahan (mis. object detection/segmentation)
yang dilatih terpisah dari model klasifikasi SVM ini.



1. User pilih tab **Kamera** (live preview via `getUserMedia`) atau **Upload**
   (drag & drop / klik untuk pilih file).
2. Klik **Ambil Foto** (kamera) atau **Analisis Foto** (upload) →
   gambar dikirim sebagai `multipart/form-data` ke `POST /api/predict/`.
3. Di backend (`deteksi/ml/inference.py`):
   - `feature_extraction.py` mengekstrak 1090 fitur (LBP+GLCM+Gabor+
     Wavelet+Canny+Hu) — urutan & parameter **identik** dengan skrip
     training supaya cocok dengan `scaler.pkl` & `pca.pkl`.
   - `scaler.transform()` → `pca.transform()` → `svm.predict()` +
     `svm.predict_proba()` → `label_encoder.inverse_transform()`.
4. Hasil (label, confidence, breakdown probabilitas 3 kelas, rekomendasi)
   dikembalikan sebagai JSON dan dirender oleh `app.js` ke kartu
   "Hasil Deteksi" — sama seperti desain (badge warna hijau/kuning/merah).

## Login, Register, Lupa Password (baru)

Sekarang ada autentikasi nyata (Django `auth`), bukan cuma UI:

- **`/login/`** — form masuk (username atau email + password).
- **`/register/`** — form daftar akun baru (nama, username, email, password).
  Setelah daftar, otomatis login.
- **`/lupa-password/`** — form lupa password. Tautan reset dikirim lewat
  email — karena belum ada SMTP asli, email **dicetak ke terminal**
  tempat `runserver` berjalan (`EMAIL_BACKEND` = console backend di
  `settings.py`). Cari baris berisi `reset-password/...` di terminal,
  buka link itu di browser untuk lanjut atur password baru.
- **`/logout/`** — tombol "Keluar" di menu profil (pojok kanan atas).

**Halaman Deteksi (`/deteksi/`) & endpoint `/api/predict/` sekarang wajib
login.** Kalau belum login dan mencoba deteksi ban (upload gambar atau
pakai kamera), otomatis diarahkan ke halaman login (bawa `?next=` supaya
balik ke halaman Deteksi lagi setelah berhasil masuk). Di halaman login
ada juga tautan "Belum punya akun? Daftar di sini" ke halaman register.

Halaman lain (Beranda, Riwayat, Tips, Bantuan, Profil, Pengaturan,
Notifikasi) **belum** diproteksi login — kalau mau semua halaman juga
wajib login, tinggal tambahkan `@login_required(login_url="deteksi:login")`
di view yang bersangkutan (`deteksi/views.py`).

Catatan desain: app ini masih memakai satu baris data profil (`Akun`,
singleton) untuk ditampilkan di header — data itu disinkronkan dengan
nama/email dari akun yang baru daftar. Kalau nanti butuh multi-user
sungguhan (tiap user punya riwayat & profil sendiri-sendiri), `Akun`
perlu diubah jadi relasi `OneToOneField` ke `User` dan `Riwayat`/
`Notifikasi` perlu ditambah kolom `user` — itu perubahan struktural yang
lebih besar dari sekadar menambah login.

## Catatan

- Fitur **Riwayat**, **Laporan**, dan **Tentang** di sidebar sengaja belum
  dibuat fungsional (sesuai permintaan — "itu ntar aja"). Link-nya sudah
  ada di sidebar tapi belum diarahkan ke halaman apa pun. Tombol
  "Download PDF Laporan" juga sudah di-nonaktifkan (placeholder) dulu.
- Mapping warna: `normal` → hijau (Kondisi Baik), `cracked` (retak) →
  kuning/amber (Perlu Perhatian), `Tear` (robek) → merah (Kondisi Buruk).
  Silakan sesuaikan teks rekomendasi di `deteksi/ml/inference.py`
  (`CLASS_DISPLAY`) sesuai kebutuhan.
- `SVC(probability=True)` di scikit-learn kadang membuat hasil
  `predict()` (dipakai untuk label utama) tidak 100% sama dengan kelas
  argmax dari `predict_proba()` (dipakai untuk breakdown %) — ini
  keterbatasan Platt scaling di libsvm, bukan bug pada kode ini.
- Endpoint `/api/predict/` memakai `@csrf_exempt` supaya gampang dipanggil
  dari `fetch()` tanpa perlu menangani CSRF token secara manual. Jika akan
  dipakai di production/publik, sebaiknya tambahkan proteksi (CSRF token,
  rate limiting, autentikasi) sesuai kebutuhan.
- Tailwind CSS dimuat via CDN (`cdn.tailwindcss.com`) supaya tidak perlu
  build step — cukup untuk development. Untuk production sebaiknya pakai
  Tailwind CLI/PostCSS build supaya tidak bergantung ke CDN saat runtime.
