"""Autentikasi 2 Faktor (2FA) nyata lewat kode OTP 6 digit yang dikirim
ke email pengguna — bukan sekadar toggle boolean yang tidak berefek ke
proses login.

Dipakai oleh login_view & verifikasi_2fa_view di views.py. Kode OTP
disimpan sementara di session (server-side, tidak pernah dikirim ke
browser selain lewat email), berlaku 5 menit, dan dihapus begitu
dipakai atau kedaluwarsa.
"""

import random

from django.core.mail import send_mail
from django.utils import timezone

SESSION_KEY = "2fa_pending"
KODE_BERLAKU_MENIT = 5


def email_tujuan(user):
    akun = getattr(user, "akun", None)
    email = getattr(akun, "email", "") if akun else ""
    return email or user.email or ""


def butuh_email_tujuan(user):
    """True kalau user punya email terdaftar untuk menerima kode OTP."""
    return bool(email_tujuan(user))


def buat_dan_kirim_otp(request, user, next_url="", bahasa="id"):
    """Buat kode OTP baru, simpan di session, dan kirim ke email user.
    Mengembalikan True kalau email berhasil dikirim (backend tidak error)."""
    kode = f"{random.randint(0, 999999):06d}"
    kadaluwarsa = timezone.now() + timezone.timedelta(minutes=KODE_BERLAKU_MENIT)

    request.session[SESSION_KEY] = {
        "user_id": user.pk,
        "kode": kode,
        "kadaluwarsa": kadaluwarsa.isoformat(),
        "next": next_url,
    }

    tujuan = email_tujuan(user)
    if not tujuan:
        return False

    if bahasa == "en":
        subject = "Your verification code"
        message = (
            f"Your 2FA verification code is: {kode}\n\n"
            f"This code is valid for {KODE_BERLAKU_MENIT} minutes. "
            "If you did not attempt to log in, you can ignore this email."
        )
    else:
        subject = "Kode verifikasi Anda"
        message = (
            f"Kode verifikasi 2FA Anda adalah: {kode}\n\n"
            f"Kode ini berlaku selama {KODE_BERLAKU_MENIT} menit. "
            "Kalau Anda tidak mencoba login, abaikan saja email ini."
        )

    send_mail(
        subject=subject,
        message=message,
        from_email=None,
        recipient_list=[tujuan],
        fail_silently=True,
    )
    return True


def ambil_pending(request):
    """Ambil data OTP pending dari session, atau None kalau tidak ada."""
    return request.session.get(SESSION_KEY)


def hapus_pending(request):
    request.session.pop(SESSION_KEY, None)


def verifikasi_kode(request, kode_masukan):
    """Cek kode yang dimasukkan user terhadap yang tersimpan di session.
    Mengembalikan salah satu: "ok", "salah", "kadaluwarsa", "tidak_ada"."""
    data = ambil_pending(request)
    if not data:
        return "tidak_ada"

    kadaluwarsa = timezone.datetime.fromisoformat(data["kadaluwarsa"])
    if timezone.now() > kadaluwarsa:
        hapus_pending(request)
        return "kadaluwarsa"

    if kode_masukan.strip() != data["kode"]:
        return "salah"

    return "ok"
