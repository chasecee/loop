class MediaProcessor {
  constructor(targetWidth = 240, targetHeight = 320) {
    this.targetWidth = targetWidth;
    this.targetHeight = targetHeight;
    this.gifFrameReader = null;
  }

  async processFile(file) {
    if (file.type.startsWith("image/gif")) {
      return await this.processGif(file);
    } else if (file.type.startsWith("image/")) {
      return await this.processImage(file);
    }
    // For videos, we'll still use server-side processing
    return { file };
  }

  async processGif(file) {
    const frames = await this.extractGifFrames(file);
    const processedFrames = await this.processFrames(frames);

    // Create a FormData with processed frames
    const formData = new FormData();
    formData.append("original_file", file);

    processedFrames.forEach((frame, index) => {
      formData.append(
        `frame_${index.toString().padStart(6, "0")}.jpg`,
        frame.blob
      );
      formData.append(`duration_${index}`, frame.delay / 1000); // Convert to seconds
    });

    return {
      formData,
      metadata: {
        type: "gif",
        frame_count: frames.length,
        original_filename: file.name,
        width: this.targetWidth,
        height: this.targetHeight,
        durations: processedFrames.map((f) => f.delay / 1000),
      },
    };
  }

  async processImage(file) {
    const img = await this.loadImage(file);
    const canvas = document.createElement("canvas");
    canvas.width = this.targetWidth;
    canvas.height = this.targetHeight;

    const ctx = canvas.getContext("2d");
    ctx.drawImage(img, 0, 0, this.targetWidth, this.targetHeight);

    const blob = await new Promise((resolve) => {
      canvas.toBlob(resolve, "image/jpeg", 0.85);
    });

    const formData = new FormData();
    formData.append("file", blob, file.name.replace(/\.[^/.]+$/, ".jpg"));

    return { formData };
  }

  async extractGifFrames(file) {
    // We'll use the gif.js library for this
    if (!this.gifFrameReader) {
      // Load gif.js dynamically if needed
      await this.loadGifJs();
    }

    return new Promise((resolve, reject) => {
      const frames = [];
      const reader = new FileReader();

      reader.onload = (e) => {
        const gif = new GIF({
          src: e.target.result,
          onload: () => {
            for (let i = 0; i < gif.frames.length; i++) {
              frames.push({
                imageData: gif.frames[i].imageData,
                delay: gif.frames[i].delay,
              });
            }
            resolve(frames);
          },
          onerror: reject,
        });
      };

      reader.readAsDataURL(file);
    });
  }

  async processFrames(frames) {
    return Promise.all(
      frames.map(async (frame) => {
        const canvas = document.createElement("canvas");
        canvas.width = this.targetWidth;
        canvas.height = this.targetHeight;

        const ctx = canvas.getContext("2d");
        ctx.putImageData(frame.imageData, 0, 0);

        // Resize if needed
        if (
          frame.imageData.width !== this.targetWidth ||
          frame.imageData.height !== this.targetHeight
        ) {
          const tempCanvas = document.createElement("canvas");
          tempCanvas.width = this.targetWidth;
          tempCanvas.height = this.targetHeight;
          const tempCtx = tempCanvas.getContext("2d");
          tempCtx.drawImage(canvas, 0, 0, this.targetWidth, this.targetHeight);
          canvas = tempCanvas;
        }

        const blob = await new Promise((resolve) => {
          canvas.toBlob(resolve, "image/jpeg", 0.85);
        });

        return {
          blob,
          delay: frame.delay,
        };
      })
    );
  }

  loadImage(file) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = reject;
      img.src = URL.createObjectURL(file);
    });
  }

  async loadGifJs() {
    if (typeof GIF !== "undefined") return;

    return new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = "/static/js/lib/gif.js";
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }
}

// Export for use in other modules
window.MediaProcessor = MediaProcessor;
