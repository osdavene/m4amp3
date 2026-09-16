document.addEventListener("DOMContentLoaded", () => {
    let selectedFiles = [];

    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("fileInput");
    const folderInput = document.getElementById("folderInput");
    const browseFilesBtn = document.getElementById("browseFilesBtn");
    const browseFolderBtn = document.getElementById("browseFolderBtn");
    const fileListContainer = document.getElementById("fileListContainer");
    const fileList = document.getElementById("fileList");
    const fileCount = document.getElementById("fileCount");
    const clearFilesBtn = document.getElementById("clearFilesBtn");
    const convertBtn = document.getElementById("convertBtn");
    const bitrateGroup = document.getElementById("bitrateGroup");
    const progressBox = document.getElementById("progressBox");
    const progressBarFill = document.getElementById("progressBarFill");
    const progressStatus = document.getElementById("progressStatus");
    const progressPercent = document.getElementById("progressPercent");
    const alertBox = document.getElementById("alertBox");

    const validExtensions = new Set([
        "m4a", "mp3", "wav", "flac", "ogg", "opus", "aac",
        "wma", "aiff", "aif", "m4r", "mp4", "webm", "mkv",
        "mov", "avi", "amr", "3gp"
    ]);

    // Button clicks
    browseFilesBtn.addEventListener("click", () => fileInput.click());
    browseFolderBtn.addEventListener("click", () => folderInput.click());

    // Drag and drop events
    ["dragenter", "dragover"].forEach((eventName) => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add("dragover");
        });
    });

    ["dragleave", "drop"].forEach((eventName) => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove("dragover");
        });
    });

    dropzone.addEventListener("drop", async (e) => {
        const items = e.dataTransfer.items;
        if (items && items.length > 0) {
            const files = [];
            for (let i = 0; i < items.length; i++) {
                const entry = items[i].webkitGetAsEntry ? items[i].webkitGetAsEntry() : null;
                if (entry) {
                    await traverseFileTree(entry, files);
                } else {
                    const file = items[i].getAsFile();
                    if (file) files.push(file);
                }
            }
            handleNewFiles(files);
        } else if (e.dataTransfer.files.length) {
            handleNewFiles(e.dataTransfer.files);
        }
    });

    // Helper for recursively reading folders dropped
    function traverseFileTree(item, fileListAcc) {
        return new Promise((resolve) => {
            if (item.isFile) {
                item.file((file) => {
                    fileListAcc.push(file);
                    resolve();
                });
            } else if (item.isDirectory) {
                const dirReader = item.createReader();
                dirReader.readEntries(async (entries) => {
                    for (const entry of entries) {
                        await traverseFileTree(entry, fileListAcc);
                    }
                    resolve();
                });
            } else {
                resolve();
            }
        });
    }

    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length) {
            handleNewFiles(e.target.files);
        }
    });

    folderInput.addEventListener("change", (e) => {
        if (e.target.files.length) {
            handleNewFiles(e.target.files);
        }
    });

    clearFilesBtn.addEventListener("click", () => {
        selectedFiles = [];
        fileInput.value = "";
        folderInput.value = "";
        updateFileListUI();
        hideAlert();
    });

    // Toggle bitrate visibility on format change
    document.querySelectorAll('input[name="target_format"]').forEach((radio) => {
        radio.addEventListener("change", (e) => {
            const val = e.target.value;
            if (val === "wav" || val === "flac" || val === "aiff") {
                bitrateGroup.style.opacity = "0.4";
                bitrateGroup.style.pointerEvents = "none";
            } else {
                bitrateGroup.style.opacity = "1";
                bitrateGroup.style.pointerEvents = "auto";
            }
        });
    });

    function handleNewFiles(files) {
        hideAlert();
        let addedCount = 0;
        for (const file of files) {
            const ext = file.name.split('.').pop().toLowerCase();
            if (!validExtensions.has(ext)) {
                continue;
            }

            const exists = selectedFiles.some(f => f.name === file.name && f.size === file.size);
            if (!exists) {
                selectedFiles.push(file);
                addedCount++;
            }
        }

        if (addedCount === 0 && files.length > 0 && selectedFiles.length === 0) {
            showAlert("No se encontraron archivos de audio compatibles.", "error");
        }
        updateFileListUI();
    }

    function formatBytes(bytes) {
        if (bytes === 0) return "0 Bytes";
        const k = 1024;
        const sizes = ["Bytes", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
    }

    function updateFileListUI() {
        if (selectedFiles.length === 0) {
            fileListContainer.style.display = "none";
            convertBtn.disabled = true;
            fileCount.textContent = "0";
            return;
        }

        fileListContainer.style.display = "block";
        fileCount.textContent = selectedFiles.length.toString();
        convertBtn.disabled = false;
        fileList.innerHTML = "";

        selectedFiles.forEach((file, index) => {
            const item = document.createElement("div");
            item.className = "file-item";

            const info = document.createElement("div");
            info.className = "file-info";
            info.innerHTML = `
                <span class="file-name">${escapeHtml(file.name)}</span>
                <span class="file-size">(${formatBytes(file.size)})</span>
            `;

            const removeBtn = document.createElement("button");
            removeBtn.className = "btn-remove-file";
            removeBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            `;
            removeBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                selectedFiles.splice(index, 1);
                updateFileListUI();
            });

            item.appendChild(info);
            item.appendChild(removeBtn);
            fileList.appendChild(item);
        });
    }

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    function showAlert(msg, type = "success") {
        alertBox.textContent = msg;
        alertBox.className = `alert-box alert-${type}`;
        alertBox.style.display = "block";
    }

    function hideAlert() {
        alertBox.style.display = "none";
    }

    // Conversion Logic
    convertBtn.addEventListener("click", async () => {
        if (selectedFiles.length === 0) return;

        const formatRadio = document.querySelector('input[name="target_format"]:checked');
        const targetFormat = formatRadio ? formatRadio.value : "mp3";

        const bitrateRadio = document.querySelector('input[name="bitrate"]:checked');
        const bitrate = bitrateRadio ? bitrateRadio.value : "192k";

        hideAlert();
        convertBtn.disabled = true;
        progressBox.style.display = "block";
        progressBarFill.style.width = "0%";
        progressStatus.textContent = "Subiendo y convirtiendo audios...";
        progressPercent.textContent = "0%";

        const formData = new FormData();
        selectedFiles.forEach(file => {
            formData.append("files", file);
        });
        formData.append("target_format", targetFormat);
        formData.append("bitrate", bitrate);

        const xhr = new XMLHttpRequest();
        xhr.open("POST", "/api/convert", true);
        xhr.responseType = "blob";

        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 60);
                progressBarFill.style.width = `${percent}%`;
                progressPercent.textContent = `${percent}%`;
                if (percent >= 60) {
                    progressStatus.textContent = `FFmpeg convirtiendo a .${targetFormat.toUpperCase()}...`;
                }
            }
        };

        xhr.onload = async () => {
            progressBarFill.style.width = "100%";
            progressPercent.textContent = "100%";

            if (xhr.status === 200) {
                progressStatus.textContent = "¡Conversión completada!";
                
                let filename = selectedFiles.length === 1 
                    ? selectedFiles[0].name.replace(/\.[^/.]+$/, "") + "." + targetFormat
                    : `audios_${targetFormat}.zip`;

                const disposition = xhr.getResponseHeader("Content-Disposition");
                if (disposition && disposition.indexOf("filename=") !== -1) {
                    const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
                    if (matches != null && matches[1]) {
                        filename = matches[1].replace(/['"]/g, "");
                    }
                }

                const blob = xhr.response;
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = downloadUrl;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(downloadUrl);
                a.remove();

                showAlert(`¡Éxito! Archivo "${filename}" descargado con éxito.`, "success");
            } else {
                progressStatus.textContent = "Error en la conversión.";
                try {
                    const errorText = await xhr.response.text();
                    const errorJson = JSON.parse(errorText);
                    const errorDetail = errorJson.detail?.message || errorJson.detail || "Error al procesar los archivos.";
                    showAlert(`Error: ${errorDetail}`, "error");
                } catch {
                    showAlert("Ocurrió un error inesperado en el servidor.", "error");
                }
            }

            convertBtn.disabled = false;
        };

        xhr.onerror = () => {
            progressStatus.textContent = "Error de conexión.";
            showAlert("No se pudo conectar con el servidor.", "error");
            convertBtn.disabled = false;
        };

        xhr.send(formData);
    });
});
