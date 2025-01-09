// Install Vue.js and dependencies first
// npm install vue@3 axios @vue/cli-service

<template>
  <div id="app">
    <h1>Image Annotation Tool</h1>
    
    <!-- Upload Section -->
    <input type="file" @change="onImageUpload" accept="image/*" />
    <div v-if="imageSrc" class="image-container">
      <canvas ref="imageCanvas" @mousedown="startDrag" @mousemove="drag" @mouseup="stopDrag" />
    </div>

    <!-- JSON Data Display and Edit -->
    <div v-if="annotations.length" class="annotations-container">
      <h2>Annotations</h2>
      <ul>
        <li v-for="(annotation, index) in annotations" :key="index" class="annotation-item">
          Class: {{ annotation.class_id }}, Score: {{ annotation.score }}
          <ul>
            <li>Contours: {{ annotation.linearized_contours }}</li>
          </ul>
          <button @click="removeAnnotation(index)" class="remove-button">Remove Annotation</button>
        </li>
      </ul>
      <button @click="addAnnotation" class="add-button">Add New Annotation</button>
    </div>

    <!-- Download Button -->
    <button @click="downloadAnnotatedImage" :disabled="!annotations.length" class="download-button">Download Annotated Image</button>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      image: null,
      imageSrc: '',
      annotations: [],
      isDragging: false,
      dragPoint: null,
    };
  },
  methods: {
    async onImageUpload(event) {
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
        formData.append('file', file);

        try {
          const response = await axios.post('http://127.0.0.1:8000/predict/?threshold=0.5&target_class_id=10', formData);
          this.annotations = response.data.predictions;
          this.loadImageToCanvas();
        } catch (error) {
          console.error('Error sending image to backend:', error);
        }
      }
    },
    loadImageToCanvas() {
      const canvas = this.$refs.imageCanvas;
      if (!canvas) {
        console.error("Canvas reference is not available");
        return;
      }
      const ctx = canvas.getContext('2d');
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
      if (!this.annotations.length) return;
      const canvas = this.$refs.imageCanvas;
      if (!canvas) {
        console.error("Canvas reference is not available");
        return;
      }
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        console.error("Canvas context could not be initialized");
        return;
      }

      this.annotations.forEach((annotation) => {
        annotation.linearized_contours.forEach((contour) => {
          ctx.beginPath();
          contour.forEach(([x, y], index) => {
            if (index === 0) {
              ctx.moveTo(x, y);
            } else {
              ctx.lineTo(x, y);
            }
          });
          ctx.closePath();
          ctx.lineWidth = 2; // Thicker line
          ctx.strokeStyle = 'rgb(85, 255, 51)';
          ctx.stroke();
        });
      });
    },
    startDrag(event) {
      const canvas = this.$refs.imageCanvas;
      const rect = canvas.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;

      this.annotations.forEach((annotation) => {
        annotation.linearized_contours.forEach((contour) => {
          contour.forEach((point, index) => {
            const [px, py] = point;
            if (Math.abs(px - x) < 10 && Math.abs(py - y) < 10) {
              this.isDragging = true;
              this.dragPoint = { annotation, contour, index };
            }
          });
        });
      });
    },
    drag(event) {
      if (!this.isDragging) return;

      const canvas = this.$refs.imageCanvas;
      const rect = canvas.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;

      const { contour, index } = this.dragPoint;
      contour[index] = [x, y];
      this.loadImageToCanvas();
    },
    stopDrag() {
      this.isDragging = false;
      this.dragPoint = null;
    },
    addAnnotation() {
      this.annotations.push({
        class_id: 10,
        score: 1.0,
        linearized_contours: [[
          [50, 50],
          [150, 50],
          [150, 150],
          [50, 150]
        ]],
      });
      this.loadImageToCanvas();
    },
    removeAnnotation(index) {
      this.annotations.splice(index, 1);
      this.loadImageToCanvas();
    },
    downloadAnnotatedImage() {
      const canvas = this.$refs.imageCanvas;
      if (!canvas) {
        console.error("Canvas reference is not available");
        return;
      }
      const link = document.createElement('a');
      link.download = 'annotated_image.png';
      link.href = canvas.toDataURL('image/png');
      link.click();
    },
  },
};
</script>

 <style>
#app {
 font-family: Avenir, Helvetica, Arial, sans-serif;
 text-align: center;
 color: #e0e0e0;
 margin-top: 60px;
 background-color: #1b1b1b;
}

.title {
 font-size: 2rem;
 font-weight: bold;
 margin-bottom: 3rem;
 color: #e0e0e0;
}

.upload-section {
 display: flex;
 justify-content: center;
 margin-bottom: 3rem;
}

.upload-input {
 padding: 0.5rem;
 font-size: 1rem;
 background-color: #1b1b1b;
 color: #e0e0e0;
 border: none;
}

.upload-input:focus {
 box-shadow: none;
}

.image-container {
 border: 1px solid #374151;
 margin: 0 auto;
 max-width: 80%;
}

canvas {
 display: block;
 max-width: 100%;
 cursor: cross;
}

body{
  background-color:#1b1b1b;
}

.annotations-container {
 margin: 3rem auto;
 max-width: 60%;
 background-color: #404040;
 padding: 1.5rem;
 border-radius: 0.5rem;
}

.annotations-container h2 {
 font-size: 1.5rem;
 font-weight: bold;
 margin-bottom: 1rem;
 color: #e0e0e0;
}

.annotation-item {
 margin-bottom: 1rem;
 padding: 1rem;
 border: 1px solid #374151;
}

.annotation-item span {
 margin-right: 1rem;
 color: #e0e0e0;
}

.remove-button {
 background-color: #f44336;
 color: white;
 padding: 0.25rem 0.5rem;
 font-size: 0.75rem;
 border: none;
 border-radius: 0.25rem;
 cursor: pointer;
}

.remove-button:hover {
 background-color: #da190b;
}

.add-button {
 background-color: #4CAF50;
 color: white;
 padding: 0.25rem 0.5rem;
 font-size: 0.75rem;
 border: none;
 border-radius: 0.25rem;
 cursor: pointer;
 margin-top: 1rem;
}

.add-button:hover {
 background-color: #45a049;
}

.download-button {
 background-color: #2196F3;
 color: white;
 padding: 0.5rem 1rem;
 font-size: 1rem;
 border: none;
 border-radius: 0.25rem;
 cursor: pointer;
 margin-top: 2rem;
}

.download-button:hover {
 background-color: #0d8ef1;
}
</style>
