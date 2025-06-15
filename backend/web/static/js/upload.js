// Initialize media processor
const mediaProcessor = new MediaProcessor();

// File upload handling
function initializeUpload() {
  const uploadArea = document.getElementById("uploadArea");
  const fileInput = document.getElementById("fileInput");
  const uploadProgress = document.getElementById("uploadProgress");
  const progressBar = document.getElementById("progressBar");
  const uploadStatus = document.getElementById("uploadStatus");

  // Drag and drop handling
  uploadArea.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadArea.classList.add("drag-over");
  });

  uploadArea.addEventListener("dragleave", () => {
    uploadArea.classList.remove("drag-over");
  });

  uploadArea.addEventListener("drop", async (e) => {
    e.preventDefault();
    uploadArea.classList.remove("drag-over");

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      await handleFiles(files);
    }
  });

  // File input handling
  fileInput.addEventListener("change", async () => {
    if (fileInput.files.length > 0) {
      await handleFiles(fileInput.files);
    }
  });

  async function handleFiles(files) {
    uploadProgress.classList.remove("hidden");

    for (const file of files) {
      try {
        uploadStatus.textContent = `Processing ${file.name}...`;
        progressBar.style.width = "10%";

        // Process file in browser if possible
        const processed = await mediaProcessor.processFile(file);

        uploadStatus.textContent = `Uploading ${file.name}...`;
        progressBar.style.width = "50%";

        // Upload to server
        const response = await uploadFile(processed);

        if (response.success) {
          uploadStatus.textContent = `Successfully uploaded ${file.name}`;
          progressBar.style.width = "100%";

          // Refresh media list
          setTimeout(() => {
            window.location.reload();
          }, 1000);
        } else {
          throw new Error(response.message || "Upload failed");
        }
      } catch (error) {
        console.error("Upload error:", error);
        uploadStatus.textContent = `Error: ${error.message}`;
        progressBar.style.width = "0%";
      }
    }
  }

  async function uploadFile(processed) {
    if (processed.formData) {
      // Upload pre-processed frames
      const response = await fetch("/api/upload", {
        method: "POST",
        body: processed.formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Upload failed");
      }

      return await response.json();
    } else {
      // Regular file upload (for videos or fallback)
      const formData = new FormData();
      formData.append("file", processed.file);

      const response = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Upload failed");
      }

      return await response.json();
    }
  }
}

// Initialize when DOM is ready
document.addEventListener("DOMContentLoaded", initializeUpload);
