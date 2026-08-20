import base64
import io
import json
import platform
import time

import django
from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from PIL import Image

from .ml import inference
from .models import Akun, LogAktivitas, Notifikasi, Pengaturan, Riwayat, KredensialFingerprint
from .notifications import cek_pengingat_dan_ringkasan, kirim_notifikasi
from . import otp
from . import fingerprint
from .i18n import get_text
from .templatetags.i18n_extras import kelas_i18n, status_title, status_desc

# Versi aplikasi (metadata rilis, ditampilkan di "Tentang Aplikasi")
APP_VERSION = "1.0.0"

# Metadata tampilan (warna/badge) per status — ini token desain, bukan data
# hasil deteksi, jadi aman untuk tetap statis.
STATUS_META = {
    "BAIK": {
        "label": "BAIK", "label_title": "Baik", "badge": "text-emerald-700 bg-emerald-50", "banner": "bg-emerald-50 text-emerald-700",
        "dot": "bg-emerald-500", "value_color": "text-emerald-600",
        "desc_full": "Ban dalam kondisi baik dan aman digunakan.",
    },
    "PERHATIAN": {
        "label": "PERHATIAN", "label_title": "Perhatian", "badge": "text-amber-700 bg-amber-50", "banner": "bg-amber-50 text-amber-700",
        "dot": "bg-amber-500", "value_color": "text-amber-500",
        "desc_full": "Ban masih dapat digunakan, namun ada beberapa bagian yang perlu diperhatikan.",
    },
    "BERMASALAH": {
        "label": "BERMASALAH", "label_title": "Bermasalah", "badge": "text-red-700 bg-red-50", "banner": "bg-red-50 text-red-700",
        "dot": "bg-red-500", "value_color": "text-red-600",
        "desc_full": "Ban dalam kondisi kritis dan berisiko terhadap keselamatan berkendara.",
    },
}


def _is_admin(user):
    """Admin = staff/superuser Django (dicek langsung, bukan lewat field
    Akun.peran, supaya konsisten dengan hak akses /admin/ bawaan)."""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


# ============================================================
# AUTENTIKASI — login, register, logout
# ============================================================

def login_view(request):
    """Form login nyata (django.contrib.auth). Kalau user datang dari
    halaman yang butuh login (mis. /deteksi/), parameter ?next= dipakai
    supaya setelah login diarahkan balik ke halaman tujuan semula."""
    if request.user.is_authenticated:
        return redirect("deteksi:deteksi_page")

    next_url = request.GET.get("next") or request.POST.get("next") or ""

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            messages.error(request, "Username/email dan password wajib diisi.")
        else:
            # Boleh login pakai username ATAU email.
            login_username = username
            if "@" in username:
                user_match = User.objects.filter(email__iexact=username).first()
                if user_match:
                    login_username = user_match.username

            user = authenticate(request, username=login_username, password=password)
            if user is not None:
                pengaturan = Pengaturan.get_instance()
                if pengaturan.autentikasi_2fa and otp.butuh_email_tujuan(user):
                    otp.buat_dan_kirim_otp(request, user, next_url=next_url, bahasa=pengaturan.bahasa)
                    return redirect("deteksi:verifikasi_2fa")
                login(request, user)
                if request.POST.get("ingat_saya") == "1":
                    # "Ingat saya": sesi bertahan 30 hari meski browser ditutup.
                    request.session.set_expiry(60 * 60 * 24 * 30)
                else:
                    # Tanpa "Ingat saya": sesi berakhir saat browser ditutup.
                    request.session.set_expiry(0)
                messages.success(request, f"Selamat datang kembali, {user.first_name or user.username}!")
                return redirect(next_url or "deteksi:deteksi_page")
            messages.error(request, "Username/email atau password salah.")

    return render(request, "deteksi/auth/login.html", {"next": next_url})


def verifikasi_2fa_view(request):
    """Halaman input kode OTP 2FA — muncul di antara login password dan
    sesi resmi terbentuk, kalau Autentikasi 2 Faktor diaktifkan di
    Pengaturan. Kode dicek terhadap yang tersimpan di session (dibuat &
    dikirim oleh login_view lewat otp.buat_dan_kirim_otp)."""
    data = otp.ambil_pending(request)
    if not data:
        messages.error(request, "Tidak ada proses verifikasi 2FA yang aktif. Silakan login ulang.")
        return redirect("deteksi:login")

    user = User.objects.filter(pk=data["user_id"]).first()
    if user is None:
        otp.hapus_pending(request)
        return redirect("deteksi:login")

    if request.method == "POST":
        if request.POST.get("kirim_ulang") == "1":
            pengaturan = Pengaturan.get_instance()
            otp.buat_dan_kirim_otp(request, user, next_url=data.get("next", ""), bahasa=pengaturan.bahasa)
            messages.success(request, "Kode verifikasi baru telah dikirim ke email Anda.")
            return redirect("deteksi:verifikasi_2fa")

        kode_masukan = request.POST.get("kode", "")
        hasil = otp.verifikasi_kode(request, kode_masukan)
        if hasil == "ok":
            next_url = data.get("next", "")
            otp.hapus_pending(request)
            login(request, user)
            messages.success(request, f"Selamat datang kembali, {user.first_name or user.username}!")
            return redirect(next_url or "deteksi:deteksi_page")
        elif hasil == "kadaluwarsa":
            messages.error(request, "Kode verifikasi sudah kedaluwarsa. Silakan minta kode baru.")
        elif hasil == "tidak_ada":
            messages.error(request, "Sesi verifikasi tidak ditemukan. Silakan login ulang.")
            return redirect("deteksi:login")
        else:
            messages.error(request, "Kode verifikasi salah. Silakan coba lagi.")

    return render(request, "deteksi/auth/verifikasi_2fa.html", {
        "email_tujuan": otp.email_tujuan(user),
        "punya_fingerprint": fingerprint.punya_fingerprint(user),
    })


def fingerprint_login_opsi_view(request):
    """AJAX langkah 1 saat login: buat challenge WebAuthn untuk user yang
    lagi pending verifikasi 2FA (bukan session Django auth, karena user
    belum resmi login — masih di tahap yang sama dengan verifikasi_2fa_view)."""
    data = otp.ambil_pending(request)
    if not data:
        return JsonResponse({"ok": False, "error": "Sesi login sudah kedaluwarsa."}, status=400)
    user = User.objects.filter(pk=data["user_id"]).first()
    if user is None or not fingerprint.punya_fingerprint(user):
        return JsonResponse({"ok": False, "error": "Fingerprint tidak tersedia untuk akun ini."}, status=400)
    opsi_json = fingerprint.buat_opsi_login(request, user)
    return JsonResponse(json.loads(opsi_json))


@require_POST
def fingerprint_login_verifikasi_view(request):
    """AJAX langkah 2 saat login: verifikasi hasil navigator.credentials.get()
    dan, kalau cocok, selesaikan proses login (gantinya kode OTP email)."""
    data = otp.ambil_pending(request)
    if not data:
        return JsonResponse({"ok": False, "error": "Sesi login sudah kedaluwarsa. Silakan login ulang."}, status=400)

    user = User.objects.filter(pk=data["user_id"]).first()
    if user is None:
        otp.hapus_pending(request)
        return JsonResponse({"ok": False, "error": "Akun tidak ditemukan."}, status=400)

    try:
        body = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "Data tidak valid."}, status=400)

    ok, pesan_error = fingerprint.verifikasi_login(request, user, body)
    if not ok:
        return JsonResponse({"ok": False, "error": pesan_error}, status=400)

    next_url = data.get("next", "")
    otp.hapus_pending(request)
    login(request, user)
    messages.success(request, f"Selamat datang kembali, {user.first_name or user.username}!")
    return JsonResponse({"ok": True, "redirect": next_url or reverse("deteksi:deteksi_page")})


def register_view(request):
    """Form pendaftaran akun baru (nyata, tersimpan di tabel auth_user)."""
    if request.user.is_authenticated:
        return redirect("deteksi:deteksi_page")

    next_url = request.GET.get("next") or request.POST.get("next") or ""

    form_data = {"nama_lengkap": "", "email": "", "username": ""}

    if request.method == "POST":
        nama_lengkap = request.POST.get("nama_lengkap", "").strip()
        email = request.POST.get("email", "").strip()
        username = request.POST.get("username", "").strip()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")

        form_data = {"nama_lengkap": nama_lengkap, "email": email, "username": username}
        errors = []

        if not nama_lengkap:
            errors.append("Nama lengkap wajib diisi.")
        if not username:
            errors.append("Username wajib diisi.")
        elif User.objects.filter(username__iexact=username).exists():
            errors.append("Username sudah dipakai, silakan pilih username lain.")
        if not email:
            errors.append("Email wajib diisi.")
        elif User.objects.filter(email__iexact=email).exists():
            errors.append("Email sudah terdaftar. Silakan login atau gunakan reset password.")
        if password1 != password2:
            errors.append("Konfirmasi password tidak cocok.")
        if password1 and not errors:
            try:
                validate_password(password1)
            except ValidationError as e:
                errors.extend(e.messages)

        if not errors:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=nama_lengkap,
            )

            # Signal `buat_akun_untuk_user_baru` sudah otomatis membuat
            # baris Akun (profil) untuk user ini; di sini kita tinggal
            # sinkronkan nama & email yang diisi di form pendaftaran.
            akun = Akun.get_for_user(user)
            akun.nama_lengkap = nama_lengkap
            akun.email = email
            akun.save(update_fields=["nama_lengkap", "email", "updated_at"])

            login(request, user)
            messages.success(request, "Pendaftaran berhasil! Selamat datang di Deteksi Ban.")
            fingerprint_url = reverse("deteksi:daftarkan_fingerprint")
            if next_url:
                fingerprint_url = f"{fingerprint_url}?next={next_url}"
            return redirect(fingerprint_url)

        for err in errors:
            messages.error(request, err)

    return render(request, "deteksi/auth/register.html", {"next": next_url, "form_data": form_data})


@login_required
def daftarkan_fingerprint_view(request):
    """Halaman setelah register: tawarkan daftarkan fingerprint sebagai
    alternatif 2FA. Boleh dilewati (skip) kalau perangkat user tidak
    punya sensor biometrik atau user tidak mau."""
    next_url = request.GET.get("next") or ""
    sudah_punya = fingerprint.punya_fingerprint(request.user)
    return render(request, "deteksi/auth/daftarkan_fingerprint.html", {
        "next": next_url,
        "sudah_punya": sudah_punya,
    })


@login_required
def lewati_fingerprint_view(request):
    next_url = request.GET.get("next") or request.POST.get("next") or ""
    return redirect(next_url or "deteksi:deteksi_page")


@login_required
@require_POST
def fingerprint_registrasi_opsi_view(request):
    """AJAX langkah 1: server buat challenge WebAuthn buat registrasi."""
    opsi_json = fingerprint.buat_opsi_registrasi(request, request.user)
    return JsonResponse(json.loads(opsi_json))


@login_required
@require_POST
def fingerprint_registrasi_verifikasi_view(request):
    """AJAX langkah 2: verifikasi hasil dari navigator.credentials.create()
    dan simpan kredensialnya kalau valid."""
    try:
        body = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "Data tidak valid."}, status=400)

    nama_perangkat = body.pop("nama_perangkat", "") if isinstance(body, dict) else ""
    ok, pesan_error = fingerprint.verifikasi_dan_simpan_registrasi(
        request, request.user, body, nama_perangkat=nama_perangkat
    )
    if ok:
        LogAktivitas.catat(request, "Mendaftarkan fingerprint", detail=nama_perangkat or "Perangkat")
        return JsonResponse({"ok": True})
    return JsonResponse({"ok": False, "error": pesan_error}, status=400)


def logout_view(request):
    """Keluar dari sesi login (POST only, dipanggil dari tombol 'Keluar')."""
    if request.method == "POST":
        logout(request)
        messages.success(request, "Anda berhasil keluar.")
    return redirect("deteksi:login")


@login_required(login_url="deteksi:login")
def beranda(request):
    """Halaman Beranda — ringkasan statistik nyata dari riwayat deteksi.
    Admin melihat statistik seluruh pengguna; pengguna biasa hanya
    melihat statistik riwayat deteksinya sendiri."""
    model_ready = inference.is_ready()
    model_error = inference.get_error()

    # Cek nyata (bukan cron) apakah sudah waktunya kirim pengingat
    # perawatan dan/atau ringkasan mingguan sesuai toggle di Pengaturan.
    cek_pengingat_dan_ringkasan(request.user)

    qs = Riwayat.objects.all() if _is_admin(request.user) else Riwayat.objects.filter(user=request.user)
    total = qs.count()

    now = timezone.now()
    minggu_ini_start = now - timezone.timedelta(days=7)
    minggu_lalu_start = now - timezone.timedelta(days=14)

    total_minggu_ini = qs.filter(created_at__gte=minggu_ini_start).count()
    total_minggu_lalu = qs.filter(created_at__gte=minggu_lalu_start, created_at__lt=minggu_ini_start).count()
    delta_pct = None
    if total_minggu_lalu:
        delta_pct = round((total_minggu_ini - total_minggu_lalu) * 100 / total_minggu_lalu)

    avg_confidence = qs.aggregate(v=Avg("confidence"))["v"]
    total_waktu_ms = qs.aggregate(v=Sum("processing_ms"))["v"] or 0

    # Tren rata-rata keyakinan minggu ini vs minggu lalu
    avg_conf_minggu_ini = qs.filter(created_at__gte=minggu_ini_start).aggregate(v=Avg("confidence"))["v"]
    avg_conf_minggu_lalu = qs.filter(created_at__gte=minggu_lalu_start, created_at__lt=minggu_ini_start).aggregate(v=Avg("confidence"))["v"]
    conf_delta_pct = None
    if avg_conf_minggu_ini is not None and avg_conf_minggu_lalu:
        conf_delta_pct = round((avg_conf_minggu_ini - avg_conf_minggu_lalu) * 100 / avg_conf_minggu_lalu)

    # Tren total waktu analisis minggu ini vs minggu lalu
    waktu_minggu_ini = qs.filter(created_at__gte=minggu_ini_start).aggregate(v=Sum("processing_ms"))["v"] or 0
    waktu_minggu_lalu = qs.filter(created_at__gte=minggu_lalu_start, created_at__lt=minggu_ini_start).aggregate(v=Sum("processing_ms"))["v"] or 0
    waktu_delta_pct = None
    if waktu_minggu_lalu:
        waktu_delta_pct = round((waktu_minggu_ini - waktu_minggu_lalu) * 100 / waktu_minggu_lalu)

    # Format durasi total waktu analisis secara ringkas (detik/menit/jam)
    bahasa = Pengaturan.get_instance().bahasa
    t = get_text(bahasa)
    total_detik = total_waktu_ms / 1000
    if total_detik >= 3600:
        total_waktu_label = f"{total_detik / 3600:.1f} {t['common_jam']}"
    elif total_detik >= 60:
        total_waktu_label = f"{total_detik / 60:.1f} {t['common_menit']}"
    else:
        total_waktu_label = f"{total_detik:.1f} {t['common_detik']}"

    terakhir = qs.first()

    counts = {"BAIK": 0, "PERHATIAN": 0, "BERMASALAH": 0}
    for row in qs.filter(created_at__gte=minggu_ini_start).values("label").annotate(n=Count("id")):
        counts[row["label"]] = row["n"]
    total_periode = sum(counts.values())

    circumference = 263.9
    offset = 0
    donut = []
    for key in ("BAIK", "PERHATIAN", "BERMASALAH"):
        pct = round(counts[key] * 100 / total_periode) if total_periode else 0
        dash = round(circumference * pct / 100, 1)
        donut.append({
            "key": key, "count": counts[key], "pct": pct,
            "meta": STATUS_META[key],
            "dash": dash, "dash_gap": round(circumference - dash, 1),
            "dash_offset": round(-offset, 1),
        })
        offset += circumference * pct / 100

    aktivitas = list(qs[:5])

    context = {
        "model_ready": model_ready,
        "model_error": model_error,
        "total_deteksi": total,
        "delta_pct": delta_pct,
        "avg_confidence": round(avg_confidence, 1) if avg_confidence is not None else None,
        "conf_delta_pct": conf_delta_pct,
        "total_waktu_detik": round(total_waktu_ms / 1000, 1),
        "total_waktu_label": total_waktu_label,
        "waktu_delta_pct": waktu_delta_pct,
        "terakhir": terakhir,
        "terakhir_meta": STATUS_META.get(terakhir.label) if terakhir else None,
        "donut": donut,
        "total_periode": total_periode,
        "aktivitas": aktivitas,
    }
    return render(request, "deteksi/beranda.html", context)


@login_required(login_url="deteksi:login")
def deteksi_page(request):
    """Halaman Deteksi — tampilan hasil lengkap (Gambar, Detail, Ringkasan).
    Wajib login: kalau belum login, otomatis diarahkan ke form login
    (bawa ?next= supaya balik ke sini lagi setelah berhasil login)."""
    model_ready = inference.is_ready()
    model_error = inference.get_error()
    return render(request, "deteksi/deteksi.html", {
        "model_ready": model_ready,
        "model_error": model_error,
    })


@login_required(login_url="deteksi:login")
def riwayat_page(request):
    """Halaman Riwayat — daftar hasil deteksi yang tersimpan di database.
    Admin melihat riwayat semua pengguna; pengguna biasa hanya melihat
    riwayat deteksinya sendiri."""
    base_qs = Riwayat.objects.all() if _is_admin(request.user) else Riwayat.objects.filter(user=request.user)
    qs = base_qs

    status = request.GET.get("status")
    if status in dict(Riwayat.STATUS_CHOICES):
        qs = qs.filter(label=status)

    q = request.GET.get("q")
    if q:
        qs = qs.filter(kelas__icontains=q)

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    riwayat_list = []
    for item in page_obj.object_list:
        riwayat_list.append({
            "obj": item,
            "meta": STATUS_META[item.label],
        })

    return render(request, "deteksi/riwayat.html", {
        "riwayat_list": riwayat_list,
        "page_obj": page_obj,
        "active_status": status or "",
        "total_all": base_qs.count(),
    })


# Konten edukasi statis (bukan hasil deteksi) — token konten halaman Tips.
TIPS_UTAMA = [
    {
        "nomor": 1,
        "judul": "Cek Tekanan Angin Secara Rutin",
        "deskripsi": "Periksa tekanan angin minimal seminggu sekali untuk menjaga performa dan keamanan.",
        "gambar": "deteksi/img/tips/cek-tekanan-angin.png",
    },
    {
        "nomor": 2,
        "judul": "Rotasi Ban Setiap 10.000 km",
        "deskripsi": "Rotasi ban secara berkala agar keausan merata dan umur ban lebih panjang.",
        "gambar": "deteksi/img/tips/rotasi-ban.png",
    },
    {
        "nomor": 3,
        "judul": "Jaga Keseimbangan & Spooring",
        "deskripsi": "Spooring dan balancing yang tepat membantu ban aus merata dan kendaraan lebih stabil.",
        "gambar": "deteksi/img/tips/jaga-keseimbangan.png",
    },
    {
        "nomor": 4,
        "judul": "Periksa Kedalaman Alur Ban",
        "deskripsi": "Pastikan kedalaman alur minimal 1.6 mm untuk menjaga daya cengkeram di jalan basah.",
        "gambar": "deteksi/img/tips/periksa-kedalaman-alur.png",
    },
    {
        "nomor": 5,
        "judul": "Hindari Beban Berlebih",
        "deskripsi": "Beban berlebih dapat membuat ban cepat aus, meningkatkan risiko pecah ban, dan boros BBM.",
        "gambar": "deteksi/img/tips/hindari-beban-berlebih.png",
    },
    {
        "nomor": 6,
        "judul": "Perhatikan Kondisi Ban",
        "deskripsi": "Periksa retakan, benjolan, atau benda asing yang menempel pada ban secara rutin.",
        "gambar": "deteksi/img/tips/perhatikan-kondisi-ban.png",
    },
]

TIPS_UTAMA_EN = [
    {
        "nomor": 1,
        "judul": "Check Tire Pressure Regularly",
        "deskripsi": "Check the air pressure at least once a week to maintain performance and safety.",
        "gambar": "deteksi/img/tips/cek-tekanan-angin.png",
    },
    {
        "nomor": 2,
        "judul": "Rotate Tires Every 10,000 km",
        "deskripsi": "Rotate the tires periodically so wear is even and the tires last longer.",
        "gambar": "deteksi/img/tips/rotasi-ban.png",
    },
    {
        "nomor": 3,
        "judul": "Maintain Balance & Alignment",
        "deskripsi": "Proper alignment and balancing help tires wear evenly and keep the vehicle more stable.",
        "gambar": "deteksi/img/tips/jaga-keseimbangan.png",
    },
    {
        "nomor": 4,
        "judul": "Check Tire Tread Depth",
        "deskripsi": "Make sure the tread depth is at least 1.6 mm to maintain grip on wet roads.",
        "gambar": "deteksi/img/tips/periksa-kedalaman-alur.png",
    },
    {
        "nomor": 5,
        "judul": "Avoid Overloading",
        "deskripsi": "Overloading can wear tires out faster, increase the risk of a blowout, and waste fuel.",
        "gambar": "deteksi/img/tips/hindari-beban-berlebih.png",
    },
    {
        "nomor": 6,
        "judul": "Watch the Tire Condition",
        "deskripsi": "Regularly check for cracks, bulges, or foreign objects stuck in the tire.",
        "gambar": "deteksi/img/tips/perhatikan-kondisi-ban.png",
    },
]

RINGKASAN_TIPS = [
    "Cek tekanan angin minimal seminggu sekali",
    "Rotasi ban setiap 10.000 km",
    "Lakukan spooring & balancing secara berkala",
    "Pastikan kedalaman alur minimal 1.6 mm",
    "Hindari beban berlebih pada kendaraan",
    "Periksa kondisi ban sebelum perjalanan jauh",
]

RINGKASAN_TIPS_EN = [
    "Check tire pressure at least once a week",
    "Rotate tires every 10,000 km",
    "Get alignment & balancing done periodically",
    "Make sure tread depth is at least 1.6 mm",
    "Avoid overloading the vehicle",
    "Check tire condition before long trips",
]

JADWAL_PERAWATAN = [
    {"judul": "Cek Tekanan Angin", "interval": "Setiap 1 Minggu", "icon": "tekanan"},
    {"judul": "Rotasi Ban", "interval": "Setiap 10.000 km", "icon": "rotasi"},
    {"judul": "Spooring & Balancing", "interval": "Setiap 10.000 km", "icon": "spooring"},
    {"judul": "Cek Kedalaman Alur", "interval": "Setiap 1 Bulan", "icon": "alur"},
    {"judul": "Pemeriksaan Kondisi Ban", "interval": "Sebelum Perjalanan Jauh", "icon": "periksa"},
]

JADWAL_PERAWATAN_EN = [
    {"judul": "Check Tire Pressure", "interval": "Every 1 Week", "icon": "tekanan"},
    {"judul": "Tire Rotation", "interval": "Every 10,000 km", "icon": "rotasi"},
    {"judul": "Alignment & Balancing", "interval": "Every 10,000 km", "icon": "spooring"},
    {"judul": "Check Tread Depth", "interval": "Every 1 Month", "icon": "alur"},
    {"judul": "Tire Condition Check", "interval": "Before Long Trips", "icon": "periksa"},
]


def tips_page(request):
    """Halaman Tips — panduan perawatan ban (konten edukasi statis)."""
    bahasa = Pengaturan.get_instance().bahasa
    if bahasa == "en":
        return render(request, "deteksi/tips.html", {
            "tips_utama": TIPS_UTAMA_EN,
            "ringkasan_tips": RINGKASAN_TIPS_EN,
            "jadwal_perawatan": JADWAL_PERAWATAN_EN,
        })
    return render(request, "deteksi/tips.html", {
        "tips_utama": TIPS_UTAMA,
        "ringkasan_tips": RINGKASAN_TIPS,
        "jadwal_perawatan": JADWAL_PERAWATAN,
    })


# Konten edukasi statis (bukan hasil deteksi) — token konten halaman Bantuan.
TOPIK_BANTUAN = [
    {
        "judul": "Cara Melakukan Deteksi",
        "deskripsi": "Pelajari langkah-langkah melakukan deteksi ban dengan kamera atau upload.",
        "icon": "kamera",
    },
    {
        "judul": "Laporan & PDF",
        "deskripsi": "Cara melihat, mengunduh, dan membagikan laporan deteksi dalam format PDF.",
        "icon": "laporan",
    },
    {
        "judul": "Riwayat Deteksi",
        "deskripsi": "Kelola dan lihat kembali riwayat deteksi yang pernah Anda lakukan.",
        "icon": "riwayat",
    },
    {
        "judul": "Pengaturan Akun",
        "deskripsi": "Atur profil, notifikasi, dan preferensi aplikasi sesuai kebutuhan Anda.",
        "icon": "pengaturan",
    },
]

TOPIK_BANTUAN_EN = [
    {
        "judul": "How to Run a Detection",
        "deskripsi": "Learn the steps to detect a tire using the camera or by uploading an image.",
        "icon": "kamera",
    },
    {
        "judul": "Reports & PDF",
        "deskripsi": "How to view, download, and share detection reports in PDF format.",
        "icon": "laporan",
    },
    {
        "judul": "Detection History",
        "deskripsi": "Manage and revisit the detections you've made in the past.",
        "icon": "riwayat",
    },
    {
        "judul": "Account Settings",
        "deskripsi": "Manage your profile, notifications, and app preferences as needed.",
        "icon": "pengaturan",
    },
]

FAQ_BANTUAN = [
    {
        "pertanyaan": "Bagaimana cara melakukan deteksi ban?",
        "jawaban": "Buka halaman Deteksi, pilih sumber gambar (kamera atau upload), lalu ambil atau unggah foto ban. Sistem akan memproses dan menampilkan hasil deteksi secara otomatis.",
    },
    {
        "pertanyaan": "Format gambar apa yang didukung untuk upload?",
        "jawaban": "Saat ini format yang didukung adalah JPG dan PNG dengan ukuran file yang wajar agar proses deteksi berjalan lancar.",
    },
    {
        "pertanyaan": "Berapa lama proses deteksi berlangsung?",
        "jawaban": "Proses deteksi umumnya hanya membutuhkan waktu beberapa detik, tergantung ukuran gambar dan koneksi perangkat Anda.",
    },
    {
        "pertanyaan": "Bagaimana cara mengunduh laporan dalam PDF?",
        "jawaban": "Setelah hasil deteksi muncul, klik tombol \"Download PDF\" pada halaman hasil untuk mengunduh laporan lengkapnya.",
    },
    {
        "pertanyaan": "Apakah data saya aman?",
        "jawaban": "Ya. Semua data dan gambar yang Anda kirim disimpan dengan aman dan tidak dibagikan tanpa izin Anda.",
    },
    {
        "pertanyaan": "Bagaimana cara menghapus riwayat deteksi?",
        "jawaban": "Buka halaman Riwayat, pilih data deteksi yang ingin dihapus, lalu gunakan opsi hapus pada item tersebut.",
    },
]

FAQ_BANTUAN_EN = [
    {
        "pertanyaan": "How do I detect a tire?",
        "jawaban": "Open the Detection page, choose an image source (camera or upload), then take or upload a tire photo. The system will process it and show the result automatically.",
    },
    {
        "pertanyaan": "Which image formats are supported for upload?",
        "jawaban": "Currently JPG and PNG are supported, with a reasonable file size so the detection process runs smoothly.",
    },
    {
        "pertanyaan": "How long does the detection process take?",
        "jawaban": "Detection usually takes only a few seconds, depending on the image size and your device's connection.",
    },
    {
        "pertanyaan": "How do I download the report as a PDF?",
        "jawaban": "Once the detection result appears, click the \"Download PDF\" button on the result page to download the full report.",
    },
    {
        "pertanyaan": "Is my data safe?",
        "jawaban": "Yes. All data and images you submit are stored securely and are never shared without your permission.",
    },
    {
        "pertanyaan": "How do I delete a detection from my history?",
        "jawaban": "Open the History page, select the detection you want to delete, then use the delete option on that item.",
    },
]


def bantuan_page(request):
    """Halaman Bantuan — pusat bantuan & FAQ (konten edukasi statis)."""
    bahasa = Pengaturan.get_instance().bahasa
    if bahasa == "en":
        return render(request, "deteksi/bantuan.html", {
            "topik_bantuan": TOPIK_BANTUAN_EN,
            "faq_bantuan": FAQ_BANTUAN_EN,
        })
    return render(request, "deteksi/bantuan.html", {
        "topik_bantuan": TOPIK_BANTUAN,
        "faq_bantuan": FAQ_BANTUAN,
    })


def tentang_page(request):
    """Halaman Tentang — profil & informasi aplikasi (info rilis nyata,
    bukan data contoh, diambil dari APP_VERSION & environment)."""
    bahasa = Pengaturan.get_instance().bahasa
    info_aplikasi = {
        "nama": "TireScan" if bahasa == "en" else "Deteksi Ban",
        "versi": APP_VERSION,
        "rilis": "May 2024" if bahasa == "en" else "Mei 2024",
        "teknologi": "AI Vision, Machine Learning",
        "negara": "Indonesia",
    }
    return render(request, "deteksi/tentang.html", {
        "info_aplikasi": info_aplikasi,
    })


@login_required(login_url="deteksi:login")
def notifikasi_page(request):
    """Halaman Notifikasi — data nyata dari database (model Notifikasi),
    difilter khusus milik user yang sedang login."""
    notifikasi_list = Notifikasi.objects.filter(user=request.user)
    belum_dibaca = notifikasi_list.filter(dibaca=False).count()
    return render(request, "deteksi/notifikasi.html", {
        "notifikasi_list": notifikasi_list,
        "belum_dibaca_count": belum_dibaca,
    })


@csrf_exempt
def tandai_notifikasi_dibaca_view(request, pk):
    """Tandai satu notifikasi sebagai sudah dibaca (dipanggil via AJAX saat
    notifikasi dibuka), supaya badge lonceng ikut berkurang secara nyata."""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Method not allowed"}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Silakan login terlebih dahulu."}, status=401)
    notif = get_object_or_404(Notifikasi, pk=pk, user=request.user)
    if not notif.dibaca:
        notif.dibaca = True
        notif.save(update_fields=["dibaca"])
    sisa = Notifikasi.objects.filter(user=request.user, dibaca=False).count()
    return JsonResponse({"success": True, "unread_count": sisa})


@csrf_exempt
def tandai_semua_notifikasi_dibaca_view(request):
    """Tandai seluruh notifikasi milik user yang sedang login sebagai sudah dibaca."""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Method not allowed"}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Silakan login terlebih dahulu."}, status=401)
    Notifikasi.objects.filter(user=request.user, dibaca=False).update(dibaca=True)
    return JsonResponse({"success": True, "unread_count": 0})




def _alur_confidence_bars(breakdown):
    """Susun breakdown probabilitas (nyata, dari model) untuk ditampilkan
    sebagai bar tingkat keyakinan di tab Detail Analisis."""
    return breakdown or []


@login_required(login_url="deteksi:login")
def laporan_page(request, pk):
    """Halaman Laporan — laporan detail satu hasil deteksi nyata dari
    database. Hanya pemilik riwayat tersebut atau admin yang boleh
    membukanya."""
    item = get_object_or_404(Riwayat, pk=pk)

    if not _is_admin(request.user) and item.user_id != request.user.id:
        messages.error(request, "Anda tidak memiliki akses ke laporan ini.")
        return redirect("deteksi:riwayat_page")

    status_meta = STATUS_META[item.label]
    retakan_terdeteksi = item.code_label == "cracked"
    robek_terdeteksi = item.code_label == "Tear"

    qs = Riwayat.objects.all() if _is_admin(request.user) else Riwayat.objects.filter(user=request.user)
    total = qs.count()
    counts = dict(qs.values_list("label").annotate(n=Count("id")))
    counts = {k: counts.get(k, 0) for k in ("BAIK", "PERHATIAN", "BERMASALAH")}

    circumference = 263.9
    offset = 0
    stats = []
    for key in ("BAIK", "PERHATIAN", "BERMASALAH"):
        pct = round(counts[key] * 100 / total) if total else 0
        dash = round(circumference * pct / 100, 1)
        stats.append({
            "key": key, "count": counts[key], "pct": pct, "meta": STATUS_META[key],
            "dash": dash, "dash_gap": round(circumference - dash, 1),
            "dash_offset": round(-offset, 1),
        })
        offset += circumference * pct / 100

    # navigasi prev/next berdasar urutan waktu (item terbaru dulu)
    older = qs.filter(created_at__lt=item.created_at).order_by("-created_at").first()
    newer = qs.filter(created_at__gt=item.created_at).order_by("created_at").first()

    context = {
        "item": item,
        "prev_item": newer,
        "next_item": older,
        "total": total,
        "status_meta": status_meta,
        "retakan_terdeteksi": retakan_terdeteksi,
        "robek_terdeteksi": robek_terdeteksi,
        "breakdown": item.breakdown,
        "stats": stats,
        "total_deteksi": total,
    }
    return render(request, "deteksi/laporan.html", context)


@login_required(login_url="deteksi:login")
def profil_page(request):
    """Halaman Informasi Akun — data nyata dari database, satu profil
    Akun per pengguna yang sedang login. Form 'Edit Profil' (nama &
    email) POST ke sini juga."""
    akun = Akun.get_for_user(request.user)

    if request.method == "POST":
        nama_lengkap = request.POST.get("nama_lengkap", "").strip()
        email = request.POST.get("email", "").strip()

        if not nama_lengkap:
            messages.error(request, "Nama lengkap tidak boleh kosong.")
            return redirect("deteksi:profil_page")

        if email != akun.email:
            akun.email_terverifikasi = False  # email baru perlu verifikasi ulang

        akun.nama_lengkap = nama_lengkap
        akun.email = email
        akun.save()
        messages.success(request, "Profil berhasil diperbarui.")
        return redirect("deteksi:profil_page")

    return render(request, "deteksi/profil.html", {
        "akun": akun,
    })


@login_required(login_url="deteksi:login")
@require_POST
def upload_foto_profil_view(request):
    """Upload foto profil (JPG/PNG, maksimal 2MB) — divalidasi & disimpan
    nyata sebagai file media, bukan sekadar preview di browser."""
    akun = Akun.get_for_user(request.user)
    foto = request.FILES.get("foto")

    if not foto:
        messages.error(request, "Tidak ada file yang dipilih.")
        return redirect("deteksi:profil_page")

    if foto.content_type not in ("image/jpeg", "image/png"):
        messages.error(request, "Format file harus JPG atau PNG.")
        return redirect("deteksi:profil_page")

    if foto.size > 2 * 1024 * 1024:
        messages.error(request, "Ukuran file maksimal 2MB.")
        return redirect("deteksi:profil_page")

    akun.foto = foto
    akun.save(update_fields=["foto", "updated_at"])
    messages.success(request, "Foto profil berhasil diperbarui.")
    return redirect("deteksi:profil_page")


@login_required(login_url="deteksi:login")
@require_POST
def ubah_telepon_view(request):
    """Ubah nomor telepon akun — tersimpan nyata di database."""
    akun = Akun.get_for_user(request.user)
    telepon = request.POST.get("telepon", "").strip()

    if not telepon:
        messages.error(request, "Nomor telepon tidak boleh kosong.")
        return redirect("deteksi:profil_page")

    akun.telepon = telepon
    akun.save(update_fields=["telepon", "updated_at"])
    messages.success(request, "Nomor telepon berhasil diperbarui.")
    return redirect("deteksi:profil_page")


@login_required(login_url="deteksi:login")
def pengaturan_page(request):
    """Halaman Pengaturan — preferensi aplikasi nyata, tersimpan di database
    (singleton Pengaturan), bukan sekadar tampilan statis."""
    pengaturan = Pengaturan.get_instance()

    if request.method == "POST":
        pengaturan.tema = request.POST.get("tema", pengaturan.tema)
        pengaturan.bahasa = request.POST.get("bahasa", pengaturan.bahasa)
        pengaturan.zona_waktu = request.POST.get("zona_waktu", pengaturan.zona_waktu)
        pengaturan.format_tanggal = request.POST.get("format_tanggal", pengaturan.format_tanggal)
        pengaturan.notifikasi_email = request.POST.get("notifikasi_email") == "on"
        pengaturan.push_notification = request.POST.get("push_notification") == "on"
        pengaturan.pengingat_perawatan = request.POST.get("pengingat_perawatan") == "on"
        pengaturan.ringkasan_mingguan = request.POST.get("ringkasan_mingguan") == "on"
        pengaturan.save()
        t_msg = get_text(pengaturan.bahasa)
        messages.success(request, t_msg.get("pengaturan_simpan_berhasil", "Perubahan pengaturan berhasil disimpan."))
        return redirect("deteksi:pengaturan_page")

    # Info nyata untuk panel "Tentang Aplikasi"
    bahasa = pengaturan.bahasa
    db_engine = django_settings.DATABASES["default"]["ENGINE"].rsplit(".", 1)[-1]
    info_aplikasi = {
        "nama": "TireScan" if bahasa == "en" else "Deteksi Ban",
        "versi": APP_VERSION,
        "django_versi": django.get_version(),
        "python_versi": platform.python_version(),
        "database": db_engine,
        "model_status": ("Ready" if bahasa == "en" else "Siap") if inference.is_ready() else ("Not ready" if bahasa == "en" else "Belum siap"),
        "total_riwayat": Riwayat.objects.count(),
    }

    # Sesi login aktif nyata (dari tabel django_session), dipakai panel
    # Keamanan > Kelola Sesi Login — bukan data contoh.
    if not request.session.session_key:
        request.session.save()
    current_key = request.session.session_key
    sesi_list = []
    for sesi in Session.objects.filter(expire_date__gt=timezone.now()).order_by("-expire_date"):
        sesi_list.append({
            "key": sesi.session_key,
            "expire_date": sesi.expire_date,
            "is_current": sesi.session_key == current_key,
        })

    return render(request, "deteksi/pengaturan.html", {
        "pengaturan": pengaturan,
        "info_aplikasi": info_aplikasi,
        "sesi_list": sesi_list,
        "tema_choices": Pengaturan.TEMA_CHOICES,
        "bahasa_choices": Pengaturan.BAHASA_CHOICES,
        "zona_waktu_choices": Pengaturan.ZONA_WAKTU_CHOICES,
        "format_tanggal_choices": Pengaturan.FORMAT_TANGGAL_CHOICES,
    })


@login_required(login_url="deteksi:login")
@login_required(login_url="deteksi:login")
@require_POST
def hapus_cache_view(request):
    """Bersihkan cache aplikasi & sesi kedaluwarsa (aksi nyata, bukan simulasi)."""
    cache.clear()
    now = timezone.now()
    sesi_dihapus = Session.objects.filter(expire_date__lt=now).count()
    Session.objects.filter(expire_date__lt=now).delete()

    if sesi_dihapus:
        messages.success(request, f"Cache dibersihkan. {sesi_dihapus} sesi kedaluwarsa juga dihapus.")
    else:
        messages.success(request, "Cache aplikasi berhasil dibersihkan.")
    return redirect("deteksi:pengaturan_page")


@login_required(login_url="deteksi:login")
@require_POST
def toggle_2fa_view(request):
    """Aktifkan/nonaktifkan Autentikasi 2 Faktor — status tersimpan nyata
    di baris Pengaturan (singleton), dipakai di badge & tombol panel Keamanan."""
    pengaturan = Pengaturan.get_instance()
    pengaturan.autentikasi_2fa = not pengaturan.autentikasi_2fa
    pengaturan.save()
    if pengaturan.autentikasi_2fa:
        messages.success(request, "Autentikasi 2 Faktor berhasil diaktifkan.")
    else:
        messages.success(request, "Autentikasi 2 Faktor dinonaktifkan.")
    return redirect("deteksi:pengaturan_page")


@login_required(login_url="deteksi:login")
@require_POST
def akhiri_sesi_view(request, session_key):
    """Akhiri satu sesi login aktif (hapus baris django_session terkait),
    kecuali sesi yang sedang dipakai request ini sendiri."""
    if session_key == request.session.session_key:
        messages.error(request, "Sesi yang sedang Anda gunakan tidak bisa diakhiri dari sini.")
    else:
        deleted, _ = Session.objects.filter(session_key=session_key).delete()
        if deleted:
            messages.success(request, "Sesi login berhasil diakhiri.")
        else:
            messages.error(request, "Sesi tidak ditemukan (mungkin sudah berakhir).")
    return redirect("deteksi:pengaturan_page")


def _decode_image(request):
    """Ambil gambar dari file upload biasa ATAU dari base64 (hasil kamera)."""
    if request.FILES.get("image"):
        f = request.FILES["image"]
        f.seek(0)
        return Image.open(f), f, f.name

    body = request.POST.get("image_base64")
    if not body:
        try:
            data = json.loads(request.body.decode("utf-8"))
            body = data.get("image_base64")
        except Exception:
            body = None

    if not body:
        return None, None, None

    if "," in body:
        body = body.split(",", 1)[1]
    raw = base64.b64decode(body)
    from django.core.files.base import ContentFile
    django_file = ContentFile(raw, name="kamera.jpg")
    return Image.open(io.BytesIO(raw)), django_file, "kamera.jpg"


@csrf_exempt
@require_POST
def predict_view(request):
    bahasa = Pengaturan.get_instance().bahasa
    t = get_text(bahasa)
    # Endpoint ini dipanggil via fetch() dari halaman Deteksi, yang sendiri
    # sudah dilindungi @login_required. Dicek ulang di sini (bukan cuma
    # redirect ke halaman login) supaya kalau ada yang panggil endpoint
    # ini langsung tanpa lewat halaman, responsnya tetap JSON yang rapi
    # dan JS di frontend bisa mengarahkan ke form login.
    if not request.user.is_authenticated:
        return JsonResponse(
            {
                "success": False,
                "error": "Please log in first to detect a tire." if bahasa == "en" else "Silakan login terlebih dahulu untuk melakukan deteksi ban.",
                "login_required": True,
                "login_url": f"{reverse('deteksi:login')}?next={reverse('deteksi:deteksi_page')}",
            },
            status=401,
        )

    try:
        img, django_file, filename = _decode_image(request)
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid image / failed to read." if bahasa == "en" else "Gambar tidak valid / gagal dibaca."}, status=400)

    if img is None:
        return JsonResponse({"success": False, "error": "No image was sent." if bahasa == "en" else "Tidak ada gambar yang dikirim."}, status=400)

    width, height = img.size

    start = time.perf_counter()
    result = inference.predict(img)
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    if result.get("success"):
        # Lokalisasi teks hasil deteksi (nama kelas, judul status, deskripsi,
        # rekomendasi) sesuai bahasa aktif saat ini, sebelum disimpan ke
        # Riwayat & dikirim sebagai JSON — supaya hasil deteksi baru selalu
        # konsisten dengan bahasa yang sedang dipilih pengguna.
        code_label = result.get("code_label", "")
        status_key = result.get("label", "")
        result["kelas"] = kelas_i18n(code_label, bahasa)
        result["desc"] = status_desc(status_key, bahasa) or result.get("desc", "")
        if status_key == "BAIK":
            result["rekomendasi"] = (
                "The tire is in good condition and safe to use. Keep up regular routine checks."
                if bahasa == "en" else
                "Ban dalam kondisi baik dan aman digunakan. Tetap lakukan pengecekan rutin secara berkala."
            )
        elif status_key == "PERHATIAN":
            result["rekomendasi"] = (
                "A crack was detected on the tire surface. It's recommended to have the tire checked at a "
                "workshop and to monitor how the crack develops."
                if bahasa == "en" else
                "Terdeteksi retak pada permukaan ban. Disarankan untuk memeriksakan ban ke bengkel dan "
                "memantau perkembangan retakan."
            )
        elif status_key == "BERMASALAH":
            result["rekomendasi"] = (
                "A tear was detected on the tire. The tire condition is poor and risky — replace it as "
                "soon as possible to avoid the risk of an accident."
                if bahasa == "en" else
                "Terdeteksi robek pada ban. Kondisi ban buruk dan berisiko. Segera ganti ban untuk "
                "menghindari risiko kecelakaan."
            )
        for b in result.get("breakdown", []):
            b["kelas"] = kelas_i18n(b.get("code", ""), bahasa)

        result["filename"] = filename
        result["width"] = width
        result["height"] = height

        try:
            django_file.seek(0)
        except Exception:
            pass
        riwayat = Riwayat.objects.create(
            user=request.user,
            image=django_file,
            code_label=code_label,
            kelas=result.get("kelas", ""),
            label=result.get("label", ""),
            color=result.get("color", "gray"),
            confidence=result.get("confidence", 0),
            desc=result.get("desc", ""),
            rekomendasi=result.get("rekomendasi", ""),
            breakdown=result.get("breakdown", []),
            original_filename=filename or "",
            width=width,
            height=height,
            processing_ms=elapsed_ms,
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:255],
        )
        result["riwayat_id"] = riwayat.pk
        result["laporan_url"] = f"/laporan/{riwayat.pk}/"

        # Buat notifikasi nyata sesuai hasil deteksi ini (bukan data
        # contoh statis) — supaya badge lonceng di header selalu
        # mencerminkan aktivitas yang benar-benar terjadi.
        if riwayat.color == "green":
            judul_notif = "Detection complete: tire in good condition" if bahasa == "en" else "Deteksi selesai: kondisi ban baik"
            icon_notif = "upload"
        else:
            judul_notif = "Tire problem detected" if bahasa == "en" else "Kondisi ban bermasalah terdeteksi"
            icon_notif = "peringatan"

        if bahasa == "en":
            pesan_notif = f'The detection result shows a "{riwayat.kelas}" condition with {riwayat.confidence:.0f}% confidence.'
        else:
            pesan_notif = f'Hasil deteksi menunjukkan kondisi "{riwayat.kelas}" dengan keyakinan {riwayat.confidence:.0f}%.'

        kirim_notifikasi(
            request.user,
            judul_notif,
            pesan_notif,
            tag=f"{t['beranda_deteksi_prefix']} #{riwayat.pk}",
            icon=icon_notif,
        )

    status = 200 if result.get("success") else 500
    return JsonResponse(result, status=status)
