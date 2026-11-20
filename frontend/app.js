// AutoVlog Studio - Frontend Client Logic

// ==========================================
// --- Universal Modal Manager & Close Handlers (Top Level) ---
// ==========================================
window.closeInstagramModal = function() {
  const m = document.getElementById('ig-modal-overlay');
  if (m) m.classList.add('hidden');
};
window.closeYouTubeModal = function() {
  const m = document.getElementById('yt-modal-overlay');
  if (m) m.classList.add('hidden');
};
window.closeVideoUpdateModal = function() {
  const m = document.getElementById('video-update-modal');
  if (m) m.classList.add('hidden');
};
window.closeSequenceModal = function() {
  const m = document.getElementById('upload-sequence-modal');
  if (m) m.classList.add('hidden');
  if (typeof pendingBatchFiles !== 'undefined') pendingBatchFiles = [];
  const fi = document.getElementById('file-input');
  if (fi) fi.value = '';
};
window.closeQuickPreviewModal = function() {
  const m = document.getElementById('preview-modal-card');
  if (m) m.classList.add('hidden');
  const player = document.getElementById('quick-preview-player');
  if (player) {
    try { player.pause(); } catch (e) {}
  }
};

// Delegated Global Event Listeners for Instant Closing
document.addEventListener('click', (e) => {
  // 1. Any button with data-close-modal or modal close classes
  const closeBtn = e.target.closest('[data-close-modal], .btn-close-modal, #ig-close-modal-btn, #ig-cancel-modal-btn, #yt-close-modal-btn, #yt-cancel-modal-btn, #close-update-modal-btn, #cancel-update-modal-btn, #close-seq-modal-btn, #cancel-seq-btn, #close-preview-btn');
  if (closeBtn) {
    const targetId = closeBtn.getAttribute('data-close-modal');
    if (targetId) {
      const targetEl = document.getElementById(targetId);
      if (targetEl) targetEl.classList.add('hidden');
    }
    const parentModal = closeBtn.closest('.modal-overlay, .modal-backdrop, .preview-modal-card, #preview-modal-card, #video-update-modal, #ig-modal-overlay, #yt-modal-overlay, #upload-sequence-modal');
    if (parentModal) {
      parentModal.classList.add('hidden');
    }
    return;
  }

  // 2. Click outside modal on dark backdrop
  if (e.target.classList.contains('modal-overlay') || e.target.classList.contains('modal-backdrop')) {
    e.target.classList.add('hidden');
  }
});

// Escape key closes any active modal
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' || e.key === 'Esc') {
    document.querySelectorAll('.modal-overlay, .modal-backdrop, .preview-modal-card, #preview-modal-card').forEach(el => {
      el.classList.add('hidden');
    });
    const player = document.getElementById('quick-preview-player');
    if (player) {
      try { player.pause(); } catch (err) {}
    }
  }
});

let currentClips = [];
let currentPlan = null;
let currentVoiceover = null;
let activePreset = 'fast_reel';
let activeAudioMode = 'mute_all';
let activeVisualFilter = 'beauty_glow';
let activeTransition = 'fade';
let sseEventSource = null;

// Voice recording state
let mediaRecorder = null;
let audioChunks = [];
let recordStartTime = 0;
let recordTimerInterval = null;

// DOM Elements
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const browseBtn = document.getElementById('browse-btn');
const clipsList = document.getElementById('clips-list');
const clipCountLabel = document.getElementById('clip-count-label');
const totalRawDuration = document.getElementById('total-raw-duration');

// Sequence Batch Modal Elements
const uploadSequenceModal = document.getElementById('upload-sequence-modal');
const closeSeqModalBtn = document.getElementById('close-seq-modal-btn');
const cancelSeqBtn = document.getElementById('cancel-seq-btn');
const confirmSeqBtn = document.getElementById('confirm-seq-btn');
const seqSortNameBtn = document.getElementById('seq-sort-name-btn');
const seqReverseBtn = document.getElementById('seq-reverse-btn');
const sequenceQueueList = document.getElementById('sequence-queue-list');
const seqCountLabel = document.getElementById('seq-count-label');
const clearAllClipsBtn = document.getElementById('clear-all-clips-btn');
let pendingBatchFiles = [];

const filterCards = document.querySelectorAll('.filter-card');
const transCards = document.querySelectorAll('.trans-card');
const radioPills = document.querySelectorAll('.radio-pill');
const presetCards = document.querySelectorAll('.preset-card');
const musicSelect = document.getElementById('music-select');
const aspectSelect = document.getElementById('aspect-select');
const showTextOverlaysCheckbox = document.getElementById('show-text-overlays');
const rotateV2hRow = document.getElementById('rotate-v2h-row');
const autoRotateV2hCheckbox = document.getElementById('auto-rotate-v2h');
const musicVolume = document.getElementById('music-volume');
const volumeVal = document.getElementById('volume-val');

// Voiceover Elements
const voTabBtns = document.querySelectorAll('.vo-tab-btn');
const storyTtsInput = document.getElementById('story-tts-input');
const ttsLangSelect = document.getElementById('tts-lang-select');
const ttsVoiceEffect = document.getElementById('tts-voice-effect');
const generateTtsBtn = document.getElementById('generate-tts-btn');

const recordVoBtn = document.getElementById('record-vo-btn');
const recordBtnText = document.getElementById('record-btn-text');
const uploadVoBtn = document.getElementById('upload-vo-btn');
const voiceFileInput = document.getElementById('voice-file-input');
const voActiveBanner = document.getElementById('vo-active-banner');
const voNameLabel = document.getElementById('vo-name-label');
const voEffectLabel = document.getElementById('vo-effect-label');
const morphVoiceSelect = document.getElementById('morph-voice-select');
const applyMorphBtn = document.getElementById('apply-morph-btn');
const voAudioPlayer = document.getElementById('vo-audio-player');
const removeVoBtn = document.getElementById('remove-vo-btn');
const voVolumeRow = document.getElementById('vo-volume-row');
const voiceVolume = document.getElementById('voice-volume');
const voVolVal = document.getElementById('vo-vol-val');
const voStatusBadge = document.getElementById('vo-status-badge');

const quickPreviewBtn = document.getElementById('quick-preview-btn');
const previewModalCard = document.getElementById('preview-modal-card');
const quickPreviewPlayer = document.getElementById('quick-preview-player');
const previewMetaDesc = document.getElementById('preview-meta-desc');
const closePreviewBtn = document.getElementById('close-preview-btn');

const replanBtn = document.getElementById('replan-btn');
const storySummaryText = document.getElementById('story-summary-text');
const timelineContainer = document.getElementById('timeline-container');
const estDurationBadge = document.getElementById('est-duration-badge');
const renderBtn = document.getElementById('render-btn');

const progressBox = document.getElementById('progress-box');
const progressStatusTitle = document.getElementById('progress-status-title');
const progressPercentage = document.getElementById('progress-percentage');
const progressBarFill = document.getElementById('progress-bar-fill');
const progressLogMessage = document.getElementById('progress-log-message');

const outputCard = document.getElementById('output-card');
const finalVideoPlayer = document.getElementById('final-video-player');
const downloadVlogBtn = document.getElementById('download-vlog-btn');

function setupEventListeners() {
  // Drag & Drop
  browseBtn.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', handleFileInput);

  ['dragenter', 'dragover'].forEach(name => {
    dropZone.addEventListener(name, (e) => {
      e.preventDefault();
      dropZone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(name => {
    dropZone.addEventListener(name, (e) => {
      e.preventDefault();
      dropZone.classList.remove('dragover');
    });
  });

  dropZone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = Array.from(dt.files || []);
    if (files.length > 1) {
      openSequenceModal(files);
    } else if (files.length === 1) {
      uploadFiles(files);
    }
  });

  const quickFilterSelect = document.getElementById('quick-filter-select');
  const outFilterSelect = document.getElementById('out-filter-select');
  const quickTransSelect = document.getElementById('quick-trans-select');
  const outTransSelect = document.getElementById('out-trans-select');
  const quickMusicSelect = document.getElementById('quick-music-select');
  const outMusicSelect = document.getElementById('out-music-select');
  const modalMusicSelect = document.getElementById('modal-music-select');
  const quickResSelect = document.getElementById('quick-res-select');
  const resolutionSelect = document.getElementById('resolution-select');
  const modalResSelect = document.getElementById('modal-res-select');
  const modalAspectSelect = document.getElementById('modal-aspect-select');

  const videoUpdateModal = document.getElementById('video-update-modal');
  const openUpdateModalBtn = document.getElementById('open-update-modal-btn');
  const closeUpdateModalBtn = document.getElementById('close-update-modal-btn');
  const cancelUpdateModalBtn = document.getElementById('cancel-update-modal-btn');
  const modalReRenderBtn = document.getElementById('modal-re-render-btn');
  const modalOpenTimelineBtn = document.getElementById('modal-open-timeline-btn');
  const editVlogBtn = document.getElementById('edit-vlog-btn');
  const modalFilterCards = document.querySelectorAll('#modal-filter-cards .filter-card');
  const modalTransCards = document.querySelectorAll('#modal-trans-cards .trans-card');

  function openVideoUpdateModal() {
    if (videoUpdateModal) {
      videoUpdateModal.classList.remove('hidden');
    }
  }

  function closeVideoUpdateModal() {
    if (videoUpdateModal) {
      videoUpdateModal.classList.add('hidden');
    }
  }

  function scrollToEditorAndHighlight() {
    closeVideoUpdateModal();
    const storySection = document.getElementById('story-arc-section');
    const quickBar = document.getElementById('quick-effects-bar');
    if (storySection) {
      storySection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      storySection.classList.remove('editor-pulse-highlight');
      if (quickBar) quickBar.classList.remove('editor-pulse-highlight');
      void storySection.offsetWidth;
      storySection.classList.add('editor-pulse-highlight');
      if (quickBar) quickBar.classList.add('editor-pulse-highlight');
      setTimeout(() => {
        storySection.classList.remove('editor-pulse-highlight');
        if (quickBar) quickBar.classList.remove('editor-pulse-highlight');
      }, 2800);
    }
  }

  window.openVideoUpdateModal = openVideoUpdateModal;
  window.closeVideoUpdateModal = closeVideoUpdateModal;
  window.scrollToEditorAndHighlight = scrollToEditorAndHighlight;

  if (openUpdateModalBtn) {
    openUpdateModalBtn.addEventListener('click', openVideoUpdateModal);
  }
  if (closeUpdateModalBtn) {
    closeUpdateModalBtn.addEventListener('click', closeVideoUpdateModal);
  }
  if (cancelUpdateModalBtn) {
    cancelUpdateModalBtn.addEventListener('click', closeVideoUpdateModal);
  }
  if (videoUpdateModal) {
    videoUpdateModal.addEventListener('click', (e) => {
      if (e.target === videoUpdateModal) closeVideoUpdateModal();
    });
  }
  if (modalOpenTimelineBtn) {
    modalOpenTimelineBtn.addEventListener('click', () => {
      closeVideoUpdateModal();
      scrollToEditorAndHighlight();
    });
  }
  if (editVlogBtn) {
    editVlogBtn.addEventListener('click', scrollToEditorAndHighlight);
  }
  if (modalReRenderBtn) {
    modalReRenderBtn.addEventListener('click', () => {
      closeVideoUpdateModal();
      startRendering();
    });
  }

  function setVisualFilter(filterVal) {
    activeVisualFilter = filterVal;
    filterCards.forEach(c => {
      c.classList.toggle('active', c.dataset.filter === filterVal);
    });
    modalFilterCards.forEach(c => {
      c.classList.toggle('active', c.dataset.filter === filterVal);
    });
    if (quickFilterSelect) quickFilterSelect.value = filterVal;
    if (outFilterSelect) outFilterSelect.value = filterVal;
  }

  function setTransition(transVal) {
    activeTransition = transVal;
    transCards.forEach(c => {
      c.classList.toggle('active', c.dataset.trans === transVal);
    });
    modalTransCards.forEach(c => {
      c.classList.toggle('active', c.dataset.trans === transVal);
    });
    if (quickTransSelect) quickTransSelect.value = transVal;
    if (outTransSelect) outTransSelect.value = transVal;
  }

  function setMusicTrack(trackId) {
    if (musicSelect) musicSelect.value = trackId;
    if (quickMusicSelect) quickMusicSelect.value = trackId;
    if (outMusicSelect) outMusicSelect.value = trackId;
    if (modalMusicSelect) modalMusicSelect.value = trackId;
  }

  function setResolution(resVal) {
    if (resolutionSelect) resolutionSelect.value = resVal;
    if (quickResSelect) quickResSelect.value = resVal;
    if (modalResSelect) modalResSelect.value = resVal;
  }

  function setAspect(aspectVal) {
    if (aspectSelect) aspectSelect.value = aspectVal;
    if (modalAspectSelect) modalAspectSelect.value = aspectVal;
    if (aspectVal === '16:9') {
      rotateV2hRow.classList.remove('hidden');
    } else {
      rotateV2hRow.classList.add('hidden');
    }
  }

  // Beauty & Visual Filters Grid
  filterCards.forEach(card => {
    card.addEventListener('click', () => {
      setVisualFilter(card.dataset.filter);
    });
  });

  modalFilterCards.forEach(card => {
    card.addEventListener('click', () => {
      setVisualFilter(card.dataset.filter);
    });
  });

  if (quickFilterSelect) {
    quickFilterSelect.addEventListener('change', (e) => setVisualFilter(e.target.value));
  }
  if (outFilterSelect) {
    outFilterSelect.addEventListener('change', (e) => setVisualFilter(e.target.value));
  }

  // Transitions Grid
  transCards.forEach(card => {
    card.addEventListener('click', () => {
      setTransition(card.dataset.trans);
    });
  });

  modalTransCards.forEach(card => {
    card.addEventListener('click', () => {
      setTransition(card.dataset.trans);
    });
  });

  if (quickTransSelect) {
    quickTransSelect.addEventListener('change', (e) => setTransition(e.target.value));
  }
  if (outTransSelect) {
    outTransSelect.addEventListener('change', (e) => setTransition(e.target.value));
  }

  // Music Selectors
  if (musicSelect) {
    musicSelect.addEventListener('change', (e) => setMusicTrack(e.target.value));
  }
  if (quickMusicSelect) {
    quickMusicSelect.addEventListener('change', (e) => setMusicTrack(e.target.value));
  }
  if (outMusicSelect) {
    outMusicSelect.addEventListener('change', (e) => setMusicTrack(e.target.value));
  }
  if (modalMusicSelect) {
    modalMusicSelect.addEventListener('change', (e) => setMusicTrack(e.target.value));
  }

  // Resolution Selectors
  if (resolutionSelect) {
    resolutionSelect.addEventListener('change', (e) => setResolution(e.target.value));
  }
  if (quickResSelect) {
    quickResSelect.addEventListener('change', (e) => setResolution(e.target.value));
  }
  if (modalResSelect) {
    modalResSelect.addEventListener('change', (e) => setResolution(e.target.value));
  }

  // Modal Aspect Selector
  if (modalAspectSelect) {
    modalAspectSelect.addEventListener('change', (e) => {
      setAspect(e.target.value);
      generatePlan();
    });
  }

  // Audio Mode Selector
  radioPills.forEach(pill => {
    pill.addEventListener('click', () => {
      radioPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      const input = pill.querySelector('input');
      input.checked = true;
      activeAudioMode = input.value;
      generatePlan();
    });
  });

  // Presets
  presetCards.forEach(card => {
    card.addEventListener('click', () => {
      presetCards.forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      activePreset = card.dataset.preset;
      generatePlan();
    });
  });

  // Aspect Ratio change
  aspectSelect.addEventListener('change', (e) => {
    setAspect(e.target.value);
    generatePlan();
  });

  // Volume slider
  musicVolume.addEventListener('input', (e) => {
    volumeVal.textContent = `${e.target.value}%`;
  });

  // Voiceover Volume slider
  voiceVolume.addEventListener('input', (e) => {
    voVolVal.textContent = `${e.target.value}%`;
  });

  // Voiceover Tabs
  voTabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      voTabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const targetTab = btn.dataset.tab;
      document.querySelectorAll('.vo-tab-pane').forEach(pane => {
        if (pane.id === `tab-${targetTab}`) {
          pane.classList.remove('hidden');
        } else {
          pane.classList.add('hidden');
        }
      });
    });
  });

  // AI Story to Funny Voice TTS Generation
  if (generateTtsBtn) {
    generateTtsBtn.addEventListener('click', handleGenerateTts);
  }

  // Live Morph Character Effect
  if (applyMorphBtn) {
    applyMorphBtn.addEventListener('click', handleApplyMorph);
  }

  // Voiceover Record & Upload Handlers
  recordVoBtn.addEventListener('click', toggleVoiceRecording);
  uploadVoBtn.addEventListener('click', () => voiceFileInput.click());
  voiceFileInput.addEventListener('change', handleVoiceFileInput);
  removeVoBtn.addEventListener('click', deleteVoiceover);

  // Quick 3s Preview Button
  quickPreviewBtn.addEventListener('click', () => triggerQuickPreview());
  closePreviewBtn.addEventListener('click', () => previewModalCard.classList.add('hidden'));

  // Re-plan button
  replanBtn.addEventListener('click', () => generatePlan());

  // Master Render Button
  renderBtn.addEventListener('click', () => startRendering());

  // Batch Sequence Modal Buttons
  if (closeSeqModalBtn) closeSeqModalBtn.addEventListener('click', closeSequenceModal);
  if (cancelSeqBtn) cancelSeqBtn.addEventListener('click', closeSequenceModal);
  if (confirmSeqBtn) confirmSeqBtn.addEventListener('click', () => {
    if (pendingBatchFiles.length > 0) {
      const filesToUpload = [...pendingBatchFiles];
      closeSequenceModal();
      uploadFiles(filesToUpload);
    }
  });
  if (seqSortNameBtn) seqSortNameBtn.addEventListener('click', () => {
    pendingBatchFiles.sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' }));
    renderSequenceQueue();
  });
  if (seqReverseBtn) seqReverseBtn.addEventListener('click', () => {
    pendingBatchFiles.reverse();
    renderSequenceQueue();
  });
  if (clearAllClipsBtn) clearAllClipsBtn.addEventListener('click', clearAllClips);
}

async function loadInitialState() {
  try {
    const statusRes = await fetch('/api/status');
    const statusData = await statusRes.json();
    if (statusData.current_voiceover) {
      currentVoiceover = statusData.current_voiceover;
      showVoiceoverBanner(currentVoiceover);
    }

    const res = await fetch('/api/clips');
    const clips = await res.json();
    currentClips = clips;
    renderClipsList();
    if (clips.length > 0) {
      generatePlan();
    }
    initAutoSave();
  } catch (err) {
    console.error('Failed to load initial state:', err);
  }
}

function initAutoSave() {
  const storyInput = document.getElementById('story-tts-input');
  if (storyInput) {
    const saved = localStorage.getItem('autovlog_saved_story');
    if (saved && !storyInput.value.trim()) {
      storyInput.value = saved;
    }
    storyInput.addEventListener('input', () => {
      localStorage.setItem('autovlog_saved_story', storyInput.value);
    });
  }
}

// --- Upload Handling ---
function handleFileInput(e) {
  const files = Array.from(e.target.files || []);
  if (files.length === 0) return;
  if (files.length > 1) {
    openSequenceModal(files);
  } else {
    uploadFiles(files);
  }
}

function openSequenceModal(files) {
  // Natural alphanumeric sort by default (e.g., 1.mp4, 2.mp4, 10.mp4)
  pendingBatchFiles = [...files].sort((a, b) =>
    a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' })
  );
  renderSequenceQueue();
  if (uploadSequenceModal) uploadSequenceModal.classList.remove('hidden');
}

function closeSequenceModal() {
  if (uploadSequenceModal) uploadSequenceModal.classList.add('hidden');
  pendingBatchFiles = [];
  fileInput.value = '';
}

function renderSequenceQueue() {
  if (!sequenceQueueList) return;
  sequenceQueueList.innerHTML = '';
  if (seqCountLabel) seqCountLabel.textContent = `${pendingBatchFiles.length} Clips in sequence`;

  pendingBatchFiles.forEach((file, index) => {
    const item = document.createElement('div');
    item.className = 'seq-item';
    const sizeMb = (file.size / (1024 * 1024)).toFixed(1);

    item.innerHTML = `
      <span class="seq-handle">⋮⋮</span>
      <span class="seq-num-badge">#${index + 1}</span>
      <span class="seq-name" title="${file.name}">${file.name}</span>
      <span class="seq-size">${sizeMb} MB</span>
      <div class="seq-reorder-btns">
        <button type="button" class="btn-seq-move" onclick="moveSeqItemUp(${index})" ${index === 0 ? 'disabled' : ''} title="Move Up in sequence">▲</button>
        <button type="button" class="btn-seq-move" onclick="moveSeqItemDown(${index})" ${index === pendingBatchFiles.length - 1 ? 'disabled' : ''} title="Move Down in sequence">▼</button>
      </div>
    `;
    sequenceQueueList.appendChild(item);
  });
}

function moveSeqItemUp(idx) {
  if (idx <= 0) return;
  const temp = pendingBatchFiles[idx];
  pendingBatchFiles[idx] = pendingBatchFiles[idx - 1];
  pendingBatchFiles[idx - 1] = temp;
  renderSequenceQueue();
}

function moveSeqItemDown(idx) {
  if (idx >= pendingBatchFiles.length - 1) return;
  const temp = pendingBatchFiles[idx];
  pendingBatchFiles[idx] = pendingBatchFiles[idx + 1];
  pendingBatchFiles[idx + 1] = temp;
  renderSequenceQueue();
}

window.moveSeqItemUp = moveSeqItemUp;
window.moveSeqItemDown = moveSeqItemDown;

async function clearAllClips() {
  if (currentClips.length === 0) return;
  if (!confirm('Are you sure you want to clear all uploaded clips and start fresh?')) return;

  try {
    const res = await fetch('/api/clips/clear', { method: 'POST' });
    const data = await res.json();
    if (data.status === 'success') {
      currentClips = [];
      currentPlan = null;
      renderClipsList();
      renderTimeline();
    }
  } catch (err) {
    alert('Failed to clear clips: ' + err.message);
  }
}

async function uploadFiles(fileList) {
  const formData = new FormData();
  for (let i = 0; i < fileList.length; i++) {
    formData.append('files', fileList[i]);
  }

  dropZone.classList.add('uploading');
  dropZone.querySelector('.drop-title').textContent = `Analyzing ${fileList.length} clips and preserving selection sequence...`;

  try {
    const res = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (data.status === 'success') {
      currentClips = data.clips;
      renderClipsList();
      generatePlan();
    }
  } catch (err) {
    alert('Failed to upload video clips: ' + err.message);
  } finally {
    dropZone.classList.remove('uploading');
    dropZone.querySelector('.drop-title').textContent = 'Drag & drop raw clips here';
    fileInput.value = '';
  }
}

async function rotateClip(clipId) {
  try {
    const res = await fetch(`/api/clips/${clipId}/rotate`, { method: 'POST' });
    const data = await res.json();
    if (data.status === 'success') {
      const clip = currentClips.find(c => c.id === clipId);
      if (clip) {
        clip.rotation = data.rotation;
        clip.is_vertical = data.is_vertical;
      }
      renderClipsList();
      generatePlan();
    }
  } catch (err) {
    console.error('Rotate failed:', err);
  }
}

async function deleteClip(clipId) {
  try {
    const res = await fetch(`/api/clips/${clipId}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.status === 'success') {
      currentClips = currentClips.filter(c => c.id !== clipId);
      renderClipsList();
      if (currentClips.length > 0) {
        generatePlan();
      } else {
        currentPlan = null;
        renderTimeline();
      }
    }
  } catch (err) {
    console.error('Delete clip failed:', err);
  }
}

// --- Rendering UI Lists ---
function renderClipsList() {
  clipCountLabel.textContent = `${currentClips.length} Clip${currentClips.length === 1 ? '' : 's'} Loaded`;
  
  const totalSeconds = currentClips.reduce((acc, c) => acc + (c.duration || 0), 0);
  const mins = Math.floor(totalSeconds / 60);
  const secs = Math.floor(totalSeconds % 60);
  totalRawDuration.textContent = `${mins}:${secs < 10 ? '0' : ''}${secs} Raw`;

  if (currentClips.length === 0) {
    clipsList.innerHTML = `
      <div class="empty-state">
        <p>No video clips added yet. Drop clips above to get started.</p>
      </div>
    `;
    renderBtn.disabled = true;
    quickPreviewBtn.disabled = true;
    return;
  }

  quickPreviewBtn.disabled = false;
  clipsList.innerHTML = '';
  currentClips.forEach(clip => {
    const card = document.createElement('div');
    card.className = 'clip-card';
    
    const tag = clip.is_vertical ? '9:16 VERTICAL' : '16:9 WIDE';
    const tagColor = clip.is_vertical ? 'rgba(168, 85, 247, 0.85)' : 'rgba(6, 182, 212, 0.85)';
    const rot = clip.rotation || 0;

    card.innerHTML = `
      <div class="clip-thumb-wrap">
        <img src="${clip.thumbnail_url}" alt="${clip.filename}" style="transform: rotate(${rot}deg)" onerror="this.src='/static/thumb-placeholder.png'">
        <span class="clip-duration-badge">${Math.round(clip.duration)}s</span>
        <span class="clip-tag-badge" style="background: ${tagColor}">${tag}</span>
        <div class="clip-actions-overlay">
          <button class="clip-action-btn" title="Rotate 90°" onclick="rotateClip('${clip.id}')">🔄</button>
          <button class="clip-action-btn delete" title="Remove clip" onclick="deleteClip('${clip.id}')">✕</button>
        </div>
      </div>
      <div class="clip-info">
        <div class="clip-name" title="${clip.filename}">${clip.filename}</div>
      </div>
    `;
    clipsList.appendChild(card);
  });
}

// --- Story Planning ---
async function generatePlan() {
  if (currentClips.length === 0) return;

  storySummaryText.textContent = 'Generating AI storyline arc and calculating smart speed ramping...';

  try {
    const res = await fetch('/api/plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        preset: activePreset,
        audio_mode: activeAudioMode,
        aspect_ratio: aspectSelect.value
      })
    });
    const plan = await res.json();
    currentPlan = plan;
    renderTimeline();
  } catch (err) {
    console.error('Failed to generate story plan:', err);
    storySummaryText.textContent = 'Failed to generate story plan.';
  }
}

function updateTimelineDurations() {
  if (!currentPlan || !currentPlan.timeline) return;
  const totalSecs = currentPlan.timeline.reduce((acc, item) => acc + (item.final_duration || 0), 0);
  currentPlan.estimated_total_duration = Math.round(totalSecs * 10) / 10;
  estDurationBadge.textContent = `~${currentPlan.estimated_total_duration}s`;
}

let draggedIndex = null;

function saveCurrentTextareaInputs() {
  if (!currentPlan || !currentPlan.timeline) return;
  currentPlan.timeline.forEach((item, idx) => {
    const el = document.getElementById(`clip-script-${idx}`);
    if (el) {
      item.voiceover_text = el.value;
    }
  });
}

async function syncReorderedClipsToBackend() {
  if (!currentPlan || !currentPlan.timeline) return;
  try {
    const clipIds = currentPlan.timeline.map(item => item.id);
    await fetch('/api/clips/reorder', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        clip_ids: clipIds,
        timeline: currentPlan.timeline
      })
    });
    const clipMap = new Map(currentClips.map(c => [c.id, c]));
    currentClips = clipIds.map(id => clipMap.get(id)).filter(Boolean);
  } catch (err) {
    console.error('Failed to sync reorder to backend:', err);
  }
}

function moveClipUp(index) {
  if (!currentPlan || !currentPlan.timeline || index <= 0) return;
  saveCurrentTextareaInputs();
  
  const temp = currentPlan.timeline[index];
  currentPlan.timeline[index] = currentPlan.timeline[index - 1];
  currentPlan.timeline[index - 1] = temp;
  
  currentPlan.timeline.forEach((item, i) => { item.order = i; });
  renderTimeline();
  syncReorderedClipsToBackend();
}

function moveClipDown(index) {
  if (!currentPlan || !currentPlan.timeline || index >= currentPlan.timeline.length - 1) return;
  saveCurrentTextareaInputs();
  
  const temp = currentPlan.timeline[index];
  currentPlan.timeline[index] = currentPlan.timeline[index + 1];
  currentPlan.timeline[index + 1] = temp;
  
  currentPlan.timeline.forEach((item, i) => { item.order = i; });
  renderTimeline();
  syncReorderedClipsToBackend();
}

window.moveClipUp = moveClipUp;
window.moveClipDown = moveClipDown;

function renderTimeline() {
  if (!currentPlan || !currentPlan.timeline || currentPlan.timeline.length === 0) {
    timelineContainer.innerHTML = `
      <div class="empty-timeline">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"></rect>
          <line x1="7" y1="2" x2="7" y2="22"></line>
          <line x1="17" y1="2" x2="17" y2="22"></line>
          <line x1="2" y1="12" x2="22" y2="12"></line>
        </svg>
        <p>Your structured timeline chapters will appear here</p>
      </div>
    `;
    storySummaryText.textContent = "Add your clips to let the local AI craft today's vlog story.";
    estDurationBadge.textContent = '~0.0s';
    renderBtn.disabled = true;
    return;
  }

  storySummaryText.textContent = currentPlan.story_summary;
  estDurationBadge.textContent = `~${currentPlan.estimated_total_duration}s`;
  renderBtn.disabled = false;

  timelineContainer.innerHTML = '';
  currentPlan.timeline.forEach((item, index) => {
    const row = document.createElement('div');
    row.className = 'timeline-item';
    row.id = `timeline-card-${index}`;
    row.setAttribute('draggable', 'true');

    const rawDur = Math.max(0.5, (item.end_time || 5.0) - (item.start_time || 0.0));
    const hasVo = Boolean(item.voiceover_duration && item.voiceover_duration > 0.2);

    const standardSpeeds = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0];
    let allSpeeds = [...standardSpeeds];
    if (item.speed_multiplier && !allSpeeds.some(s => Math.abs(s - item.speed_multiplier) < 0.04)) {
      allSpeeds.push(item.speed_multiplier);
      allSpeeds.sort((a, b) => a - b);
    }

    const speedOptions = allSpeeds.map(s => {
      const isSelected = Math.abs((item.speed_multiplier || 1.0) - s) < 0.04;
      const isCustom = !standardSpeeds.includes(s);
      return `<option value="${s}" ${isSelected ? 'selected' : ''}>${s}x Speed ${isCustom ? '(Auto Synced)' : ''}</option>`;
    }).join('');

    const currentClipFilter = item.visual_filter || 'global';
    const filterOptions = `
      <option value="global" ${currentClipFilter === 'global' ? 'selected' : ''}>🌐 Global Filter</option>
      <option value="beauty_glow" ${currentClipFilter === 'beauty_glow' ? 'selected' : ''}>✨ Beauty Face Glow</option>
      <option value="warm_golden" ${currentClipFilter === 'warm_golden' ? 'selected' : ''}>🌅 Golden Hour</option>
      <option value="cinematic_teal_orange" ${currentClipFilter === 'cinematic_teal_orange' ? 'selected' : ''}>🎬 Hollywood Teal & Orange</option>
      <option value="vivid_punch" ${currentClipFilter === 'vivid_punch' ? 'selected' : ''}>💎 Vivid HDR Pop</option>
      <option value="cozy_lofi" ${currentClipFilter === 'cozy_lofi' ? 'selected' : ''}>☕ Cozy Lo-Fi Film</option>
      <option value="natural_clean" ${currentClipFilter === 'natural_clean' ? 'selected' : ''}>🌿 Clean Natural</option>
      <option value="none" ${currentClipFilter === 'none' ? 'selected' : ''}>🚫 Original / Raw</option>
    `;

    const clipMaxDur = Math.round((item.duration || 60) * 10) / 10;
    const clipStartTime = Math.round((item.start_time || 0.0) * 10) / 10;
    const clipEndTime = Math.round((item.end_time || item.duration || 5.0) * 10) / 10;

    row.innerHTML = `
      <!-- Top Row: Move Buttons, Thumbnail, Info, Speeds & Clip Actions -->
      <div class="timeline-top-row">
        <!-- Reorder / Swipe Controls -->
        <div class="timeline-reorder-col">
          <button type="button" class="btn-reorder" onclick="moveClipUp(${index})" ${index === 0 ? 'disabled' : ''} title="Move Clip Up (Shift Earlier in Vlog)">
            ▲
          </button>
          <span class="timeline-drag-handle" title="Drag and Swipe to reorder">⋮⋮</span>
          <button type="button" class="btn-reorder" onclick="moveClipDown(${index})" ${index === currentPlan.timeline.length - 1 ? 'disabled' : ''} title="Move Clip Down (Shift Later in Vlog)">
            ▼
          </button>
        </div>

        <div class="timeline-thumb-col">
          <img src="${item.thumbnail_url}" class="timeline-thumb" alt="thumb" style="transform: rotate(${item.rotation || 0}deg)" onerror="this.src='/static/thumb-placeholder.png'">
          <span class="timeline-clip-num">#${index + 1}</span>
        </div>
        
        <div class="timeline-header-info">
          <div class="timeline-title-row">
            <span class="timeline-role-badge role-${item.role}">${item.role_label}</span>
            <span class="timeline-filename-pill" title="${item.filename}">${item.filename}</span>
            
            <div class="timeline-quick-actions">
              <button type="button" class="btn-clip-mini-action" onclick="triggerReplaceClip(${index})" title="Replace this video with another file while keeping script & voice">
                <span>🔄 Swap</span>
              </button>
              <button type="button" class="btn-clip-mini-action btn-clip-del" onclick="deleteSingleClip(${index})" title="Delete this clip from timeline">
                <span>🗑️</span>
              </button>
            </div>
          </div>
          
          <div class="timeline-speed-row">
            <label class="timeline-speed-label">⚡ Speed:</label>
            <select class="timeline-speed-select" data-index="${index}" id="speed-select-${index}" title="Video Speed Multiplier">
              ${speedOptions}
            </select>
            <span class="timeline-sync-tag ${hasVo ? '' : 'hidden'}" id="sync-tag-${index}">🎯 Synced (${item.final_duration}s)</span>
          </div>
        </div>

        <div class="timeline-meta-col">
          <div class="duration-tag" id="dur-tag-${index}">⏱️ ${item.final_duration}s</div>
          <div class="raw-tag" id="raw-tag-${index}">Raw: ${Math.round(rawDur * 10) / 10}s</div>
        </div>
      </div>

      <!-- Middle Row: Per-Clip Visual Filter & Trim Range Toolbar -->
      <div class="clip-custom-toolbar">
        <div class="clip-filter-box">
          <label class="clip-tool-label">🎨 Clip Filter:</label>
          <select class="custom-select-xs clip-filter-select" data-index="${index}" id="clip-filter-${index}">
            ${filterOptions}
          </select>
        </div>

        <div class="clip-trim-box">
          <label class="clip-tool-label">✂️ Trim (s):</label>
          <input type="number" step="0.1" min="0" max="${clipMaxDur}" value="${clipStartTime}" class="clip-trim-input" data-index="${index}" id="trim-start-${index}" title="Clip start time in seconds">
          <span class="trim-sep">to</span>
          <input type="number" step="0.1" min="0.5" max="${clipMaxDur}" value="${clipEndTime}" class="clip-trim-input" data-index="${index}" id="trim-end-${index}" title="Clip end time in seconds">
          <button type="button" class="btn-clip-apply-trim" onclick="applyClipTrim(${index})" title="Apply trim range">✓</button>
        </div>
      </div>

      <!-- Dedicated Per-Clip Script & Voiceover Studio Box -->
      <div class="clip-voice-box">
        <div class="clip-voice-header flex-between">
          <div class="clip-voice-title-wrap">
            <span class="clip-voice-label">🎙️ या क्लिपसाठी संवाद / Script for this Clip:</span>
            <span class="clip-char-count" id="char-count-${index}">${(item.voiceover_text || '').length} chars</span>
          </div>
          <div class="clip-stt-wrap">
            <button type="button" id="btn-clip-mic-${index}" class="btn-clip-mic-sm" onclick="triggerClipSTT(${index})" title="Speak to auto-type for this clip (बोलून टाईप करा)">
              <span>🎙️ Speak</span>
            </button>
            <button type="button" id="btn-clip-trans-${index}" class="btn-clip-trans-sm" onclick="transliterateClipScript(${index})" title="Convert typed English/Roman words to Marathi Devanagari">
              <span>🔤 मराठी</span>
            </button>
            <span id="clip-stt-badge-${index}" class="badge-listening-sm hidden">🔴 Listening...</span>
          </div>
        </div>

        <textarea 
          id="clip-script-${index}" 
          class="clip-script-textarea" 
          rows="2" 
          placeholder="उदा: 'Aaj mi office la lavakar gelo' टाईप करा, ते आपोआप मराठी होईल किंवा 🎙️ Speak बटण दाबून बोला..."
          data-index="${index}"
        >${item.voiceover_text || ''}</textarea>

        <div class="clip-voice-toolbar">
          <div class="clip-voice-options">
            <select id="clip-lang-${index}" class="custom-select-xs" title="Select Voice Language">
              <option value="mr" ${item.voiceover_lang === 'mr' || !item.voiceover_lang ? 'selected' : ''}>मराठी (Marathi)</option>
              <option value="hi" ${item.voiceover_lang === 'hi' ? 'selected' : ''}>हिंदी (Hindi)</option>
              <option value="en" ${item.voiceover_lang === 'en' ? 'selected' : ''}>English</option>
            </select>

            <select id="clip-effect-${index}" class="custom-select-xs" title="Select Heavy Cartoon Character Voice">
              <option value="gian_classic" ${item.voiceover_effect === 'gian_classic' || !item.voiceover_effect ? 'selected' : ''}>🦍 Gian (जाड व भारी आवाज)</option>
              <option value="motu_chubby_cartoon" ${item.voiceover_effect === 'motu_chubby_cartoon' ? 'selected' : ''}>🍔 Motu (जाडजूड कार्टून)</option>
              <option value="kalia_pehelwan" ${item.voiceover_effect === 'kalia_pehelwan' ? 'selected' : ''}>🦁 Kalia Pehelwan (दबंग कालिया)</option>
              <option value="oggy_bob_heavy" ${item.voiceover_effect === 'oggy_bob_heavy' ? 'selected' : ''}>🐶 Bob The Bulldog (बॉब कुत्रा)</option>
              <option value="chingum_heavy_cop" ${item.voiceover_effect === 'chingum_heavy_cop' ? 'selected' : ''}>👮 Inspector Chingum (दबंग इन्स्पेक्टर)</option>
              <option value="cartoon_iron_giant" ${item.voiceover_effect === 'cartoon_iron_giant' ? 'selected' : ''}>🤖 Iron Giant (राक्षसी रोबोट)</option>
            </select>
          </div>

          <button 
            type="button" 
            id="btn-gen-clip-voice-${index}" 
            class="btn-clip-generate-voice" 
            onclick="generateClipVoice(${index})"
            title="Convert this text to audio and automatically scale this clip speed"
          >
            <span>✨ Convert to Audio</span>
          </button>
        </div>

        <!-- Mini Audio Player & Speed Auto-Scale Row -->
        <div id="clip-audio-row-${index}" class="clip-audio-player-row ${hasVo ? '' : 'hidden'}">
          <div class="clip-audio-meta">
            <span class="clip-audio-icon">🔊</span>
            <span class="clip-audio-duration" id="clip-vo-dur-${index}">Voice: ${item.voiceover_duration ? Math.round(item.voiceover_duration * 10) / 10 : 0}s</span>
          </div>
          <audio id="clip-audio-player-${index}" controls src="${item.voiceover_url || ''}" class="clip-mini-audio" preload="none"></audio>
          <button type="button" class="btn-remove-clip-vo" title="Remove voice from this clip" onclick="deleteClipVoice(${index})">✕</button>
        </div>
      </div>
    `;

    // Drag-and-Drop Event Listeners for Swiping/Reordering
    row.addEventListener('dragstart', (e) => {
      saveCurrentTextareaInputs();
      draggedIndex = index;
      row.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', String(index));
    });

    row.addEventListener('dragend', () => {
      row.classList.remove('dragging');
      document.querySelectorAll('.timeline-item').forEach(el => el.classList.remove('drag-over'));
    });

    row.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      row.classList.add('drag-over');
    });

    row.addEventListener('dragleave', () => {
      row.classList.remove('drag-over');
    });

    row.addEventListener('drop', (e) => {
      e.preventDefault();
      row.classList.remove('drag-over');
      if (draggedIndex === null || draggedIndex === index) return;
      
      saveCurrentTextareaInputs();
      const movedItem = currentPlan.timeline.splice(draggedIndex, 1)[0];
      currentPlan.timeline.splice(index, 0, movedItem);
      currentPlan.timeline.forEach((itm, i) => { itm.order = i; });
      draggedIndex = null;
      renderTimeline();
      syncReorderedClipsToBackend();
    });

    // Speed Select Listener
    const speedSelect = row.querySelector('.timeline-speed-select');
    speedSelect.addEventListener('change', (e) => {
      const idx = parseInt(e.target.dataset.index);
      const newSpeed = parseFloat(e.target.value);
      currentPlan.timeline[idx].speed_multiplier = newSpeed;
      
      const rDur = Math.max(0.5, (currentPlan.timeline[idx].end_time || 5.0) - (currentPlan.timeline[idx].start_time || 0.0));
      const newFinalDur = Math.max(0.5, Math.round((rDur / newSpeed) * 10) / 10);
      currentPlan.timeline[idx].final_duration = newFinalDur;

      const durTag = document.getElementById(`dur-tag-${idx}`);
      if (durTag) durTag.textContent = `⏱️ ${newFinalDur}s`;
      updateTimelineDurations();
      syncReorderedClipsToBackend();
    });

    // Clip Filter Select Listener
    const clipFilterSelect = row.querySelector('.clip-filter-select');
    if (clipFilterSelect) {
      clipFilterSelect.addEventListener('change', (e) => {
        const idx = parseInt(e.target.dataset.index);
        currentPlan.timeline[idx].visual_filter = e.target.value;
        syncReorderedClipsToBackend();
      });
    }

    // Script Textarea Input Listener
    const scriptTextarea = row.querySelector('.clip-script-textarea');
    if (scriptTextarea) {
      scriptTextarea.addEventListener('input', (e) => {
        const idx = parseInt(e.target.dataset.index);
        currentPlan.timeline[idx].voiceover_text = e.target.value;
        const charCountEl = document.getElementById(`char-count-${idx}`);
        if (charCountEl) {
          charCountEl.textContent = `${e.target.value.length} chars`;
        }
      });
    }

    timelineContainer.appendChild(row);
  });
}

async function generateClipVoice(index) {
  if (!currentPlan || !currentPlan.timeline || !currentPlan.timeline[index]) return;
  const item = currentPlan.timeline[index];
  const clipId = item.id;

  const scriptInput = document.getElementById(`clip-script-${index}`);
  const text = scriptInput ? scriptInput.value.trim() : '';
  if (!text) {
    alert('या क्लिपसाठी संवाद / मजकूर टाईप किंवा पेस्ट करा (Please enter or paste script text for this clip).');
    if (scriptInput) scriptInput.focus();
    return;
  }

  const langSelect = document.getElementById(`clip-lang-${index}`);
  const effectSelect = document.getElementById(`clip-effect-${index}`);
  const btn = document.getElementById(`btn-gen-clip-voice-${index}`);

  const lang = langSelect ? langSelect.value : 'mr';
  const voiceEffect = effectSelect ? effectSelect.value : 'gian_classic';

  const origBtnHtml = btn ? btn.innerHTML : '';
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span>⏳ Synthesizing Voice...</span>';
    btn.classList.add('loading');
  }

  try {
    const res = await fetch(`/api/clips/${clipId}/voiceover`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: text,
        lang: lang,
        voice_effect: voiceEffect
      })
    });

    const data = await res.json();
    if (data.status === 'success') {
      const updatedClip = data.clip;
      item.voiceover_file = updatedClip.voiceover_file;
      item.voiceover_url = updatedClip.voiceover_url;
      item.voiceover_text = updatedClip.voiceover_text;
      item.voiceover_lang = updatedClip.voiceover_lang;
      item.voiceover_effect = updatedClip.voiceover_effect;
      item.voiceover_duration = updatedClip.voiceover_duration;
      item.speed_multiplier = updatedClip.speed_multiplier;
      item.final_duration = updatedClip.final_duration;

      // Update in currentClips array as well
      const c = currentClips.find(cl => cl.id === clipId);
      if (c) {
        Object.assign(c, updatedClip);
      }

      updateTimelineDurations();
      renderTimeline();
      syncReorderedClipsToBackend();

      // Auto play audio for immediate feedback
      setTimeout(() => {
        const audioPlayer = document.getElementById(`clip-audio-player-${index}`);
        if (audioPlayer) {
          audioPlayer.play().catch(() => {});
        }
      }, 200);
    } else {
      alert('Voice generation failed: ' + (data.detail || 'Unknown error'));
    }
  } catch (err) {
    alert('Voice generation error: ' + err.message);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = origBtnHtml;
      btn.classList.remove('loading');
    }
  }
}

async function deleteClipVoice(index) {
  if (!currentPlan || !currentPlan.timeline || !currentPlan.timeline[index]) return;
  const item = currentPlan.timeline[index];
  const clipId = item.id;

  try {
    const res = await fetch(`/api/clips/${clipId}/voiceover`, { method: 'DELETE' });
    const data = await res.json();
    if (data.status === 'success') {
      if (data.plan) {
        currentPlan = data.plan;
      } else {
        item.voiceover_file = null;
        item.voiceover_url = null;
        item.voiceover_text = '';
        item.voiceover_duration = 0.0;
      }

      const c = currentClips.find(cl => cl.id === clipId);
      if (c) {
        c.voiceover_file = null;
        c.voiceover_url = null;
        c.voiceover_text = '';
        c.voiceover_duration = 0.0;
      }

      renderTimeline();
    }
  } catch (err) {
    console.error('Delete clip voice error:', err);
  }
}

window.generateClipVoice = generateClipVoice;
window.deleteClipVoice = deleteClipVoice;

// --- Per-Clip Custom Trim, Replace & Delete Handlers ---
let activeReplacingClipIndex = null;

function applyClipTrim(index) {
  if (!currentPlan || !currentPlan.timeline || !currentPlan.timeline[index]) return;
  const item = currentPlan.timeline[index];
  
  const startInput = document.getElementById(`trim-start-${index}`);
  const endInput = document.getElementById(`trim-end-${index}`);
  
  const rawStart = parseFloat(startInput.value);
  const rawEnd = parseFloat(endInput.value);
  
  if (isNaN(rawStart) || isNaN(rawEnd) || rawStart < 0 || rawEnd <= rawStart) {
    alert('Please enter valid Start and End seconds (Start must be less than End).');
    return;
  }
  
  item.start_time = Math.round(rawStart * 10) / 10;
  item.end_time = Math.round(rawEnd * 10) / 10;
  
  const rawDur = Math.max(0.5, item.end_time - item.start_time);
  
  // Recalculate speed if clip has voiceover
  if (item.voiceover_duration && item.voiceover_duration > 0.2) {
    item.speed_multiplier = Math.max(0.25, Math.min(16.0, Math.round((rawDur / item.voiceover_duration) * 100) / 100));
  }
  
  const newFinalDur = Math.max(0.5, Math.round((rawDur / item.speed_multiplier) * 10) / 10);
  item.final_duration = newFinalDur;
  
  renderTimeline();
  syncReorderedClipsToBackend();
}

function triggerReplaceClip(index) {
  activeReplacingClipIndex = index;
  const replaceInput = document.getElementById('replace-clip-input');
  if (replaceInput) {
    replaceInput.value = '';
    replaceInput.click();
  }
}

async function deleteSingleClip(index) {
  if (!currentPlan || !currentPlan.timeline || !currentPlan.timeline[index]) return;
  const item = currentPlan.timeline[index];
  const clipId = item.id;
  
  if (!confirm(`Are you sure you want to remove clip #${index + 1} (${item.filename}) from the vlog?`)) {
    return;
  }
  
  try {
    const res = await fetch(`/api/clips/${clipId}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.status === 'success') {
      currentClips = currentClips.filter(c => c.id !== clipId);
      currentPlan.timeline.splice(index, 1);
      currentPlan.timeline.forEach((itm, i) => { itm.order = i; });
      renderTimeline();
      updateUploadCount();
    }
  } catch (err) {
    alert('Failed to delete clip: ' + err.message);
  }
}

function scrollToEditorAndHighlight() {
  const storySection = document.getElementById('story-arc-section') || document.querySelector('.preview-panel');
  if (storySection) {
    storySection.scrollIntoView({ behavior: 'smooth' });
    storySection.classList.add('editor-pulse-highlight');
    setTimeout(() => {
      storySection.classList.remove('editor-pulse-highlight');
    }, 2500);
  }
}

window.applyClipTrim = applyClipTrim;
window.triggerReplaceClip = triggerReplaceClip;
window.deleteSingleClip = deleteSingleClip;
window.scrollToEditorAndHighlight = scrollToEditorAndHighlight;

// --- Quick 3-Second Live Preview ---
async function triggerQuickPreview() {
  if (currentClips.length === 0) {
    alert('Please upload clips first to generate a live preview.');
    return;
  }

  quickPreviewBtn.disabled = true;
  quickPreviewBtn.innerHTML = '<span>⏳ Rendering Preview...</span>';

  try {
    const res = await fetch('/api/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        aspect_ratio: aspectSelect.value,
        visual_filter: activeVisualFilter,
        transition_type: activeTransition,
        show_text_overlays: showTextOverlaysCheckbox.checked
      })
    });

    const data = await res.json();
    if (data.status === 'success') {
      previewModalCard.classList.remove('hidden');
      previewMetaDesc.textContent = `Live Sample with ${activeVisualFilter.replace('_', ' ').toUpperCase()} & ${activeTransition.toUpperCase()} transition`;
      quickPreviewPlayer.src = `${data.preview_url}?t=${Date.now()}`;
      quickPreviewPlayer.play();
      previewModalCard.scrollIntoView({ behavior: 'smooth' });
    }
  } catch (err) {
    alert('Preview generation failed: ' + err.message);
  } finally {
    quickPreviewBtn.disabled = false;
    quickPreviewBtn.innerHTML = '<span>▶️ Quick 3s Preview</span>';
  }
}

// --- Voiceover Narration Logic ---
async function toggleVoiceRecording() {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    // Stop recording
    mediaRecorder.stop();
    recordVoBtn.classList.remove('recording');
    recordBtnText.textContent = '🎙️ Record Voice';
    clearInterval(recordTimerInterval);
    return;
  }

  // Start recording
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunks.push(e.data);
    };

    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
      stream.getTracks().forEach(track => track.stop());
      await uploadVoiceoverBlob(audioBlob, 'mic_recording.webm');
    };

    mediaRecorder.start();
    recordStartTime = Date.now();
    recordVoBtn.classList.add('recording');
    recordBtnText.textContent = '⏹️ Stop (00:00)';

    recordTimerInterval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - recordStartTime) / 1000);
      const mins = Math.floor(elapsed / 60);
      const secs = elapsed % 60;
      recordBtnText.textContent = `⏹️ Stop (${mins < 10 ? '0' : ''}${mins}:${secs < 10 ? '0' : ''}${secs})`;
    }, 1000);

  } catch (err) {
    alert('Could not access microphone: ' + err.message);
  }
}

async function handleVoiceFileInput(e) {
  const file = e.target.files[0];
  if (file) {
    await uploadVoiceoverFile(file);
  }
}

async function uploadVoiceoverBlob(blob, filename) {
  const formData = new FormData();
  formData.append('file', blob, filename);
  await sendVoiceoverUpload(formData);
}

async function uploadVoiceoverFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  await sendVoiceoverUpload(formData);
}

const voSyncBadgeRow = document.getElementById('vo-sync-badge-row');
const voSyncDesc = document.getElementById('vo-sync-desc');
const syncNowBtn = document.getElementById('sync-now-btn');

if (syncNowBtn) {
  syncNowBtn.addEventListener('click', () => {
    generatePlan();
  });
}

async function sendVoiceoverUpload(formData) {
  try {
    const res = await fetch('/api/voiceover/upload', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (data.status === 'success') {
      currentVoiceover = data.voiceover;
      showVoiceoverBanner(data.voiceover);
      if (data.plan) {
        currentPlan = data.plan;
        renderTimeline();
      }
    }
  } catch (err) {
    alert('Failed to upload voiceover: ' + err.message);
  }
}

async function handleGenerateTts() {
  const text = storyTtsInput.value.trim();
  if (!text) {
    alert('कृपया व्लॉगसाठी कथा किंवा मजकूर टाईप करा (Please enter vlog story text).');
    storyTtsInput.focus();
    return;
  }

  const origHtml = generateTtsBtn.innerHTML;
  generateTtsBtn.disabled = true;
  generateTtsBtn.innerHTML = '<span>⏳ Generating Voice & Auto-Syncing Speeds...</span>';

  try {
    const res = await fetch('/api/voiceover/generate-tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: text,
        lang: ttsLangSelect.value,
        voice_effect: ttsVoiceEffect.value
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to generate funny voice');
    }

    const data = await res.json();
    if (data.status === 'success') {
      currentVoiceover = data.voiceover;
      showVoiceoverBanner(data.voiceover);
      if (data.plan) {
        currentPlan = data.plan;
        renderTimeline();
      }
    }
  } catch (err) {
    alert('Error generating funny voice: ' + err.message);
  } finally {
    generateTtsBtn.disabled = false;
    generateTtsBtn.innerHTML = origHtml;
  }
}

async function handleApplyMorph() {
  if (!currentVoiceover) {
    alert('No active voiceover track to apply funny effects to.');
    return;
  }

  const origText = applyMorphBtn.textContent;
  applyMorphBtn.disabled = true;
  applyMorphBtn.textContent = 'Applying...';

  try {
    const res = await fetch('/api/voiceover/apply-effect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        voice_effect: morphVoiceSelect.value
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to apply effect');
    }

    const data = await res.json();
    if (data.status === 'success') {
      currentVoiceover = data.voiceover;
      showVoiceoverBanner(data.voiceover);
      if (data.plan) {
        currentPlan = data.plan;
        renderTimeline();
      }
    }
  } catch (err) {
    alert('Error morphing voice: ' + err.message);
  } finally {
    applyMorphBtn.disabled = false;
    applyMorphBtn.textContent = origText;
  }
}

function showVoiceoverBanner(vo) {
  voActiveBanner.classList.remove('hidden');
  voVolumeRow.classList.remove('hidden');
  voNameLabel.textContent = vo.filename || 'Funny Voiceover Audio';

  const effectMap = {
    'gian_classic': '🦍 Gian (डोरेमॉनचा जाड व भारी जियान)',
    'motu_chubby_cartoon': '🍔 Motu (मोटू पतलूचा जाडजूड कार्टून)',
    'kalia_pehelwan': '🦁 Kalia Pehelwan (छोटा भीमचा कालिया)',
    'oggy_bob_heavy': '🐶 Bob The Bulldog (ऑगीचा जाडजूड बॉब)',
    'chingum_heavy_cop': '👮 Inspector Chingum (दबंग इन्स्पेक्टर)',
    'cartoon_iron_giant': '🤖 Cartoon Iron Giant (राक्षसी रोबोट)'
  };

  const effectText = effectMap[vo.voice_effect] || vo.voice_effect || 'Heavy Cartoon Voice';
  if (voEffectLabel) {
    voEffectLabel.textContent = `🦍 Active Cartoon: ${effectText}`;
  }

  if (vo.voice_effect && morphVoiceSelect) {
    morphVoiceSelect.value = vo.voice_effect;
  }

  if (voSyncBadgeRow && vo.duration) {
    voSyncBadgeRow.classList.remove('hidden');
    if (voSyncDesc) {
      voSyncDesc.textContent = `🎯 Video Timeline Auto-Matched to Voiceover Duration (~${vo.duration}s)`;
    }
  }

  voAudioPlayer.src = `${vo.audio_url}?t=${Date.now()}`;
  voStatusBadge.textContent = '✓ Voice Added';
  voStatusBadge.style.color = '#34d399';
  voStatusBadge.style.background = 'rgba(16, 185, 129, 0.2)';
}

async function deleteVoiceover() {
  try {
    await fetch('/api/voiceover', { method: 'DELETE' });
    currentVoiceover = null;
    voActiveBanner.classList.add('hidden');
    voVolumeRow.classList.add('hidden');
    if (voSyncBadgeRow) {
      voSyncBadgeRow.classList.add('hidden');
    }
    voAudioPlayer.src = '';
    voiceFileInput.value = '';
    voStatusBadge.textContent = 'Optional';
    voStatusBadge.style.color = '';
    voStatusBadge.style.background = '';
    generatePlan();
  } catch (err) {
    console.error('Failed to delete voiceover:', err);
  }
}


// --- Full Video Rendering Execution ---
async function startRendering() {
  if (!currentPlan) return;

  saveCurrentTextareaInputs();
  closeVideoUpdateModal();

  renderBtn.disabled = true;
  progressBox.classList.remove('hidden');
  outputCard.classList.add('hidden');
  progressBarFill.style.width = '0%';
  progressPercentage.textContent = '0%';
  progressStatusTitle.textContent = 'Rendering Daily Vlog...';
  progressLogMessage.textContent = 'Initializing studio FFmpeg pipeline...';
  progressBox.scrollIntoView({ behavior: 'smooth', block: 'center' });

  const resolutionSelect = document.getElementById('resolution-select');
  const selectedResolution = resolutionSelect ? resolutionSelect.value : '4k';

  const renderPayload = {
    timeline: currentPlan.timeline,
    aspect_ratio: aspectSelect.value,
    resolution: selectedResolution,
    music_id: musicSelect.value,
    music_volume: parseFloat(musicVolume.value) / 100.0,
    voiceover_volume: parseFloat(voiceVolume.value) / 100.0,
    visual_filter: activeVisualFilter,
    transition_type: activeTransition,
    transition_duration: 0.5,
    show_text_overlays: showTextOverlaysCheckbox.checked,
    auto_rotate_v2h: autoRotateV2hCheckbox.checked
  };

  try {
    const res = await fetch('/api/render', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(renderPayload)
    });
    
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to start render');
    }

    listenProgressStream();

  } catch (err) {
    progressStatusTitle.textContent = 'Render Error';
    progressLogMessage.textContent = err.message;
    renderBtn.disabled = false;
  }
}

function listenProgressStream() {
  if (sseEventSource) {
    sseEventSource.close();
  }

  sseEventSource = new EventSource('/api/render/stream');

  sseEventSource.onmessage = (event) => {
    try {
      const job = JSON.parse(event.data);
      progressBarFill.style.width = `${job.progress}%`;
      progressPercentage.textContent = `${job.progress}%`;
      progressLogMessage.textContent = job.message || '';

      if (job.status === 'completed') {
        sseEventSource.close();
        renderBtn.disabled = false;
        progressStatusTitle.textContent = 'Completed!';
        showFinalVideo(job.output_url);
      } else if (job.status === 'error') {
        sseEventSource.close();
        renderBtn.disabled = false;
        progressStatusTitle.textContent = 'Render Failed';
        progressLogMessage.textContent = job.error || 'An error occurred during FFmpeg execution';
      }
    } catch (err) {
      console.error('SSE parse error:', err);
    }
  };

  sseEventSource.onerror = () => {
    sseEventSource.close();
  };
}

let activeTargetVideoFilename = null;

function updateTargetVideoBadge(fn) {
  const badge = document.getElementById('ig-target-video-name');
  if (badge && fn) {
    badge.textContent = `🎬 ${fn}`;
  }
}

function showFinalVideo(outputUrl) {
  outputCard.classList.remove('hidden');
  finalVideoPlayer.src = outputUrl;
  downloadVlogBtn.href = outputUrl;
  outputCard.scrollIntoView({ behavior: 'smooth' });

  const fn = outputUrl.split('/').pop().split('?')[0];
  if (fn) {
    activeTargetVideoFilename = fn;
    updateTargetVideoBadge(fn);
  }

  // Auto-populate caption if empty
  if (!igCaptionInput.value.trim()) {
    generateSmartCaption();
  }

  // Refresh output gallery at bottom right
  if (typeof loadOutputGallery === 'function') {
    loadOutputGallery();
  }
}

// ==========================================
// --- Instagram 1-Click Auto-Poster Logic ---
// ==========================================

const igModalOverlay = document.getElementById('ig-modal-overlay');
const igConnectModalBtn = document.getElementById('ig-connect-modal-btn');
const igCloseModalBtn = document.getElementById('ig-close-modal-btn');
const igUsernameInput = document.getElementById('ig-username');
const igPasswordInput = document.getElementById('ig-password');
const ig2faGroup = document.getElementById('ig-2fa-group');
const ig2faCodeInput = document.getElementById('ig-2fa-code');
const igModalError = document.getElementById('ig-modal-error');
const igSubmitLoginBtn = document.getElementById('ig-submit-login-btn');
const igLogoutBtn = document.getElementById('ig-logout-btn');

const igAccountPill = document.getElementById('ig-account-pill');
const igUserLabel = document.getElementById('ig-user-label');
const igCaptionInput = document.getElementById('ig-caption-input');
const igAutoCaptionBtn = document.getElementById('ig-auto-caption-btn');
const igPostBtn = document.getElementById('ig-post-btn');
const igPostBtnText = document.getElementById('ig-post-btn-text');
const igUploadStatus = document.getElementById('ig-upload-status');
const igStatusMsg = document.getElementById('ig-status-msg');
const igStatusSpinner = document.getElementById('ig-status-spinner');
const igViewReelLink = document.getElementById('ig-view-reel-link');

let igConnected = false;
let igCurrentUsername = null;

function setupInstagramEventListeners() {
  if (igConnectModalBtn) {
    igConnectModalBtn.addEventListener('click', () => {
      igModalOverlay.classList.remove('hidden');
      igModalError.classList.add('hidden');
    });
  }

  if (igCloseModalBtn) {
    igCloseModalBtn.addEventListener('click', () => {
      igModalOverlay.classList.add('hidden');
    });
  }

  if (igModalOverlay) {
    igModalOverlay.addEventListener('click', (e) => {
      if (e.target === igModalOverlay) {
        igModalOverlay.classList.add('hidden');
      }
    });
  }

  if (igSubmitLoginBtn) {
    igSubmitLoginBtn.addEventListener('click', handleInstagramLogin);
  }

  if (igLogoutBtn) {
    igLogoutBtn.addEventListener('click', handleInstagramLogout);
  }

  if (igAutoCaptionBtn) {
    igAutoCaptionBtn.addEventListener('click', generateSmartCaption);
  }

  if (igPostBtn) {
    igPostBtn.addEventListener('click', handlePostReelToInstagram);
  }
}

async function checkInstagramStatus() {
  try {
    const res = await fetch('/api/instagram/status');
    const data = await res.json();
    updateInstagramUI(data.logged_in, data.username);
  } catch (err) {
    console.warn('Could not fetch Instagram status:', err);
  }
}

function updateInstagramUI(isLoggedIn, username) {
  igConnected = isLoggedIn;
  igCurrentUsername = username;

  if (isLoggedIn && username) {
    igAccountPill.classList.add('connected');
    igUserLabel.textContent = `@${username}`;
    igConnectModalBtn.textContent = 'Manage';
    igLogoutBtn.classList.remove('hidden');
    igUsernameInput.value = username;
  } else {
    igAccountPill.classList.remove('connected');
    igUserLabel.textContent = 'Not Connected';
    igConnectModalBtn.textContent = 'Connect';
    igLogoutBtn.classList.add('hidden');
  }
}

async function handleInstagramLogin() {
  const username = igUsernameInput ? igUsernameInput.value.trim() : '';
  const password = igPasswordInput ? igPasswordInput.value : '';
  const code = ig2faCodeInput ? ig2faCodeInput.value.trim() : '';
  const sessionIdInput = document.getElementById('ig-session-id');
  const sessionid = sessionIdInput ? sessionIdInput.value.trim() : '';

  if (!sessionid && (!username || !password)) {
    showModalError('Please enter your Instagram username & password, or paste your Session ID.');
    return;
  }

  const origHtml = igSubmitLoginBtn.innerHTML;
  igSubmitLoginBtn.disabled = true;
  igSubmitLoginBtn.innerHTML = '<span>⏳ Connecting to Instagram...</span>';
  igModalError.classList.add('hidden');

  try {
    const res = await fetch('/api/instagram/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: username,
        password: password,
        verification_code: code || null,
        sessionid: sessionid || null
      })
    });

    let data;
    try {
      data = await res.json();
    } catch (parseErr) {
      throw new Error('Connection failed: Invalid server response. Please try connecting via Session ID.');
    }

    if (!res.ok) {
      throw new Error(data.detail || 'Login failed');
    }

    if (data.status === '2fa_required') {
      if (ig2faGroup) ig2faGroup.classList.remove('hidden');
      showModalError(data.message || '2FA Verification Code required. Check your SMS or Authenticator App and enter the code above.');
      if (ig2faCodeInput) ig2faCodeInput.focus();
      return;
    }

    if (data.status === 'challenge_required') {
      showModalError(data.message || 'Security checkpoint: Please open the Instagram app on your mobile phone, tap "This Was Me", and click Connect again.');
      return;
    }

    updateInstagramUI(true, data.username);
    igModalOverlay.classList.add('hidden');
    alert(`🎉 Successfully connected to Instagram as @${data.username}! You can now auto-post Reels in 1-click.`);

  } catch (err) {
    showModalError(err.message);
  } finally {
    igSubmitLoginBtn.disabled = false;
    igSubmitLoginBtn.innerHTML = origHtml;
  }
}

async function handleInstagramLogout() {
  try {
    await fetch('/api/instagram/logout', { method: 'POST' });
    updateInstagramUI(false, null);
    igPasswordInput.value = '';
    igModalOverlay.classList.add('hidden');
  } catch (err) {
    console.error('Logout error:', err);
  }
}

function showModalError(msg) {
  igModalError.textContent = msg;
  igModalError.classList.remove('hidden');
}

function generateSmartCaption() {
  const storyText = storyTtsInput ? storyTtsInput.value.trim() : '';
  const firstLine = storyText ? storyText.slice(0, 100).replace(/\n/g, ' ') : "A day in my life! ✨";

  const hashtags = [
    '#marathivlog',
    '#dailyvlog',
    '#reelsindia',
    '#reelsinstagram',
    '#codinglife',
    '#workvlog',
    '#gianvoice',
    '#marathireels',
    '#viralreels',
    '#productivity'
  ];

  const fullCaption = `⚡ Daily Work Vlog ✨\n${firstLine}...\n\nEdited & Voiced with AutoVlog AI Studio 🦍🔥\n\n${hashtags.join(' ')}`;
  igCaptionInput.value = fullCaption;
}

async function handlePostReelToInstagram() {
  if (!igConnected) {
    igModalOverlay.classList.remove('hidden');
    showModalError('Please connect your Instagram account first to auto-post Reels.');
    return;
  }

  const caption = igCaptionInput.value.trim();
  const targetFile = activeTargetVideoFilename || (currentOutputVideos.length > 0 ? currentOutputVideos[0].filename : null);

  igPostBtn.disabled = true;
  igPostBtnText.textContent = '⏳ Uploading 4K Reel to Instagram...';
  igUploadStatus.classList.remove('hidden');
  igStatusSpinner.classList.remove('hidden');
  igStatusMsg.textContent = 'Connecting to Instagram servers & processing video...';
  igViewReelLink.classList.add('hidden');

  try {
    const res = await fetch('/api/instagram/post-reel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filename: targetFile,
        caption: caption
      })
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || 'Failed to post Reel to Instagram');
    }

    igStatusSpinner.classList.add('hidden');
    igStatusMsg.textContent = '🎉 Reel Published Successfully to Instagram!';
    
    if (data.reel_url) {
      igViewReelLink.href = data.reel_url;
      igViewReelLink.classList.remove('hidden');
    }

    igPostBtnText.textContent = '✓ Published to Instagram!';

    setTimeout(() => {
      igPostBtn.disabled = false;
      igPostBtnText.textContent = '🚀 Post Reel to Instagram Now';
    }, 4000);

  } catch (err) {
    igStatusSpinner.classList.add('hidden');
    igStatusMsg.textContent = `❌ Error: ${err.message}`;
    igPostBtn.disabled = false;
    igPostBtnText.textContent = '🚀 Try Posting Again';
  }
}

// ==========================================
// --- Output Videos Gallery (Below Right Side) ---
// ==========================================

let currentOutputVideos = [];

async function loadOutputGallery() {
  const outputsList = document.getElementById('outputs-list');
  const emptyOutputsMsg = document.getElementById('empty-outputs-msg');
  const outputCountBadge = document.getElementById('output-count-badge');
  if (!outputsList) return;

  try {
    const res = await fetch('/api/outputs');
    if (!res.ok) throw new Error('Failed to load output history');
    const videos = await res.json();
    currentOutputVideos = videos || [];

    if (outputCountBadge) {
      outputCountBadge.textContent = `${currentOutputVideos.length} video${currentOutputVideos.length === 1 ? '' : 's'}`;
    }

    if (currentOutputVideos.length === 0) {
      if (emptyOutputsMsg) emptyOutputsMsg.classList.remove('hidden');
      outputsList.innerHTML = '';
      return;
    }

    if (!activeTargetVideoFilename && currentOutputVideos.length > 0) {
      activeTargetVideoFilename = currentOutputVideos[0].filename;
      updateTargetVideoBadge(activeTargetVideoFilename);
    }

    if (emptyOutputsMsg) emptyOutputsMsg.classList.add('hidden');
    outputsList.innerHTML = '';

    currentOutputVideos.forEach((vid, idx) => {
      const card = document.createElement('div');
      card.className = 'output-item glass-card';
      card.id = `output-card-${idx}`;

      const resBadgeClass = vid.is_8k ? 'badge-8k-purple' : (vid.is_4k ? 'badge-4k-gold' : 'badge-hd');
      const cornerBadge = vid.is_8k ? '<div class="badge-8k-corner">8K</div>' : (vid.is_4k ? '<div class="badge-4k-corner">4K</div>' : '');
      const durLabel = vid.duration > 0 ? `${vid.duration}s` : 'Video';

      card.innerHTML = `
        <div class="output-item-main">
          <div class="output-thumb-wrap" onclick="playOutputVideo('${vid.url}', '${vid.filename}')">
            <video src="${vid.url}" preload="metadata" class="output-item-video-preview" muted playsinline></video>
            <div class="output-play-overlay">
              <span>▶</span>
            </div>
            ${cornerBadge}
          </div>

          <div class="output-item-details">
            <div class="output-item-title-row">
              <span class="output-item-name" title="${vid.filename}">🎬 ${vid.filename}</span>
              <span class="badge-output-res ${resBadgeClass}">${vid.resolution_label}</span>
            </div>

            <div class="output-item-meta-row">
              <span class="output-meta-tag">⏱️ ${durLabel}</span>
              <span class="output-meta-tag">💾 ${vid.size_mb} MB</span>
              <span class="output-meta-tag">📅 ${vid.created_at}</span>
            </div>

            <div class="output-item-actions">
              <button type="button" class="btn-action-sm btn-play-out" onclick="playOutputVideo('${vid.url}', '${vid.filename}')">
                <span>▶️ Play</span>
              </button>
              <button type="button" class="btn-action-sm btn-edit-out" onclick="openVideoUpdateModal()" title="Update visual filters, scene transitions, soundtrack & quality">
                <span>🎨 Update</span>
              </button>
              <button type="button" class="btn-action-sm btn-timeline-out" onclick="scrollToEditorAndHighlight()" title="Edit individual clips, scripts & speeds in timeline">
                <span>✏️ Timeline</span>
              </button>
              <a href="${vid.url}" download="${vid.filename}" class="btn-action-sm btn-download-link">
                <span>⬇️ Download</span>
              </a>
              <button type="button" class="btn-action-sm btn-action-ig" onclick="prepareAndPostOutputToInstagram('${vid.filename}')" title="Auto-post to Instagram Reels">
                <span>📱 Instagram</span>
              </button>
              <button type="button" class="btn-action-sm btn-action-yt" onclick="prepareAndPostOutputToYouTube('${vid.filename}')" title="Auto-post to YouTube">
                <span>▶️ YouTube</span>
              </button>
              <button type="button" class="btn-action-sm btn-delete-output" onclick="deleteOutputVideo('${vid.filename}')" title="Delete this video">
                <span>🗑️</span>
              </button>
            </div>
          </div>
        </div>
      `;

      outputsList.appendChild(card);
    });

  } catch (err) {
    console.error('Error loading output gallery:', err);
  }
}

function playOutputVideo(url, filename) {
  const outputCard = document.getElementById('output-card');
  const finalPlayer = document.getElementById('final-video-player');
  const downloadBtn = document.getElementById('download-vlog-btn');

  activeTargetVideoFilename = filename;
  updateTargetVideoBadge(filename);

  if (outputCard && finalPlayer) {
    outputCard.classList.remove('hidden');
    // Only update src if it is a different video to prevent reload loops
    const currentSrcPath = finalPlayer.src ? new URL(finalPlayer.src, window.location.origin).pathname : '';
    const newSrcPath = new URL(url, window.location.origin).pathname;

    if (currentSrcPath !== newSrcPath) {
      finalPlayer.src = url;
      finalPlayer.load();
    }
    finalPlayer.scrollIntoView({ behavior: 'smooth' });
    finalPlayer.play().catch(() => {});
  }

  if (downloadBtn) {
    downloadBtn.href = url;
    downloadBtn.setAttribute('download', filename);
  }
}

function prepareAndPostOutputToInstagram(filename) {
  playOutputVideo(`/outputs/${filename}`, filename);
  const igBox = document.querySelector('.ig-autopost-box');
  if (igBox) {
    igBox.scrollIntoView({ behavior: 'smooth' });
  }
}

function prepareAndPostOutputToYouTube(filename) {
  playOutputVideo(`/outputs/${filename}`, filename);
  const ytBox = document.querySelector('.yt-autopost-box');
  if (ytBox) {
    ytBox.scrollIntoView({ behavior: 'smooth' });
  }
  if (typeof generateSmartYouTubeMetadata === 'function') {
    generateSmartYouTubeMetadata();
  }
}

async function deleteOutputVideo(filename) {
  if (!confirm(`Are you sure you want to delete "${filename}"?`)) return;

  try {
    const res = await fetch(`/api/outputs/${encodeURIComponent(filename)}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.status === 'success') {
      loadOutputGallery();
    } else {
      alert('Delete failed: ' + (data.detail || 'Unknown error'));
    }
  } catch (err) {
    alert('Delete error: ' + err.message);
  }
}

window.loadOutputGallery = loadOutputGallery;
window.playOutputVideo = playOutputVideo;
window.prepareAndPostOutputToInstagram = prepareAndPostOutputToInstagram;
window.deleteOutputVideo = deleteOutputVideo;

// Hook into initial setup
const originalSetupEventListeners = setupEventListeners;
setupEventListeners = function() {
  originalSetupEventListeners();
  setupInstagramEventListeners();
  
  const refreshOutputsBtn = document.getElementById('refresh-outputs-btn');
  if (refreshOutputsBtn) {
    refreshOutputsBtn.addEventListener('click', () => {
      loadOutputGallery();
    });
  }

  const addClipBtn = document.getElementById('add-clip-btn');
  const addClipInput = document.getElementById('add-clip-input');
  const replaceClipInput = document.getElementById('replace-clip-input');

  if (addClipBtn && addClipInput) {
    addClipBtn.addEventListener('click', () => {
      addClipInput.value = '';
      addClipInput.click();
    });

    addClipInput.addEventListener('change', async (e) => {
      const files = Array.from(e.target.files);
      if (files.length > 0) {
        await uploadFiles(files);
      }
    });
  }

  if (replaceClipInput) {
    replaceClipInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file || activeReplacingClipIndex === null || !currentPlan || !currentPlan.timeline[activeReplacingClipIndex]) return;
      
      const item = currentPlan.timeline[activeReplacingClipIndex];
      const clipId = item.id;
      
      const formData = new FormData();
      formData.append('file', file);
      
      try {
        const res = await fetch(`/api/clips/${clipId}/replace`, {
          method: 'POST',
          body: formData
        });
        const data = await res.json();
        if (data.status === 'success') {
          const updated = data.clip;
          item.filename = updated.filename;
          item.file_path = updated.file_path;
          item.thumbnail_url = updated.thumbnail_url;
          item.duration = updated.duration;
          item.raw_duration = updated.duration;
          item.rotation = updated.rotation;
          item.is_vertical = updated.is_vertical;
          item.speed_multiplier = updated.speed_multiplier;
          item.final_duration = updated.final_duration;
          item.start_time = 0.0;
          item.end_time = updated.duration;
          
          const origClip = currentClips.find(c => c.id === clipId);
          if (origClip) {
            Object.assign(origClip, updated);
          }
          
          renderTimeline();
          syncReorderedClipsToBackend();
        } else {
          alert('Failed to replace clip: ' + (data.detail || 'Unknown error'));
        }
      } catch (err) {
        alert('Failed to replace clip: ' + err.message);
      } finally {
        activeReplacingClipIndex = null;
      }
    });
  }
};
// ==========================================
// --- Speech-to-Text & Transliteration Logic ---
// ==========================================

let activeSpeechRecognition = null;

function isSpeechRecognitionAvailable() {
  return Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);
}

function startSpeechToText(targetTextarea, statusBadgeEl, micBtnEl, langCode = 'mr') {
  if (!isSpeechRecognitionAvailable()) {
    alert("Speech recognition (Mic to Text) is supported in Chrome, Edge, and Safari browsers.");
    return;
  }

  // Toggle stop if already running
  if (activeSpeechRecognition) {
    try {
      activeSpeechRecognition.stop();
    } catch (e) {}
    activeSpeechRecognition = null;
    if (statusBadgeEl) statusBadgeEl.classList.add('hidden');
    if (micBtnEl) micBtnEl.classList.remove('recording');
    return;
  }

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = new SpeechRecognition();
  activeSpeechRecognition = recognition;

  const langMap = {
    'mr': 'mr-IN',
    'hi': 'hi-IN',
    'en': 'en-IN'
  };
  recognition.lang = langMap[langCode] || 'mr-IN';
  recognition.continuous = true;
  recognition.interimResults = true;

  if (statusBadgeEl) {
    statusBadgeEl.classList.remove('hidden');
    statusBadgeEl.textContent = '🔴 Listening... बोलत रहा...';
  }
  if (micBtnEl) micBtnEl.classList.add('recording');

  recognition.onresult = async (event) => {
    let finalTranscript = '';
    for (let i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        finalTranscript += event.results[i][0].transcript;
      }
    }

    if (finalTranscript) {
      const currentVal = targetTextarea.value;
      const separator = currentVal && !currentVal.endsWith(' ') && !currentVal.endsWith('\n') ? ' ' : '';
      let newText = currentVal + separator + finalTranscript.trim();

      const autoToggle = document.getElementById('auto-transliterate-toggle');
      if ((!autoToggle || autoToggle.checked) && /[a-zA-Z]/.test(newText) && langCode !== 'en') {
        newText = await transliterateRomanToDevanagari(newText, langCode);
      }

      targetTextarea.value = newText;
      targetTextarea.dispatchEvent(new Event('input'));
    }
  };

  recognition.onerror = (event) => {
    console.warn('Speech recognition error:', event.error);
    if (statusBadgeEl) {
      statusBadgeEl.textContent = `⚠️ ${event.error}`;
      setTimeout(() => statusBadgeEl.classList.add('hidden'), 3000);
    }
    if (micBtnEl) micBtnEl.classList.remove('recording');
    activeSpeechRecognition = null;
  };

  recognition.onend = () => {
    if (statusBadgeEl) statusBadgeEl.classList.add('hidden');
    if (micBtnEl) micBtnEl.classList.remove('recording');
    activeSpeechRecognition = null;
  };

  try {
    recognition.start();
  } catch (err) {
    console.error('Failed to start recognition:', err);
  }
}

async function transliterateRomanToDevanagari(text, lang = 'mr') {
  if (!text || !text.trim()) return text;
  try {
    const res = await fetch('/api/transliterate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, lang })
    });
    if (!res.ok) throw new Error('Transliteration failed');
    const data = await res.json();
    return data.transliterated || text;
  } catch (err) {
    console.warn('Transliteration error:', err);
    return text;
  }
}

async function handleMainStoryTransliterate() {
  const storyInput = document.getElementById('story-tts-input');
  const langSelect = document.getElementById('tts-lang-select');
  if (!storyInput) return;
  const raw = storyInput.value;
  if (!raw.trim()) return;

  const lang = langSelect ? langSelect.value : 'mr';
  const converted = await transliterateRomanToDevanagari(raw, lang);
  storyInput.value = converted;
  storyInput.dispatchEvent(new Event('input'));
}

async function transliterateClipScript(index) {
  if (!currentPlan || !currentPlan.timeline || !currentPlan.timeline[index]) return;
  const textarea = document.getElementById(`clip-script-${index}`);
  const langSelect = document.getElementById(`clip-lang-${index}`);
  if (!textarea) return;
  const raw = textarea.value;
  if (!raw.trim()) return;

  const lang = langSelect ? langSelect.value : 'mr';
  const converted = await transliterateRomanToDevanagari(raw, lang);
  textarea.value = converted;
  currentPlan.timeline[index].voiceover_text = converted;
  const charCountEl = document.getElementById(`char-count-${index}`);
  if (charCountEl) charCountEl.textContent = `${converted.length} chars`;
  syncReorderedClipsToBackend();
}

function triggerClipSTT(index) {
  const textarea = document.getElementById(`clip-script-${index}`);
  const statusBadge = document.getElementById(`clip-stt-badge-${index}`);
  const micBtn = document.getElementById(`btn-clip-mic-${index}`);
  const langSelect = document.getElementById(`clip-lang-${index}`);
  if (!textarea) return;
  const lang = langSelect ? langSelect.value : 'mr';
  startSpeechToText(textarea, statusBadge, micBtn, lang);
}

window.transliterateClipScript = transliterateClipScript;
window.triggerClipSTT = triggerClipSTT;

// Live Typing Transliteration on Space/Enter key
function setupLiveTransliterationListener(textarea, langGetter) {
  if (!textarea) return;
  
  textarea.addEventListener('keyup', async (e) => {
    const autoToggle = document.getElementById('auto-transliterate-toggle');
    if (autoToggle && !autoToggle.checked) return;
    
    // Trigger on Space, Enter, or Punctuation
    if (e.key === ' ' || e.key === 'Enter' || e.key === ',' || e.key === '.') {
      const val = textarea.value;
      const cursorPos = textarea.selectionStart;
      const textBeforeCursor = val.slice(0, cursorPos);
      const words = textBeforeCursor.trim().split(/\s+/);
      const lastWord = words[words.length - 1];

      // If last word contains English letters
      if (lastWord && /^[a-zA-Z]+$/.test(lastWord)) {
        const lang = (typeof langGetter === 'function' ? langGetter() : 'mr') || 'mr';
        if (lang === 'en') return;

        const convertedWord = await transliterateRomanToDevanagari(lastWord, lang);
        if (convertedWord && convertedWord !== lastWord) {
          const lastWordIndex = textBeforeCursor.lastIndexOf(lastWord);
          if (lastWordIndex !== -1) {
            const newVal = val.slice(0, lastWordIndex) + convertedWord + val.slice(lastWordIndex + lastWord.length);
            textarea.value = newVal;
            textarea.selectionStart = textarea.selectionEnd = lastWordIndex + convertedWord.length + 1;
            textarea.dispatchEvent(new Event('input'));
          }
        }
      }
    }
  });
}

// ==========================================
// --- YouTube 1-Click Studio Uploader Logic ---
// ==========================================

const ytModalOverlay = document.getElementById('yt-modal-overlay');
const ytConnectModalBtn = document.getElementById('yt-connect-modal-btn');
const ytCloseModalBtn = document.getElementById('yt-close-modal-btn');
const ytChannelNameInput = document.getElementById('yt-channel-name');
const ytApiKeyInput = document.getElementById('yt-api-key');
const ytSaveBtn = document.getElementById('yt-save-btn');
const ytLogoutBtn = document.getElementById('yt-logout-btn');

const ytAccountPill = document.getElementById('yt-account-pill');
const ytUserLabel = document.getElementById('yt-user-label');
const ytTitleInput = document.getElementById('yt-title-input');
const ytDescInput = document.getElementById('yt-desc-input');
const ytTagsInput = document.getElementById('yt-tags-input');
const ytPrivacySelect = document.getElementById('yt-privacy-select');
const ytAutoMetaBtn = document.getElementById('yt-auto-meta-btn');
const ytPostBtn = document.getElementById('yt-post-btn');
const ytPostBtnText = document.getElementById('yt-post-btn-text');
const ytUploadStatus = document.getElementById('yt-upload-status');
const ytStatusMsg = document.getElementById('yt-status-msg');
const ytStatusSpinner = document.getElementById('yt-status-spinner');
const ytViewLink = document.getElementById('yt-view-link');

function setupYouTubeEventListeners() {
  if (ytConnectModalBtn) {
    ytConnectModalBtn.addEventListener('click', () => {
      ytModalOverlay.classList.remove('hidden');
    });
  }

  if (ytCloseModalBtn) {
    ytCloseModalBtn.addEventListener('click', () => {
      ytModalOverlay.classList.add('hidden');
    });
  }

  if (ytModalOverlay) {
    ytModalOverlay.addEventListener('click', (e) => {
      if (e.target === ytModalOverlay) ytModalOverlay.classList.add('hidden');
    });
  }

  if (ytSaveBtn) {
    ytSaveBtn.addEventListener('click', handleYouTubeSave);
  }

  if (ytLogoutBtn) {
    ytLogoutBtn.addEventListener('click', handleYouTubeLogout);
  }

  if (ytAutoMetaBtn) {
    ytAutoMetaBtn.addEventListener('click', generateSmartYouTubeMetadata);
  }

  if (ytPostBtn) {
    ytPostBtn.addEventListener('click', handlePostVideoToYouTube);
  }
}

async function checkYouTubeStatus() {
  try {
    const res = await fetch('/api/youtube/status');
    const data = await res.json();
    updateYouTubeUI(data.connected, data.channel_title);
  } catch (err) {
    console.warn('Could not fetch YouTube status:', err);
  }
}

function updateYouTubeUI(isConnected, channelTitle) {
  if (isConnected && channelTitle) {
    ytAccountPill.classList.add('connected');
    ytUserLabel.textContent = channelTitle;
    ytConnectModalBtn.textContent = 'Settings';
    ytLogoutBtn.classList.remove('hidden');
    ytChannelNameInput.value = channelTitle;
  } else {
    ytAccountPill.classList.remove('connected');
    ytUserLabel.textContent = 'My YouTube Channel';
    ytConnectModalBtn.textContent = 'Settings';
    ytLogoutBtn.classList.add('hidden');
  }
}

async function handleYouTubeSave() {
  const name = ytChannelNameInput.value.trim() || 'My YouTube Channel';
  const apiKey = ytApiKeyInput.value.trim() || null;

  try {
    const res = await fetch('/api/youtube/connect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ channel_name: name, api_key: apiKey })
    });
    const data = await res.json();
    updateYouTubeUI(true, data.channel_title);
    ytModalOverlay.classList.add('hidden');
    alert('🎉 YouTube channel settings saved!');
  } catch (err) {
    alert('Failed to save settings: ' + err.message);
  }
}

async function handleYouTubeLogout() {
  try {
    await fetch('/api/youtube/logout', { method: 'POST' });
    updateYouTubeUI(false, null);
    ytModalOverlay.classList.add('hidden');
  } catch (err) {
    console.error('Logout error:', err);
  }
}

async function generateSmartYouTubeMetadata() {
  const storyText = storyTtsInput ? storyTtsInput.value.trim() : '';
  const resolutionSelect = document.getElementById('resolution-select');
  const resVal = resolutionSelect ? resolutionSelect.value : '8k';
  const is8k = (resVal === '8k');
  const is4k = (resVal === '4k');

  try {
    const res = await fetch('/api/youtube/generate-metadata', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        story_text: storyText,
        is_8k: is8k,
        is_4k: is4k
      })
    });
    const data = await res.json();
    if (data.title && ytTitleInput) ytTitleInput.value = data.title;
    if (data.description && ytDescInput) ytDescInput.value = data.description;
    if (data.tags && ytTagsInput) ytTagsInput.value = data.tags;
  } catch (err) {
    console.error('Error generating YouTube metadata:', err);
  }
}

async function handlePostVideoToYouTube() {
  const targetFile = activeTargetVideoFilename || (currentOutputVideos.length > 0 ? currentOutputVideos[0].filename : null);
  const title = ytTitleInput.value.trim() || 'Daily Work Vlog (8K Ultra HD)';
  const desc = ytDescInput.value.trim() || '';
  const tags = ytTagsInput.value.trim() || 'daily vlog, 8k, marathi';
  const privacy = ytPrivacySelect ? ytPrivacySelect.value : 'public';

  ytPostBtn.disabled = true;
  ytPostBtnText.textContent = '⏳ Uploading Video to YouTube...';
  ytUploadStatus.classList.remove('hidden');
  ytStatusSpinner.classList.remove('hidden');
  ytStatusMsg.textContent = 'Preparing 8K / 4K video streams & publishing to YouTube...';
  ytViewLink.classList.add('hidden');

  try {
    const res = await fetch('/api/youtube/post-video', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filename: targetFile,
        title: title,
        description: desc,
        tags: tags,
        privacy: privacy
      })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to upload video to YouTube');

    ytStatusSpinner.classList.add('hidden');
    ytStatusMsg.textContent = `🎉 Video Published Successfully to YouTube (${privacy.toUpperCase()})!`;
    
    if (data.youtube_url) {
      ytViewLink.href = data.youtube_url;
      ytViewLink.classList.remove('hidden');
    }

    ytPostBtnText.textContent = '✓ Published to YouTube!';
    setTimeout(() => {
      ytPostBtn.disabled = false;
      ytPostBtnText.textContent = '🚀 Publish Video to YouTube';
    }, 4000);

  } catch (err) {
    ytStatusSpinner.classList.add('hidden');
    ytStatusMsg.textContent = `❌ Error: ${err.message}`;
    ytPostBtn.disabled = false;
    ytPostBtnText.textContent = '🚀 Try Posting to YouTube Again';
  }
}

window.prepareAndPostOutputToYouTube = prepareAndPostOutputToYouTube;

// Update target video badges
const origUpdateTargetVideoBadge = updateTargetVideoBadge;
updateTargetVideoBadge = function(fn) {
  if (typeof origUpdateTargetVideoBadge === 'function') origUpdateTargetVideoBadge(fn);
  const ytBadge = document.getElementById('yt-target-video-name');
  if (ytBadge && fn) {
    ytBadge.textContent = `🎬 ${fn}`;
  }
};

// ==========================================
// --- Theme Switcher (Black & White / Dark & Light) ---
// ==========================================

function initTheme() {
  const savedTheme = localStorage.getItem('autovlog_theme') || 'dark';
  applyTheme(savedTheme);

  const themeToggleBtn = document.getElementById('theme-toggle-btn');
  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', toggleTheme);
  }
}

function applyTheme(theme) {
  const isLight = (theme === 'light');
  document.documentElement.setAttribute('data-theme', isLight ? 'light' : 'dark');
  document.body.setAttribute('data-theme', isLight ? 'light' : 'dark');
  
  const themeLabel = document.getElementById('theme-label');
  const themeToggleBtn = document.getElementById('theme-toggle-btn');
  if (themeLabel) {
    themeLabel.textContent = isLight ? 'Light Mode' : 'Dark Mode';
  }
  if (themeToggleBtn) {
    themeToggleBtn.classList.toggle('light-active', isLight);
  }
  localStorage.setItem('autovlog_theme', isLight ? 'light' : 'dark');
}

function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
  const newTheme = (currentTheme === 'light') ? 'dark' : 'light';
  applyTheme(newTheme);
}

window.toggleTheme = toggleTheme;
window.applyTheme = applyTheme;

// Setup main STT mic & transliterate listeners
const origSetupEventListeners2 = setupEventListeners;
setupEventListeners = function() {
  origSetupEventListeners2();
  setupYouTubeEventListeners();
  initTheme();

  const mainSttMicBtn = document.getElementById('main-stt-mic-btn');
  const mainSttStatusBadge = document.getElementById('main-stt-status-badge');
  const storyTtsInput = document.getElementById('story-tts-input');
  const ttsLangSelect = document.getElementById('tts-lang-select');
  const mainTransliterateBtn = document.getElementById('main-transliterate-btn');

  if (mainSttMicBtn && storyTtsInput) {
    mainSttMicBtn.addEventListener('click', () => {
      const lang = ttsLangSelect ? ttsLangSelect.value : 'mr';
      startSpeechToText(storyTtsInput, mainSttStatusBadge, mainSttMicBtn, lang);
    });
  }

  if (mainTransliterateBtn) {
    mainTransliterateBtn.addEventListener('click', handleMainStoryTransliterate);
  }

  if (storyTtsInput) {
    setupLiveTransliterationListener(storyTtsInput, () => ttsLangSelect ? ttsLangSelect.value : 'mr');
  }
};

const origLoadInitialState2 = loadInitialState;
loadInitialState = function() {
  origLoadInitialState2();
  checkYouTubeStatus();
};

// ==========================================
// --- Universal Modal Close & Escape Manager ---
// ==========================================

function closeInstagramModal() {
  const m = document.getElementById('ig-modal-overlay');
  if (m) m.classList.add('hidden');
}

function closeYouTubeModal() {
  const m = document.getElementById('yt-modal-overlay');
  if (m) m.classList.add('hidden');
}

function closeVideoUpdateModal() {
  const m = document.getElementById('video-update-modal');
  if (m) m.classList.add('hidden');
}

function closeSequenceModal() {
  const m = document.getElementById('upload-sequence-modal');
  if (m) m.classList.add('hidden');
  pendingBatchFiles = [];
}

function closeQuickPreviewModal() {
  const m = document.getElementById('preview-modal-card');
  if (m) m.classList.add('hidden');
  const player = document.getElementById('quick-preview-player');
  if (player) player.pause();
}

window.closeInstagramModal = closeInstagramModal;
window.closeYouTubeModal = closeYouTubeModal;
window.closeVideoUpdateModal = closeVideoUpdateModal;
window.closeSequenceModal = closeSequenceModal;
window.closeQuickPreviewModal = closeQuickPreviewModal;

// Global Delegated Click Handler for all Modals and Close Buttons
document.addEventListener('click', (e) => {
  // 1. Any button with data-close-modal or class btn-close-modal / btn-action-sm
  const closeBtn = e.target.closest('[data-close-modal], .btn-close-modal, #ig-close-modal-btn, #yt-close-modal-btn, #close-update-modal-btn, #cancel-update-modal-btn, #close-seq-modal-btn, #cancel-seq-btn, #close-preview-btn');
  if (closeBtn) {
    const targetId = closeBtn.getAttribute('data-close-modal');
    if (targetId) {
      const targetEl = document.getElementById(targetId);
      if (targetEl) targetEl.classList.add('hidden');
    }
    const parentModal = closeBtn.closest('.modal-overlay, .modal-backdrop, .preview-modal-card, #preview-modal-card, #video-update-modal, #ig-modal-overlay, #yt-modal-overlay, #upload-sequence-modal');
    if (parentModal) {
      parentModal.classList.add('hidden');
    }
    return;
  }

  // 2. Click outside modal box on backdrop overlay
  if (e.target.classList.contains('modal-overlay') || e.target.classList.contains('modal-backdrop')) {
    e.target.classList.add('hidden');
  }
});

// Escape key closes all open modals
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' || e.key === 'Esc') {
    document.querySelectorAll('.modal-overlay, .modal-backdrop, .preview-modal-card, #preview-modal-card').forEach(el => {
      el.classList.add('hidden');
    });
  }
});

// --- Start Application Lifecycle ---
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadInitialState();
  });
} else {
  setupEventListeners();
  loadInitialState();
}


