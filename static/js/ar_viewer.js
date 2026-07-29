/* ar_viewer.js
 * Two independent features:
 *
 * 1. Live AR Camera (initLiveARCamera): a lightweight, fully in-browser
 *    "AR" preview. It overlays colored furniture silhouettes on top of
 *    the live camera feed wherever the user taps.
 *    ASSUMPTION: True markerless AR (plane detection, occlusion) needs
 *    WebXR device support, which isn't guaranteed on every browser/OS
 *    combination. This 2D-overlay-on-camera approach demonstrates the
 *    same "see it before you buy it" workflow described in the spec
 *    without requiring a WebXR-capable device, and degrades gracefully
 *    everywhere getUserMedia works.
 *
 * 2. 3D Room Viewer (renderRoomViewer / renderStaticRoomViewer): a
 *    minimal three.js scene showing a room box with placeholder
 *    furniture blocks, since no licensed 3D furniture asset library is
 *    bundled with this offline project.
 */

/* ---------------------- Live AR Camera ---------------------- */
function initLiveARCamera() {
    const video = document.getElementById("ar-video");
    const canvas = document.getElementById("ar-overlay");
    const startBtn = document.getElementById("ar-start-btn");
    const stopBtn = document.getElementById("ar-stop-btn");
    const pieceButtons = document.querySelectorAll(".ar-piece-btn");

    let stream = null;
    let selectedPiece = null;
    const placedItems = [];

    pieceButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            pieceButtons.forEach((b) => b.classList.remove("selected"));
            btn.classList.add("selected");
            selectedPiece = { piece: btn.dataset.piece, color: btn.dataset.color };
        });
    });

    startBtn.addEventListener("click", async () => {
        try {
            stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: { ideal: "environment" }, width: { ideal: 1280 } },
                audio: false,
            });
            video.srcObject = stream;
            await video.play();
            resizeCanvas();
            startBtn.disabled = true;
            stopBtn.disabled = false;
        } catch (err) {
            alert("Could not access camera: " + err.message);
        }
    });

    stopBtn.addEventListener("click", () => {
        if (stream) {
            stream.getTracks().forEach((t) => t.stop());
            stream = null;
        }
        startBtn.disabled = false;
        stopBtn.disabled = true;
    });

    function resizeCanvas() {
        canvas.width = video.videoWidth || video.clientWidth;
        canvas.height = video.videoHeight || video.clientHeight;
    }

    window.addEventListener("resize", resizeCanvas);

    canvas.addEventListener("click", (e) => {
        if (!selectedPiece) {
            alert("Pick a furniture piece to place first.");
            return;
        }
        const rect = canvas.getBoundingClientRect();
        const x = ((e.clientX - rect.left) / rect.width) * canvas.width;
        const y = ((e.clientY - rect.top) / rect.height) * canvas.height;
        placedItems.push({ x, y, ...selectedPiece });
        drawOverlay();
    });

    function drawOverlay() {
        const ctx = canvas.getContext("2d");
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        placedItems.forEach((item) => {
            const w = canvas.width * 0.18;
            const h = canvas.height * 0.14;
            ctx.fillStyle = item.color + "cc";
            ctx.strokeStyle = "#ffffff";
            ctx.lineWidth = 2;
            roundRect(ctx, item.x - w / 2, item.y - h / 2, w, h, 10);
            ctx.fill();
            ctx.stroke();
            ctx.fillStyle = "#ffffff";
            ctx.font = "14px sans-serif";
            ctx.textAlign = "center";
            ctx.fillText(item.piece, item.x, item.y + 5);
        });
    }

    function roundRect(ctx, x, y, w, h, r) {
        ctx.beginPath();
        ctx.moveTo(x + r, y);
        ctx.arcTo(x + w, y, x + w, y + h, r);
        ctx.arcTo(x + w, y + h, x, y + h, r);
        ctx.arcTo(x, y + h, x, y, r);
        ctx.arcTo(x, y, x + w, y, r);
        ctx.closePath();
    }
}

/* ---------------------- three.js Room Viewer ---------------------- */
function _buildRoomScene(container, furnitureNames) {
    container.innerHTML = "";
    const width = container.clientWidth || 600;
    const height = container.clientHeight || 360;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x05050a);

    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(6, 6, 9);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    container.appendChild(renderer.domElement);

    scene.add(new THREE.AmbientLight(0xffffff, 0.6));
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight.position.set(5, 10, 5);
    scene.add(dirLight);

    // Floor
    const floor = new THREE.Mesh(
        new THREE.PlaneGeometry(12, 12),
        new THREE.MeshStandardMaterial({ color: 0x23233a })
    );
    floor.rotation.x = -Math.PI / 2;
    scene.add(floor);

    // Back walls
    const wallMaterial = new THREE.MeshStandardMaterial({ color: 0x171725 });
    const backWall = new THREE.Mesh(new THREE.PlaneGeometry(12, 6), wallMaterial);
    backWall.position.set(0, 3, -6);
    scene.add(backWall);
    const sideWall = new THREE.Mesh(new THREE.PlaneGeometry(12, 6), wallMaterial);
    sideWall.rotation.y = Math.PI / 2;
    sideWall.position.set(-6, 3, 0);
    scene.add(sideWall);

    // Furniture placeholders: a colored box per item, arranged in a row
    const palette = [0x7c6fe0, 0x6f9be0, 0xe0a56f, 0x4caf7d, 0xe05c5c];
    const items = (furnitureNames && furnitureNames.length ? furnitureNames : ["Sofa", "Table", "Chair"]).slice(0, 6);
    const spacing = 10 / Math.max(items.length, 1);

    items.forEach((item, i) => {
        const name = typeof item === "string" ? item : item.name;
        const h = 0.6 + (i % 3) * 0.3;
        const box = new THREE.Mesh(
            new THREE.BoxGeometry(1.2, h, 1.2),
            new THREE.MeshStandardMaterial({ color: palette[i % palette.length] })
        );
        box.position.set(-5 + spacing * i + spacing / 2, h / 2, -2 + (i % 2) * 2);
        box.userData.label = name;
        scene.add(box);
    });

    let angle = 0;
    function animate() {
        requestAnimationFrame(animate);
        angle += 0.004;
        camera.position.x = Math.sin(angle) * 10;
        camera.position.z = Math.cos(angle) * 10;
        camera.lookAt(0, 1, 0);
        renderer.render(scene, camera);
    }
    animate();
}

function renderRoomViewer(containerId, styleTheme, furniture) {
    const container = document.getElementById(containerId);
    if (!container || typeof THREE === "undefined") return;
    _buildRoomScene(container, furniture);
}

function renderStaticRoomViewer(containerId) {
    const container = document.getElementById(containerId);
    if (!container || typeof THREE === "undefined") return;
    _buildRoomScene(container, null);
}
