from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin

from .models import Akun, LogAktivitas, Notifikasi, Pengaturan, Riwayat

User = get_user_model()


# ============================================================
# Kelola Pengguna — pakai User bawaan Django, dengan profil Akun
# (peran, telepon, foto, status aktif) ditempel sebagai inline.
# ============================================================

class AkunInline(admin.StackedInline):
    model = Akun
    can_delete = False
    fk_name = "user"
    extra = 0
    fields = ("foto", "peran", "telepon", "aktif", "kode_pengguna", "email_terverifikasi")
    readonly_fields = ("kode_pengguna",)
    verbose_name_plural = "Profil Akun"


admin.site.unregister(User)


@admin.register(User)
class UserAdmin(DefaultUserAdmin):
    inlines = (AkunInline,)
    list_display = (
        "username", "email", "first_name", "last_name",
        "peran_display", "status_aktif_display", "is_staff", "date_joined",
    )
    list_filter = DefaultUserAdmin.list_filter + ("akun__peran", "akun__aktif")

    @admin.display(description="Peran")
    def peran_display(self, obj):
        akun = getattr(obj, "akun", None)
        return akun.get_peran_display() if akun else "-"

    @admin.display(description="Status", boolean=True)
    def status_aktif_display(self, obj):
        akun = getattr(obj, "akun", None)
        return akun.aktif if akun else True

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        aksi = "Mengubah pengguna" if change else "Menambah pengguna"
        LogAktivitas.catat(request, aksi, detail=f"Username: {obj.username}")

    def delete_model(self, request, obj):
        username = obj.username
        super().delete_model(request, obj)
        LogAktivitas.catat(request, "Menghapus pengguna", detail=f"Username: {username}")

    def delete_queryset(self, request, queryset):
        usernames = ", ".join(queryset.values_list("username", flat=True))
        count = queryset.count()
        super().delete_queryset(request, queryset)
        LogAktivitas.catat(request, "Menghapus pengguna (massal)", detail=f"{count} akun: {usernames}")


# ============================================================
# Kelola Deteksi / Laporan
# ============================================================

@admin.register(Riwayat)
class RiwayatAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at", "label", "kelas", "confidence", "processing_ms")
    list_filter = ("label", "kelas", "created_at")
    search_fields = ("user__username", "user__email", "kelas", "code_label")
    readonly_fields = (
        "created_at", "code_label", "kelas", "label", "color", "confidence",
        "desc", "rekomendasi", "breakdown", "original_filename", "width",
        "height", "processing_ms", "user_agent",
    )
    ordering = ("-created_at",)

    def delete_model(self, request, obj):
        pk = obj.pk
        super().delete_model(request, obj)
        LogAktivitas.catat(request, "Menghapus laporan deteksi", detail=f"Riwayat #{pk}")

    def delete_queryset(self, request, queryset):
        count = queryset.count()
        super().delete_queryset(request, queryset)
        LogAktivitas.catat(request, "Menghapus laporan deteksi (massal)", detail=f"{count} baris riwayat")


# ============================================================
# Pengaturan Sistem (singleton) & Notifikasi
# ============================================================

@admin.register(Pengaturan)
class PengaturanAdmin(admin.ModelAdmin):
    list_display = ("__str__", "tema", "zona_waktu", "format_tanggal", "updated_at")
    readonly_fields = ("updated_at",)

    def has_add_permission(self, request):
        # Singleton — cukup satu baris pengaturan untuk seluruh aplikasi.
        return not Pengaturan.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        LogAktivitas.catat(request, "Mengubah pengaturan sistem")


@admin.register(Notifikasi)
class NotifikasiAdmin(admin.ModelAdmin):
    list_display = ("judul", "user", "icon", "dibaca", "created_at")
    list_filter = ("icon", "dibaca")
    ordering = ("-created_at",)


# ============================================================
# Log Aktivitas — hanya-baca, otomatis terisi dari aksi admin lain
# ============================================================

@admin.register(LogAktivitas)
class LogAktivitasAdmin(admin.ModelAdmin):
    list_display = ("created_at", "aktor", "aksi", "detail")
    list_filter = ("aksi",)
    ordering = ("-created_at",)
    readonly_fields = ("aktor", "aksi", "detail", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
