/**
 * Face Recognition System - Frontend JavaScript
 * Handles all API interactions and UI updates
 */

const API_BASE_URL = 'http://127.0.0.1:8000/api';

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
    checkAPIStatus();
});

function initializeApp() {
    console.log('🚀 Face Recognition System initialized');
}

// ============================================
// API STATUS CHECK
// ============================================

async function checkAPIStatus() {
    const statusElement = document.getElementById('apiStatus');
    try {
        const response = await fetch('http://127.0.0.1:8000/health');
        if (response.ok) {
            statusElement.textContent = 'Connected';
            statusElement.parentElement.style.background = 'rgba(76, 175, 80, 0.1)';
            statusElement.parentElement.style.borderColor = 'rgba(76, 175, 80, 0.3)';
            statusElement.style.color = '#4caf50';
        } else {
            throw new Error('API not responding');
        }
    } catch (error) {
        statusElement.textContent = 'Disconnected';
        statusElement.parentElement.style.background = 'rgba(244, 67, 54, 0.1)';
        statusElement.parentElement.style.borderColor = 'rgba(244, 67, 54, 0.3)';
        statusElement.style.color = '#f44336';
    }
}

// ============================================
// EVENT LISTENERS
// ============================================

function setupEventListeners() {
    // Tab navigation
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    // Detect tab
    setupUploadArea('detectUploadArea', 'detectImageInput', 'detectPreview', 'detectBtn');
    document.getElementById('detectBtn').addEventListener('click', handleDetectFace, false);

    // Save tab
    setupUploadArea('saveUploadArea', 'saveImageInput', 'savePreview', 'saveBtn');
    document.getElementById('saveBtn').addEventListener('click', handleSaveFace, false);
    document.getElementById('personName').addEventListener('input', validateSaveForm);

    // Recognize tab
    setupUploadArea('recognizeUploadArea', 'recognizeImageInput', 'recognizePreview', 'recognizeBtn');
    document.getElementById('recognizeBtn').addEventListener('click', handleRecognizeFace, false);

    // Manage tab
    document.getElementById('refreshListBtn').addEventListener('click', loadFacesList);

    // Bulk Save Toggle
    document.getElementById('bulkSaveToggle').addEventListener('change', (e) => {
        const isBulk = e.target.checked;
        document.getElementById('nameFieldLabel').textContent = isBulk ? 'Full Names (Comma separated) *' : 'Full Name *';
        document.getElementById('personName').placeholder = isBulk ? 'e.g. John Doe, Jane Smith' : 'Enter full name';
        document.getElementById('bulkSaveHint').style.display = isBulk ? 'block' : 'none';

        // Hide/Show secondary info (Email/Phone - usually only for single save)
        const emailField = document.getElementById('personEmail').parentElement;
        const phoneField = document.getElementById('personPhone').parentElement;
        emailField.style.display = isBulk ? 'none' : 'block';
        phoneField.style.display = isBulk ? 'none' : 'block';

        if (isBulk && document.getElementById('saveImageInput').files.length > 0) {
            previewBulkOrder();
        } else if (!isBulk) {
            document.getElementById('saveResult').style.display = 'none';
        }
    });

    // Special listener for Save tab image upload to trigger preview
    document.getElementById('saveImageInput').addEventListener('change', () => {
        if (document.getElementById('bulkSaveToggle').checked) {
            previewBulkOrder();
        }
    });
}

function setupUploadArea(areaId, inputId, previewId, btnId) {
    const area = document.getElementById(areaId);
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    const btn = document.getElementById(btnId);

    area.addEventListener('click', () => input.click());

    area.addEventListener('dragover', (e) => {
        e.preventDefault();
        area.style.borderColor = 'var(--border-glow)';
        area.style.background = 'rgba(102, 126, 234, 0.05)';
    });

    area.addEventListener('dragleave', () => {
        area.style.borderColor = 'var(--border-color)';
        area.style.background = '';
    });

    area.addEventListener('drop', (e) => {
        e.preventDefault();
        area.style.borderColor = 'var(--border-color)';
        area.style.background = '';

        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            handleImageUpload(file, input, preview, btn, area);
        }
    });

    input.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            handleImageUpload(file, input, preview, btn, area);
        }
    });
}

function handleImageUpload(file, input, preview, btn, area) {
    const reader = new FileReader();
    reader.onload = (e) => {
        preview.src = e.target.result;
        preview.style.display = 'block';
        area.querySelector('.upload-content').style.display = 'none';
        btn.disabled = false;
    };
    reader.readAsDataURL(file);
}

function validateSaveForm() {
    const name = document.getElementById('personName').value.trim();
    const imageInput = document.getElementById('saveImageInput');
    const saveBtn = document.getElementById('saveBtn');

    saveBtn.disabled = !(name && imageInput.files.length > 0);
}

// ============================================
// TAB SWITCHING
// ============================================

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');

    // Load faces list when switching to manage tab
    if (tabName === 'manage') {
        loadFacesList();
    }
}

/**
 * Scales backend coordinates to match local natural image dimensions
 */
function scaleBoundingBox(bbox, imageMeta, targetImg) {
    if (!imageMeta || !targetImg || !targetImg.naturalWidth) return bbox;

    const scaleX = targetImg.naturalWidth / imageMeta.width;
    const scaleY = targetImg.naturalHeight / imageMeta.height;

    return {
        x: Math.round(bbox.x * scaleX),
        y: Math.round(bbox.y * scaleY),
        width: Math.round(bbox.width * scaleX),
        height: Math.round(bbox.height * scaleY)
    };
}

// ============================================
// LOADING OVERLAY
// ============================================

/**
 * Extracts a cropped thumbnail from an image source based on bounding box
 * Improved with 25% padding for better head-centered clarity
 */
async function extractFaceThumbnail(imgSource, bbox) {
    return new Promise((resolve) => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');

        canvas.width = 120;
        canvas.height = 120;

        if (!imgSource || !imgSource.complete) {
            resolve(null);
            return;
        }

        // Add 25% padding for a "clearer" head-centered look
        const padding = 0.25;
        let px = bbox.x - (bbox.width * padding);
        let py = bbox.y - (bbox.height * padding);
        let pw = bbox.width * (1 + padding * 2);
        let ph = bbox.height * (1 + padding * 2);

        // Ensure we don't crop outside image
        const nw = imgSource.naturalWidth;
        const nh = imgSource.naturalHeight;

        px = Math.max(0, px);
        py = Math.max(0, py);
        pw = Math.min(nw - px, pw);
        ph = Math.min(nh - py, ph);

        ctx.drawImage(
            imgSource,
            px, py, pw, ph,
            0, 0, 120, 120
        );

        resolve(canvas.toDataURL('image/jpeg', 0.95));
    });
}

function showLoading() {
    document.getElementById('loadingOverlay').classList.add('active');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('active');
}

// ============================================
// FACE DETECTION
// ============================================

async function handleDetectFace(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    const imageInput = document.getElementById('detectImageInput');
    const resultContainer = document.getElementById('detectResult');
    const mode = document.querySelector('input[name="detectionMode"]:checked').value;

    if (!imageInput.files.length) {
        showError(resultContainer, 'Please select an image first');
        return;
    }

    const formData = new FormData();
    formData.append('image', imageInput.files[0]);

    let endpoint = '';
    switch (mode) {
        case 'basic':
            endpoint = '/face-detection';
            break;
        case 'landmarks':
            endpoint = '/face-detection-landmarks';
            break;
        case 'deep':
            endpoint = '/face-detection-deep';
            break;
        case 'multiple':
            endpoint = '/face-detection-multiple';
            break;
    }

    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        hideLoading();

        if (data.success) {
            if (mode === 'multiple') {
                if (data.faces_detected > 0) {
                    displayMultiDetectionResult_Info(data, resultContainer);
                } else {
                    showInfo(resultContainer, 'No faces detected in the image');
                }
            } else if (data.face_detected) {
                displayDetectionResult(data, mode, resultContainer);
            } else {
                showInfo(resultContainer, data.message || 'No face detected in the image');
            }
        } else {
            showError(resultContainer, data.message || 'Detection failed');
        }
    } catch (error) {
        hideLoading();
        showError(resultContainer, `Error: ${error.message}`);
    }
}

async function displayMultiDetectionResult_Info(data, container) {
    const sourceImg = document.getElementById('detectPreview');
    let html = '<div class="result-success">';
    html += `<h3 style="margin-bottom: 1rem; color: #4caf50;">✅ Group Detection Successful</h3>`;
    html += `<p style="margin-bottom: 1.5rem; color: var(--text-secondary);">Found <b>${data.faces_detected}</b> face(s) in this image (Sorted Left-to-Right).</p>`;

    html += '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 1rem;">';

    for (let i = 0; i < data.detections.length; i++) {
        const det = data.detections[i];
        const scaledBBox = scaleBoundingBox(det.bounding_box, data.image_meta, sourceImg);
        const thumbData = await extractFaceThumbnail(sourceImg, scaledBBox);

        html += `<div style="background: rgba(255,255,255,0.05); border: 1px solid rgba(102, 126, 234, 0.2); padding: 1rem; border-radius: 12px; display: flex; align-items: center; gap: 1rem;">`;

        // Numbered Thumbnail
        html += `<div style="position: relative; width: 60px; height: 60px; min-width: 60px;">`;
        if (thumbData) {
            html += `<img src="${thumbData}" style="width: 100%; height: 100%; border-radius: 8px; object-fit: cover; border: 1.5px solid var(--primary);">`;
        }
        html += `<span style="position: absolute; top: -8px; left: -8px; background: var(--primary); color: white; width: 22px; height: 22px; border-radius: 50%; font-size: 11px; font-weight: bold; display: flex; align-items: center; justify-content: center; border: 1.5px solid white;">${i + 1}</span>`;
        html += `</div>`;

        html += `<div>`;
        html += `<h4 style="margin: 0; font-size: 0.95rem; color: white;">Face #${i + 1}</h4>`;
        html += `<p style="margin: 0.2rem 0 0; font-size: 0.8rem; color: var(--text-muted);">Conf: ${(det.confidence * 100).toFixed(1)}%</p>`;
        html += `<p style="margin: 0.1rem 0 0; font-size: 0.7rem; font-family: monospace; color: var(--text-secondary); opacity: 0.7;">[X:${scaledBBox.x}, Y:${scaledBBox.y}, W:${scaledBBox.width}]</p>`;
        html += `</div>`;

        html += '</div>';
    }

    html += '</div>';
    html += '</div>';

    container.innerHTML = html;
    container.style.display = 'block';
}

function displayDetectionResult(data, mode, container) {
    let html = '<div class="result-success">';
    html += '<h3 style="margin-bottom: 1rem; color: #4caf50;">✅ Face Detected Successfully</h3>';

    // Bounding Box
    if (data.bounding_box) {
        html += '<div class="result-item">';
        html += '<span class="result-label">Bounding Box:</span>';
        html += `<span class="result-value">X: ${data.bounding_box.x}, Y: ${data.bounding_box.y}, W: ${data.bounding_box.width}, H: ${data.bounding_box.height}</span>`;
        html += '</div>';
    }

    // Confidence
    if (data.confidence) {
        html += '<div class="result-item">';
        html += '<span class="result-label">Confidence:</span>';
        html += `<span class="result-value">${(data.confidence * 100).toFixed(2)}%</span>`;
        html += '</div>';
    }

    // Embedding
    if (data.face_embedding) {
        html += '<div class="result-item">';
        html += '<span class="result-label">Embedding Dimension:</span>';
        html += `<span class="result-value">${data.face_embedding.length}D vector</span>`;
        html += '</div>';
    }

    // Deep Analysis
    if (mode === 'deep') {
        if (data.emotion) {
            html += '<div class="result-item">';
            html += '<span class="result-label">Emotion:</span>';
            html += `<span class="result-value">${data.emotion}</span>`;
            html += '</div>';
        }

        if (data.age) {
            html += '<div class="result-item">';
            html += '<span class="result-label">Age:</span>';
            html += `<span class="result-value">${data.age} years</span>`;
            html += '</div>';
        }

        if (data.gender) {
            html += '<div class="result-item">';
            html += '<span class="result-label">Gender:</span>';
            html += `<span class="result-value">${data.gender} (${(data.gender_confidence).toFixed(2)}%)</span>`;
            html += '</div>';
        }

        if (data.emotion_scores) {
            html += '<div class="result-item" style="flex-direction: column; align-items: flex-start;">';
            html += '<span class="result-label" style="margin-bottom: 0.5rem;">Emotion Scores:</span>';
            html += '<div style="width: 100%;">';
            for (const [emotion, score] of Object.entries(data.emotion_scores)) {
                const percentage = score.toFixed(2);
                html += `<div style="margin-bottom: 0.5rem;">`;
                html += `<div style="display: flex; justify-content: space-between; margin-bottom: 0.2rem;">`;
                html += `<span style="font-size: 0.85rem; text-transform: capitalize;">${emotion}</span>`;
                html += `<span style="font-size: 0.85rem;">${percentage}%</span>`;
                html += `</div>`;
                html += `<div style="height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden;">`;
                html += `<div style="width: ${percentage}%; height: 100%; background: linear-gradient(90deg, #667eea, #764ba2);"></div>`;
                html += `</div>`;
                html += `</div>`;
            }
            html += '</div>';
            html += '</div>';
        }
    }

    // Landmarks
    if (mode === 'landmarks') {
        if (data.all_landmarks && data.total_landmarks) {
            html += '<div class="result-item">';
            html += '<span class="result-label">Total Landmarks:</span>';
            html += `<span class="result-value">${data.total_landmarks} 3D points</span>`;
            html += '</div>';
        }

        if (data.categorized) {
            html += '<div class="result-item" style="flex-direction: column; align-items: flex-start;">';
            html += '<span class="result-label" style="margin-bottom: 0.5rem;">Categorized Landmarks:</span>';
            html += '<div style="width: 100%; display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem;">';

            const categories = {
                'left_eye': 'Left Eye',
                'right_eye': 'Right Eye',
                'left_eyebrow': 'Left Eyebrow',
                'right_eyebrow': 'Right Eyebrow',
                'nose': 'Nose',
                'mouth': 'Mouth',
                'lips': 'Lips',
                'face_oval': 'Face Oval'
            };

            for (const [key, label] of Object.entries(categories)) {
                if (data.categorized[key]) {
                    html += '<div style="padding: 0.5rem; background: rgba(255,255,255,0.05); border-radius: 8px;">';
                    html += `<div style="font-size: 0.85rem; color: var(--text-secondary);">${label}</div>`;
                    html += `<div style="font-size: 0.9rem; font-weight: 600; color: #667eea;">${data.categorized[key].length} points</div>`;
                    html += '</div>';
                }
            }

            html += '</div>';
            html += '</div>';

            // Show sample landmark coordinates
            if (data.all_landmarks && data.all_landmarks.length > 0) {
                html += '<div class="result-item" style="flex-direction: column; align-items: flex-start;">';
                html += '<span class="result-label" style="margin-bottom: 0.5rem;">Landmark Coordinates (showing 20 of ' + data.all_landmarks.length + '):</span>';
                html += '<div style="width: 100%; font-family: monospace; font-size: 0.85rem; background: rgba(0,0,0,0.3); padding: 0.75rem; border-radius: 8px; max-height: 200px; overflow-y: auto;">';

                // Show first 20 landmarks
                for (let i = 0; i < Math.min(20, data.all_landmarks.length); i++) {
                    const lm = data.all_landmarks[i];
                    html += `<div style="margin-bottom: 0.3rem; color: var(--text-secondary);">`;
                    html += `[${String(lm.index).padStart(3, ' ')}] x:${lm.x.toFixed(1).padStart(6, ' ')}, y:${lm.y.toFixed(1).padStart(6, ' ')}, z:${lm.z.toFixed(4)}`;
                    html += '</div>';
                }

                if (data.all_landmarks.length > 20) {
                    html += '<div style="margin-top: 0.5rem; color: var(--text-muted); font-size: 0.8rem;">... and ' + (data.all_landmarks.length - 20) + ' more points (scroll in API response for all)</div>';
                }
                html += '</div>';
                html += '</div>';
            }
        }
    }

    html += '</div>';
    container.innerHTML = html;
    container.style.display = 'block';
}

// ============================================
// SAVE FACE
// ============================================

async function handleSaveFace(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    const imageInput = document.getElementById('saveImageInput');
    const name = document.getElementById('personName').value.trim();
    const email = document.getElementById('personEmail').value.trim();
    const phone = document.getElementById('personPhone').value.trim();
    const resultContainer = document.getElementById('saveResult');
    const isBulkMode = document.getElementById('bulkSaveToggle').checked;

    if (!imageInput.files.length || !name) {
        showError(resultContainer, 'Please provide an image and name');
        return;
    }

    const formData = new FormData();
    formData.append('image', imageInput.files[0]);
    formData.append('names', name); // In single mode, this is 'name', in bulk it's 'names'

    // Adjust key for single mode vs bulk mode
    if (!isBulkMode) {
        formData.delete('names');
        formData.append('name', name);
        if (email) formData.append('email', email);
        if (phone) formData.append('phone', phone);
    }

    const endpoint = isBulkMode ? '/save-multiple-faces' : '/save-face';

    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        hideLoading();

        if (data.success) {
            if (isBulkMode) {
                let html = '<div class="result-success">';
                html += `<h3 style="margin-bottom:1rem; color:#4caf50;">✅ Bulk Save Complete</h3>`;
                html += `<p style="margin-bottom:1rem;">Processed ${data.saved_faces.length} face(s):</p><ul style="text-align:left; margin-left:1rem;">`;
                data.saved_faces.forEach(f => {
                    html += `<li>${f.success ? '✅' : '❌'} ${f.name || 'Unknown'}: ${f.message}</li>`;
                });
                html += '</ul></div>';
                resultContainer.innerHTML = html;
                resultContainer.style.display = 'block';
            } else {
                showSuccess(resultContainer, `✅ ${data.message}<br>Face ID: ${data.face_id}`);
            }
        } else {
            showError(resultContainer, data.message);
        }
    } catch (error) {
        hideLoading();
        showError(resultContainer, `Error: ${error.message}`);
    }
}

/**
 * Previews the face order in the Save Tab to help with name mapping
 */
async function previewBulkOrder() {
    const isBulkMode = document.getElementById('bulkSaveToggle').checked;
    const imageInput = document.getElementById('saveImageInput');
    const resultContainer = document.getElementById('saveResult');
    const sourceImg = document.getElementById('savePreview');

    if (!isBulkMode || !imageInput.files.length) {
        return;
    }

    const formData = new FormData();
    formData.append('image', imageInput.files[0]);

    showLoading();
    try {
        const response = await fetch(`${API_BASE_URL}/face-detection-multiple`, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        hideLoading();

        if (data.success && data.faces_detected > 0) {
            let html = '<div style="background: rgba(102, 126, 234, 0.1); border: 1px dashed var(--primary); padding: 1rem; border-radius: 12px; margin-bottom: 1.5rem;">';
            html += '<h4 style="margin: 0 0 1rem 0; font-size: 0.9rem; color: var(--primary);">📍 Face Order Preview (Left-to-Right)</h4>';
            html += '<div style="display: flex; flex-wrap: wrap; gap: 0.75rem;">';

            for (let i = 0; i < data.detections.length; i++) {
                const det = data.detections[i];
                const scaledBBox = scaleBoundingBox(det.bounding_box, data.image_meta, sourceImg);
                const thumbData = await extractFaceThumbnail(sourceImg, scaledBBox);

                html += `<div style="position: relative; width: 60px; height: 60px;">`;
                html += `<img src="${thumbData}" style="width: 100%; height: 100%; border-radius: 8px; border: 2px solid var(--primary); object-fit: cover;">`;
                html += `<span style="position: absolute; top: -5px; left: -5px; background: var(--primary); color: white; width: 22px; height: 22px; border-radius: 50%; font-size: 11px; font-weight: bold; display: flex; align-items: center; justify-content: center; border: 1.5px solid white;">${i + 1}</span>`;
                html += `</div>`;
            }

            html += '</div>';
            html += '<p style="margin: 0.75rem 0 0 0; font-size: 0.75rem; color: var(--text-muted);">Match your names to these numbers: (1), (2), (3)...</p>';
            html += '</div>';

            resultContainer.innerHTML = html;
            resultContainer.style.display = 'block';
        }
    } catch (e) {
        hideLoading();
        console.error("Preview failed", e);
    }
}

function resetSaveForm() {
    document.getElementById('saveImageInput').value = '';
    document.getElementById('savePreview').style.display = 'none';
    document.getElementById('saveUploadArea').querySelector('.upload-content').style.display = 'block';
    document.getElementById('personName').value = '';
    document.getElementById('personEmail').value = '';
    document.getElementById('personPhone').value = '';
    document.getElementById('saveBtn').disabled = true;
    document.getElementById('saveResult').style.display = 'none';
}

// ============================================
// RECOGNIZE FACE
// ============================================

async function handleRecognizeFace(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    const imageInput = document.getElementById('recognizeImageInput');
    const resultContainer = document.getElementById('recognizeResult');
    const isMultiMode = document.getElementById('multiFaceToggle').checked;

    if (!imageInput.files.length) {
        showError(resultContainer, 'Please select an image first');
        return;
    }

    const formData = new FormData();
    formData.append('image', imageInput.files[0]);

    const endpoint = isMultiMode ? '/recognize-multiple-faces' : '/recognize-face';

    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        hideLoading();

        if (!data.success) {
            showError(resultContainer, data.message || 'Operation failed');
            return;
        }

        if (isMultiMode) {
            displayMultiRecognitionResult(data, resultContainer);
        } else {
            if (data.recognized) {
                let html = '<div class="result-success">';
                html += '<h3 style="margin-bottom: 1rem; color: #4caf50;">✅ Face Recognized!</h3>';
                html += '<div class="result-item">';
                html += '<span class="result-label">Name:</span>';
                html += `<span class="result-value">${data.name}</span>`;
                html += '</div>';
                html += '<div class="result-item">';
                html += '<span class="result-label">Confidence:</span>';
                html += `<span class="result-value">${(data.confidence * 100).toFixed(2)}%</span>`;
                html += '</div>';
                if (data.email) {
                    html += '<div class="result-item">';
                    html += '<span class="result-label">Email:</span>';
                    html += `<span class="result-value">${data.email}</span>`;
                    html += '</div>';
                }
                if (data.phone) {
                    html += '<div class="result-item">';
                    html += '<span class="result-label">Phone:</span>';
                    html += `<span class="result-value">${data.phone}</span>`;
                    html += '</div>';
                }
                html += '</div>';
                resultContainer.innerHTML = html;
                resultContainer.style.display = 'block';
            } else {
                showInfo(resultContainer, data.message || 'Face not recognized');
            }
        }
    } catch (error) {
        hideLoading();
        showError(resultContainer, `Error: ${error.message}`);
    }
}

async function displayMultiRecognitionResult(data, container) {
    if (data.faces_detected === 0) {
        showInfo(container, 'No faces detected in the group photo');
        return;
    }

    const sourceImg = document.getElementById('recognizePreview');
    let html = '<div class="result-success">';
    html += `<h3 style="margin-bottom: 1.5rem; color: #4caf50;">👥 Group Analysis Complete</h3>`;
    html += `<p style="margin-bottom: 1.5rem; color: var(--text-secondary);">Detected ${data.faces_detected} face(s), identified ${data.recognized_faces.filter(f => f.recognized).length} registered individuals.</p>`;

    html += '<div style="display: flex; flex-direction: column; gap: 1rem;">';

    for (let i = 0; i < data.recognized_faces.length; i++) {
        const face = data.recognized_faces[i];
        const color = face.recognized ? '#4caf50' : '#ffa000';
        const scaledBBox = scaleBoundingBox(face.bounding_box, data.image_meta, sourceImg);
        const thumbData = await extractFaceThumbnail(sourceImg, scaledBBox);

        html += `<div style="background: rgba(255,255,255,0.05); border: 1px solid ${color}33; padding: 1rem; border-radius: 12px; display: flex; align-items: center; gap: 1rem;">`;

        // Face Thumbnail with Number Badge
        html += `<div style="position: relative; width: 64px; height: 64px; min-width: 64px;">`;
        if (thumbData) {
            html += `<img src="${thumbData}" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover; border: 2px solid ${color};">`;
        } else {
            html += `<div style="width: 100%; height: 100%; background: ${color}22; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: ${color}; border: 2px solid ${color};">`;
            html += `<svg viewBox="0 0 24 24" fill="none" style="width: 24px; height: 24px;"><path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 5C13.66 5 15 6.34 15 8C15 9.66 13.66 11 12 11C10.34 11 9 9.66 9 8C9 6.34 10.34 5 12 5ZM12 19.2C9.5 19.2 7.29 17.92 6 15.98C6.03 13.99 10 12.9 12 12.9C13.99 12.9 17.97 13.99 18 15.98C16.71 17.92 14.5 19.2 12 19.2Z" fill="currentColor"/></svg></div>`;
        }
        html += `<span style="position: absolute; top: -5px; left: -5px; background: var(--primary); color: white; width: 22px; height: 22px; border-radius: 50%; font-size: 12px; font-weight: bold; display: flex; align-items: center; justify-content: center; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">${i + 1}</span>`;
        html += `</div>`;

        // Details
        html += '<div style="flex: 1;">';
        html += `<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem;">`;
        html += `<h4 style="margin: 0; font-size: 1.1rem; color: ${face.recognized ? 'white' : 'var(--text-secondary)'};">${face.name || 'Unknown Face'}</h4>`;
        html += `<span style="font-size: 0.7rem; padding: 0.15rem 0.4rem; background: ${color}22; color: ${color}; border-radius: 4px; font-weight: 700; text-transform: uppercase;">${face.recognized ? 'Identified' : 'Unknown'}</span>`;
        html += `</div>`;

        html += `<p style="margin: 0; font-size: 0.85rem; color: var(--text-muted);">${face.recognized ? `Confidence: ${(face.confidence * 100).toFixed(1)}%` : `No match found`}</p>`;

        // Bounding Box Coordinates (Scaled)
        html += `<p style="margin: 0.2rem 0 0; font-size: 0.75rem; font-family: monospace; color: var(--text-secondary); opacity: 0.7;">`;
        html += `X:${scaledBBox.x}, Y:${scaledBBox.y}, W:${scaledBBox.width}`;
        html += `</p>`;

        if (face.email) html += `<p style="margin: 0.2rem 0 0; font-size: 0.85rem; color: var(--text-secondary); opacity: 0.8;">📧 ${face.email}</p>`;

        html += '</div>';
        html += '</div>';
    }

    html += '</div>';
    html += '</div>';

    container.innerHTML = html;
    container.style.display = 'block';
}

// ============================================
// MANAGE FACES
// ============================================

async function loadFacesList() {
    const listContainer = document.getElementById('facesList');
    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}/list-faces`);
        const data = await response.json();
        hideLoading();

        if (data.success && data.faces.length > 0) {
            let html = `<p style="margin-bottom: 1rem; color: var(--text-secondary);">Total Faces: ${data.total_faces}</p>`;

            data.faces.forEach(face => {
                html += '<div class="face-card" style="display: flex; align-items: center; gap: 1rem; padding: 1rem; background: rgba(255,255,255,0.03); border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 1rem;">';

                // Thumbnail
                if (face.thumbnail) {
                    html += `<img src="${face.thumbnail}" style="width: 60px; height: 60px; border-radius: 8px; object-fit: cover; border: 1.5px solid var(--primary);">`;
                } else {
                    html += `<div style="width: 60px; height: 60px; background: rgba(255,255,255,0.05); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: var(--text-muted); border: 1.5px solid rgba(255,255,255,0.1);">`;
                    html += `<svg viewBox="0 0 24 24" fill="none" style="width: 24px; height: 24px;"><path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 5C13.66 5 15 6.34 15 8C15 9.66 13.66 11 12 11C10.34 11 9 9.66 9 8C9 6.34 10.34 5 12 5ZM12 19.2C9.5 19.2 7.29 17.92 6 15.98C6.03 13.99 10 12.9 12 12.9C13.99 12.9 17.97 13.99 18 15.98C16.71 17.92 14.5 19.2 12 19.2Z" fill="currentColor"/></svg></div>`;
                }

                html += '<div class="face-info" style="flex: 1;">';
                html += `<h3 style="margin: 0; font-size: 1.1rem; color: white;">${face.name}</h3>`;
                html += `<p style="margin: 0.25rem 0 0 0; font-size: 0.8rem; color: var(--text-muted);">ID: ${face.id} | Added: ${new Date(face.created_at).toLocaleDateString()}</p>`;
                if (face.email) html += `<p style="margin: 0.1rem 0 0 0; font-size: 0.8rem; color: var(--text-secondary); opacity: 0.8;">📧 ${face.email}</p>`;
                html += '</div>';
                html += '<div class="face-actions">';
                html += `<button type="button" class="btn-icon" onclick="deleteFace(${face.id}, '${face.name}')" title="Delete">`;
                html += '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">';
                html += '<path d="M6 19C6 20.1 6.9 21 8 21H16C17.1 21 18 20.1 18 19V7H6V19ZM19 4H15.5L14.5 3H9.5L8.5 4H5V6H19V4Z" fill="currentColor"/>';
                html += '</svg>';
                html += '</button>';
                html += '</div>';
                html += '</div>';
            });

            listContainer.innerHTML = html;
        } else {
            listContainer.innerHTML = '<p style="text-align: center; color: var(--text-muted); padding: 2rem;">No faces registered yet</p>';
        }
    } catch (error) {
        hideLoading();
        listContainer.innerHTML = `<p style="text-align: center; color: #f44336; padding: 2rem;">Error loading faces: ${error.message}</p>`;
    }
}

async function deleteFace(faceId, name) {
    if (!confirm(`Are you sure you want to delete ${name}?`)) {
        return;
    }

    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}/delete-face?face_id=${faceId}`, {
            method: 'DELETE'
        });

        const data = await response.json();
        hideLoading();

        if (data.success) {
            loadFacesList();
        } else {
            alert(`Error: ${data.message}`);
        }
    } catch (error) {
        hideLoading();
        alert(`Error: ${error.message}`);
    }
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

function showSuccess(container, message) {
    container.innerHTML = `<div class="result-success"><p>${message}</p></div>`;
    container.style.display = 'block';
}

function showError(container, message) {
    container.innerHTML = `<div class="result-error"><p>❌ ${message}</p></div>`;
    container.style.display = 'block';
}

function showInfo(container, message) {
    container.innerHTML = `<div class="result-info"><p>ℹ️ ${message}</p></div>`;
    container.style.display = 'block';
}
