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
  const btnGanti = document.getElementById("btn-ganti");

  const resultEmpty = document.getElementById("result-empty");
  const resultContent = document.getElementById("result-content");
  const resultError = document.getElementById("result-error");
  const resultErrorMsg = document.getElementById("result-error-msg");

  const resultBanner = document.getElementById("result-banner");
  const resultIcon = document.getElementById("result-icon");
  const resultLabel = document.getElementById("result-label");
  const resultDesc = document.getElementById("result-desc");
  const resultConfidence = document.getElementById("result-confidence");
  const resultConfidenceBar = document.getElementById("result-confidence-bar");
  const resultBreakdown = document.getElementById("result-breakdown");
  const resultRekomendasi = document.getElementById("result-rekomendasi");
  const resultTime = document.getElementById("result-time");

  // ── State ───────────────────────────────────────────────────
  let activeTab = "kamera";
  let stream = null;
  let selectedFile = null;   // File dari input upload
  let capturedBlob = null;   // Blob hasil ambil foto kamera
  let analyzed = false;

  const COLOR_MAP = {
    green: { bg: "bg-emerald-50", text: "text-emerald-700", bar: "bg-emerald-500", icon: "text-emerald-600 bg-emerald-100" },
    amber: { bg: "bg-amber-50", text: "text-amber-700", bar: "bg-amber-500", icon: "text-amber-600 bg-amber-100" },
    red:   { bg: "bg-red-50", text: "text-red-700", bar: "bg-red-500", icon: "text-red-600 bg-red-100" },
    gray:  { bg: "bg-slate-50", text: "text-slate-700", bar: "bg-slate-400", icon: "text-slate-600 bg-slate-100" },
  };

  const ICONS = {
    green: '<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>',
    amber: '<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v4m0 4h.01M10.3 3.9 1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z"/></svg>',
    red:   '<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path stroke-linecap="round" d="M9 9l6 6M15 9l-6 6"/></svg>',
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
      btnAmbilLabel.textContent = "Ambil Foto";
      btnAmbil.disabled = false;
    } catch (err) {
      cameraPlaceholder.innerHTML =
        '<svg class="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">' +
        '<path stroke-linecap="round" stroke-linejoin="round" d="M4 8a2 2 0 012-2h1.5l1-1.5h7l1 1.5H18a2 2 0 012 2v9a2 2 0 01-2 2H6a2 2 0 01-2-2V8z"/>' +
        '<circle cx="12" cy="12.5" r="3.2" stroke-linecap="round"/></svg>' +
        '<p class="text-sm text-center px-4">Kamera tidak tersedia. Izinkan akses kamera atau gunakan tab Upload.</p>';
      show(cameraPlaceholder, "flex");
      btnAmbil.disabled = true;
    }
  }

  function showUploadUI() {
    resetPreviewArea();
    stopCamera();
    show(dropzone, "flex");
    btnAmbilLabel.textContent = "Pilih Gambar Dulu";
    btnAmbil.disabled = true;
  }

  function activateTab(tab) {
    activeTab = tab;
    setTabStyle();
    if (tab === "kamera") {
      startCamera();
    } else {
      showUploadUI();
    }
  }

  // ── Tab switching ───────────────────────────────────────────
  tabKamera.addEventListener("click", () => { if (!analyzed) activateTab("kamera"); });
  tabUpload.addEventListener("click", () => { if (!analyzed) activateTab("upload"); });

  // ── Upload dropzone ─────────────────────────────────────────
  dropzone.addEventListener("click", () => fileInput.click());
  dropzone.addEventListener("dragover", (e) => { e.preventDefault(); dropzone.classList.add("border-blue-400"); });
  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("border-blue-400"));
  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("border-blue-400");
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });
  fileInput.addEventListener("change", () => {
    if (fileInput.files && fileInput.files[0]) handleFileSelected(fileInput.files[0]);
  });

  function handleFileSelected(file) {
    if (!file.type.match(/image\/(png|jpeg|jpg)/)) {
      alert("Format tidak didukung. Gunakan JPG atau PNG.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      alert("Ukuran file maksimal 10MB.");
      return;
    }
    selectedFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      imgEl.src = e.target.result;
      hide(dropzone);
      show(imgEl);
      btnAmbilLabel.textContent = "Analisis Foto";
      btnAmbil.disabled = false;
    };
    reader.readAsDataURL(file);
  }

  // ── Tombol Ambil Foto / Analisis ────────────────────────────
  btnAmbil.addEventListener("click", () => {
    if (analyzed) return;

    if (activeTab === "kamera") {
      if (!stream) return;
      captureCanvas.width = videoEl.videoWidth;
      captureCanvas.height = videoEl.videoHeight;
      const ctx = captureCanvas.getContext("2d");
      ctx.drawImage(videoEl, 0, 0, captureCanvas.width, captureCanvas.height);
      captureCanvas.toBlob((blob) => {
        capturedBlob = blob;
        imgEl.src = captureCanvas.toDataURL("image/jpeg", 0.92);
        hide(videoEl); hide(viewfinder);
        show(imgEl);
        stopCamera();
        analyzeImage(capturedBlob);
      }, "image/jpeg", 0.92);
    } else {
      if (selectedFile) analyzeImage(selectedFile);
    }
  });

  // ── Tombol Ganti Foto ────────────────────────────────────────
  btnGanti.addEventListener("click", () => {
    analyzed = false;
    selectedFile = null;
    capturedBlob = null;
    fileInput.value = "";
    btnGanti.disabled = true;
    tabKamera.disabled = false;
    tabUpload.disabled = false;
    hide(resultContent); hide(resultError);
    show(resultEmpty, "flex");
    activateTab(activeTab);
  });

  // ── Panggil API prediksi ─────────────────────────────────────
  function analyzeImage(fileOrBlob) {
    show(loadingOverlay, "flex");
    btnAmbil.disabled = true;
    tabKamera.disabled = true;
    tabUpload.disabled = true;

    const formData = new FormData();
    formData.append("image", fileOrBlob, "ban.jpg");

    fetch(window.PREDICT_URL, { method: "POST", body: formData })
      .then((res) => res.json().then((data) => ({ ok: res.ok, data })))
      .then(({ data }) => {
        hide(loadingOverlay);
        analyzed = true;
        btnGanti.disabled = false;
        if (data.success) {
          renderResult(data);
        } else {
          renderError(data.error || "Terjadi kesalahan saat menganalisis gambar.");
        }
      })
      .catch(() => {
        hide(loadingOverlay);
        analyzed = true;
        btnGanti.disabled = false;
        renderError("Gagal terhubung ke server. Periksa koneksi Anda dan coba lagi.");
      });
  }

  function renderError(msg) {
    hide(resultEmpty); hide(resultContent);
    resultErrorMsg.textContent = msg;
    show(resultError, "flex");
  }

  function renderResult(data) {
    hide(resultEmpty); hide(resultError);
    show(resultContent, "block");

    const c = COLOR_MAP[data.color] || COLOR_MAP.gray;

    resultBanner.className = "rounded-xl px-4 py-4 flex items-center gap-3 mb-5 " + c.bg + " " + c.text;
    resultIcon.className = "w-11 h-11 rounded-full flex items-center justify-center flex-shrink-0 " + c.icon;
    resultIcon.innerHTML = ICONS[data.color] || ICONS.amber;
    resultLabel.textContent = data.label;
    resultLabel.className = "text-xl font-bold " + c.text;
    resultDesc.textContent = data.desc || "";

    resultConfidence.textContent = data.confidence + "%";
    resultConfidenceBar.style.width = data.confidence + "%";

    resultBreakdown.innerHTML = "";
    (data.breakdown || []).forEach((item) => {
      const bc = COLOR_MAP[item.color] || COLOR_MAP.gray;
      const row = document.createElement("div");
      row.innerHTML =
        '<div class="flex items-center justify-between text-xs mb-1">' +
          '<span class="text-slate-500">' + item.kelas + '</span>' +
          '<span class="font-semibold text-slate-700">' + item.value + '%</span>' +
        '</div>' +
        '<div class="w-full h-1.5 rounded-full bg-slate-100 overflow-hidden">' +
          '<div class="h-full rounded-full ' + bc.bar + '" style="width:' + item.value + '%"></div>' +
        '</div>';
      row.className = "mb-2";
      resultBreakdown.appendChild(row);
    });

    resultRekomendasi.textContent = data.rekomendasi || "-";

    const now = new Date();
    resultTime.textContent = now.toLocaleDateString("id-ID", {
      day: "2-digit", month: "long", year: "numeric",
    }) + ", " + now.toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" }) + " WIB";
  }

  // ── Init ────────────────────────────────────────────────────
  setTabStyle();
  activateTab("kamera");
})();
