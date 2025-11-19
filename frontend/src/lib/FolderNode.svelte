<script lang="ts">
  // OJO: este tipo es local al componente
  type Folder = {
    id: string;
    name: string;
    parent_id: string | null;
    owner: string;
    created_at: string;
  };

  export let folder: Folder;
  export let folders: Folder[];
  export let currentFolderId: string | null;
  export let onOpen: (id: string | null) => void;

  const children = () => folders.filter((f) => f.parent_id === folder.id);
</script>

<div class="ml-2">
  <button
    class={`block w-full text-left px-2 py-1 rounded text-xs hover:bg-slate-100 ${
      currentFolderId === folder.id ? "bg-slate-200 font-semibold" : ""
    }`}
    on:click={() => onOpen(folder.id)}
  >
    📁 {folder.name}
  </button>

  {#if children().length}
    <div class="ml-3 mt-1">
      {#each children() as child}
        <FolderNode
          folder={child}
          {folders}
          {currentFolderId}
          {onOpen}
        />
      {/each}
    </div>
  {/if}
</div>
