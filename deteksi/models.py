from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Pengaturan(models.Model):
    """Preferensi aplikasi & akun (singleton, satu baris untuk seluruh app).

    Diisi & diubah nyata lewat halaman Pengaturan (form POST) dan dipakai
    langsung oleh tampilan lain (mis. satuan pengukuran, format tanggal) —
    tidak ada nilai contoh/dummy yang hanya ditampilkan tanpa tersimpan.
    """

    TEMA_CHOICES = [
        ("terang", "Terang"),
        ("gelap", "Gelap"),
    ]
    ZONA_WAKTU_CHOICES = [
        ("Asia/Jakarta", "(UTC+07:00) Jakarta"),
    ]
    FORMAT_TANGGAL_CHOICES = [
        ("d M Y", "DD MMM YYYY (12 Mei 2024)"),
        ("d/m/Y", "DD/MM/YYYY (12/05/2024)"),
        ("Y-m-d", "YYYY-MM-DD (2024-05-12)"),
    ]
    BAHASA_CHOICES = [
        ("id", "Bahasa Indonesia"),
        ("en", "English"),
    ]

    tema = models.CharField(max_length=10, choices=TEMA_CHOICES, default="terang")
    bahasa = models.CharField(max_length=5, choices=BAHASA_CHOICES, default="id")
    zona_waktu = models.CharField(max_length=32, choices=ZONA_WAKTU_CHOICES, default="Asia/Jakarta")
    format_tanggal = models.CharField(max_length=16, choices=FORMAT_TANGGAL_CHOICES, default="d M Y")

    notifikasi_email = models.BooleanField(default=True)
    push_notification = models.BooleanField(default=True)
    pengingat_perawatan = models.BooleanField(default=True)
    ringkasan_mingguan = models.BooleanField(default=False)

    autentikasi_2fa = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pengaturan Aplikasi"
        verbose_name_plural = "Pengaturan Aplikasi"

    def __str__(self):
        return "Pengaturan Aplikasi"

    @classmethod
    def get_instance(cls):
        """Ambil satu-satunya baris pengaturan; buat dengan nilai default
        jika belum pernah disimpan sebelumnya."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Riwayat(models.Model):
    """Satu baris riwayat = satu hasil deteksi nyata dari model ML.

    Semua field di sini diisi langsung dari output pipeline inferensi
    (deteksi.ml.inference.predict) atau dari request itu sendiri — tidak
    ada nilai contoh/dummy yang di-hardcode.
    """

    STATUS_CHOICES = [
        ("BAIK", "Baik"),
        ("PERHATIAN", "Perhatian"),
        ("BERMASALAH", "Bermasalah"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="riwayat",
        help_text="Pengguna yang melakukan deteksi ini (kosong = data lama sebelum multi-user).",
    )
    image = models.ImageField(upload_to="riwayat/%Y/%m/")
    created_at = models.DateTimeField(auto_now_add=True)

    # Hasil langsung dari inference.predict()
    code_label = models.CharField(max_length=32)        # mis. "normal", "cracked", "Tear"
    kelas = models.CharField(max_length=32)              # mis. "Normal", "Retak", "Robek"
    label = models.CharField(max_length=16, choices=STATUS_CHOICES)  # BAIK/PERHATIAN/BERMASALAH
    color = models.CharField(max_length=16)
    confidence = models.FloatField()                     # confidence kelas terpilih (%)
    desc = models.TextField(blank=True)
    rekomendasi = models.TextField(blank=True)
    breakdown = models.JSONField(default=list)           # probabilitas per kelas

    # Metadata gambar & permintaan (nyata, diambil saat request)
    original_filename = models.CharField(max_length=255, blank=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    processing_ms = models.PositiveIntegerField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Riwayat Deteksi"
        verbose_name_plural = "Riwayat Deteksi"

    def __str__(self):
        return f"{self.label} - {self.created_at:%Y-%m-%d %H:%M}"


class Notifikasi(models.Model):
    """Satu baris = satu notifikasi nyata, tersimpan di database.

    Status `dibaca` diubah lewat endpoint tandai-dibaca (AJAX) saat
    notifikasi dibuka / tombol "Tandai semua dibaca" ditekan — bukan lagi
    list statis di memori proses yang tidak pernah berubah.
    """

    ICON_CHOICES = [
        ("peringatan", "Peringatan"),
        ("laporan", "Laporan"),
        ("lonceng", "Lonceng"),
        ("upload", "Upload"),
        ("jadwal", "Jadwal"),
        ("info", "Info"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifikasi",
        help_text="Pengguna pemilik notifikasi ini (kosong = notifikasi lama sebelum multi-user, ditampilkan ke semua orang untuk kompatibilitas mundur).",
    )
    judul = models.CharField(max_length=150)
    pesan = models.TextField()
    tag = models.CharField(max_length=100, blank=True)
    icon = models.CharField(max_length=16, choices=ICON_CHOICES, default="info")
    dibaca = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Notifikasi"
        verbose_name_plural = "Notifikasi"

    def __str__(self):
        return self.judul


class Akun(models.Model):
    """Profil tambahan tiap pengguna (satu baris per User, lewat OneToOne),
    dipakai di halaman Informasi Akun. Diisi & diubah nyata lewat form
    (Edit Profil, ubah nomor telepon, upload foto) dan tersimpan di
    database — bukan nilai contoh/dummy yang hanya ditampilkan tanpa
    tersimpan.

    Sebelum restrukturisasi multi-user, model ini singleton (satu baris
    untuk seluruh aplikasi). Sekarang setiap User punya baris Akun sendiri,
    dibuat otomatis lewat signal `post_save` di bawah saat User baru
    disimpan, supaya kode lama yang memanggil akun.user tidak perlu
    menangani kasus "belum ada profil" secara manual.
    """

    PERAN_CHOICES = [
        ("admin", "Admin"),
        ("pengguna", "Pengguna"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="akun",
        null=True,
        blank=True,
        help_text="Pemilik profil ini. Kosong hanya untuk baris akun peninggalan sebelum multi-user.",
    )
    foto = models.ImageField(upload_to="akun/", blank=True, null=True)
    nama_lengkap = models.CharField(max_length=150, default="Pengguna Baru")
    email = models.EmailField(blank=True)
    email_terverifikasi = models.BooleanField(default=False)
    telepon = models.CharField(max_length=32, blank=True)
    peran = models.CharField(max_length=16, choices=PERAN_CHOICES, default="pengguna")
    kode_pengguna = models.CharField(max_length=32, unique=True, blank=True)
    aktif = models.BooleanField(default=True, help_text="Nonaktifkan untuk menangguhkan akses tanpa menghapus akun.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Akun"
        verbose_name_plural = "Akun"

    def __str__(self):
        return self.nama_lengkap

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and not self.kode_pengguna:
            self.kode_pengguna = f"USR-{self.created_at:%Y%m%d}-{self.pk:04d}"
            super().save(update_fields=["kode_pengguna"])

    @classmethod
    def get_for_user(cls, user):
        """Ambil (atau buat) profil Akun milik `user` tertentu."""
        obj, _ = cls.objects.get_or_create(
            user=user,
            defaults={
                "nama_lengkap": user.get_full_name() or user.username,
                "email": user.email,
                "peran": "admin" if user.is_staff else "pengguna",
            },
        )
        return obj


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def buat_akun_untuk_user_baru(sender, instance, created, **kwargs):
    """Setiap kali User baru dibuat (lewat register maupun lewat Django
    admin/createsuperuser), otomatis buatkan baris Akun (profil) yang
    terhubung, supaya tidak ada user tanpa profil."""
    if created:
        Akun.get_for_user(instance)


class LogAktivitas(models.Model):
    """Satu baris = satu aktivitas nyata yang tercatat dari panel admin
    (mis. menghapus laporan, menambah/menonaktifkan pengguna), dipakai di
    menu Log Aktivitas. Dicatat lewat helper `catat()` yang dipanggil dari
    view/aksi admin terkait — bukan data contoh statis."""

    aktor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="log_aktivitas",
    )
    aksi = models.CharField(max_length=255)
    detail = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Log Aktivitas"
        verbose_name_plural = "Log Aktivitas"

    def __str__(self):
        return f"{self.aksi} ({self.created_at:%Y-%m-%d %H:%M})"

    @classmethod
    def catat(cls, request, aksi, detail=""):
        aktor = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
        return cls.objects.create(aktor=aktor, aksi=aksi, detail=detail)


class KredensialFingerprint(models.Model):
    """Satu baris = satu 'kunci' fingerprint/biometrik (WebAuthn) yang
    didaftarkan user dari perangkatnya (sensor sidik jari HP/laptop,
    Face ID, Windows Hello, dll — tergantung apa yang tersedia di
    perangkat user, browser yang memilihkan sendiri).

    Yang tersimpan cuma public key hasil registrasi WebAuthn, BUKAN
    data biometrik itu sendiri — data sidik jari asli tidak pernah
    meninggalkan perangkat user. Dipakai sebagai alternatif dari 2FA
    lewat kode email (lihat otp.py & fingerprint.py) saat login.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="kredensial_fingerprint",
    )
    nama_perangkat = models.CharField(
        max_length=100, blank=True,
        help_text="Label bebas biar user bisa bedain kalau daftar dari beberapa perangkat, mis. 'HP Ardi'.",
    )
    credential_id = models.CharField(max_length=255, unique=True)
    public_key = models.TextField(help_text="Public key COSE, disimpan base64.")
    sign_count = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Kredensial Fingerprint"
        verbose_name_plural = "Kredensial Fingerprint"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.nama_perangkat or 'Perangkat'} — {self.user}"
