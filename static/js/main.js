/* main.js
 * Handles the Room Analysis page and the Design Studio page:
 *  - camera access via MediaDevices API (getUserMedia)
 *  - photo capture -> canvas -> blob -> upload
 *  - calling the Flask JSON APIs
 *  - rendering results into the DOM
 *  - simple client-side "session handoff" between analyze -> design via
 *    sessionStorage, since there is no server-side wizard state.
 */

let selectedImageBlob = null;
let selectedImageUrl = null;
let cameraStream = null;
let lastAnalysis = null;
let lastImagePath = null;
let lastDesignResult = null;
let currentDesignId = null;

/* ============================== Analyze Page ============================== */
function initAnalyzePage() {
    const fileInput = document.getElementById("image-input");
    const chooseBtn = document.getElementById("choose-file-btn");
    const useCameraBtn = document.getElementById("use-camera-btn");
    const cancelCameraBtn = document.getElementById("cancel-camera-btn");
    const captureBtn = document.getElementById("capture-btn");
    const changeImageBtn = document.getElementById("change-image-btn");
    const analyzeBtn = document.getElementById("analyze-btn");
    const proceedBtn = document.getElementById("proceed-btn");

    const placeholder = document.getElementById("upload-placeholder");
    const previewWrap = document.getElementById("preview-wrap");
    const previewImg = document.getElementById("preview-img");
    const video = document.getElementById("camera-feed");
    const cameraControls = document.getElementById("camera-controls");

    chooseBtn.addEventListener("click", () => fileInput.click());

    fileInput.addEventListener("change", () => {
        if (fileInput.files && fileInput.files[0]) {
            setSelectedImage(fileInput.files[0]);
        }
    });

    useCameraBtn.addEventListener("click", async () => {
        try {
            cameraStream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: { ideal: "environment" }, width: { ideal: 1280 } },
                audio: false,
            });
            video.srcObject = cameraStream;
            placeholder.classList.add("hidden");
            previewWrap.classList.add("hidden");
            video.classList.remove("hidden");
            cameraControls.classList.remove("hidden");
        } catch (err) {
            alert("Could not access camera: " + err.message + "\nPlease allow camera permissions or choose a photo instead.");
        }
    });

    cancelCameraBtn.addEventListener("click", stopCamera);

    captureBtn.addEventListener("click", () => {
        const canvas = document.getElementById("capture-canvas");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext("2d").drawImage(video, 0, 0);
        canvas.toBlob((blob) => {
            setSelectedImage(blob, "captured-room.jpg");
            stopCamera();
        }, "image/jpeg", 0.92);
    });

    changeImageBtn.addEventListener("click", () => {
        selectedImageBlob = null;
        previewWrap.classList.add("hidden");
        placeholder.classList.remove("hidden");
        analyzeBtn.disabled = true;
        document.getElementById("results-section").classList.add("hidden");
    });

    function stopCamera() {
        if (cameraStream) {
            cameraStream.getTracks().forEach((t) => t.stop());
            cameraStream = null;
        }
        video.classList.add("hidden");
        cameraControls.classList.add("hidden");
        placeholder.classList.remove("hidden");
    }

    function setSelectedImage(fileOrBlob, name) {
        selectedImageBlob = fileOrBlob;
        selectedImageUrl = URL.createObjectURL(fileOrBlob);
        previewImg.src = selectedImageUrl;
        placeholder.classList.add("hidden");
        video.classList.add("hidden");
        cameraControls.classList.add("hidden");
        previewWrap.classList.remove("hidden");
        analyzeBtn.disabled = false;
    }

    analyzeBtn.addEventListener("click", async () => {
        if (!selectedImageBlob) return;
        analyzeBtn.disabled = true;
        analyzeBtn.textContent = "Analyzing...";

        const formData = new FormData();
        formData.append("image", selectedImageBlob, "room.jpg");
        formData.append("room_type", document.getElementById("room-type").value);

        try {
            const res = await fetch("/api/analyze", { method: "POST", body: formData });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || "Analysis failed");

            lastAnalysis = data.analysis;
            lastImagePath = data.image_path;
            renderAnalysisResults(data.analysis);
            document.getElementById("results-section").classList.remove("hidden");
            document.getElementById("results-section").scrollIntoView({ behavior: "smooth" });
        } catch (err) {
            alert(err.message);
        } finally {
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = "Analyze Room";
        }
    });

    proceedBtn.addEventListener("click", () => {
        sessionStorage.setItem("gruha_analysis", JSON.stringify({
            analysis: lastAnalysis,
            image_path: lastImagePath,
            image_url: selectedImageUrl,
            room_type: document.getElementById("room-type").value,
        }));
        window.location.href = "/design";
    });
}

function renderAnalysisResults(a) {
    document.getElementById("res-width").textContent = a.dimensions.width_feet;
    document.getElementById("res-length").textContent = a.dimensions.length_feet;
    document.getElementById("res-height").textContent = a.dimensions.height_feet;
    document.getElementById("res-area").textContent = a.dimensions.area_sq_feet;

    document.getElementById("res-light-quality").textContent = a.lighting.quality;
    document.getElementById("res-brightness").textContent = a.lighting.brightness;
    document.getElementById("res-light-note").textContent = a.lighting.note;

    const paletteEl = document.getElementById("res-palette");
    paletteEl.innerHTML = "";
    a.color_palette.forEach((hex) => {
        const swatch = document.createElement("span");
        swatch.style.background = hex;
        swatch.title = hex;
        paletteEl.appendChild(swatch);
    });

    document.getElementById("res-complexity").textContent = a.room_features.complexity;
    document.getElementById("res-edges").textContent = a.room_features.detected_edges;
    document.getElementById("res-orientation").textContent = a.room_features.orientation;
}

/* ============================== Design Studio Page ============================== */
function initDesignPage() {
    // Tabs
    document.querySelectorAll(".tab-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
            document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
            btn.classList.add("active");
            document.getElementById("tab-" + btn.dataset.tab).classList.add("active");
        });
    });

    // Budget slider <-> input sync
    const budgetInput = document.getElementById("budget-input");
    const budgetSlider = document.getElementById("budget-slider");
    budgetInput.addEventListener("input", () => (budgetSlider.value = budgetInput.value));
    budgetSlider.addEventListener("input", () => (budgetInput.value = budgetSlider.value));

    // Pull handoff data from the Analyze page, if present
    const handoff = sessionStorage.getItem("gruha_analysis");
    if (handoff) {
        const data = JSON.parse(handoff);
        lastAnalysis = data.analysis;
        lastImagePath = data.image_path;
        if (data.room_type) document.getElementById("room-type-select").value = data.room_type;
        if (data.image_url) {
            document.getElementById("room-preview-wrap").classList.remove("hidden");
            document.getElementById("room-preview-img").src = data.image_url;
            document.getElementById("room-preview-caption").textContent =
                "Room photo used for this design (Preview mode)";
        }
    }

    document.getElementById("generate-btn").addEventListener("click", generateDesign);
    document.getElementById("save-catalog-btn").addEventListener("click", saveDesign);
    document.getElementById("viewer-3d-btn").addEventListener("click", () => switchTab("viewer3d"));
    document.getElementById("open-3d-viewer").addEventListener("click", () => switchTab("viewer3d"));
    document.getElementById("export-pdf-btn").addEventListener("click", exportDesign);
    document.getElementById("share-btn").addEventListener("click", shareDesign);
}

function switchTab(tabName) {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    document.querySelector(`.tab-btn[data-tab="${tabName}"]`).classList.add("active");
    document.getElementById("tab-" + tabName).classList.add("active");
}

async function generateDesign() {
    const statusEl = document.getElementById("ai-status");
    statusEl.textContent = "● Generating design...";
    statusEl.className = "status-active";

    const payload = {
        room_type: document.getElementById("room-type-select").value,
        style_theme: document.getElementById("style-theme").value,
        budget: parseFloat(document.getElementById("budget-input").value || "5000"),
        image_path: lastImagePath,
        analysis: lastAnalysis,
    };

    try {
        const res = await fetch("/api/generate-design", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.error || "Design generation failed");

        lastDesignResult = result;
        renderDesignResult(result);
        statusEl.textContent = "● AI Design Complete ✓";
    } catch (err) {
        statusEl.textContent = "● Error generating design";
        alert(err.message);
    }
}

function renderDesignResult(result) {
    // Overview tab
    document.getElementById("ov-style-title").textContent = result.style.style_theme;
    document.getElementById("ov-style-desc").textContent = result.style.description;
    const hintsEl = document.getElementById("ov-furniture-hints");
    hintsEl.innerHTML = "";
    result.style.recommended_furniture.forEach((f) => {
        const li = document.createElement("li");
        li.textContent = f;
        hintsEl.appendChild(li);
    });

    const paletteEl = document.getElementById("ov-palette");
    paletteEl.innerHTML = "";
    result.style.color_palette.forEach((hex) => {
        const s = document.createElement("span");
        s.style.background = hex;
        s.title = hex;
        paletteEl.appendChild(s);
    });

    const materialsEl = document.getElementById("ov-materials");
    materialsEl.innerHTML = "";
    result.style.materials.forEach((m) => {
        const li = document.createElement("li");
        li.textContent = m;
        materialsEl.appendChild(li);
    });

    document.getElementById("ov-story").textContent = result.design_story;

    // Furniture tab
    const grid = document.getElementById("furniture-grid");
    grid.innerHTML = "";
    result.furniture.forEach((f) => {
        const card = document.createElement("div");
        card.className = "furniture-item";
        card.innerHTML = `
            <div class="furniture-icon">🪑</div>
            <h5>${f.name}</h5>
            <p class="muted">Qty: ${f.quantity}</p>
            <p class="muted small">₹${f.price_min} - ₹${f.price_max}</p>
            <span class="badge badge-${f.priority}">${f.priority}</span>`;
        grid.appendChild(card);
    });

    const tipsList = document.getElementById("layout-tips-list");
    tipsList.innerHTML = "";
    result.layout_tips.forEach((t) => {
        const li = document.createElement("li");
        li.textContent = t;
        tipsList.appendChild(li);
    });

    const util = result.space_utilization;
    document.getElementById("space-bar-fill").style.width = util.utilization_percent + "%";
    document.getElementById("space-util-pct").textContent = util.utilization_percent;
    document.getElementById("space-util-rating").textContent = util.rating;
    document.getElementById("space-total-sqft").textContent = util.total_furniture_sqft;
    document.getElementById("space-room-sqft").textContent = util.room_area_sqft;

    // Budget tab
    const budgetEl = document.getElementById("budget-breakdown");
    budgetEl.innerHTML = "<h4>Budget Breakdown</h4>";
    result.budget_plan.allocations.forEach((a) => {
        const row = document.createElement("div");
        row.className = "budget-row";
        row.innerHTML = `
            <div class="budget-row-top"><span>${a.category}</span><span>₹${a.amount.toFixed(2)}</span></div>
            <div class="budget-bar-track"><div class="budget-bar-fill" style="width:${a.percent}%"></div></div>
            <div class="budget-row-pct">${a.percent}%</div>`;
        budgetEl.appendChild(row);
    });

    const savingsList = document.getElementById("savings-tips-list");
    savingsList.innerHTML = "";
    result.budget_plan.savings_tips.forEach((t) => {
        const li = document.createElement("li");
        li.textContent = t;
        savingsList.appendChild(li);
    });

    // Render a simple 3D preview automatically once a design exists
    if (window.renderRoomViewer) {
        window.renderRoomViewer("three-viewer", result.style.style_theme, result.furniture);
        document.getElementById("three-viewer").classList.remove("hidden");
    }
}

async function saveDesign() {
    if (!lastDesignResult) {
        alert("Generate a design first!");
        return;
    }
    const payload = {
        room_type: document.getElementById("room-type-select").value,
        style_theme: document.getElementById("style-theme").value,
        budget: parseFloat(document.getElementById("budget-input").value || "5000"),
        image_path: lastImagePath,
        result: lastDesignResult,
    };
    try {
        const res = await fetch("/api/save-design", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Save failed");
        currentDesignId = data.design_id;
        window.gruhaCurrentDesignId = data.design_id;
        alert("Design saved to your catalog!");
    } catch (err) {
        alert(err.message);
    }
}

function exportDesign() {
    // ASSUMPTION: full PDF layout export would need a server-side PDF
    // engine (e.g. WeasyPrint) which isn't part of this offline build.
    // The browser's native print-to-PDF covers the same use case.
    if (!lastDesignResult) {
        alert("Generate a design first!");
        return;
    }
    window.print();
}

function shareDesign() {
    const text = lastDesignResult
        ? `Check out my ${document.getElementById("style-theme").value} design on Gruha Alankara!`
        : "Check out Gruha Alankara - AI interior design!";
    if (navigator.share) {
        navigator.share({ title: "Gruha Alankara", text, url: window.location.href });
    } else {
        navigator.clipboard.writeText(text + " " + window.location.href);
        alert("Link copied to clipboard!");
    }
}
