// LOOP - Web Interface JavaScript

class LoopApp {
  constructor() {
    this.init();
    this.setupEventListeners();
    this.updateStatus();

    // Update status every 5 seconds
    setInterval(() => this.updateStatus(), 5000);
  }

  init() {
    console.log("🎬 LOOP Web Interface initialized");
    this.showAlert("Connected to LOOP!", "success");
  }

  setupEventListeners() {
    // Upload functionality
    this.setupUpload();

    // Media controls
    this.setupControls();

    // Keyboard shortcuts
    this.setupKeyboardShortcuts();
  }

  setupUpload() {
    const uploadArea = document.getElementById("upload-area");
    const fileInput = document.getElementById("file-input");

    if (!uploadArea || !fileInput) return;

    // Click to upload
    uploadArea.addEventListener("click", () => {
      fileInput.click();
    });

    // File input change
    fileInput.addEventListener("change", (e) => {
      const files = Array.from(e.target.files);
      if (files.length > 0) {
        this.uploadFiles(files);
      }
    });

    // Drag and drop
    uploadArea.addEventListener("dragover", (e) => {
      e.preventDefault();
      uploadArea.classList.add("dragover");
    });

    uploadArea.addEventListener("dragleave", (e) => {
      e.preventDefault();
      uploadArea.classList.remove("dragover");
    });

    uploadArea.addEventListener("drop", (e) => {
      e.preventDefault();
      uploadArea.classList.remove("dragover");

      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) {
        this.uploadFiles(files);
      }
    });
  }

  setupControls() {
    // Play/Pause button
    const playPauseBtn = document.getElementById("play-pause-btn");
    if (playPauseBtn) {
      playPauseBtn.addEventListener("click", () => {
        this.togglePlayPause();
      });
    }

    // Previous button
    const prevBtn = document.getElementById("prev-btn");
    if (prevBtn) {
      prevBtn.addEventListener("click", () => {
        this.previousMedia();
      });
    }

    // Next button
    const nextBtn = document.getElementById("next-btn");
    if (nextBtn) {
      nextBtn.addEventListener("click", () => {
        this.nextMedia();
      });
    }

    // Media item clicks
    document.addEventListener("click", (e) => {
      if (e.target.closest(".media-item")) {
        const mediaItem = e.target.closest(".media-item");
        const slug = mediaItem.dataset.slug;
        if (slug) {
          this.activateMedia(slug);
        }
      }
    });
  }

  setupKeyboardShortcuts() {
    document.addEventListener("keydown", (e) => {
      // Ignore if typing in an input
      if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") {
        return;
      }

      switch (e.key) {
        case " ":
          e.preventDefault();
          this.togglePlayPause();
          break;
        case "ArrowLeft":
          e.preventDefault();
          this.previousMedia();
          break;
        case "ArrowRight":
          e.preventDefault();
          this.nextMedia();
          break;
      }
    });
  }

  async uploadFiles(files) {
    for (const file of files) {
      await this.uploadFile(file);
    }
    this.refreshMediaList();
  }

  async uploadFile(file) {
    const formData = new FormData();
    formData.append("file", file);

    try {
      this.showAlert(`Uploading ${file.name}...`, "info");

      const response = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();

      if (result.success) {
        this.showAlert(`Successfully uploaded ${file.name}!`, "success");
      } else {
        this.showAlert(
          `Failed to upload ${file.name}: ${result.detail || "Unknown error"}`,
          "error"
        );
      }
    } catch (error) {
      console.error("Upload error:", error);
      this.showAlert(`Error uploading ${file.name}: ${error.message}`, "error");
    }
  }

  async togglePlayPause() {
    try {
      const response = await fetch("/api/playback/toggle", {
        method: "POST",
      });

      if (response.ok) {
        this.updateStatus();
      }
    } catch (error) {
      console.error("Toggle play/pause error:", error);
      this.showAlert("Failed to toggle playback", "error");
    }
  }

  async previousMedia() {
    try {
      const response = await fetch("/api/playback/previous", {
        method: "POST",
      });

      if (response.ok) {
        this.updateStatus();
        this.refreshMediaList();
      }
    } catch (error) {
      console.error("Previous media error:", error);
      this.showAlert("Failed to go to previous media", "error");
    }
  }

  async nextMedia() {
    try {
      const response = await fetch("/api/playback/next", {
        method: "POST",
      });

      if (response.ok) {
        this.updateStatus();
        this.refreshMediaList();
      }
    } catch (error) {
      console.error("Next media error:", error);
      this.showAlert("Failed to go to next media", "error");
    }
  }

  async activateMedia(slug) {
    try {
      const response = await fetch(`/api/media/${slug}/activate`, {
        method: "POST",
      });

      const result = await response.json();

      if (result.success) {
        this.showAlert(result.message, "success");
        this.refreshMediaList();
      } else {
        this.showAlert("Failed to activate media", "error");
      }
    } catch (error) {
      console.error("Activate media error:", error);
      this.showAlert("Failed to activate media", "error");
    }
  }

  async updateStatus() {
    try {
      const response = await fetch("/api/status");
      const status = await response.json();

      // Update status indicator
      const statusIndicator = document.getElementById("status-indicator");
      if (statusIndicator) {
        statusIndicator.className = "status-indicator online";
        statusIndicator.textContent = "● Online";
      }

      // Update play/pause button
      const playPauseBtn = document.getElementById("play-pause-btn");
      if (playPauseBtn && status.playback) {
        playPauseBtn.innerHTML = status.playback.paused ? "▶️" : "⏸️";
        playPauseBtn.title = status.playback.paused ? "Play" : "Pause";
      }
    } catch (error) {
      console.error("Status update error:", error);

      // Update status indicator to offline
      const statusIndicator = document.getElementById("status-indicator");
      if (statusIndicator) {
        statusIndicator.className = "status-indicator offline";
        statusIndicator.textContent = "● Offline";
      }
    }
  }

  async refreshMediaList() {
    try {
      const response = await fetch("/api/media");
      const mediaData = await response.json();

      const mediaGrid = document.getElementById("media-grid");
      if (!mediaGrid) return;

      mediaGrid.innerHTML = "";

      if (mediaData.media && mediaData.media.length > 0) {
        mediaData.media.forEach((media) => {
          const mediaItem = this.createMediaItem(
            media,
            media.slug === mediaData.active
          );
          mediaGrid.appendChild(mediaItem);
        });
      } else {
        mediaGrid.innerHTML =
          '<div class="no-media">No media files uploaded yet. Drag and drop files above to get started!</div>';
      }
    } catch (error) {
      console.error("Refresh media list error:", error);
    }
  }

  createMediaItem(media, isActive) {
    const item = document.createElement("div");
    item.className = `media-item ${isActive ? "active" : ""}`;
    item.dataset.slug = media.slug;

    const typeIcon = this.getMediaTypeIcon(media.type);

    item.innerHTML = `
            <div class="media-thumbnail">
                ${typeIcon}
            </div>
            <div class="media-info">
                <div class="media-name" title="${media.original_filename}">${
      media.original_filename
    }</div>
                <div class="media-details">
                    ${media.type.toUpperCase()} • ${media.frame_count} frames
                    ${media.width}×${media.height}
                </div>
            </div>
        `;

    return item;
  }

  getMediaTypeIcon(type) {
    const icons = {
      gif: "GIF",
      video: "VIDEO",
      image: "IMG",
    };
    return icons[type] || "DOC";
  }

  showAlert(message, type = "info") {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll(".alert");
    existingAlerts.forEach((alert) => alert.remove());

    // Create new alert
    const alert = document.createElement("div");
    alert.className = `alert alert-${type}`;
    alert.textContent = message;

    // Insert at top of container
    const container = document.querySelector(".container");
    if (container) {
      container.insertBefore(alert, container.firstChild);

      // Auto-remove after 5 seconds
      setTimeout(() => {
        if (alert.parentNode) {
          alert.remove();
        }
      }, 5000);
    }
  }
}

// Initialize when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  window.loopApp = new LoopApp();
});
