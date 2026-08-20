/* Helper WebAuthn (login/registrasi fingerprint) — dipakai bareng oleh
 * halaman "Daftarkan Fingerprint" dan "Verifikasi 2FA".
 *
 * Browser cuma ngerti ArrayBuffer buat challenge/id, sedangkan server
 * kirim/terima semuanya sebagai base64url. Dua fungsi di bawah ini
 * yang jembatanin itu.
 */

function b64urlKeBuffer(base64url) {
  const base64 = base64url.replace(/-/g, "+").replace(/_/g, "/");
  const pad = base64.length % 4 === 0 ? "" : "=".repeat(4 - (base64.length % 4));
  const raw = atob(base64 + pad);
  const buffer = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) buffer[i] = raw.charCodeAt(i);
  return buffer.buffer;
}

function bufferKeB64url(buffer) {
  const bytes = new Uint8Array(buffer);
  let str = "";
  for (let i = 0; i < bytes.byteLength; i++) str += String.fromCharCode(bytes[i]);
  return btoa(str).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function ambilCsrfToken() {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : "";
}

async function fingerprintTersedia() {
  return !!(window.PublicKeyCredential);
}

/** Daftarkan fingerprint baru dari perangkat ini. Return {ok, error?} */
async function daftarkanFingerprint(urlOpsi, urlVerifikasi, namaPerangkat) {
  const resOpsi = await fetch(urlOpsi, {
    method: "POST",
    headers: { "X-CSRFToken": ambilCsrfToken() },
  });
  const opsi = await resOpsi.json();
  if (!resOpsi.ok) return { ok: false, error: opsi.error || "Gagal memuat opsi registrasi." };

  opsi.challenge = b64urlKeBuffer(opsi.challenge);
  opsi.user.id = b64urlKeBuffer(opsi.user.id);
  if (opsi.excludeCredentials) {
    opsi.excludeCredentials = opsi.excludeCredentials.map((c) => ({
      ...c,
      id: b64urlKeBuffer(c.id),
    }));
  }

  let credential;
  try {
    credential = await navigator.credentials.create({ publicKey: opsi });
  } catch (e) {
    return { ok: false, error: "Registrasi fingerprint dibatalkan atau gagal: " + e.message };
  }

  const payload = {
    id: credential.id,
    rawId: bufferKeB64url(credential.rawId),
    type: credential.type,
    response: {
      clientDataJSON: bufferKeB64url(credential.response.clientDataJSON),
      attestationObject: bufferKeB64url(credential.response.attestationObject),
    },
    nama_perangkat: namaPerangkat || "",
  };

  const resVerif = await fetch(urlVerifikasi, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": ambilCsrfToken() },
    body: JSON.stringify(payload),
  });
  const hasil = await resVerif.json();
  return hasil;
}

/** Login/verifikasi 2FA pakai fingerprint yang sudah terdaftar.
 * Return {ok, redirect?, error?} */
async function loginPakaiFingerprint(urlOpsi, urlVerifikasi) {
  const resOpsi = await fetch(urlOpsi, {
    method: "POST",
    headers: { "X-CSRFToken": ambilCsrfToken() },
  });
  const opsi = await resOpsi.json();
  if (!resOpsi.ok) return { ok: false, error: opsi.error || "Fingerprint tidak tersedia." };

  opsi.challenge = b64urlKeBuffer(opsi.challenge);
  if (opsi.allowCredentials) {
    opsi.allowCredentials = opsi.allowCredentials.map((c) => ({
      ...c,
      id: b64urlKeBuffer(c.id),
    }));
  }

  let credential;
  try {
    credential = await navigator.credentials.get({ publicKey: opsi });
  } catch (e) {
    return { ok: false, error: "Verifikasi fingerprint dibatalkan atau gagal: " + e.message };
  }

  const payload = {
    id: credential.id,
    rawId: bufferKeB64url(credential.rawId),
    type: credential.type,
    response: {
      clientDataJSON: bufferKeB64url(credential.response.clientDataJSON),
      authenticatorData: bufferKeB64url(credential.response.authenticatorData),
      signature: bufferKeB64url(credential.response.signature),
      userHandle: credential.response.userHandle ? bufferKeB64url(credential.response.userHandle) : null,
    },
  };

  const resVerif = await fetch(urlVerifikasi, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": ambilCsrfToken() },
    body: JSON.stringify(payload),
  });
  return await resVerif.json();
}
