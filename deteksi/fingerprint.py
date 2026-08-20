"""Login pakai fingerprint/biometrik lewat standar WebAuthn — alternatif
dari kode OTP email untuk langkah kedua (2FA).

Cara kerja singkatnya:
- User daftarkan fingerprint dari perangkatnya (browser yang manggil
  sensor biometrik asli lewat `navigator.credentials.create`). Yang
  dikirim balik ke server cuma hasil kriptografi (public key), BUKAN
  data sidik jari itu sendiri — data biometrik asli tidak pernah
  meninggalkan perangkat user.
- Server simpan public key itu (lihat model KredensialFingerprint).
- Saat login & butuh 2FA, kalau user punya kredensial fingerprint
  terdaftar, dia bisa pilih verifikasi pakai fingerprint (lewat
  `navigator.credentials.get`) sebagai ganti kode OTP email.

Semua fungsi di sini membungkus library `webauthn` (py_webauthn) supaya
views.py tidak perlu tahu detail WebAuthn-nya.
"""

import base64

from django.conf import settings

import webauthn
from webauthn.helpers.structs import (
    AttestationConveyancePreference,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from .models import KredensialFingerprint

SESSION_KEY_REGISTRASI = "fingerprint_registrasi_challenge"
SESSION_KEY_LOGIN = "fingerprint_login_challenge"


def _rp_id():
    return getattr(settings, "WEBAUTHN_RP_ID", "localhost")


def _rp_name():
    return getattr(settings, "WEBAUTHN_RP_NAME", "Deteksi Ban")


def _origin():
    return getattr(settings, "WEBAUTHN_ORIGIN", "http://localhost:8000")


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _unb64(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))


def punya_fingerprint(user):
    """True kalau user sudah daftarkan minimal satu fingerprint/perangkat."""
    return KredensialFingerprint.objects.filter(user=user).exists()


# ------------------------------------------------------------------
# REGISTRASI (mendaftarkan fingerprint baru dari perangkat user)
# ------------------------------------------------------------------

def buat_opsi_registrasi(request, user):
    """Langkah 1 registrasi: buat 'tantangan' (challenge) WebAuthn dan
    kembalikan opsinya sebagai dict siap dikirim ke browser (JSON)."""
    kredensial_lama = [
        PublicKeyCredentialDescriptor(id=_unb64(k.credential_id))
        for k in KredensialFingerprint.objects.filter(user=user)
    ]

    opsi = webauthn.generate_registration_options(
        rp_id=_rp_id(),
        rp_name=_rp_name(),
        user_id=str(user.pk).encode("utf-8"),
        user_name=user.username,
        user_display_name=user.get_full_name() or user.username,
        attestation=AttestationConveyancePreference.NONE,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
        exclude_credentials=kredensial_lama,
    )

    request.session[SESSION_KEY_REGISTRASI] = _b64(opsi.challenge)
    return webauthn.options_to_json(opsi)


def verifikasi_dan_simpan_registrasi(request, user, credential_json, nama_perangkat=""):
    """Langkah 2 registrasi: verifikasi jawaban dari browser, lalu simpan
    kredensial baru. Return (True, "") kalau sukses, (False, pesan_error)
    kalau gagal."""
    challenge_b64 = request.session.pop(SESSION_KEY_REGISTRASI, None)
    if not challenge_b64:
        return False, "Sesi registrasi fingerprint sudah kedaluwarsa. Silakan coba lagi."

    try:
        hasil = webauthn.verify_registration_response(
            credential=credential_json,
            expected_challenge=_unb64(challenge_b64),
            expected_rp_id=_rp_id(),
            expected_origin=_origin(),
        )
    except Exception as e:  # noqa: BLE001 — semua error verifikasi diperlakukan sama
        return False, f"Verifikasi fingerprint gagal: {e}"

    KredensialFingerprint.objects.create(
        user=user,
        nama_perangkat=nama_perangkat or "Perangkat",
        credential_id=_b64(hasil.credential_id),
        public_key=_b64(hasil.credential_public_key),
        sign_count=hasil.sign_count,
    )
    return True, ""


# ------------------------------------------------------------------
# LOGIN (verifikasi fingerprint sebagai pengganti kode OTP email)
# ------------------------------------------------------------------

def buat_opsi_login(request, user):
    """Langkah 1 login: buat challenge WebAuthn untuk kredensial yang
    sudah terdaftar milik user ini."""
    kredensial_milik_user = [
        PublicKeyCredentialDescriptor(id=_unb64(k.credential_id))
        for k in KredensialFingerprint.objects.filter(user=user)
    ]

    opsi = webauthn.generate_authentication_options(
        rp_id=_rp_id(),
        allow_credentials=kredensial_milik_user,
        user_verification=UserVerificationRequirement.REQUIRED,
    )

    request.session[SESSION_KEY_LOGIN] = _b64(opsi.challenge)
    return webauthn.options_to_json(opsi)


def verifikasi_login(request, user, credential_json):
    """Langkah 2 login: cek jawaban fingerprint dari browser terhadap
    kredensial yang tersimpan. Return (True, "") kalau cocok & sah,
    (False, pesan_error) kalau tidak."""
    challenge_b64 = request.session.pop(SESSION_KEY_LOGIN, None)
    if not challenge_b64:
        return False, "Sesi verifikasi fingerprint sudah kedaluwarsa. Silakan coba lagi."

    credential_id_dipakai = credential_json.get("id") if isinstance(credential_json, dict) else None
    kredensial = KredensialFingerprint.objects.filter(user=user).first()
    if credential_id_dipakai:
        for k in KredensialFingerprint.objects.filter(user=user):
            if k.credential_id.rstrip("=") == credential_id_dipakai or _b64_urlsafe_match(k.credential_id, credential_id_dipakai):
                kredensial = k
                break

    if kredensial is None:
        return False, "Fingerprint ini tidak terdaftar untuk akun ini."

    try:
        hasil = webauthn.verify_authentication_response(
            credential=credential_json,
            expected_challenge=_unb64(challenge_b64),
            expected_rp_id=_rp_id(),
            expected_origin=_origin(),
            credential_public_key=_unb64(kredensial.public_key),
            credential_current_sign_count=kredensial.sign_count,
        )
    except Exception as e:  # noqa: BLE001
        return False, f"Verifikasi fingerprint gagal: {e}"

    kredensial.sign_count = hasil.new_sign_count
    from django.utils import timezone
    kredensial.last_used_at = timezone.now()
    kredensial.save(update_fields=["sign_count", "last_used_at"])
    return True, ""


def _b64_urlsafe_match(stored_b64: str, incoming_b64url: str) -> bool:
    """credential_id yang balik dari browser formatnya base64url (tanpa
    padding), sedangkan yang kita simpan base64 standar — normalisasi
    dulu sebelum dibandingkan."""
    try:
        return _unb64(stored_b64) == webauthn.base64url_to_bytes(incoming_b64url)
    except Exception:  # noqa: BLE001
        return False
