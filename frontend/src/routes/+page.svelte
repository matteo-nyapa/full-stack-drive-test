<script lang="ts">
  import { onMount } from "svelte";
  import FolderNode from "$lib/FolderNode.svelte";

  const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

  type FileItem = {
    id: string;
    name: string;
    size: number;
    mime_type: string;
    upload_date: string;
    path: string;
    folder_id: string | null;
    owner: string;
  };

  type Folder = {
    id: string;
    name: string;
    parent_id: string | null;
    owner: string;
    created_at: string;
  };

  // ---------- AUTH ----------
  let username = "";
  let password = "";
  let token: string | null = null;
  let isLoggedIn = false;

  // ---------- FOLDERS / FILES ----------
  let folders: Folder[] = [];
  let currentFolderId: string | null = null; // null = root
  let files: FileItem[] = [];
  let search = "";

  // Upload
  let selectedFile: FileList | null = null;
  let isLoading = false;

  // New folder
  let newFolderName = "";

  // Messages
  let message: string | null = null;
  let error: string | null = null;

  // ---------- HELPERS ----------
  function setMessage(msg: string | null, err: string | null = null) {
    message = msg;
    error = err;
  }

  function ensureLoggedIn(): boolean {
    if (!token) {
      setMessage(null, "You must be logged in to use the drive.");
      return false;
    }
    return true;
  }

  function getAuthHeaders(): HeadersInit {
    const headers: HeadersInit = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    return headers;
  }

  function saveAuth() {
    if (token && username) {
      localStorage.setItem("drive-token", token);
      localStorage.setItem("drive-username", username);
    } else {
      localStorage.removeItem("drive-token");
      localStorage.removeItem("drive-username");
    }
  }

  function loadAuth() {
    const storedToken = localStorage.getItem("drive-token");
    const storedUser = localStorage.getItem("drive-username");
    if (storedToken && storedUser) {
      token = storedToken;
      username = storedUser;
      isLoggedIn = true;
    }
  }

  // breadcrumbs del path actual
  function getCurrentPath(): Folder[] {
    if (!currentFolderId) return [];
    const map = new Map<string, Folder>();
    folders.forEach((f) => map.set(f.id, f));
    const path: Folder[] = [];
    let current = map.get(currentFolderId);
    while (current) {
      path.unshift(current);
      current = current.parent_id ? map.get(current.parent_id) ?? null : null;
    }
    return path;
  }

  function buildFilesQuery() {
    const params = new URLSearchParams();
    if (currentFolderId) {
      params.append("folder_id", currentFolderId);
    } else {
      // root
      params.append("folder_id", "root");
    }
    if (search.trim()) {
      params.append("q", search.trim());
    }
    const qs = params.toString();
    return qs ? `?${qs}` : "";
  }

  // ---------- AUTH ----------
  async function handleAuth(endpoint: "login" | "register") {
    setMessage(null, null);

    if (!username.trim() || !password.trim()) {
      setMessage(null, "Username and password are required.");
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/auth/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: username.trim(),
          password: password.trim()
        })
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        const detail = data?.detail ?? "Authentication failed.";
        throw new Error(detail);
      }

      const data = (await res.json()) as { access_token: string };
      token = data.access_token;
      isLoggedIn = true;
      saveAuth();
      password = "";

      setMessage(
        endpoint === "login"
          ? `Welcome back, ${username}!`
          : `User ${username} registered successfully.`
      );

      await refreshAll();
    } catch (e: any) {
      console.error(e);
      setMessage(null, e.message ?? "Authentication error.");
      token = null;
      isLoggedIn = false;
      saveAuth();
    }
  }

  function logout() {
    token = null;
    isLoggedIn = false;
    files = [];
    folders = [];
    currentFolderId = null;
    saveAuth();
    setMessage("You have been logged out.");
  }

  // ---------- API CALLS ----------
  async function fetchFolders() {
    if (!ensureLoggedIn()) return;
    try {
      const res = await fetch(`${API_BASE}/folders`, {
        headers: getAuthHeaders()
      });
      if (!res.ok) throw new Error("Failed to load folders.");
      folders = await res.json();
    } catch (e: any) {
      console.error(e);
      setMessage(null, e.message ?? "Could not load folders.");
    }
  }

  async function fetchFiles() {
    if (!ensureLoggedIn()) return;
    isLoading = true;
    setMessage(null, null);

    try {
      const res = await fetch(`${API_BASE}/files${buildFilesQuery()}`, {
        headers: getAuthHeaders()
      });
      if (!res.ok) throw new Error("Failed to load files.");
      files = await res.json();
    } catch (e: any) {
      console.error(e);
      setMessage(null, e.message ?? "Could not load files.");
    } finally {
      isLoading = false;
    }
  }

  async function refreshAll() {
    await fetchFolders();
    await fetchFiles();
  }

  async function createFolder() {
    if (!ensureLoggedIn()) return;
    if (!newFolderName.trim()) return;

    try {
      const res = await fetch(`${API_BASE}/folders`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders()
        },
        body: JSON.stringify({
          name: newFolderName.trim(),
          parent_id: currentFolderId
        })
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        const detail = data?.detail ?? "Error creating folder.";
        throw new Error(detail);
      }
      const created: Folder = await res.json();
      folders = [...folders, created];
      newFolderName = "";
      setMessage(`Folder "${created.name}" created.`);
    } catch (e: any) {
      console.error(e);
      setMessage(null, e.message ?? "Could not create folder.");
    }
  }

  async function upload() {
    if (!ensureLoggedIn()) return;
    if (!selectedFile || selectedFile.length === 0) {
      setMessage(null, "Please select a file first.");
      return;
    }

    const file = selectedFile[0];
    const formData = new FormData();
    formData.append("file", file);
    formData.append("folder_id", currentFolderId ?? "root");

    isLoading = true;
    setMessage(null, null);

    try {
      const res = await fetch(`${API_BASE}/files`, {
        method: "POST",
        body: formData,
        headers: getAuthHeaders()
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        const detail = data?.detail ?? "Error uploading file.";
        throw new Error(detail);
      }
      const created: FileItem = await res.json();
      files = [created, ...files];
      setMessage(`File "${created.name}" uploaded successfully.`);
      selectedFile = null;
    } catch (e: any) {
      console.error(e);
      setMessage(null, e.message ?? "Error uploading file.");
    } finally {
      isLoading = false;
    }
  }

  async function rename(file: FileItem, newName: string) {
    if (!ensureLoggedIn()) return;
    if (!newName || newName === file.name) return;

    try {
      const res = await fetch(`${API_BASE}/files/${file.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders()
        },
        body: JSON.stringify({ name: newName })
      });
      if (!res.ok) throw new Error("Error renaming file.");
      const updated: FileItem = await res.json();
      files = files.map((f) => (f.id === file.id ? updated : f));
      setMessage(`File renamed to "${updated.name}".`);
    } catch (e: any) {
      console.error(e);
      setMessage(null, e.message ?? "Could not rename file.");
    }
  }

  async function remove(file: FileItem) {
    if (!ensureLoggedIn()) return;
    if (!confirm(`Delete "${file.name}"?`)) return;

    try {
      const res = await fetch(`${API_BASE}/files/${file.id}`, {
        method: "DELETE",
        headers: getAuthHeaders()
      });
      if (!res.ok) throw new Error("Error deleting file.");
      files = files.filter((f) => f.id !== file.id);
      setMessage(`File "${file.name}" deleted.`);
    } catch (e: any) {
      console.error(e);
      setMessage(null, e.message ?? "Could not delete file.");
    }
  }

  function download(file: FileItem) {
    if (!ensureLoggedIn()) return;
    const url = `${API_BASE}/files/${file.id}/download`;
    window.open(url, "_blank");
  }

  function openFolder(folderId: string | null) {
    currentFolderId = folderId;
    fetchFiles();
  }

  function applySearch() {
    fetchFiles();
  }

  // ---------- LIFECYCLE ----------
  onMount(async () => {
    loadAuth();
    if (isLoggedIn) {
      await refreshAll();
    }
  });
</script>

<main class="min-h-screen flex items-center justify-center bg-slate-100 px-4">
  {#if !isLoggedIn}
    <!-- LOGIN SCREEN -->
    <div class="w-full max-w-md bg-white rounded-2xl shadow-md p-6">
      <h1 class="text-2xl font-bold mb-4 text-slate-800 text-center">Mini Drive</h1>

      {#if message}
        <div class="mb-3 rounded-lg bg-green-100 text-green-800 px-3 py-2 text-sm">
          {message}
        </div>
      {/if}
      {#if error}
        <div class="mb-3 rounded-lg bg-red-100 text-red-800 px-3 py-2 text-sm">
          {error}
        </div>
      {/if}

      <div class="flex flex-col gap-3 mb-4">
        <div class="flex flex-col gap-1">
          <label class="text-sm text-slate-600" for="login-username">Username</label>
          <input
            id="login-username"
            type="text"
            bind:value={username}
            class="border rounded-lg px-3 py-2 text-sm border-slate-300 focus:outline-none focus:border-blue-500"
          />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm text-slate-600" for="login-password">Password</label>
          <input
            id="login-password"
            type="password"
            bind:value={password}
            class="border rounded-lg px-3 py-2 text-sm border-slate-300 focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      <div class="flex gap-3 justify-center">
        <button
          class="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium"
          on:click={() => handleAuth("login")}
        >
          Login
        </button>
        <button
          class="px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm font-medium"
          on:click={() => handleAuth("register")}
        >
          Register
        </button>
      </div>
    </div>
  {:else}
    <!-- APP -->
    <div class="w-full max-w-6xl flex gap-6">
      <!-- SIDEBAR: FOLDERS TREE -->
      <aside class="w-64 bg-white rounded-xl shadow-sm p-4 flex flex-col">
        <div class="flex items-center justify-between mb-3">
          <span class="font-semibold text-slate-800 text-sm">Folders</span>
        </div>

        <button
          class="text-left text-sm mb-2 px-2 py-1 rounded hover:bg-slate-100"
          on:click={() => openFolder(null)}
        >
          📁 <strong>My Drive</strong>
        </button>

        <div class="flex-1 overflow-y-auto text-sm">
          {#each folders as folder}
            {#if folder.parent_id === null}
              <FolderNode
                {folder}
                {folders}
                {currentFolderId}
                onOpen={openFolder}
              />
            {/if}
          {/each}
        </div>

        <div class="mt-4 pt-3 border-t flex flex-col gap-2">
          <label class="text-xs text-slate-500" for="new-folder-name">
            New folder in current path
          </label>
          <div class="flex gap-2">
            <input
              id="new-folder-name"
              type="text"
              placeholder="Folder name"
              bind:value={newFolderName}
              class="flex-1 border rounded-lg px-2 py-1 text-xs border-slate-300 focus:outline-none focus:border-blue-500"
            />
            <button
              class="px-3 py-1 rounded-lg bg-blue-600 text-white text-xs font-medium"
              on:click={createFolder}
            >
              Create
            </button>
          </div>
        </div>
      </aside>

      <!-- MAIN CONTENT -->
      <div class="flex-1">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h1 class="text-2xl font-bold text-slate-800">Mini Drive</h1>
            <p class="text-xs text-slate-500">
              Logged in as <strong>{username}</strong>
            </p>
          </div>
          <button
            class="px-3 py-1 rounded-lg border border-slate-300 text-xs text-slate-700"
            on:click={logout}
          >
            Logout
          </button>
        </div>

        {#if message}
          <div class="mb-3 rounded-lg bg-green-100 text-green-800 px-4 py-2 text-sm">
            {message}
          </div>
        {/if}
        {#if error}
          <div class="mb-3 rounded-lg bg-red-100 text-red-800 px-4 py-2 text-sm">
            {error}
          </div>
        {/if}

        <!-- BREADCRUMBS -->
        <div class="mb-4 text-xs text-slate-600 flex items-center flex-wrap gap-1">
          <button
            class="hover:underline"
            on:click={() => openFolder(null)}
          >
            My Drive
          </button>
          {#each getCurrentPath() as folder}
            <span>/</span>
            <button
              class="hover:underline"
              on:click={() => openFolder(folder.id)}
            >
              {folder.name}
            </button>
          {/each}
        </div>

        <!-- UPLOAD -->
        <section class="mb-6">
          <div
            class="border-2 border-dashed border-slate-300 rounded-xl p-4 bg-white flex flex-col gap-3"
          >
            <p class="text-sm text-slate-600">
              Upload to this folder.
            </p>
            <input
              id="file-input"
              type="file"
              class="block text-sm text-slate-700"
              bind:files={selectedFile}
            />
            <button
              class="inline-flex items-center px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium disabled:opacity-50"
              on:click|preventDefault={upload}
              disabled={isLoading}
            >
              {#if isLoading}
                Uploading...
              {:else}
                Upload file
              {/if}
            </button>
          </div>
        </section>

        <!-- SEARCH -->
        <section class="mb-4 flex items-center gap-2">
          <input
            id="search-input"
            type="text"
            placeholder="Search by name..."
            bind:value={search}
            class="flex-1 border rounded-lg px-3 py-1 text-sm border-slate-300 focus:outline-none focus:border-blue-500"
          />
          <button
            class="text-xs px-3 py-1 rounded-lg border border-slate-300 text-slate-700"
            on:click={applySearch}
          >
            Search
          </button>
          <button
            class="text-xs px-3 py-1 rounded-lg border border-slate-300 text-slate-700"
            on:click={refreshAll}
          >
            Reload
          </button>
        </section>

        <!-- FILES -->
        <section class="bg-white rounded-xl shadow-sm p-4">
          {#if isLoading && files.length === 0}
            <p class="text-sm text-slate-500">Loading files...</p>
          {:else if files.length === 0}
            <p class="text-sm text-slate-500">No files in this folder.</p>
          {:else}
            <table class="w-full text-sm">
              <thead class="text-left text-slate-500 border-b">
                <tr>
                  <th class="py-2">Name</th>
                  <th class="py-2">Type</th>
                  <th class="py-2">Date</th>
                  <th class="py-2 text-right">Actions</th>
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
                    <td class="py-2 pr-4 text-slate-500">
                      {file.mime_type}
                    </td>
                    <td class="py-2 pr-4 text-slate-500">
                      {new Date(file.upload_date).toLocaleString()}
                    </td>
                    <td class="py-2 text-right space-x-2">
                      <button
                        class="text-xs px-2 py-1 rounded border border-slate-300 text-slate-700"
                        on:click={() => download(file)}
                      >
                        Download
                      </button>
                      <button
                        class="text-xs px-2 py-1 rounded bg-red-500 text-white"
                        on:click={() => remove(file)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          {/if}
        </section>
      </div>
    </div>
  {/if}
</main>
