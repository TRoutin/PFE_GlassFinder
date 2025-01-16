<template>
  <div id="app">
    <h1>GlassFinder</h1>
    <div class="main-container">
      <!-- Slider Section -->
      <div class="slider-container">
        <ScoreSlider ref="scoreSlider" :default-value="0.6" @slider-change="onSliderChange" />
      </div>

      <!-- Image Upload and Canvas Section -->
      <div class="content-container">
        <!-- Upload Section -->
        <input type="file" @change="onImageUpload" accept="image/*" />

        <div class="image-container">
          <canvas
            ref="imageCanvas"

          ></canvas>
          <canvas ref="annotationCanvas"
            @mousedown="onMouseDown"
            @mousemove="onMouseMove"
            @mouseup="onMouseUp"
            @click="onCanvasClick"
            @contextmenu.prevent="onContextMenu"></canvas>
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
    </div>
  </div>
</template>


<script>
import axios from "axios";
import ScoreSlider from "./components/ScoreSlider.vue";


export default {
  components: {
    ScoreSlider,
  },
  data() {
    return {
      image: null,
      imageSrc: "",
      annotations: [], // Format: [{ points: [{ x, y }, { x, y }, { x, y }, { x, y }] }]
      visibleAnnotations: [], // To hold filtered annotations
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
        this.visibleAnnotations = [...this.annotations];

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
        .post("http://127.0.0.1:8000/predict/?threshold=0&target_class_id=10", formData)
        .then((response) => {
          this.annotations = response.data.predictions.map(({ linearized_contours, score }) => {
            return { 
              points: linearized_contours[0].map(([x, y]) => ({ x, y })),
              score // Store the score
            };
          });
          this.filterAnnotations(this.$refs.scoreSlider.sliderValue);
          this.loadImageToCanvas();
        })
        .catch((error) => {
          console.error("Error sending image to backend:", error);
        });
      }
    },
    loadImageToCanvas() {
      const imageCanvas = this.$refs.imageCanvas;
      const annotationCanvas = this.$refs.annotationCanvas;

      if (!imageCanvas || !annotationCanvas) {
        console.error("Canvas references are not available");
        return;
      }

      const imageCtx = imageCanvas.getContext("2d");
      const annotationCtx = annotationCanvas.getContext("2d");

      if (!imageCtx || !annotationCtx) {
        console.error("Canvas contexts could not be initialized");
        return;
      }

      const image = new Image();
      image.onload = () => {
        imageCanvas.width = image.width;
        imageCanvas.height = image.height;
        annotationCanvas.width = image.width;
        annotationCanvas.height = image.height;

        imageCtx.drawImage(image, 0, 0);
        this.drawAnnotations();
      };
      image.src = this.imageSrc;
    },

    onSliderChange(value) {
      this.filterAnnotations(value);
      this.loadImageToCanvas();
    },

    filterAnnotations(scoreThreshold) {
      this.visibleAnnotations = this.annotations.filter(
        (annotation) => annotation.score >= scoreThreshold
      );
    },

    drawAnnotations() {
      const annotationCanvas = this.$refs.annotationCanvas;
      const ctx = annotationCanvas.getContext("2d");

      ctx.clearRect(0, 0, annotationCanvas.width, annotationCanvas.height);

      this.visibleAnnotations.forEach((annotation) => {
        const { points } = annotation;
        ctx.beginPath();
        points.forEach(({ x, y }, index) => {
          if (index === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        });
        ctx.closePath();
        ctx.lineWidth = annotation === this.selectedAnnotation ? 3 : 2;
        ctx.strokeStyle = annotation === this.selectedAnnotation ? "blue" : "rgb(85, 255, 51)";
        ctx.stroke();
      });
    },

    getScaledCoordinates(event) {
      const canvas = this.$refs.annotationCanvas;
      const rect = canvas.getBoundingClientRect();
      const scaleX = canvas.width / rect.width;
      const scaleY = canvas.height / rect.height;
      const x = (event.clientX - rect.left) * scaleX;
      const y = (event.clientY - rect.top) * scaleY;
      return { x, y };
    },

    onMouseDown(event) {
    const { x, y } = this.getScaledCoordinates(event);

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
      const { x, y } = this.getScaledCoordinates(event);


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
        this.showContextMenu = false;
      }
      this.loadImageToCanvas();
    },
    onMouseMove(event) {
    const { x, y } = this.getScaledCoordinates(event);

    if (this.drawMode && this.newAnnotation) {
      const { points } = this.newAnnotation;
      points[1] = { x, y: points[0].y };
      points[2] = { x, y };
      points[3] = { x: points[0].x, y };
      this.loadImageToCanvas();

      const ctx = this.$refs.annotationCanvas.getContext("2d");
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
      const { x, y } = this.getScaledCoordinates(event);


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
        this.showContextMenu = false;
      }

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
      this.visibleAnnotations = this.visibleAnnotations.filter((visibleAnnotations) => visibleAnnotations !== this.selectedAnnotation);
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
    // Create a new canvas to combine both image and annotation canvases
    const combinedCanvas = document.createElement('canvas');
    const imageCanvas = this.$refs.imageCanvas;
    const annotationCanvas = this.$refs.annotationCanvas;
    
    // Set the combined canvas size
    combinedCanvas.width = imageCanvas.width;
    combinedCanvas.height = imageCanvas.height;

    const combinedCtx = combinedCanvas.getContext('2d');
    
    // Draw the image canvas onto the combined canvas
    combinedCtx.drawImage(imageCanvas, 0, 0);
    
    // Set all annotations to green and draw the annotation canvas
    combinedCtx.drawImage(annotationCanvas, 0, 0);
    
    // Create a new image to apply green annotations
    const annotationImage = new Image();
    annotationImage.onload = () => {
      combinedCtx.drawImage(annotationImage, 0, 0);
      // Export the combined canvas as an image
      const link = document.createElement('a');
      link.download = 'annotated_image.png';
      link.href = combinedCanvas.toDataURL('image/png');
      link.click();
    };

    // Redraw the annotations in green before loading them onto the combined canvas
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = annotationCanvas.width;
    tempCanvas.height = annotationCanvas.height;
    const tempCtx = tempCanvas.getContext('2d');
    tempCtx.clearRect(0, 0, tempCanvas.width, tempCanvas.height);
    
    // Draw annotations in green on the temp canvas
    this.annotations.forEach((annotation) => {
      const { points } = annotation;
      tempCtx.beginPath();
      points.forEach(({ x, y }, index) => {
        if (index === 0) tempCtx.moveTo(x, y);
        else tempCtx.lineTo(x, y);
      });
      tempCtx.closePath();
      tempCtx.lineWidth = 2;
      tempCtx.strokeStyle = "rgb(85, 255, 51)";
      tempCtx.stroke();
    });

    // Load the temp canvas onto the image and proceed
    annotationImage.src = tempCanvas.toDataURL();
  }


  },
  
  mounted() {
    this.$nextTick(() => {
      this.loadImageToCanvas();
      // Get the initial value of the slider and filter annotations
      const sliderValue = this.$refs.scoreSlider.value || 0.6; // Default fallback to 0.6
      this.filterAnnotations(sliderValue);
    });
  },
};
</script>

<style>
body {
  background-color: #1b1b1b;
  margin: 0;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  text-align: center;
  color: #e0e0e0;
}

.main-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 80vh;
}

.slider-container {
  display: flex;
  justify-content: center;
  margin-right: 20px;
  height: 100%;
}

.content-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 70vw;

}

.image-container {
  display: flex;
  flex-flow: row nowrap; 
  border: 1px solid #374151;
  margin: 20px auto;
  max-width: 70%;
  max-height: 60%;
  text-align: center;
}

canvas {
  display: grid;
  max-width: 100%;
  height: auto;
  cursor: crosshair;
}

canvas:nth-child(1) { /* Image Canvas */
  position: relative;
  z-index: 1;
}

canvas:nth-child(2) { /* Annotation Canvas */
  box-sizing: border-box; 
    width: 100%; 
    flex: none; 
    z-index: 2;
    margin-left: -100%; 
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


