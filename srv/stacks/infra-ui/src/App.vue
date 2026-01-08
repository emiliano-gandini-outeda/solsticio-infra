<script setup>
import { ref, onMounted } from "vue";
import { api } from "./api";

const containers = ref([]);
const loading = ref(false);
const error = ref("");

async function load() {
  loading.value = true;
  error.value = "";
  try {
    containers.value = await api("/containers");
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

async function action(name, cmd) {
  try {
    await api(`/containers/${name}/${cmd}`, { method: "POST" });
    await load();
  } catch(e) { error.value = e.message; }
}

async function remove(name) {
  if (!confirm(`Eliminar ${name}?`)) return;
  try {
    await api(`/containers/${name}`, { method: "DELETE" });
    await load();
  } catch(e) { error.value = e.message; }
}

async function test(name) {
  try {
    await api(`/containers/${name}/test`, { method: "POST" });
    await load();
  } catch(e) { error.value = e.message; }
}

async function deploy() {
  const stack = prompt("Stack a deployar:");
  if (!stack) return;
  try {
    await api("/deploy", {
      method: "POST",
      body: JSON.stringify({ stack })
    });
    alert("Deploy encolado");
  } catch(e) { error.value = e.message; }
}

onMounted(load);
</script>

<template>
<main>
  <h1>Infra Dashboard</h1>
  <div class="controls">
    <button @click="load">↻ Refresh</button>
    <button @click="deploy">🚀 Deploy stack</button>
  </div>

  <p v-if="loading">Cargando…</p>
  <p v-if="error" class="error">{{ error }}</p>

  <table>
    <thead>
      <tr>
        <th>Nombre</th>
        <th>Estado</th>
        <th>Acciones</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="c in containers" :key="c.name">
        <td>{{ c.name }}</td>
        <td :class="c.status">{{ c.status }}</td>
        <td>
          <button @click="action(c.name,'start')">▶</button>
          <button @click="action(c.name,'stop')">■</button>
          <button @click="test(c.name)">🧪 Test 1h</button>
          <button @click="remove(c.name)">🗑</button>
        </td>
      </tr>
    </tbody>
  </table>
</main>
</template>

<style>
main { font-family: system-ui; padding: 1rem; max-width: 900px; margin: auto; }
.controls { margin-bottom: 1rem; }
button { margin-right: 0.3rem; padding: 0.3rem 0.6rem; }
.error { color: red; }
table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
td, th { border: 1px solid #ccc; padding: 0.4rem; text-align: center; }
td.running { color: green; font-weight: bold; }
td.exited { color: red; font-weight: bold; }
</style>
