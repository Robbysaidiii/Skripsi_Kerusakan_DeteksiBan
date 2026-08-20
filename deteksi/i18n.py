"""
Kamus terjemahan sederhana untuk fitur ganti bahasa (Indonesia/English).

Kenapa bukan Django i18n bawaan (gettext)?
- Django i18n bawaan (django-admin makemessages/compilemessages) butuh
  tool "gettext" terinstal di komputer/server, dan biasanya pengaturan
  bahasanya per-session (lewat cookie), bukan tersimpan di database.
- Di project ini, bahasa disimpan di model `Pengaturan` (satu baris
  untuk seluruh aplikasi), jadi kita cukup pakai kamus Python biasa:
  gampang dibaca, tidak butuh compile apa pun, dan otomatis nyambung
  ke context processor yang sudah ada (lihat context_processors.py).

Cara pakai di template:
    {{ t.nav_beranda }}          -> "Beranda" atau "Home"

Cara nambah teks baru:
    1. Tambahkan key baru di kedua dict di bawah (id & en).
    2. Pakai key itu di template dengan {{ t.key_baru }}.

Untuk teks yang dibuat di backend (views.py) dengan bagian dinamis
(mis. "{{ delta_pct }}% dari minggu lalu"), lihat helper get_text(bahasa)
di bawah dan pakai t["key"] langsung di Python.
"""

TRANSLATIONS = {
    "id": {
        # ==================================================================
        # SIDEBAR & HEADER (base.html)
        # ==================================================================
        "nav_beranda": "Beranda",
        "nav_deteksi": "Deteksi",
        "nav_riwayat": "Riwayat",
        "nav_laporan": "Laporan",
        "nav_tips": "Tips",
        "nav_tentang": "Tentang",
        "nav_pengaturan": "Pengaturan",
        "nav_bantuan": "Bantuan",

        "sidebar_keamanan_judul": "Keamanan Data",
        "sidebar_keamanan_desc": "Semua data Anda aman dan tidak disimpan tanpa izin.",

        "dropdown_profil_saya": "Profil Saya",
        "dropdown_home": "Home",
        "dropdown_notifikasi": "Notifikasi",
        "dropdown_bantuan": "Bantuan",
        "dropdown_keluar": "Keluar",

        # ==================================================================
        # UMUM / SHARED
        # ==================================================================
        "common_simpan": "Simpan",
        "common_simpan_perubahan": "Simpan Perubahan",
        "common_batal": "Batal",
        "common_tutup": "Tutup",
        "common_lihat": "Lihat",
        "common_wib": "WIB",
        "common_dari_minggu_lalu": "dari minggu lalu",
        "common_jam": "jam",
        "common_menit": "menit",
        "common_detik": "detik",
        "common_yang_lalu": "yang lalu",

        # ==================================================================
        # BERANDA (beranda.html)
        # ==================================================================
        "beranda_judul": "Beranda",
        "beranda_welcome": "Selamat datang kembali 👋",
        "beranda_subtitle": "Pantau kondisi ban kendaraan Anda dengan mudah dan cepat.",
        "beranda_model_belum_siap": "Model belum siap",

        "beranda_stat_total_deteksi": "Total Deteksi",
        "beranda_belum_ada_minggu_lalu": "Belum ada data minggu lalu",
        "beranda_stat_avg_confidence": "Rata-rata Keyakinan Model",
        "beranda_dihitung_seluruh_riwayat": "Dihitung dari seluruh riwayat",
        "beranda_stat_total_waktu": "Total Waktu Analisis",
        "beranda_akumulasi_waktu_server": "Akumulasi waktu proses server",
        "beranda_stat_kondisi_terakhir": "Kondisi Ban Terakhir",
        "beranda_belum_ada_deteksi": "Belum ada deteksi",

        "beranda_deteksi_sekarang_judul": "Deteksi Ban Sekarang",
        "beranda_deteksi_sekarang_desc": "Mulai deteksi dengan mengupload gambar ban atau menggunakan kamera.",
        "beranda_upload_gambar": "Upload Gambar",
        "beranda_gunakan_kamera": "Gunakan Kamera",

        "beranda_aktivitas_terakhir": "Aktivitas Terakhir",
        "beranda_lihat_semua": "Lihat Semua",
        "beranda_deteksi_prefix": "Deteksi",
        "beranda_keyakinan": "Keyakinan",
        "beranda_belum_ada_aktivitas": "Belum ada aktivitas deteksi.",

        "beranda_statistik_deteksi": "Statistik Deteksi",
        "beranda_tujuh_hari_terakhir": "7 Hari Terakhir",
        "beranda_total": "Total",

        "beranda_aksi_cepat": "Aksi Cepat",
        "beranda_mulai_deteksi": "Mulai Deteksi",
        "beranda_deteksi_kondisi_sekarang": "Deteksi kondisi ban sekarang",
        "beranda_lihat_riwayat": "Lihat Riwayat",
        "beranda_lihat_semua_riwayat": "Lihat semua riwayat deteksi Anda",
        "beranda_laporan_terakhir": "Laporan Terakhir",
        "beranda_buka_laporan_terbaru": "Buka laporan deteksi terbaru",
        "beranda_belum_ada_laporan": "Belum Ada Laporan",
        "beranda_lakukan_deteksi_pertama": "Lakukan deteksi pertama Anda",

        # ==================================================================
        # DETEKSI (deteksi.html + deteksi_page.js)
        # ==================================================================
        "deteksi_judul": "Deteksi",
        "deteksi_subtitle_awal": "Unggah atau ambil foto ban untuk memulai deteksi",
        "deteksi_download_pdf": "Download PDF",
        "deteksi_ambil_upload_judul": "Ambil / Upload Gambar Ban",
        "deteksi_tab_kamera": "Kamera",
        "deteksi_tab_upload": "Upload",
        "deteksi_dropzone_text": "Klik atau seret gambar ban ke sini",
        "deteksi_dropzone_format": "JPG atau PNG",
        "deteksi_kamera_mengaktifkan": "Mengaktifkan kamera…",
        "deteksi_menganalisis": "Menganalisis gambar…",
        "deteksi_btn_ambil_foto": "Ambil Foto",
        "deteksi_btn_pilih_gambar_dulu": "Pilih Gambar Dulu",
        "deteksi_btn_analisis_foto": "Analisis Foto",
        "deteksi_format_didukung": "Format yang didukung: JPG, PNG (Maks. 10MB)",
        "deteksi_gambar_diupload_judul": "Gambar yang Diupload",
        "deteksi_ulang": "Deteksi Ulang",
        "deteksi_detail_judul": "Detail Deteksi",
        "deteksi_nama_file": "Nama File",
        "deteksi_metode_deteksi": "Metode Deteksi",
        "deteksi_metode_nilai": "SVM + Fitur Tekstur",
        "deteksi_ukuran_gambar": "Ukuran Gambar",
        "deteksi_waktu_deteksi": "Waktu Deteksi",
        "deteksi_ringkasan_hasil": "Ringkasan Hasil",
        "deteksi_ringkasan_kosong": "Hasil ringkasan akan muncul di sini setelah gambar dianalisis.",
        "deteksi_kondisi_ban": "Kondisi Ban",
        "deteksi_rekomendasi": "Rekomendasi",
        "deteksi_riwayat_judul": "Riwayat Deteksi",
        "deteksi_segera_hadir": "Segera hadir",
        "deteksi_riwayat_segera_hadir_desc": "Fitur riwayat deteksi akan tersedia pada pembaruan berikutnya.",
        "deteksi_kamera_tidak_tersedia": "Kamera tidak tersedia. Izinkan akses kamera atau gunakan tab Upload.",
        "deteksi_format_tidak_didukung": "Format tidak didukung. Gunakan JPG atau PNG.",
        "deteksi_ukuran_maks": "Ukuran file maksimal 10MB.",
        "deteksi_selesai_pada": "Deteksi selesai pada",
        "deteksi_probabilitas_kelas_ini": "Probabilitas kelas ini",
        "deteksi_error_umum": "Terjadi kesalahan saat menganalisis gambar.",
        "deteksi_error_koneksi": "Gagal terhubung ke server. Periksa koneksi Anda dan coba lagi.",

        # ==================================================================
        # RIWAYAT (riwayat.html)
        # ==================================================================
        "riwayat_judul": "Riwayat Deteksi",
        "riwayat_subtitle": "Daftar semua hasil deteksi yang telah dilakukan",
        "riwayat_cari_placeholder": "Cari kelas (Normal/Retak/Robek)...",
        "riwayat_tab_semua": "Semua",
        "riwayat_tab_baik": "Baik",
        "riwayat_tab_perhatian": "Perhatian",
        "riwayat_tab_bermasalah": "Bermasalah",
        "riwayat_th_tanggal": "Tanggal Deteksi",
        "riwayat_th_gambar": "Gambar",
        "riwayat_th_kondisi": "Kondisi Ban",
        "riwayat_th_ringkasan": "Ringkasan",
        "riwayat_th_aksi": "Aksi",
        "riwayat_keyakinan": "Keyakinan",
        "riwayat_kelas_terdeteksi": "Kelas terdeteksi",
        "riwayat_durasi_proses": "Durasi proses",
        "riwayat_lihat_laporan": "Lihat Laporan",
        "riwayat_kosong": "Belum ada riwayat deteksi. Mulai deteksi ban Anda terlebih dahulu.",
        "riwayat_menampilkan": "Menampilkan",
        "riwayat_dari": "dari",
        "riwayat_data": "data",

        # ==================================================================
        # LAPORAN (laporan.html)
        # ==================================================================
        "laporan_judul": "Laporan Deteksi",
        "laporan_subtitle": "Ringkasan hasil deteksi kondisi ban",
        "laporan_kembali_riwayat": "Kembali ke Riwayat",
        "laporan_lebih_lama": "Lebih lama",
        "laporan_lebih_baru": "Lebih baru",
        "laporan_preview": "Preview",
        "laporan_download_pdf": "Download PDF",
        "laporan_bagikan": "Bagikan",
        "laporan_tautan_disalin": "Tautan disalin",
        "laporan_tidak_ada_gambar": "Tidak ada gambar",
        "laporan_tanggal_deteksi": "Tanggal Deteksi",
        "laporan_metode_deteksi": "Metode Deteksi",
        "laporan_metode_nilai": "AI Vision (SVM + PCA)",
        "laporan_kelas_terdeteksi": "Kelas Terdeteksi",
        "laporan_ukuran_gambar": "Ukuran Gambar",
        "laporan_durasi_proses": "Durasi Proses",
        "laporan_file_asli": "File Asli",
        "laporan_kondisi_ban": "Kondisi Ban",
        "laporan_tingkat_keyakinan": "Tingkat Keyakinan Model",
        "laporan_tab_ringkasan": "Ringkasan",
        "laporan_tab_detail": "Detail Analisis",
        "laporan_tab_rekomendasi": "Rekomendasi",
        "laporan_ringkasan_hasil": "Ringkasan Hasil",
        "laporan_probabilitas_per_kelas": "Probabilitas per Kelas",
        "laporan_rekomendasi": "Rekomendasi",
        "laporan_keyakinan_per_kelas": "Tingkat Keyakinan per Kelas",
        "laporan_analisis_pipeline": "Analisis dilakukan dengan pipeline ekstraksi fitur (LBP, GLCM, Gabor, Wavelet, Canny, Hu Moments) yang diproses melalui scaler, PCA, dan model SVM. Kelas dengan probabilitas tertinggi ({kelas}, {confidence}%) dipilih sebagai hasil akhir.",
        "laporan_info_teknis": "Informasi Teknis Permintaan",
        "laporan_kode_kelas_model": "Kode Kelas (model)",
        "laporan_user_agent": "User Agent",
        "laporan_rekomendasi_utama": "Rekomendasi Utama",
        "laporan_langkah_disarankan": "Langkah yang Disarankan",
        "laporan_langkah_1": "Periksa tekanan angin ban secara rutin, minimal sebulan sekali.",
        "laporan_langkah_2": "Lakukan rotasi ban setiap 10.000 km untuk keausan yang lebih merata.",
        "laporan_langkah_3_masalah": "Segera bawa kendaraan ke bengkel terpercaya untuk pemeriksaan lebih lanjut.",
        "laporan_langkah_3_normal": "Lakukan deteksi ulang secara berkala untuk memantau perkembangan kondisi ban.",
        "laporan_info_deteksi": "Informasi Deteksi",
        "laporan_waktu_deteksi": "Waktu Deteksi",
        "laporan_metode": "Metode",
        "laporan_metode_ml_nilai": "AI Vision (Machine Learning)",
        "laporan_keyakinan": "Keyakinan",
        "laporan_statistik_keseluruhan": "Statistik Keseluruhan",
        "laporan_total_deteksi": "Total Deteksi",
        "laporan_preview_judul": "Preview Laporan",
        "laporan_cetak_unduh": "Cetak / Unduh PDF",

        # ==================================================================
        # NOTIFIKASI (notifikasi.html)
        # ==================================================================
        "notif_judul": "Notifikasi",
        "notif_subtitle": "Informasi terbaru seputar deteksi dan laporan Anda",
        "notif_tab_semua": "Semua",
        "notif_tab_belum_dibaca": "Belum Dibaca",
        "notif_tab_dibaca": "Dibaca",
        "notif_tandai_semua_dibaca": "Tandai semua dibaca",
        "notif_filter_semua": "Semua",
        "notif_detail_judul": "Detail Notifikasi",

        # ==================================================================
        # TIPS (tips.html)
        # ==================================================================
        "tips_judul": "Tips Perawatan Ban",
        "tips_subtitle": "Tips dan panduan untuk menjaga ban tetap dalam kondisi terbaik",
        "tips_utama_judul": "Tips Utama",
        "tips_ingat_judul": "Ingat!",
        "tips_ingat_desc": "Perawatan ban yang baik meningkatkan keselamatan, performa kendaraan, dan menghemat biaya perbaikan.",
        "tips_ringkasan_judul": "Ringkasan Tips",
        "tips_jadwal_judul": "Jadwal Perawatan Rekomendasi",

        # ==================================================================
        # TENTANG (tentang.html)
        # ==================================================================
        "tentang_judul": "Tentang Deteksi Ban",
        "tentang_subtitle": "Kenali lebih dekat aplikasi Deteksi Ban",
        "tentang_apa_itu_judul": "Apa itu Deteksi Ban?",
        "tentang_apa_itu_desc": "Deteksi Ban adalah aplikasi berbasis Artificial Intelligence (AI) yang dirancang untuk membantu pengguna memeriksa kondisi ban kendaraan dengan cepat, akurat, dan mudah.",
        "tentang_fitur1_judul": "Deteksi Cerdas",
        "tentang_fitur1_desc": "AI menganalisis gambar ban untuk mendeteksi keausan tapak, kedalaman alur, retakan, dan benjolan.",
        "tentang_fitur2_judul": "Hasil Akurat & Cepat",
        "tentang_fitur2_desc": "Dapatkan hasil analisis dalam hitungan detik lengkap dengan rekomendasi perawatan.",
        "tentang_fitur3_judul": "Laporan Mudah",
        "tentang_fitur3_desc": "Unduh laporan hasil deteksi dalam format PDF untuk kebutuhan dokumentasi dan riwayat.",
        "tentang_misi_judul": "Misi Kami",
        "tentang_misi_desc": "Membantu setiap pengendara menjaga keselamatan di jalan dengan teknologi deteksi ban yang mudah diakses dan terpercaya.",
        "tentang_visi_judul": "Visi Kami",
        "tentang_visi_desc": "Menjadi solusi deteksi kondisi ban terdepan di Indonesia yang mendukung keselamatan dan kenyamanan berkendara.",
        "tentang_privasi_judul": "Privasi & Keamanan",
        "tentang_privasi_desc": "Kami berkomitmen untuk menjaga privasi dan keamanan data pengguna. Semua data diproses dengan aman dan tidak disimpan tanpa izin.",
        "tentang_info_aplikasi_judul": "Informasi Aplikasi",
        "tentang_versi": "Versi",
        "tentang_rilis": "Rilis",
        "tentang_teknologi": "Teknologi",
        "tentang_dikembangkan_di": "Dikembangkan di",

        # ==================================================================
        # BANTUAN (bantuan.html)
        # ==================================================================
        "bantuan_judul": "Bantuan",
        "bantuan_subtitle": "Kami siap membantu Anda. Temukan jawaban atau hubungi kami.",
        "bantuan_cari_placeholder": "Cari bantuan... (contoh: cara upload, laporan, deteksi)",
        "bantuan_topik_populer": "Topik Bantuan Populer",
        "bantuan_faq_judul": "Pertanyaan yang Sering Diajukan",
        "bantuan_lihat_semua_faq": "Lihat semua FAQ",
        "bantuan_tidak_menemukan": "Tidak menemukan jawaban yang Anda cari? Hubungi kami, kami dengan senang hati membantu Anda.",
        "bantuan_masih_butuh_judul": "Masih butuh bantuan?",
        "bantuan_masih_butuh_desc": "Tim kami siap membantu Anda melalui kontak berikut.",
        "bantuan_live_chat": "Live Chat",
        "bantuan_live_chat_status": "Online",
        "bantuan_live_chat_desc": "Chat langsung dengan tim kami",
        "bantuan_email": "Email",
        "bantuan_email_respon": "Respon dalam 1x24 jam",
        "bantuan_telepon": "Telepon",
        "bantuan_telepon_jam": "Senin - Jumat, 09.00 - 17.00 WIB",
        "bantuan_panduan_judul": "Panduan Penggunaan",
        "bantuan_panduan_desc": "Unduh panduan lengkap aplikasi Deteksi Ban untuk memudahkan Anda.",
        "bantuan_unduh_panduan": "Unduh Panduan (PDF)",

        # ==================================================================
        # PROFIL (profil.html)
        # ==================================================================
        "profil_judul": "Informasi Akun",
        "profil_subtitle": "Kelola data profil dan informasi akun Anda.",
        "profil_edit": "Edit Profil",
        "profil_foto_hint": "JPG, PNG maksimal 2MB",
        "profil_nama_lengkap": "Nama Lengkap",
        "profil_email": "Email",
        "profil_terverifikasi": "Terverifikasi",
        "profil_belum_verifikasi": "Belum diverifikasi",
        "profil_nomor_telepon": "Nomor Telepon",
        "profil_ubah": "Ubah",
        "profil_peran": "Peran",
        "profil_bergabung_sejak": "Bergabung Sejak",
        "profil_id_pengguna": "ID Pengguna",
        "profil_edit_modal_judul": "Edit Profil",
        "profil_ubah_email_hint": "Mengubah email akan membatalkan status verifikasi saat ini.",
        "profil_ubah_telepon_modal_judul": "Ubah Nomor Telepon",

        # ==================================================================
        # PENGATURAN (pengaturan.html)
        # ==================================================================
        "pengaturan_judul": "Pengaturan",
        "pengaturan_subtitle": "Kelola preferensi aplikasi dan pengaturan akun Anda.",
        "pengaturan_umum_judul": "Umum",
        "pengaturan_umum_desc": "Atur preferensi aplikasi.",
        "pengaturan_tema": "Tema",
        "pengaturan_label_bahasa": "Bahasa",
        "pengaturan_zona_waktu": "Zona Waktu",
        "pengaturan_format_tanggal": "Format Tanggal",
        "pengaturan_notifikasi_judul": "Notifikasi",
        "pengaturan_notifikasi_desc": "Atur preferensi notifikasi.",
        "pengaturan_email": "Email",
        "pengaturan_email_desc": "Terima notifikasi melalui email",
        "pengaturan_push": "Push Notification",
        "pengaturan_push_desc": "Terima notifikasi di perangkat ini",
        "pengaturan_pengingat": "Pengingat Perawatan",
        "pengaturan_pengingat_desc": "Dapatkan pengingat untuk perawatan ban",
        "pengaturan_ringkasan_mingguan": "Ringkasan Mingguan",
        "pengaturan_ringkasan_mingguan_desc": "Terima ringkasan aktivitas deteksi setiap minggu",
        "pengaturan_simpan": "Simpan Perubahan",
        "pengaturan_keamanan_judul": "Keamanan",
        "pengaturan_keamanan_desc": "Atur keamanan akun Anda.",
        "pengaturan_2fa": "Autentikasi 2 Faktor (2FA)",
        "pengaturan_2fa_aktif": "Aktif",
        "pengaturan_2fa_desc": "Tambahkan lapisan keamanan ekstra untuk akun Anda",
        "pengaturan_2fa_nonaktifkan": "Nonaktifkan",
        "pengaturan_2fa_aktifkan": "Aktifkan",
        "pengaturan_kelola_sesi": "Kelola Sesi Login",
        "pengaturan_kelola_sesi_desc": "Lihat dan kelola perangkat yang sedang masuk",
        "pengaturan_aktif": "aktif",
        "pengaturan_lainnya_judul": "Lainnya",
        "pengaturan_lainnya_desc": "Penyimpanan & informasi aplikasi.",
        "pengaturan_hapus_cache": "Hapus Cache",
        "pengaturan_hapus_cache_desc": "Bersihkan data sementara untuk meningkatkan performa aplikasi",
        "pengaturan_bersihkan": "Bersihkan",
        "pengaturan_tentang_aplikasi": "Tentang Aplikasi",
        "pengaturan_tentang_aplikasi_desc": "Lihat informasi versi dan kebijakan aplikasi",
        "pengaturan_status_model_ml": "Status Model ML",
        "pengaturan_total_data_deteksi": "Total Data Deteksi",
        "pengaturan_framework": "Framework",
        "pengaturan_python": "Python",
        "pengaturan_database": "Database",
        "pengaturan_kelola_sesi_modal_judul": "Kelola Sesi Login",
        "pengaturan_sesi": "Sesi",
        "pengaturan_sesi_ini": "Sesi ini",
        "pengaturan_berakhir": "Berakhir",
        "pengaturan_akhiri": "Akhiri",
        "pengaturan_tidak_ada_sesi": "Tidak ada sesi login aktif.",
        "pengaturan_simpan_berhasil": "Perubahan pengaturan berhasil disimpan.",
    },
    "en": {
        # ==================================================================
        # SIDEBAR & HEADER (base.html)
        # ==================================================================
        "nav_beranda": "Home",
        "nav_deteksi": "Detection",
        "nav_riwayat": "History",
        "nav_laporan": "Report",
        "nav_tips": "Tips",
        "nav_tentang": "About",
        "nav_pengaturan": "Settings",
        "nav_bantuan": "Help",

        "sidebar_keamanan_judul": "Data Security",
        "sidebar_keamanan_desc": "Your data is safe and never stored without permission.",

        "dropdown_profil_saya": "My Profile",
        "dropdown_home": "Home",
        "dropdown_notifikasi": "Notifications",
        "dropdown_bantuan": "Help",
        "dropdown_keluar": "Log Out",

        # ==================================================================
        # UMUM / SHARED
        # ==================================================================
        "common_simpan": "Save",
        "common_simpan_perubahan": "Save Changes",
        "common_batal": "Cancel",
        "common_tutup": "Close",
        "common_lihat": "View",
        "common_wib": "WIB",
        "common_dari_minggu_lalu": "from last week",
        "common_jam": "hr",
        "common_menit": "min",
        "common_detik": "sec",
        "common_yang_lalu": "ago",

        # ==================================================================
        # BERANDA (beranda.html)
        # ==================================================================
        "beranda_judul": "Home",
        "beranda_welcome": "Welcome back 👋",
        "beranda_subtitle": "Monitor your vehicle's tire condition easily and quickly.",
        "beranda_model_belum_siap": "Model not ready",

        "beranda_stat_total_deteksi": "Total Detections",
        "beranda_belum_ada_minggu_lalu": "No data from last week",
        "beranda_stat_avg_confidence": "Average Model Confidence",
        "beranda_dihitung_seluruh_riwayat": "Calculated from entire history",
        "beranda_stat_total_waktu": "Total Analysis Time",
        "beranda_akumulasi_waktu_server": "Accumulated server processing time",
        "beranda_stat_kondisi_terakhir": "Last Tire Condition",
        "beranda_belum_ada_deteksi": "No detection yet",

        "beranda_deteksi_sekarang_judul": "Detect Tire Now",
        "beranda_deteksi_sekarang_desc": "Start detection by uploading a tire image or using the camera.",
        "beranda_upload_gambar": "Upload Image",
        "beranda_gunakan_kamera": "Use Camera",

        "beranda_aktivitas_terakhir": "Recent Activity",
        "beranda_lihat_semua": "View All",
        "beranda_deteksi_prefix": "Detection",
        "beranda_keyakinan": "Confidence",
        "beranda_belum_ada_aktivitas": "No detection activity yet.",

        "beranda_statistik_deteksi": "Detection Statistics",
        "beranda_tujuh_hari_terakhir": "Last 7 Days",
        "beranda_total": "Total",

        "beranda_aksi_cepat": "Quick Actions",
        "beranda_mulai_deteksi": "Start Detection",
        "beranda_deteksi_kondisi_sekarang": "Detect tire condition now",
        "beranda_lihat_riwayat": "View History",
        "beranda_lihat_semua_riwayat": "View all your detection history",
        "beranda_laporan_terakhir": "Latest Report",
        "beranda_buka_laporan_terbaru": "Open the latest detection report",
        "beranda_belum_ada_laporan": "No Report Yet",
        "beranda_lakukan_deteksi_pertama": "Perform your first detection",

        # ==================================================================
        # DETEKSI (deteksi.html + deteksi_page.js)
        # ==================================================================
        "deteksi_judul": "Detection Result",
        "deteksi_subtitle_awal": "Upload or take a tire photo to start detection",
        "deteksi_download_pdf": "Download PDF",
        "deteksi_ambil_upload_judul": "Take / Upload Tire Image",
        "deteksi_tab_kamera": "Camera",
        "deteksi_tab_upload": "Upload",
        "deteksi_dropzone_text": "Click or drag a tire image here",
        "deteksi_dropzone_format": "JPG or PNG",
        "deteksi_kamera_mengaktifkan": "Activating camera…",
        "deteksi_menganalisis": "Analyzing image…",
        "deteksi_btn_ambil_foto": "Take Photo",
        "deteksi_btn_pilih_gambar_dulu": "Choose an Image First",
        "deteksi_btn_analisis_foto": "Analyze Photo",
        "deteksi_format_didukung": "Supported formats: JPG, PNG (Max. 10MB)",
        "deteksi_gambar_diupload_judul": "Uploaded Image",
        "deteksi_ulang": "Detect Again",
        "deteksi_detail_judul": "Detection Detail",
        "deteksi_nama_file": "File Name",
        "deteksi_metode_deteksi": "Detection Method",
        "deteksi_metode_nilai": "SVM + Texture Features",
        "deteksi_ukuran_gambar": "Image Size",
        "deteksi_waktu_deteksi": "Detection Time",
        "deteksi_ringkasan_hasil": "Result Summary",
        "deteksi_ringkasan_kosong": "The result summary will appear here after the image is analyzed.",
        "deteksi_kondisi_ban": "Tire Condition",
        "deteksi_rekomendasi": "Recommendation",
        "deteksi_riwayat_judul": "Detection History",
        "deteksi_segera_hadir": "Coming soon",
        "deteksi_riwayat_segera_hadir_desc": "The detection history feature will be available in a future update.",
        "deteksi_kamera_tidak_tersedia": "Camera unavailable. Allow camera access or use the Upload tab.",
        "deteksi_format_tidak_didukung": "Format not supported. Use JPG or PNG.",
        "deteksi_ukuran_maks": "Maximum file size is 10MB.",
        "deteksi_selesai_pada": "Detection completed at",
        "deteksi_probabilitas_kelas_ini": "Probability for this class",
        "deteksi_error_umum": "An error occurred while analyzing the image.",
        "deteksi_error_koneksi": "Failed to connect to the server. Check your connection and try again.",

        # ==================================================================
        # RIWAYAT (riwayat.html)
        # ==================================================================
        "riwayat_judul": "Detection History",
        "riwayat_subtitle": "List of all detections that have been performed",
        "riwayat_cari_placeholder": "Search class (Normal/Cracked/Torn)...",
        "riwayat_tab_semua": "All",
        "riwayat_tab_baik": "Good",
        "riwayat_tab_perhatian": "Caution",
        "riwayat_tab_bermasalah": "Problem",
        "riwayat_th_tanggal": "Detection Date",
        "riwayat_th_gambar": "Image",
        "riwayat_th_kondisi": "Tire Condition",
        "riwayat_th_ringkasan": "Summary",
        "riwayat_th_aksi": "Action",
        "riwayat_keyakinan": "Confidence",
        "riwayat_kelas_terdeteksi": "Detected class",
        "riwayat_durasi_proses": "Processing time",
        "riwayat_lihat_laporan": "View Report",
        "riwayat_kosong": "No detection history yet. Start detecting your tires first.",
        "riwayat_menampilkan": "Showing",
        "riwayat_dari": "of",
        "riwayat_data": "entries",

        # ==================================================================
        # LAPORAN (laporan.html)
        # ==================================================================
        "laporan_judul": "Detection Report",
        "laporan_subtitle": "Summary of the tire condition detection result",
        "laporan_kembali_riwayat": "Back to History",
        "laporan_lebih_lama": "Older",
        "laporan_lebih_baru": "Newer",
        "laporan_preview": "Preview",
        "laporan_download_pdf": "Download PDF",
        "laporan_bagikan": "Share",
        "laporan_tautan_disalin": "Link copied",
        "laporan_tidak_ada_gambar": "No image",
        "laporan_tanggal_deteksi": "Detection Date",
        "laporan_metode_deteksi": "Detection Method",
        "laporan_metode_nilai": "AI Vision (SVM + PCA)",
        "laporan_kelas_terdeteksi": "Detected Class",
        "laporan_ukuran_gambar": "Image Size",
        "laporan_durasi_proses": "Processing Time",
        "laporan_file_asli": "Original File",
        "laporan_kondisi_ban": "Tire Condition",
        "laporan_tingkat_keyakinan": "Model Confidence Level",
        "laporan_tab_ringkasan": "Summary",
        "laporan_tab_detail": "Analysis Detail",
        "laporan_tab_rekomendasi": "Recommendation",
        "laporan_ringkasan_hasil": "Result Summary",
        "laporan_probabilitas_per_kelas": "Probability per Class",
        "laporan_rekomendasi": "Recommendation",
        "laporan_keyakinan_per_kelas": "Confidence Level per Class",
        "laporan_analisis_pipeline": "The analysis was performed with a feature-extraction pipeline (LBP, GLCM, Gabor, Wavelet, Canny, Hu Moments) processed through a scaler, PCA, and an SVM model. The class with the highest probability ({kelas}, {confidence}%) was selected as the final result.",
        "laporan_info_teknis": "Request Technical Information",
        "laporan_kode_kelas_model": "Class Code (model)",
        "laporan_user_agent": "User Agent",
        "laporan_rekomendasi_utama": "Main Recommendation",
        "laporan_langkah_disarankan": "Suggested Steps",
        "laporan_langkah_1": "Check the tire air pressure regularly, at least once a month.",
        "laporan_langkah_2": "Rotate the tires every 10,000 km for more even wear.",
        "laporan_langkah_3_masalah": "Take the vehicle to a trusted workshop for further inspection as soon as possible.",
        "laporan_langkah_3_normal": "Re-run detection periodically to monitor the tire condition over time.",
        "laporan_info_deteksi": "Detection Information",
        "laporan_waktu_deteksi": "Detection Time",
        "laporan_metode": "Method",
        "laporan_metode_ml_nilai": "AI Vision (Machine Learning)",
        "laporan_keyakinan": "Confidence",
        "laporan_statistik_keseluruhan": "Overall Statistics",
        "laporan_total_deteksi": "Total Detections",
        "laporan_preview_judul": "Report Preview",
        "laporan_cetak_unduh": "Print / Download PDF",

        # ==================================================================
        # NOTIFIKASI (notifikasi.html)
        # ==================================================================
        "notif_judul": "Notifications",
        "notif_subtitle": "The latest updates about your detections and reports",
        "notif_tab_semua": "All",
        "notif_tab_belum_dibaca": "Unread",
        "notif_tab_dibaca": "Read",
        "notif_tandai_semua_dibaca": "Mark all as read",
        "notif_filter_semua": "All",
        "notif_detail_judul": "Notification Detail",

        # ==================================================================
        # TIPS (tips.html)
        # ==================================================================
        "tips_judul": "Tire Care Tips",
        "tips_subtitle": "Tips and guidance to keep your tires in the best condition",
        "tips_utama_judul": "Main Tips",
        "tips_ingat_judul": "Remember!",
        "tips_ingat_desc": "Good tire care improves safety, vehicle performance, and saves on repair costs.",
        "tips_ringkasan_judul": "Tips Summary",
        "tips_jadwal_judul": "Recommended Maintenance Schedule",

        # ==================================================================
        # TENTANG (tentang.html)
        # ==================================================================
        "tentang_judul": "About TireScan",
        "tentang_subtitle": "Get to know the TireScan application better",
        "tentang_apa_itu_judul": "What is TireScan?",
        "tentang_apa_itu_desc": "TireScan is an Artificial Intelligence (AI) based application designed to help users check their vehicle's tire condition quickly, accurately, and easily.",
        "tentang_fitur1_judul": "Smart Detection",
        "tentang_fitur1_desc": "AI analyzes tire images to detect tread wear, groove depth, cracks, and bulges.",
        "tentang_fitur2_judul": "Accurate & Fast Results",
        "tentang_fitur2_desc": "Get analysis results in seconds, complete with care recommendations.",
        "tentang_fitur3_judul": "Easy Reports",
        "tentang_fitur3_desc": "Download the detection report in PDF format for documentation and history needs.",
        "tentang_misi_judul": "Our Mission",
        "tentang_misi_desc": "Helping every driver stay safe on the road with accessible and reliable tire-detection technology.",
        "tentang_visi_judul": "Our Vision",
        "tentang_visi_desc": "To become the leading tire condition detection solution in Indonesia that supports driving safety and comfort.",
        "tentang_privasi_judul": "Privacy & Security",
        "tentang_privasi_desc": "We are committed to protecting user privacy and data security. All data is processed securely and never stored without permission.",
        "tentang_info_aplikasi_judul": "Application Information",
        "tentang_versi": "Version",
        "tentang_rilis": "Release",
        "tentang_teknologi": "Technology",
        "tentang_dikembangkan_di": "Developed in",

        # ==================================================================
        # BANTUAN (bantuan.html)
        # ==================================================================
        "bantuan_judul": "Help",
        "bantuan_subtitle": "We're here to help. Find answers or contact us.",
        "bantuan_cari_placeholder": "Search help... (e.g. how to upload, report, detection)",
        "bantuan_topik_populer": "Popular Help Topics",
        "bantuan_faq_judul": "Frequently Asked Questions",
        "bantuan_lihat_semua_faq": "View all FAQ",
        "bantuan_tidak_menemukan": "Can't find the answer you're looking for? Contact us, we're happy to help.",
        "bantuan_masih_butuh_judul": "Still need help?",
        "bantuan_masih_butuh_desc": "Our team is ready to help you through the following contacts.",
        "bantuan_live_chat": "Live Chat",
        "bantuan_live_chat_status": "Online",
        "bantuan_live_chat_desc": "Chat directly with our team",
        "bantuan_email": "Email",
        "bantuan_email_respon": "Response within 1x24 hours",
        "bantuan_telepon": "Phone",
        "bantuan_telepon_jam": "Monday - Friday, 09:00 - 17:00 WIB",
        "bantuan_panduan_judul": "User Guide",
        "bantuan_panduan_desc": "Download the complete TireScan user guide for your convenience.",
        "bantuan_unduh_panduan": "Download Guide (PDF)",

        # ==================================================================
        # PROFIL (profil.html)
        # ==================================================================
        "profil_judul": "Account Information",
        "profil_subtitle": "Manage your profile data and account information.",
        "profil_edit": "Edit Profile",
        "profil_foto_hint": "JPG, PNG max 2MB",
        "profil_nama_lengkap": "Full Name",
        "profil_email": "Email",
        "profil_terverifikasi": "Verified",
        "profil_belum_verifikasi": "Not verified",
        "profil_nomor_telepon": "Phone Number",
        "profil_ubah": "Change",
        "profil_peran": "Role",
        "profil_bergabung_sejak": "Member Since",
        "profil_id_pengguna": "User ID",
        "profil_edit_modal_judul": "Edit Profile",
        "profil_ubah_email_hint": "Changing your email will revoke your current verification status.",
        "profil_ubah_telepon_modal_judul": "Change Phone Number",

        # ==================================================================
        # PENGATURAN (pengaturan.html)
        # ==================================================================
        "pengaturan_judul": "Settings",
        "pengaturan_subtitle": "Manage your app preferences and account settings.",
        "pengaturan_umum_judul": "General",
        "pengaturan_umum_desc": "Manage application preferences.",
        "pengaturan_tema": "Theme",
        "pengaturan_label_bahasa": "Language",
        "pengaturan_zona_waktu": "Time Zone",
        "pengaturan_format_tanggal": "Date Format",
        "pengaturan_notifikasi_judul": "Notifications",
        "pengaturan_notifikasi_desc": "Manage notification preferences.",
        "pengaturan_email": "Email",
        "pengaturan_email_desc": "Receive notifications via email",
        "pengaturan_push": "Push Notification",
        "pengaturan_push_desc": "Receive notifications on this device",
        "pengaturan_pengingat": "Maintenance Reminder",
        "pengaturan_pengingat_desc": "Get reminders for tire maintenance",
        "pengaturan_ringkasan_mingguan": "Weekly Summary",
        "pengaturan_ringkasan_mingguan_desc": "Receive a weekly summary of detection activity",
        "pengaturan_simpan": "Save Changes",
        "pengaturan_keamanan_judul": "Security",
        "pengaturan_keamanan_desc": "Manage your account security.",
        "pengaturan_2fa": "Two-Factor Authentication (2FA)",
        "pengaturan_2fa_aktif": "Active",
        "pengaturan_2fa_desc": "Add an extra layer of security to your account",
        "pengaturan_2fa_nonaktifkan": "Disable",
        "pengaturan_2fa_aktifkan": "Enable",
        "pengaturan_kelola_sesi": "Manage Login Sessions",
        "pengaturan_kelola_sesi_desc": "View and manage signed-in devices",
        "pengaturan_aktif": "active",
        "pengaturan_lainnya_judul": "Other",
        "pengaturan_lainnya_desc": "Storage & app information.",
        "pengaturan_hapus_cache": "Clear Cache",
        "pengaturan_hapus_cache_desc": "Clear temporary data to improve app performance",
        "pengaturan_bersihkan": "Clear",
        "pengaturan_tentang_aplikasi": "About the App",
        "pengaturan_tentang_aplikasi_desc": "View version information and app policies",
        "pengaturan_status_model_ml": "ML Model Status",
        "pengaturan_total_data_deteksi": "Total Detection Data",
        "pengaturan_framework": "Framework",
        "pengaturan_python": "Python",
        "pengaturan_database": "Database",
        "pengaturan_kelola_sesi_modal_judul": "Manage Login Sessions",
        "pengaturan_sesi": "Session",
        "pengaturan_sesi_ini": "This session",
        "pengaturan_berakhir": "Expires",
        "pengaturan_akhiri": "End",
        "pengaturan_tidak_ada_sesi": "No active login sessions.",
        "pengaturan_simpan_berhasil": "Settings changes saved successfully.",
    },
}


def get_text(kode_bahasa):
    """Ambil kamus teks untuk kode bahasa tertentu ('id'/'en').

    Kalau kode bahasanya tidak dikenal, fallback ke Indonesia supaya
    tidak pernah error / halaman kosong.
    """
    return TRANSLATIONS.get(kode_bahasa, TRANSLATIONS["id"])
