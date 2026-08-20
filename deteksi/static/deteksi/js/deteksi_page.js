(function () {
  "use strict";

  // ── Referensi elemen ────────────────────────────────────────
  const tabKamera = document.getElementById("tab-kamera");
  const tabUpload = document.getElementById("tab-upload");

  const videoEl = document.getElementById("camera-stream");
  const imgEl = document.getElementById("preview-img");
  const dropzone = document.getElementById("upload-dropzone");
  const cameraPlaceholder = document.getElementById("camera-placeholder");
  const viewfinder = document.getElementById("viewfinder");
  const fileInput = document.getElementById("file-input");
  const captureCanvas = document.getElementById("capture-canvas");
  const loadingOverlay = document.getElementById("loading-overlay");

  const btnAmbil = document.getElementById("btn-ambil");
  const btnAmbilLabel = document.getElementById("btn-ambil-label");
  const btnDeteksiUlang = document.getElementById("btn-deteksi-ulang");
  const btnDownloadPdf = document.getElementById("btn-download-pdf");

  const captureCard = document.getElementById("capture-card");
  const imageResultCard = document.getElementById("image-result-card");
  const detailCard = document.getElementById("detail-card");
  const resultImage = document.getElementById("result-image");
  const resultImageWrapper = document.getElementById("result-image-wrapper");

  const detailFilename = document.getElementById("detail-filename");
  const detailSize = document.getElementById("detail-size");
  const detailTime = document.getElementById("detail-time");
  const pageSubtitle = document.getElementById("page-subtitle");

  const resultEmpty = document.getElementById("result-empty");
  const resultContent = document.getElementById("result-content");
  const resultError = document.getElementById("result-error");
  const resultErrorMsg = document.getElementById("result-error-msg");

  const resultBanner = document.getElementById("result-banner");
  const resultIcon = document.getElementById("result-icon");
  const resultLabel = document.getElementById("result-label");
  const resultDesc = document.getElementById("result-desc");
  const resultBreakdown = document.getElementById("result-breakdown");
  const resultRekomendasi = document.getElementById("result-rekomendasi");

  // ── State ───────────────────────────────────────────────────
  let activeTab = "kamera";
  let stream = null;
  let selectedFile = null;
  let capturedBlob = null;
  let currentLaporanUrl = null;

  const COLOR_MAP = {
    green: { bg: "bg-emerald-50", text: "text-emerald-700", bar: "bg-emerald-500", icon: "text-emerald-600 bg-emerald-100", chip: "bg-emerald-100 text-emerald-700" },
    amber: { bg: "bg-amber-50", text: "text-amber-700", bar: "bg-amber-500", icon: "text-amber-600 bg-amber-100", chip: "bg-amber-100 text-amber-700" },
    red:   { bg: "bg-red-50", text: "text-red-700", bar: "bg-red-500", icon: "text-red-600 bg-red-100", chip: "bg-red-100 text-red-700" },
    gray:  { bg: "bg-slate-50", text: "text-slate-700", bar: "bg-slate-400", icon: "text-slate-600 bg-slate-100", chip: "bg-slate-100 text-slate-600" },
  };

  const BANNER_ICONS = {
    green: '<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>',
    amber: '<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v4m0 4h.01M10.3 3.9 1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z"/></svg>',
    red:   '<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path stroke-linecap="round" d="M9 9l6 6M15 9l-6 6"/></svg>',
  };

  // Ikon baris per kelas teknis (Normal / Retak / Robek)
  const ROW_ICONS = {
    "Normal": '<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/></svg>',
    "Retak": '<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M12 3 9 9l3 2-2 4 4-1-1 7 5-9-4-1 3-4-3-1z"/></svg>',
    "Robek": '<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M4 8l6 6M10 8l-6 6M14 6l6 12M20 6l-6 12"/></svg>',
  };

  // ── Helper UI ───────────────────────────────────────────────
  function hide(el) { el.classList.add("hidden"); el.classList.remove("flex"); }
  function show(el, display) { el.classList.remove("hidden"); if (display) el.classList.add(display); }

  function setTabStyle() {
    [tabKamera, tabUpload].forEach((btn) => {
      btn.classList.remove("border-blue-600", "bg-blue-50", "text-blue-600",
                            "border-slate-200", "bg-white", "text-slate-500");
    });
    const activeBtn = activeTab === "kamera" ? tabKamera : tabUpload;
    const inactiveBtn = activeTab === "kamera" ? tabUpload : tabKamera;
    activeBtn.classList.add("border-blue-600", "bg-blue-50", "text-blue-600");
    inactiveBtn.classList.add("border-slate-200", "bg-white", "text-slate-500");
  }

  function stopCamera() {
    if (stream) {
      stream.getTracks().forEach((t) => t.stop());
      stream = null;
    }
  }

  function resetPreviewArea() {
    hide(videoEl); hide(imgEl); hide(dropzone); hide(cameraPlaceholder); hide(viewfinder);
    imgEl.src = "";
  }

  async function startCamera() {
    resetPreviewArea();
    show(cameraPlaceholder, "flex");
    btnAmbil.disabled = true;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
        audio: false,
      });
      videoEl.srcObject = stream;
      hide(cameraPlaceholder);
      show(videoEl);
      show(viewfinder);
      btnAmbilLabel.textContent = (window.I18N && window.I18N.ambilFoto) || "Ambil Foto";
      btnAmbil.disabled = false;
    } catch (err) {
      cameraPlaceholder.innerHTML =
        '<svg class="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">' +
        '<path stroke-linecap="round" stroke-linejoin="round" d="M4 8a2 2 0 012-2h1.5l1-1.5h7l1 1.5H18a2 2 0 012 2v9a2 2 0 01-2 2H6a2 2 0 01-2-2V8z"/>' +
        '<circle cx="12" cy="12.5" r="3.2" stroke-linecap="round"/></svg>' +
        '<p class="text-sm text-center px-4">' + ((window.I18N && window.I18N.kameraTidakTersedia) || 'Kamera tidak tersedia. Izinkan akses kamera atau gunakan tab Upload.') + '</p>';
      show(cameraPlaceholder, "flex");
      btnAmbil.disabled = true;
    }
  }

  function showUploadUI() {
    resetPreviewArea();
    stopCamera();
    show(dropzone, "flex");
    btnAmbilLabel.textContent = (window.I18N && window.I18N.pilihGambarDulu) || "Pilih Gambar Dulu";
    btnAmbil.disabled = true;
  }

  function activateTab(tab) {
    activeTab = tab;
    setTabStyle();
    if (tab === "kamera") startCamera();
    else showUploadUI();
  }

  tabKamera.addEventListener("click", () => activateTab("kamera"));
  tabUpload.addEventListener("click", () => activateTab("upload"));

  dropzone.addEventListener("click", () => fileInput.click());
  dropzone.addEventListener("dragover", (e) => { e.preventDefault(); dropzone.classList.add("border-blue-400"); });
  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("border-blue-400"));
  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("border-blue-400");
    if (e.dataTransfer.files && e.dataTransfer.files[0]) handleFileSelected(e.dataTransfer.files[0]);
  });
  fileInput.addEventListener("change", () => {
    if (fileInput.files && fileInput.files[0]) handleFileSelected(fileInput.files[0]);
  });

  function handleFileSelected(file) {
    if (!file.type.match(/image\/(png|jpeg|jpg)/)) {
      alert((window.I18N && window.I18N.formatTidakDidukung) || "Format tidak didukung. Gunakan JPG atau PNG.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      alert((window.I18N && window.I18N.ukuranMaks) || "Ukuran file maksimal 10MB.");
      return;
    }
    selectedFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      imgEl.src = e.target.result;
      hide(dropzone);
      show(imgEl);
      btnAmbilLabel.textContent = (window.I18N && window.I18N.analisisFoto) || "Analisis Foto";
      btnAmbil.disabled = false;
    };
    reader.readAsDataURL(file);
  }

  btnAmbil.addEventListener("click", () => {
    if (activeTab === "kamera") {
      if (!stream) return;
      captureCanvas.width = videoEl.videoWidth;
      captureCanvas.height = videoEl.videoHeight;
      const ctx = captureCanvas.getContext("2d");
      ctx.drawImage(videoEl, 0, 0, captureCanvas.width, captureCanvas.height);
      captureCanvas.toBlob((blob) => {
        capturedBlob = blob;
        const dataUrl = captureCanvas.toDataURL("image/jpeg", 0.92);
        stopCamera();
        analyzeImage(capturedBlob, dataUrl);
      }, "image/jpeg", 0.92);
    } else if (selectedFile) {
      const dataUrl = imgEl.src;
      analyzeImage(selectedFile, dataUrl);
    }
  });

  btnDeteksiUlang.addEventListener("click", () => {
    selectedFile = null;
    capturedBlob = null;
    currentLaporanUrl = null;
    btnDownloadPdf.disabled = true;
    fileInput.value = "";
    hide(imageResultCard);
    hide(detailCard);
    hide(resultContent); hide(resultError);
    show(resultEmpty, "flex");
    show(captureCard, "block");
    pageSubtitle.textContent = (window.I18N && window.I18N.subtitleAwal) || "Unggah atau ambil foto ban untuk memulai deteksi";
    activateTab(activeTab);
  });

  btnDownloadPdf.addEventListener("click", () => {
    if (currentLaporanUrl) {
      window.open(currentLaporanUrl, "_blank");
    }
  });

  // ── Panggil API prediksi ─────────────────────────────────────
  function analyzeImage(fileOrBlob, previewDataUrl) {
    show(loadingOverlay, "flex");
    btnAmbil.disabled = true;

    const formData = new FormData();
    formData.append("image", fileOrBlob, "ban.jpg");

    fetch(window.PREDICT_URL, { method: "POST", body: formData })
      .then((res) => res.json().then((data) => ({ ok: res.ok, data })))
      .then(({ data }) => {
        if (data.login_required) {
          window.location.href = data.login_url || window.LOGIN_URL || "/login/";
          return;
        }
        hide(loadingOverlay);
        if (data.success) {
          resultImage.src = previewDataUrl;
          renderResult(data);
        } else {
          hide(captureCard);
          show(imageResultCard, "block");
          resultImage.src = previewDataUrl;
          renderError(data.error || (window.I18N && window.I18N.errorUmum) || "Terjadi kesalahan saat menganalisis gambar.");
        }
      })
      .catch(() => {
        hide(loadingOverlay);
        renderError((window.I18N && window.I18N.errorKoneksi) || "Gagal terhubung ke server. Periksa koneksi Anda dan coba lagi.");
      });
  }

  function renderError(msg) {
    hide(resultEmpty); hide(resultContent);
    currentLaporanUrl = null;
    btnDownloadPdf.disabled = true;
    resultErrorMsg.textContent = msg;
    show(resultError, "flex");
    btnAmbil.disabled = false;
  }

  function renderResult(data) {
    hide(captureCard);
    show(imageResultCard, "block");
    show(detailCard, "block");
    hide(resultEmpty); hide(resultError);
    show(resultContent, "block");

    currentLaporanUrl = data.laporan_url || null;
    btnDownloadPdf.disabled = !currentLaporanUrl;

    // Border gambar ikut warna status
    const c = COLOR_MAP[data.color] || COLOR_MAP.gray;
    resultImageWrapper.className = "rounded-xl overflow-hidden border-4 " +
      (data.color === "green" ? "border-emerald-200" : data.color === "amber" ? "border-amber-200" : data.color === "red" ? "border-red-200" : "border-slate-100");

    // Detail deteksi
    detailFilename.textContent = data.filename || "-";
    detailSize.textContent = (data.width && data.height) ? (data.width + " x " + data.height + " px") : "-";
    const now = new Date();
    const locale = (window.I18N && window.I18N.bahasaAktif === "en") ? "en-US" : "id-ID";
    const waktu = now.toLocaleDateString(locale, { day: "2-digit", month: "long", year: "numeric" }) +
      ", " + now.toLocaleTimeString(locale, { hour: "2-digit", minute: "2-digit" }) + (locale === "id-ID" ? " WIB" : "");
    detailTime.textContent = waktu;
    pageSubtitle.textContent = ((window.I18N && window.I18N.deteksiSelesaiPada) || "Deteksi selesai pada") + " " + waktu;

    // Banner
    resultBanner.className = "rounded-xl px-4 py-4 flex items-center gap-3 mb-5 " + c.bg + " " + c.text;
    resultIcon.className = "w-11 h-11 rounded-full flex items-center justify-center flex-shrink-0 " + c.icon;
    resultIcon.innerHTML = BANNER_ICONS[data.color] || BANNER_ICONS.amber;
    resultLabel.textContent = data.label;
    resultLabel.className = "text-xl font-bold " + c.text;
    resultDesc.textContent = data.desc || "";

    // Breakdown probabilitas per kelas
    resultBreakdown.innerHTML = "";
    (data.breakdown || []).forEach((item) => {
      const bc = COLOR_MAP[item.color] || COLOR_MAP.gray;
      const row = document.createElement("div");
      row.className = "flex items-center gap-3";
      row.innerHTML =
        '<div class="w-11 h-11 rounded-xl bg-slate-800 text-white flex items-center justify-center flex-shrink-0">' +
          (ROW_ICONS[item.kelas] || ROW_ICONS["Normal"]) +
        '</div>' +
        '<div class="flex-1 min-w-0">' +
          '<p class="text-sm font-semibold text-slate-700">' + item.kelas + '</p>' +
          '<p class="text-xs text-slate-400">' + ((window.I18N && window.I18N.probabilitasKelasIni) || 'Probabilitas kelas ini') + '</p>' +
        '</div>' +
        '<div class="text-right flex-shrink-0">' +
          '<p class="font-bold ' + bc.text + '">' + item.value + '%</p>' +
          '<span class="inline-block text-[10px] font-semibold px-2 py-0.5 rounded-full ' + bc.chip + '">' + item.label + '</span>' +
        '</div>';
      resultBreakdown.appendChild(row);
    });

    resultRekomendasi.textContent = data.rekomendasi || "-";
  }

  // ── Init ────────────────────────────────────────────────────
  setTabStyle();
  activateTab("kamera");
})();
