"""Logika notifikasi nyata: dipakai supaya ke-4 toggle di halaman
Pengaturan > Notifikasi benar-benar berpengaruh, bukan sekadar boolean
yang tersimpan di database tanpa efek.

- notifikasi_email    -> kanal pengiriman: kirim email asli (lewat
                          EMAIL_BACKEND yang sudah dipakai untuk reset
                          password) tiap kali ada notifikasi.
- push_notification   -> kanal pengiriman: buat baris Notifikasi (bell
                          di header + halaman Notifikasi) tiap kali ada
                          notifikasi.
- pengingat_perawatan -> menyalakan/mematikan FITUR pengingat perawatan
                          ban (dicek tiap kali user membuka Beranda).
- ringkasan_mingguan  -> menyalakan/mematikan FITUR ringkasan mingguan
                          aktivitas deteksi (dicek tiap kali user membuka
                          Beranda).

Tidak ada scheduler/cron di proyek ini, jadi pengingat & ringkasan
dicek dengan pola "lazy check": setiap kali user membuka Beranda, kita
lihat apakah sudah waktunya kirim, dan kalau iya baru dibuat saat itu
juga. Ini realistis untuk skala aplikasi ini tanpa perlu Celery/cron
job terpisah.
"""

from django.core.mail import send_mail
from django.utils import timezone

from .i18n import get_text
from .models import Notifikasi, Pengaturan, Riwayat

HARI_PENGINGAT_PERAWATAN = 30
HARI_RINGKASAN_MINGGUAN = 7


def _email_tujuan(user):
    akun = getattr(user, "akun", None)
    email = getattr(akun, "email", "") if akun else ""
    return email or user.email or ""


def kirim_notifikasi(user, judul, pesan, tag="", icon="info"):
    """Titik tunggal untuk membuat notifikasi apa pun (hasil deteksi,
    pengingat perawatan, ringkasan mingguan). Menghormati toggle
    `push_notification` (in-app) dan `notifikasi_email` (email asli) di
    Pengaturan — kalau keduanya mati, tidak ada apa pun yang dikirim."""
    pengaturan = Pengaturan.get_instance()

    if pengaturan.push_notification:
        Notifikasi.objects.create(user=user, judul=judul, pesan=pesan, tag=tag, icon=icon, dibaca=False)

    if pengaturan.notifikasi_email:
        tujuan = _email_tujuan(user)
        if tujuan:
            send_mail(
                subject=judul,
                message=pesan,
                from_email=None,  # pakai DEFAULT_FROM_EMAIL di settings.py
                recipient_list=[tujuan],
                fail_silently=True,
            )


def cek_pengingat_dan_ringkasan(user):
    """Dipanggil tiap kali user membuka Beranda. Mengecek apakah sudah
    waktunya kirim pengingat perawatan dan/atau ringkasan mingguan,
    lalu memicu `kirim_notifikasi` kalau iya."""
    pengaturan = Pengaturan.get_instance()
    bahasa = pengaturan.bahasa
    t = get_text(bahasa)
    sekarang = timezone.now()

    if pengaturan.pengingat_perawatan:
        _cek_pengingat_perawatan(user, bahasa, t, sekarang)

    if pengaturan.ringkasan_mingguan:
        _cek_ringkasan_mingguan(user, bahasa, t, sekarang)


def _cek_pengingat_perawatan(user, bahasa, t, sekarang):
    terakhir_riwayat = Riwayat.objects.filter(user=user).order_by("-created_at").first()
    if not terakhir_riwayat:
        return  # belum pernah deteksi sama sekali, belum ada yang perlu diingatkan

    batas = terakhir_riwayat.created_at + timezone.timedelta(days=HARI_PENGINGAT_PERAWATAN)
    if sekarang < batas:
        return  # belum jatuh tempo

    pengingat_terakhir = (
        Notifikasi.objects.filter(user=user, tag="pengingat_perawatan").order_by("-created_at").first()
    )
    if pengingat_terakhir and pengingat_terakhir.created_at >= batas:
        return  # sudah pernah diingatkan untuk periode ini

    hari = (sekarang - terakhir_riwayat.created_at).days
    if bahasa == "en":
        judul = "Time for a tire check"
        pesan = (
            f"It's been {hari} days since your last tire detection. We recommend checking your "
            "tires again to make sure they're still safe to use."
        )
    else:
        judul = "Waktunya cek kondisi ban"
        pesan = (
            f"Sudah {hari} hari sejak deteksi ban terakhir Anda. Sebaiknya lakukan pengecekan "
            "kembali untuk memastikan ban masih aman digunakan."
        )
    kirim_notifikasi(user, judul, pesan, tag="pengingat_perawatan", icon="jadwal")


def _cek_ringkasan_mingguan(user, bahasa, t, sekarang):
    ringkasan_terakhir = (
        Notifikasi.objects.filter(user=user, tag="ringkasan_mingguan").order_by("-created_at").first()
    )
    sejak = ringkasan_terakhir.created_at if ringkasan_terakhir else user.date_joined
    batas = sejak + timezone.timedelta(days=HARI_RINGKASAN_MINGGUAN)
    if sekarang < batas:
        return  # belum 7 hari sejak ringkasan sebelumnya (atau sejak akun dibuat)

    qs = Riwayat.objects.filter(user=user, created_at__gte=sejak)
    total = qs.count()
    if total == 0:
        # Tidak ada aktivitas dalam periode ini — geser saja jendela
        # waktunya lewat notifikasi "kosong" ringan, supaya tidak dicek
        # ulang terus tiap kali Beranda dibuka.
        baik = perhatian = bermasalah = 0
    else:
        baik = qs.filter(label="BAIK").count()
        perhatian = qs.filter(label="PERHATIAN").count()
        bermasalah = qs.filter(label="BERMASALAH").count()

    if bahasa == "en":
        judul = "Your weekly detection summary"
        if total == 0:
            pesan = "No tire detections were recorded in the past 7 days."
        else:
            pesan = (
                f"In the past 7 days you ran {total} detection(s): {baik} good, "
                f"{perhatian} need attention, {bermasalah} problematic."
            )
    else:
        judul = "Ringkasan deteksi minggu ini"
        if total == 0:
            pesan = "Tidak ada aktivitas deteksi ban dalam 7 hari terakhir."
        else:
            pesan = (
                f"Dalam 7 hari terakhir Anda melakukan {total} deteksi: {baik} baik, "
                f"{perhatian} perlu perhatian, {bermasalah} bermasalah."
            )

    kirim_notifikasi(user, judul, pesan, tag="ringkasan_mingguan", icon="laporan")
