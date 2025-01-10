<template>
  <div id="app">
    <h1>GlassFinder</h1>

    <!-- Upload Section -->
    <input type="file" @change="onImageUpload" accept="image/*" />
    <div v-if="imageSrc" class="image-container">
      <canvas
        ref="imageCanvas"
        @mousedown="onMouseDown"
        @mousemove="onMouseMove"
        @mouseup="onMouseUp"
        @click="onCanvasClick"
        @contextmenu.prevent="onContextMenu"
      ></canvas>
    </div>

    <!-- Control Buttons -->
    <div class="control-buttons">
      <button @click="toggleDrawMode" class="toggle-button">
        {{ drawMode ? 'Disable Draw Mode' : 'Enable Draw Mode' }}
      </button>
      <button @click="downloadAnnotatedImage" :disabled="!annotations.length" class="download-button">
        Download Annotated Image
      </button>
    </div>

    <!-- Context Menu -->
    <div v-if="showContextMenu" :style="contextMenuStyle" class="context-menu">
      <button @click="deleteAnnotation">Delete</button>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  data() {
    return {
      image: null,
      imageSrc: "",
      annotations: [], // Format: [{ points: [{ x, y }, { x, y }, { x, y }, { x, y }] }]
      isDragging: false,
      drawMode: false, // Toggle between draw and drag modes
      newAnnotation: null, // Temporary storage for new quadrilateral
      selectedAnnotation: null, // Annotation selected for context menu
      showContextMenu: false, // Display the context menu
      contextMenuStyle: {},
      draggingPoint: null, // Corner being dragged
    };
  },
  methods: {
    onImageUpload(event) {
      const file = event.target.files[0];
      if (file) {
        this.image = file;
        this.annotations = []; // Clear existing annotations

        const reader = new FileReader();
        reader.onload = (e) => {
          this.imageSrc = e.target.result;
          this.loadImageToCanvas();
        };
        reader.readAsDataURL(file);

        // Automatically send the image to the backend
        const formData = new FormData();
        formData.append("file", file);

        axios
          .post("http://127.0.0.1:8000/predict/?threshold=0.5&target_class_id=10", formData)
          .then((response) => {
            this.annotations = response.data.predictions.map(({ linearized_contours }) => {
              return { points: linearized_contours[0].map(([x, y]) => ({ x, y })) };
            });
            this.loadImageToCanvas();
          })
          .catch((error) => {
            console.error("Error sending image to backend:", error);
          });
      }
    },
    loadImageToCanvas() {
      const canvas = this.$refs.imageCanvas;
      if (!canvas) {
        console.error("Canvas reference is not available");
        return;
      }
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        console.error("Canvas context could not be initialized");
        return;
      }
      const image = new Image();
      image.onload = () => {
        canvas.width = image.width;
        canvas.height = image.height;
        ctx.drawImage(image, 0, 0);
        this.drawAnnotations();
      };
      image.src = this.imageSrc;
    },
    drawAnnotations() {
      const canvas = this.$refs.imageCanvas;
      const ctx = canvas.getContext("2d");
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const image = new Image();
      image.src = this.imageSrc;
      ctx.drawImage(image, 0, 0);

      this.annotations.forEach((annotation) => {
        const { points } = annotation;

        ctx.beginPath();
        points.forEach(({ x, y }, index) => {
          if (index === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        });
        ctx.closePath();
        ctx.lineWidth = annotation === this.selectedAnnotation ? 3 : 2;
        ctx.strokeStyle = annotation === this.selectedAnnotation ? "blue" : "rgb(85, 255, 51)"; // Default prediction color
        ctx.stroke();
      });
    },
    onMouseDown(event) {
      const canvas = this.$refs.imageCanvas;
      const rect = canvas.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;

      if (this.drawMode) {
        // Start a new quadrilateral
        this.newAnnotation = { points: [{ x, y }, { x, y }, { x, y }, { x, y }] };
      } else {
        // Dragging mode: Check if a corner is being dragged
        this.draggingPoint = null;
        this.selectedAnnotation = this.annotations.find(({ points }) => {
          return points.some((point, index) => {
            if (Math.abs(point.x - x) < 10 && Math.abs(point.y - y) < 10) {
              this.draggingPoint = { annotation: points, pointIndex: index };
              return true;
            }
            return false;
          });
        });

        if (this.selectedAnnotation) {
          this.showContextMenu = false;
        }
      }
    },
    onCanvasClick(event) {
      const canvas = this.$refs.imageCanvas;
      const rect = canvas.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;

      const clickedAnnotation = this.annotations.find(({ points }) => {
        // Check if click is inside the annotation
        let inside = false;
        for (let i = 0, j = points.length - 1; i < points.length; j = i++) {
          const { x: xi, y: yi } = points[i];
          const { x: xj, y: yj } = points[j];
          const intersect = yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi;
          if (intersect) inside = !inside;
        }
        return inside;
      });

      if (clickedAnnotation) {
        this.selectedAnnotation = clickedAnnotation;
      } else {
        this.selectedAnnotation = null;
      }
      this.loadImageToCanvas();
    },
    onMouseMove(event) {
      const canvas = this.$refs.imageCanvas;
      const rect = canvas.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;

      if (this.drawMode && this.newAnnotation) {
        // Adjust the last corner dynamically
        const { points } = this.newAnnotation;
        points[1] = { x, y: points[0].y };
        points[2] = { x, y };
        points[3] = { x: points[0].x, y };
        this.loadImageToCanvas();

        const ctx = canvas.getContext("2d");
        ctx.beginPath();
        points.forEach(({ x, y }, index) => {
          if (index === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        });
        ctx.closePath();
        ctx.lineWidth = 2;
        ctx.strokeStyle = "rgb(85, 255, 51)";
        ctx.stroke();
      } else if (this.draggingPoint) {
        // Update the position of the dragged corner
        const { annotation, pointIndex } = this.draggingPoint;
        annotation[pointIndex] = { x, y };
        this.loadImageToCanvas();
      }
    },
    onMouseUp() {
      if (this.drawMode && this.newAnnotation) {
        // Complete the quadrilateral
        this.annotations.push(this.newAnnotation);
        this.newAnnotation = null;
        this.loadImageToCanvas();
      }
      this.draggingPoint = null;
    },
    onContextMenu(event) {
      const canvas = this.$refs.imageCanvas;
      const rect = canvas.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;

      this.selectedAnnotation = this.annotations.find(({ points }) => {
        return points.some(({ x: px, y: py }) => Math.abs(px - x) < 10 && Math.abs(py - y) < 10);

      });

      if (this.selectedAnnotation) {
        this.showContextMenu = true;
        this.contextMenuStyle = {
          top: `${event.clientY}px`,
          left: `${event.clientX}px`,
        };
      } else {
        this.showContextMenu = false;
      }
    },
    deleteAnnotation() {
      this.annotations = this.annotations.filter((annotation) => annotation !== this.selectedAnnotation);
      this.selectedAnnotation = null;
      this.showContextMenu = false;
      this.loadImageToCanvas();
    },
    toggleDrawMode() {
      this.drawMode = !this.drawMode;
      const toggleButton = document.querySelector(".toggle-button");
      if (this.drawMode) {
        toggleButton.classList.add("toggled");
      } else {
        toggleButton.classList.remove("toggled");
      }      
      this.selectedAnnotation = null;
      this.showContextMenu = false;
      this.loadImageToCanvas();
    },
    downloadAnnotatedImage() {
      const canvas = this.$refs.imageCanvas;
      const link = document.createElement("a");
      link.download = "annotated_image.png";
      link.href = canvas.toDataURL("image/png");
      link.click();
    },
  },
};
</script>

To change the background color of the toggle-button when toggled, you can add a new CSS class to the `.toggle-button` selector and toggle it based on the `drawMode` property. Here's the updated CSS code:

<style>
body {
 background-color: #1b1b1b;
}

#app {
 font-family: Avenir, Helvetica, Arial, sans-serif;
 text-align: center;
 margin-top: 20px;
 color: #e0e0e0;
}

.image-container {
 border: 1px solid #374151;
 margin: 20px auto;
 max-width: 80%;
}

canvas {
 display: block;
 max-width: 100%;
 cursor: crosshair;
}

.context-menu {
 position: absolute;
 background-color: white;
 border: 1px solid #ccc;
 z-index: 1000;
 box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.2);
 padding: 0.25rem;
 font-size: 0.9rem;
 color: #333;
}

.context-menu button {
 background-color: #ff7043;
 color: white;
 border: none;
 cursor: pointer;
 padding: 0.25rem 0.5rem;
 margin: 0;
}

.context-menu button:hover {
 background-color: #d84315;
}

.download-button {
 background-color: #4caf50;
 color: white;
 padding: 0.5rem 1rem;
 font-size: 1rem;
 border: none;
 border-radius: 0.25rem;
 cursor: pointer;
 margin-top: 20px;
}

.download-button:hover {
 background-color: #43a047;
}

.toggle-button {
 background-color: #2196f3;
 color: white;
 padding: 0.5rem 1rem;
 font-size: 1rem;
 border: none;
 border-radius: 0.25rem;
 cursor: pointer;
}

.toggle-button.toggled {
 background-color: #ff4d4d;
}

.toggle-button.toggled:hover {
 background-color: #ff3232;
}
.toggle-button:hover {
 background-color: #1e88e5;
}
</style>


