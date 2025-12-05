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
    document.getElementById('detectBtn').addEventListener('click', (e) => handleDetectFace(e));

    // Save tab
    setupUploadArea('saveUploadArea', 'saveImageInput', 'savePreview', 'saveBtn');
    document.getElementById('saveBtn').addEventListener('click', (e) => handleSaveFace(e));
    document.getElementById('personName').addEventListener('input', validateSaveForm);

    // Recognize tab
    setupUploadArea('recognizeUploadArea', 'recognizeImageInput', 'recognizePreview', 'recognizeBtn');
    document.getElementById('recognizeBtn').addEventListener('click', (e) => handleRecognizeFace(e));

    // Manage tab
    document.getElementById('refreshListBtn').addEventListener('click', loadFacesList);
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

// ============================================
// LOADING OVERLAY
// ============================================

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
    if (event) event.preventDefault();
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
    }

    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        hideLoading();

        if (data.success && data.face_detected) {
            displayDetectionResult(data, mode, resultContainer);
        } else {
            showInfo(resultContainer, data.message || 'No face detected in the image');
        }
    } catch (error) {
        hideLoading();
        showError(resultContainer, `Error: ${error.message}`);
    }
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
    if (mode === 'landmarks' && data.landmarks) {
        html += '<div class="result-item">';
        html += '<span class="result-label">Landmarks Detected:</span>';
        html += `<span class="result-value">Eyes, Nose, Mouth, Face Oval</span>`;
        html += '</div>';
    }

    html += '</div>';
    container.innerHTML = html;
    container.style.display = 'block';
}

// ============================================
// SAVE FACE
// ============================================

async function handleSaveFace(event) {
    if (event) event.preventDefault();
    const imageInput = document.getElementById('saveImageInput');
    const name = document.getElementById('personName').value.trim();
    const email = document.getElementById('personEmail').value.trim();
    const phone = document.getElementById('personPhone').value.trim();
    const resultContainer = document.getElementById('saveResult');

    if (!imageInput.files.length || !name) {
        showError(resultContainer, 'Please provide an image and name');
        return;
    }

    const formData = new FormData();
    formData.append('image', imageInput.files[0]);
    formData.append('name', name);
    if (email) formData.append('email', email);
    if (phone) formData.append('phone', phone);

    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}/save-face`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        hideLoading();

        if (data.success) {
            showSuccess(resultContainer, `✅ ${data.message}<br>Face ID: ${data.face_id}`);
            // Do not auto-reset form so user can see the success message
            // Form can be reset manually or by uploading new image
        } else {
            showError(resultContainer, data.message);
        }
    } catch (error) {
        hideLoading();
        showError(resultContainer, `Error: ${error.message}`);
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
    if (event) event.preventDefault();
    const imageInput = document.getElementById('recognizeImageInput');
    const resultContainer = document.getElementById('recognizeResult');

    if (!imageInput.files.length) {
        showError(resultContainer, 'Please select an image first');
        return;
    }

    const formData = new FormData();
    formData.append('image', imageInput.files[0]);

    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}/recognize-face`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        hideLoading();

        if (data.success && data.recognized) {
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
    } catch (error) {
        hideLoading();
        showError(resultContainer, `Error: ${error.message}`);
    }
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
                html += '<div class="face-card">';
                html += '<div class="face-info">';
                html += `<h3>${face.name}</h3>`;
                html += `<p>ID: ${face.id} | Added: ${new Date(face.created_at).toLocaleDateString()}</p>`;
                if (face.email) html += `<p>Email: ${face.email}</p>`;
                if (face.phone) html += `<p>Phone: ${face.phone}</p>`;
                html += '</div>';
                html += '<div class="face-actions">';
                html += `<button class="btn-icon" onclick="deleteFace(${face.id}, '${face.name}')" title="Delete">`;
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
