<script lang="ts">
  import { onMount } from "svelte";

  const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

  type FileItem = {
    id: string;
    name: string;
    size: number;
    mime_type: string;
    upload_date: string;
    path: string;
  };

  let files: FileItem[] = [];
  let selectedFile: FileList | null = null;
  let isLoading = false;
  let message: string | null = null;
  let error: string | null = null;

  async function fetchFiles() {
    isLoading = true;
    error = null;
    try {
      const res = await fetch(`${API_BASE}/files`);
      if (!res.ok) throw new Error("Error fetching files");
      files = await res.json();
    } catch (e) {
      console.error(e);
      error = "No se pudieron cargar los archivos";
    } finally {
      isLoading = false;
    }
  }

  async function upload() {
    if (!selectedFile || selectedFile.length === 0) {
      error = "Selecciona un archivo primero";
      return;
    }

    const file = selectedFile[0];
    const formData = new FormData();
    formData.append("file", file);

    isLoading = true;
    message = null;
    error = null;

    try {
      const res = await fetch(`${API_BASE}/files`, {
        method: "POST",
        body: formData
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Error al subir el archivo");
      }
      const created: FileItem = await res.json();
      files = [created, ...files];
      message = `Archivo "${created.name}" subido correctamente`;
      selectedFile = null;
    } catch (e: any) {
      console.error(e);
      error = e.message ?? "Error al subir el archivo";
    } finally {
      isLoading = false;
    }
  }

  async function rename(file: FileItem, newName: string) {
    if (!newName || newName === file.name) return;

    try {
      const res = await fetch(`${API_BASE}/files/${file.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newName })
      });
      if (!res.ok) throw new Error("Error al renombrar");
      const updated: FileItem = await res.json();
      files = files.map((f) => (f.id === file.id ? updated : f));
      message = `Archivo renombrado a "${updated.name}"`;
    } catch (e) {
      console.error(e);
      error = "No se pudo renombrar el archivo";
    }
  }

  async function remove(file: FileItem) {
    if (!confirm(`¿Eliminar "${file.name}"?`)) return;

    try {
      const res = await fetch(`${API_BASE}/files/${file.id}`, {
        method: "DELETE"
      });
      if (!res.ok) throw new Error("Error al eliminar");
      files = files.filter((f) => f.id !== file.id);
      message = `Archivo "${file.name}" eliminado`;
    } catch (e) {
      console.error(e);
      error = "No se pudo eliminar el archivo";
    }
  }

  function download(file: FileItem) {
    window.open(`${API_BASE}/files/${file.id}/download`, "_blank");
  }

  onMount(fetchFiles);
</script>

<main class="min-h-screen flex flex-col items-center py-10 px-4">
  <div class="w-full max-w-4xl">
    <h1 class="text-3xl font-bold mb-6 text-slate-800">Mini Drive</h1>

    {#if message}
      <div class="mb-4 rounded-lg bg-green-100 text-green-800 px-4 py-2 text-sm">
        {message}
      </div>
    {/if}
    {#if error}
      <div class="mb-4 rounded-lg bg-red-100 text-red-800 px-4 py-2 text-sm">
        {error}
      </div>
    {/if}

    <section class="mb-8">
      <div
        class="border-2 border-dashed border-slate-300 rounded-xl p-6 bg-white flex flex-col items-center gap-4"
      >
        <p class="text-sm text-slate-600">
          Arrastra un archivo aquí o selecciónalo desde tu ordenador
        </p>

        <input
          type="file"
          class="block text-sm text-slate-700"
          bind:files={selectedFile}
        />

        <button
          class="mt-2 inline-flex items-center px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium disabled:opacity-50"
          on:click|preventDefault={upload}
          disabled={isLoading}
        >
          {#if isLoading}
            Subiendo...
          {:else}
            Subir archivo
          {/if}
        </button>
      </div>
    </section>

    <section class="bg-white rounded-xl shadow-sm p-4">
      <div class="flex items-center justify-between mb-4">
        <h2 class="font-semibold text-slate-800">Archivos</h2>
        <button
          class="text-xs px-3 py-1 rounded-lg border border-slate-300 text-slate-700"
          on:click={fetchFiles}
          disabled={isLoading}
        >
          Recargar
        </button>
      </div>

      {#if isLoading && files.length === 0}
        <p class="text-sm text-slate-500">Cargando archivos...</p>
      {:else if files.length === 0}
        <p class="text-sm text-slate-500">No hay archivos subidos todavía.</p>
      {:else}
        <table class="w-full text-sm">
          <thead class="text-left text-slate-500 border-b">
            <tr>
              <th class="py-2">Nombre</th>
              <th class="py-2">Tipo</th>
              <th class="py-2">Fecha</th>
              <th class="py-2 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {#each files as file (file.id)}
              <tr class="border-b last:border-0">
                <td class="py-2 pr-4">
                  <input
                    class="w-full bg-transparent border border-transparent rounded px-1 py-0.5 hover:border-slate-300 focus:border-blue-500 focus:outline-none"
                    value={file.name}
                    on:change={(e) =>
                      rename(file, (e.target as HTMLInputElement).value)
                    }
                  />
                </td>
                <td class="py-2 pr-4 text-slate-500">{file.mime_type}</td>
                <td class="py-2 pr-4 text-slate-500">
                  {new Date(file.upload_date).toLocaleString()}
                </td>
                <td class="py-2 text-right space-x-2">
                  <button
                    class="text-xs px-2 py-1 rounded border border-slate-300 text-slate-700"
                    on:click={() => download(file)}
                  >
                    Descargar
                  </button>
                  <button
                    class="text-xs px-2 py-1 rounded bg-red-500 text-white"
                    on:click={() => remove(file)}
                  >
                    Eliminar
                  </button>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      {/if}
    </section>
  </div>
</main>
