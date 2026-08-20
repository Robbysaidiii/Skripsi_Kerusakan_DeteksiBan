from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

app_name = "deteksi"

urlpatterns = [
    # ============ Autentikasi ============
    path("login/", views.login_view, name="login"),
    path("login/verifikasi-2fa/", views.verifikasi_2fa_view, name="verifikasi_2fa"),
    path("login/verifikasi-2fa/fingerprint/opsi/", views.fingerprint_login_opsi_view, name="fingerprint_login_opsi"),
    path("login/verifikasi-2fa/fingerprint/verifikasi/", views.fingerprint_login_verifikasi_view, name="fingerprint_login_verifikasi"),
    path("register/", views.register_view, name="register"),
    path("register/daftarkan-fingerprint/", views.daftarkan_fingerprint_view, name="daftarkan_fingerprint"),
    path("register/daftarkan-fingerprint/opsi/", views.fingerprint_registrasi_opsi_view, name="fingerprint_registrasi_opsi"),
    path("register/daftarkan-fingerprint/verifikasi/", views.fingerprint_registrasi_verifikasi_view, name="fingerprint_registrasi_verifikasi"),
    path("register/daftarkan-fingerprint/lewati/", views.lewati_fingerprint_view, name="lewati_fingerprint"),
    path("logout/", views.logout_view, name="logout"),

    path(
        "lupa-password/",
        auth_views.PasswordResetView.as_view(
            template_name="deteksi/auth/password_reset_form.html",
            email_template_name="deteksi/auth/password_reset_email.txt",
            subject_template_name="deteksi/auth/password_reset_subject.txt",
            success_url="/lupa-password/terkirim/",
        ),
        name="password_reset",
    ),
    path(
        "lupa-password/terkirim/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="deteksi/auth/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset-password/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="deteksi/auth/password_reset_confirm.html",
            success_url="/reset-password/selesai/",
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset-password/selesai/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="deteksi/auth/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),

    path("", views.beranda, name="beranda"),
    path("deteksi/", views.deteksi_page, name="deteksi_page"),
    path("riwayat/", views.riwayat_page, name="riwayat_page"),
    path("tips/", views.tips_page, name="tips_page"),
    path("bantuan/", views.bantuan_page, name="bantuan_page"),
    path("tentang/", views.tentang_page, name="tentang_page"),
    path("notifikasi/", views.notifikasi_page, name="notifikasi_page"),
    path("notifikasi/<int:pk>/tandai-dibaca/", views.tandai_notifikasi_dibaca_view, name="tandai_notifikasi_dibaca"),
    path("notifikasi/tandai-semua-dibaca/", views.tandai_semua_notifikasi_dibaca_view, name="tandai_semua_notifikasi_dibaca"),
    path("profil/", views.profil_page, name="profil_page"),
    path("profil/upload-foto/", views.upload_foto_profil_view, name="upload_foto_profil"),
    path("profil/ubah-telepon/", views.ubah_telepon_view, name="ubah_telepon"),
    path("pengaturan/", views.pengaturan_page, name="pengaturan_page"),
    path("pengaturan/hapus-cache/", views.hapus_cache_view, name="hapus_cache"),
    path("pengaturan/toggle-2fa/", views.toggle_2fa_view, name="toggle_2fa"),
    path("pengaturan/akhiri-sesi/<str:session_key>/", views.akhiri_sesi_view, name="akhiri_sesi"),
    path("laporan/<int:pk>/", views.laporan_page, name="laporan_page"),
    path("api/predict/", views.predict_view, name="predict"),
]
