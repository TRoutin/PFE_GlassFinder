<template>
  <div class="slider-container">
    <label for="score-slider">Score Threshold</label>
    <input
      type="range"
      id="score-slider"
      class="vertical-slider"
      :min="0"
      :max="1"
      :step="0.01"
      v-model="sliderValue"
      @input="emitSliderChange"
    />
    <span class="slider-value">{{ Number(sliderValue).toFixed(2) }}</span>
  </div>
</template>

<script>
export default {
  props: {
    defaultValue: {
      type: Number,
      default: 0.6, // Default slider value
    },
  },
  data() {
    return {
      sliderValue: Number(this.defaultValue),
    };
  },
  methods: {
    emitSliderChange() {
      this.sliderValue = Number(this.sliderValue); // Ensure it's a number
      this.$emit("slider-change", this.sliderValue);
    },
  },
};
</script>


<style scoped>
.slider-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-right: 20px;
  background-color: #313030;
  border: 1px solid #367ae0;
  border-radius: 5px;


}

label {
  font-size: 1rem;
  color: #e0e0e0;
  margin-bottom: 10px;
  margin-top: 20px;
}

.vertical-slider {
  writing-mode: bt-lr; /* Vertical slider style */
  appearance: slider-vertical;
  width: 8px;
  height: 150px;
  background: #374151;
  outline: none;
  border-radius: 5px;
}

.vertical-slider::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  background: #4caf50;
  border-radius: 50%;
  cursor: pointer;
}

.vertical-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  background: #4caf50;
  border-radius: 50%;
  cursor: pointer;
}

.slider-value {
  margin-top: 10px;
  color: #e0e0e0;
  font-size: 0.9rem;
  margin-bottom: 20px;
}
</style>
