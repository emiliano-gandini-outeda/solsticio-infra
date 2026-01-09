<script setup>
import { ref, onMounted, computed, watch } from "vue";
import { api } from "./api";

const containers = ref([]);
const ocrJobs = ref([]);
const results = ref([]);
const loading = ref(false);
const error = ref("");
const fileInput = ref(null);
const stoppingContainers = ref({});
const blinkPhase = ref(0); // Global blink phase for coordinated blinking

// Pagination
const currentPage = ref({
  containers: 1,
  ocrJobs: 1,
  results: 1
});
const itemsPerPage = 10;

// --- Containers ---
async function loadContainers() {
  loading.value = true;
  error.value = "";
  try {
    const data = await api("/containers");
    Object.keys(stoppingContainers.value).forEach(name => {
      if (!data.find(c => c.name === name)) {
        delete stoppingContainers.value[name];
      }
    });
    containers.value = data;
  } catch (e) { error.value = e.message; }
  finally { loading.value = false; }
}

async function action(name, cmd) {
  try {
    if (cmd === 'stop') {
      stoppingContainers.value[name] = true;
    }
    await api(`/containers/${name}/${cmd}`, { method: "POST" });
    await loadContainers();
  } catch (e) {
    error.value = e.message;
    if (cmd === 'stop') {
      delete stoppingContainers.value[name];
    }
  }
}

async function remove(name) {
  if (!confirm(`Delete ${name}?`)) return;
  try {
    await api(`/containers/${name}`, { method: "DELETE" });
    await loadContainers();
  } catch (e) {
    error.value = e.message;
  }
}

async function test(name) {
  try {
    await api(`/containers/${name}/test`, { method: "POST" });
    await loadContainers();
  } catch (e) {
    error.value = e.message;
  }
}

// --- OCR Jobs ---
const OCR_API = "http://ocr.solsticio.local";

async function loadOCR() {
  try {
    const jobs = await api("http://ocr.solsticio.local/jobs/queued");
    ocrJobs.value = jobs.reverse();
    
    const res = await api("http://ocr.solsticio.local/results");
    results.value = res.reverse();
  } catch (e) {
    error.value = e.message;
  }
}

async function uploadOCR() {
  if (!fileInput.value || !fileInput.value.files.length) return;

  const file = fileInput.value.files[0];
  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch(`${OCR_API}/upload`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) throw new Error("Upload error");

    const data = await res.json();
    alert(`File queued: ${data.filename}`);

    await loadOCR();
    fileInput.value.value = "";
  } catch (e) {
    error.value = e.message;
  }
}

// Computed properties for pagination
const paginatedContainers = computed(() => {
  const start = (currentPage.value.containers - 1) * itemsPerPage;
  const end = start + itemsPerPage;
  return containers.value.slice(start, end);
});

const paginatedOCRJobs = computed(() => {
  const start = (currentPage.value.ocrJobs - 1) * itemsPerPage;
  const end = start + itemsPerPage;
  return ocrJobs.value.slice(start, end);
});

const paginatedResults = computed(() => {
  const start = (currentPage.value.results - 1) * itemsPerPage;
  const end = start + itemsPerPage;
  return results.value.slice(start, end);
});

const totalPages = computed(() => ({
  containers: Math.ceil(containers.value.length / itemsPerPage),
  ocrJobs: Math.ceil(ocrJobs.value.length / itemsPerPage),
  results: Math.ceil(results.value.length / itemsPerPage)
}));

// Pagination functions
function changePage(section, page) {
  if (page > 0 && page <= totalPages.value[section]) {
    currentPage.value[section] = page;
  }
}

// Watch for container status changes to clear stopping state
watch(containers, (newContainers) => {
  newContainers.forEach(container => {
    if (stoppingContainers.value[container.name] && container.status !== 'running') {
      delete stoppingContainers.value[container.name];
    }
  });
}, { deep: true });

// Global blink animation for coordinated blinking
let blinkInterval = null;
onMounted(() => {
  // Start coordinated blinking
  blinkInterval = setInterval(() => {
    blinkPhase.value = (blinkPhase.value + 1) % 4; // 4-phase cycle for smooth coordination
  }, 250); // Each phase = 250ms, full cycle = 1s

  loadContainers();
  loadOCR();

  // OCR refresh interval
  const ocrInterval = setInterval(loadOCR, 3000);
  
  return () => {
    if (blinkInterval) clearInterval(blinkInterval);
    if (ocrInterval) clearInterval(ocrInterval);
  };
});

// Computed property for blink state
const blinkState = computed(() => {
  return blinkPhase.value;
});
</script>

<template>
<main>
  <header class="header">
    <h1>INFRASTRUCTURE DASHBOARD</h1>
  </header>

  <div v-if="error" class="error-message">
    <span class="error-icon">!</span>
    <span class="error-text">{{ error }}</span>
    <button @click="error = ''" class="close-error">×</button>
  </div>

  <!-- Docker Containers Section -->
  <section class="card industrial-card">
    <div class="card-header">
      <div class="title-section">
        <h2 class="industrial-title">DOCKER CONTAINERS</h2>
        <div class="container-count">
          <span class="count-number">{{ containers.length }}</span>
          <span class="count-label">ACTIVE</span>
        </div>
      </div>
      <div class="card-actions">
        <button @click="loadContainers" class="btn btn-industrial">
          <span class="btn-icon">⟳</span> REFRESH
        </button>
      </div>
    </div>

    <div class="table-responsive">
      <table class="industrial-table">
        <thead>
          <tr>
            <th class="col-name">NAME</th>
            <th class="col-status">STATUS</th>
            <th class="col-actions">ACTIONS</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in paginatedContainers" :key="c.name" class="table-row-industrial">
            <td class="container-name">{{ c.name }}</td>
            <td>
              <div :class="[
                'status-indicator-industrial',
                stoppingContainers[c.name] ? 'stopping' : c.status,
                {'blinking': (c.status === 'running' || c.status === 'processing') && !stoppingContainers[c.name]}
              ]">
                <div class="status-light" :class="{'blinking-light': (c.status === 'running' || c.status === 'processing') && !stoppingContainers[c.name]}"></div>
                <span class="status-text">
                  {{ stoppingContainers[c.name] ? 'STOPPING' : c.status.toUpperCase() }}
                </span>
              </div>
            </td>
            <td class="actions-cell">
              <div class="industrial-button-group">
                <button 
                  @click="action(c.name,'start')" 
                  class="btn btn-industrial-action" 
                  title="Start"
                  :disabled="c.status === 'running' || stoppingContainers[c.name]">
                  <span class="btn-icon">▶</span>
                </button>
                <button 
                  @click="action(c.name,'stop')" 
                  class="btn btn-industrial-action btn-industrial-stop" 
                  title="Stop"
                  :disabled="c.status !== 'running' || stoppingContainers[c.name]">
                  <span class="btn-icon">■</span>
                </button>
                <button 
                  @click="test(c.name)" 
                  class="btn btn-industrial-action btn-industrial-test" 
                  title="Run test"
                  :disabled="stoppingContainers[c.name]">
                  TEST
                </button>
                <button 
                  @click="remove(c.name)" 
                  class="btn btn-industrial-action btn-industrial-delete" 
                  title="Delete"
                  :disabled="stoppingContainers[c.name]">
                  <span class="btn-icon">×</span>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Containers Pagination -->
    <div v-if="containers.length > itemsPerPage" class="pagination-industrial">
      <button 
        @click="changePage('containers', currentPage.containers - 1)"
        :disabled="currentPage.containers === 1"
        class="pagination-btn-industrial">
        ◀ PREV
      </button>
      <div class="page-indicator">
        <span class="current-page">{{ currentPage.containers }}</span>
        <span class="total-pages">/{{ totalPages.containers }}</span>
      </div>
      <button 
        @click="changePage('containers', currentPage.containers + 1)"
        :disabled="currentPage.containers === totalPages.containers"
        class="pagination-btn-industrial">
        NEXT ▶
      </button>
    </div>
  </section>

  <!-- OCR Processing Section -->
  <section class="card industrial-card">
    <div class="card-header">
      <h2 class="industrial-title">OCR PROCESSING</h2>
      <div class="card-actions">
        <button @click="loadOCR" class="btn btn-industrial">
          <span class="btn-icon">⟳</span> REFRESH OCR
        </button>
      </div>
    </div>

    <div class="upload-section-industrial">
      <div class="file-input-wrapper-industrial">
        <input 
          type="file" 
          ref="fileInput" 
          id="ocr-file"
          class="file-input-industrial" 
          accept=".pdf,.jpg,.jpeg,.png,.tiff"
        />
        <label for="ocr-file" class="file-input-label-industrial">
          SELECT FILE
        </label>
        <div class="file-info" v-if="fileInput?.files?.[0]">
          <div class="file-indicator"></div>
          <span class="file-name-industrial">{{ fileInput.files[0].name }}</span>
        </div>
      </div>
      <button @click="uploadOCR" class="btn btn-industrial-primary">
        PROCESS OCR
      </button>
    </div>

    <!-- Active Jobs -->
    <div class="subsection-industrial">
      <div class="subsection-header">
        <h3 class="industrial-subtitle">ACTIVE JOBS</h3>
        <div class="subsection-count">{{ ocrJobs.length }}</div>
      </div>
      <div class="table-responsive">
        <table class="industrial-table">
          <thead>
            <tr>
              <th class="col-id">JOB ID</th>
              <th class="col-file">FILE</th>
              <th class="col-status">STATUS</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="job in paginatedOCRJobs" :key="job.job_id" class="table-row-industrial">
              <td class="job-id-industrial">{{ job.job_id }}</td>
              <td class="filename-industrial">{{ job.filename }}</td>
              <td>
                <div :class="[
                  'status-indicator-industrial',
                  job.status,
                  {'blinking': job.status === 'processing', 'completed': job.status === 'completed'}
                ]">
                  <div class="status-light" :class="{'blinking-light': job.status === 'processing'}"></div>
                  <span class="status-text">{{ job.status.toUpperCase() }}</span>
                </div>
              </td>
            </tr>
            <tr v-if="ocrJobs.length === 0">
              <td colspan="3" class="empty-message-industrial">NO ACTIVE JOBS</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- OCR Jobs Pagination -->
      <div v-if="ocrJobs.length > itemsPerPage" class="pagination-industrial">
        <button 
          @click="changePage('ocrJobs', currentPage.ocrJobs - 1)"
          :disabled="currentPage.ocrJobs === 1"
          class="pagination-btn-industrial">
          ◀ PREV
        </button>
        <div class="page-indicator">
          <span class="current-page">{{ currentPage.ocrJobs }}</span>
          <span class="total-pages">/{{ totalPages.ocrJobs }}</span>
        </div>
        <button 
          @click="changePage('ocrJobs', currentPage.ocrJobs + 1)"
          :disabled="currentPage.ocrJobs === totalPages.ocrJobs"
          class="pagination-btn-industrial">
          NEXT ▶
        </button>
      </div>
    </div>

    <!-- Results -->
    <div class="subsection-industrial">
      <div class="subsection-header">
        <h3 class="industrial-subtitle">RESULTS</h3>
        <div class="subsection-count">{{ results.length }}</div>
      </div>
      <div class="table-responsive">
        <table class="industrial-table">
          <thead>
            <tr>
              <th class="col-id">JOB ID</th>
              <th class="col-file">FILE</th>
              <th class="col-download">DOWNLOAD</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in paginatedResults" :key="r.job_id" class="table-row-industrial">
              <td class="job-id-industrial">{{ r.job_id }}</td>
              <td class="filename-industrial">{{ r.filename }}</td>
              <td>
                <a
                  :href="`http://ocr.solsticio.local${r.download_url}`"
                  download
                  class="btn btn-industrial-download"
                >
                  DOWNLOAD
                </a>
              </td>
            </tr>
            <tr v-if="results.length === 0">
              <td colspan="3" class="empty-message-industrial">NO RESULTS AVAILABLE</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Results Pagination -->
      <div v-if="results.length > itemsPerPage" class="pagination-industrial">
        <button 
          @click="changePage('results', currentPage.results - 1)"
          :disabled="currentPage.results === 1"
          class="pagination-btn-industrial">
          ◀ PREV
        </button>
        <div class="page-indicator">
          <span class="current-page">{{ currentPage.results }}</span>
          <span class="total-pages">/{{ totalPages.results }}</span>
        </div>
        <button 
          @click="changePage('results', currentPage.results + 1)"
          :disabled="currentPage.results === totalPages.results"
          class="pagination-btn-industrial">
          NEXT ▶
        </button>
      </div>
    </div>
  </section>
</main>
</template>

<style>
/* Industrial Black Color Palette */
:root {
  --industrial-bg: #000000;
  --industrial-surface: #0a0a0a;
  --industrial-panel: #101010;
  --industrial-border: #1a1a1a;
  --industrial-border-light: #2a2a2a;
  --industrial-text: #e0e0e0;
  --industrial-text-secondary: #808080;
  --industrial-text-muted: #606060;
  --industrial-accent: #0066cc;
  --industrial-accent-hover: #0088ff;
  --industrial-success: #00cc66;
  --industrial-warning: #ff8800;
  --industrial-danger: #ff3333;
  --industrial-processing: #8844ff;
  --industrial-stopping: #ff6600;
  --industrial-shadow: rgba(0, 0, 0, 0.8);
  --industrial-glow: rgba(0, 102, 204, 0.2);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  background-color: var(--industrial-bg);
  color: var(--industrial-text);
  font-family: 'Roboto Mono', 'Courier New', monospace;
  line-height: 1.4;
  min-height: 100vh;
  font-weight: 400;
}

main {
  padding: 1rem;
  max-width: 1400px;
  margin: 0 auto;
}

/* Header */
.header {
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--industrial-border);
  position: relative;
}

.header::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  width: 150px;
  height: 2px;
  background: linear-gradient(90deg, var(--industrial-accent), transparent);
}

.header h1 {
  font-size: 1.8rem;
  font-weight: 700;
  letter-spacing: 3px;
  text-transform: uppercase;
  color: var(--industrial-text);
  text-shadow: 0 0 20px rgba(0, 102, 204, 0.3);
  position: relative;
  padding-left: 0.5rem;
}

.header h1::before {
  content: '';
  position: absolute;
  left: -0.5rem;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--industrial-accent);
  box-shadow: 0 0 10px var(--industrial-accent);
}

/* Industrial Cards */
.industrial-card {
  background: var(--industrial-panel);
  border-radius: 2px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  border: 1px solid var(--industrial-border);
  box-shadow: 0 4px 12px var(--industrial-shadow);
  position: relative;
  overflow: hidden;
}

.industrial-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 3px;
  height: 100%;
  background: linear-gradient(to bottom, var(--industrial-accent), transparent);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.industrial-title {
  font-size: 1.3rem;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--industrial-text);
  margin: 0;
  position: relative;
  padding-left: 0.5rem;
}

.industrial-title::before {
  content: '';
  position: absolute;
  left: -0.5rem;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--industrial-accent);
}

.container-count {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.8rem;
  background: var(--industrial-surface);
  border: 1px solid var(--industrial-border-light);
  border-radius: 1px;
}

.count-number {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--industrial-accent);
}

.count-label {
  font-size: 0.7rem;
  color: var(--industrial-text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* Industrial Buttons */
.btn {
  padding: 0.6rem 1.2rem;
  border: 1px solid var(--industrial-border-light);
  border-radius: 1px;
  cursor: pointer;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s ease;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  background: var(--industrial-surface);
  color: var(--industrial-text);
  font-family: 'Roboto Mono', monospace;
}

.btn-icon {
  font-size: 0.9em;
}

.btn-industrial {
  border-color: var(--industrial-border-light);
  background: var(--industrial-surface);
}

.btn-industrial:hover:not(:disabled) {
  border-color: var(--industrial-accent);
  background: var(--industrial-panel);
  box-shadow: 0 0 10px var(--industrial-glow);
}

.btn-industrial-primary {
  background: var(--industrial-accent);
  border-color: var(--industrial-accent);
  color: white;
  font-weight: 700;
}

.btn-industrial-primary:hover {
  background: var(--industrial-accent-hover);
  border-color: var(--industrial-accent-hover);
  box-shadow: 0 0 15px rgba(0, 136, 255, 0.4);
}

.btn-industrial-action {
  padding: 0.5rem 0.8rem;
  min-width: 40px;
  min-height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--industrial-surface);
  border: 1px solid var(--industrial-border-light);
  font-size: 0.8rem;
}

.btn-industrial-action:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px var(--industrial-shadow);
}

.btn-industrial-action:disabled {
  opacity: 0.3;
  cursor: not-allowed;
  background: var(--industrial-panel);
}

.btn-industrial-stop {
  border-color: var(--industrial-danger);
  color: var(--industrial-danger);
}

.btn-industrial-stop:hover:not(:disabled) {
  background: var(--industrial-danger);
  color: var(--industrial-bg);
}

.btn-industrial-test {
  border-color: var(--industrial-warning);
  color: var(--industrial-warning);
  min-width: 60px;
}

.btn-industrial-test:hover:not(:disabled) {
  background: var(--industrial-warning);
  color: var(--industrial-bg);
}

.btn-industrial-delete {
  border-color: var(--industrial-danger);
  color: var(--industrial-danger);
}

.btn-industrial-delete:hover:not(:disabled) {
  background: var(--industrial-danger);
  color: var(--industrial-bg);
}

.btn-industrial-download {
  background: var(--industrial-success);
  border-color: var(--industrial-success);
  color: var(--industrial-bg);
  text-decoration: none;
  padding: 0.5rem 1rem;
  font-weight: 700;
}

.btn-industrial-download:hover {
  background: #00dd77;
  border-color: #00dd77;
  box-shadow: 0 0 10px rgba(0, 221, 119, 0.3);
}

.industrial-button-group {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

/* Upload Section */
.upload-section-industrial {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
  padding: 1rem;
  background: var(--industrial-surface);
  border: 1px solid var(--industrial-border);
  border-radius: 1px;
  flex-wrap: wrap;
}

.file-input-wrapper-industrial {
  flex: 1;
  min-width: 200px;
}

.file-input-industrial {
  display: none;
}

.file-input-label-industrial {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1.2rem;
  background: var(--industrial-panel);
  color: var(--industrial-text);
  border-radius: 1px;
  cursor: pointer;
  border: 1px solid var(--industrial-border-light);
  transition: all 0.2s ease;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.file-input-label-industrial:hover {
  border-color: var(--industrial-accent);
  background: var(--industrial-surface);
}

.file-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.file-indicator {
  width: 8px;
  height: 8px;
  background: var(--industrial-accent);
  border-radius: 1px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.file-name-industrial {
  color: var(--industrial-text-secondary);
  font-size: 0.85rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Industrial Tables */
.table-responsive {
  overflow-x: auto;
  margin-bottom: 1rem;
  border: 1px solid var(--industrial-border);
  border-radius: 1px;
}

.industrial-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.industrial-table thead {
  background: var(--industrial-surface);
}

.industrial-table th {
  padding: 1rem;
  text-align: left;
  font-weight: 700;
  color: var(--industrial-text);
  text-transform: uppercase;
  letter-spacing: 1px;
  border-bottom: 2px solid var(--industrial-border);
  font-size: 0.8rem;
  background: linear-gradient(to bottom, var(--industrial-surface), var(--industrial-panel));
}

.col-name { width: 25%; }
.col-status { width: 20%; }
.col-actions { width: 35%; }
.col-id { width: 30%; }
.col-file { width: 50%; }
.col-download { width: 20%; }

.industrial-table td {
  padding: 1rem;
  border-bottom: 1px solid var(--industrial-border);
  color: var(--industrial-text);
  vertical-align: middle;
  background: var(--industrial-panel);
}

.table-row-industrial:hover td {
  background: var(--industrial-surface);
}

.container-name, .job-id-industrial, .filename-industrial {
  font-family: 'Roboto Mono', monospace;
  font-size: 0.85rem;
  color: var(--industrial-text);
  letter-spacing: 0.5px;
}

.actions-cell {
  display: flex;
  justify-content: flex-start;
}

/* Coordinated Blinking System */
.blinking-light {
  animation: coordinated-blink 1s infinite;
}

@keyframes coordinated-blink {
  0% { opacity: 1; }
  25% { opacity: 0.7; }
  50% { opacity: 0.4; }
  75% { opacity: 0.7; }
  100% { opacity: 1; }
}

/* Status Indicators */
.status-indicator-industrial {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.8rem;
  border-radius: 1px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  background: var(--industrial-surface);
  border: 1px solid var(--industrial-border-light);
  min-width: 120px;
  justify-content: center;
}

.status-light {
  width: 10px;
  height: 10px;
  border-radius: 1px;
  display: inline-block;
  flex-shrink: 0;
}

.running .status-light {
  background: var(--industrial-success);
  box-shadow: 0 0 10px var(--industrial-success);
}

.exited .status-light {
  background: var(--industrial-danger);
  box-shadow: 0 0 5px var(--industrial-danger);
}

.processing .status-light {
  background: var(--industrial-processing);
  box-shadow: 0 0 10px var(--industrial-processing);
}

.completed .status-light {
  background: var(--industrial-success);
  box-shadow: 0 0 10px var(--industrial-success);
}

.stopping .status-light {
  background: var(--industrial-stopping);
  box-shadow: 0 0 10px var(--industrial-stopping);
  animation: pulse-stop 1s infinite;
}

@keyframes pulse-stop {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.stopping {
  color: var(--industrial-stopping) !important;
  border-color: var(--industrial-stopping) !important;
}

.status-text {
  color: inherit;
  font-weight: 700;
}

/* Pagination */
.pagination-industrial {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid var(--industrial-border);
}

.pagination-btn-industrial {
  padding: 0.5rem 1rem;
  background: var(--industrial-surface);
  color: var(--industrial-text);
  border: 1px solid var(--industrial-border-light);
  border-radius: 1px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  font-family: 'Roboto Mono', monospace;
  min-width: 80px;
}

.pagination-btn-industrial:hover:not(:disabled) {
  border-color: var(--industrial-accent);
  background: var(--industrial-panel);
}

.pagination-btn-industrial:disabled {
  opacity: 0.2;
  cursor: not-allowed;
}

.page-indicator {
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
  color: var(--industrial-text-secondary);
  font-size: 0.9rem;
  min-width: 80px;
  justify-content: center;
}

.current-page {
  color: var(--industrial-accent);
  font-weight: 700;
  font-size: 1.1rem;
}

.total-pages {
  color: var(--industrial-text-muted);
}

/* Subsection */
.subsection-industrial {
  margin-top: 2rem;
}

.subsection-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--industrial-border);
}

.industrial-subtitle {
  font-size: 1rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--industrial-text);
  margin: 0;
  position: relative;
  padding-left: 0.5rem;
}

.industrial-subtitle::before {
  content: '';
  position: absolute;
  left: -0.5rem;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--industrial-accent);
}

.subsection-count {
  padding: 0.25rem 0.5rem;
  background: var(--industrial-surface);
  border: 1px solid var(--industrial-border-light);
  border-radius: 1px;
  font-size: 0.8rem;
  color: var(--industrial-text-secondary);
  min-width: 32px;
  text-align: center;
}

.empty-message-industrial {
  text-align: center;
  color: var(--industrial-text-muted);
  padding: 2rem !important;
  font-style: italic;
  text-transform: uppercase;
  letter-spacing: 1px;
  font-size: 0.85rem;
  background: var(--industrial-surface);
}

/* Error Message */
.error-message {
  background: rgba(255, 51, 51, 0.1);
  color: var(--industrial-danger);
  padding: 1rem;
  border-radius: 1px;
  margin-bottom: 1.5rem;
  border-left: 3px solid var(--industrial-danger);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  border: 1px solid rgba(255, 51, 51, 0.3);
}

.error-icon {
  font-size: 1rem;
  font-weight: 700;
  width: 20px;
  height: 20px;
  background: var(--industrial-danger);
  color: var(--industrial-bg);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.error-text {
  flex: 1;
}

.close-error {
  background: none;
  border: none;
  color: var(--industrial-danger);
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 1px;
  flex-shrink: 0;
}

.close-error:hover {
  background: rgba(255, 51, 51, 0.2);
}

/* Responsive */
@media (max-width: 768px) {
  main {
    padding: 0.5rem;
  }
  
  .header h1 {
    font-size: 1.4rem;
    letter-spacing: 2px;
  }
  
  .industrial-card {
    padding: 1rem;
  }
  
  .card-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .upload-section-industrial {
    flex-direction: column;
    align-items: stretch;
  }
  
  .industrial-button-group {
    justify-content: flex-start;
  }
  
  .industrial-table {
    font-size: 0.8rem;
  }
  
  .industrial-table th,
  .industrial-table td {
    padding: 0.75rem 0.5rem;
  }
  
  .btn-industrial-action {
    padding: 0.4rem 0.6rem;
    font-size: 0.75rem;
  }
}
</style>