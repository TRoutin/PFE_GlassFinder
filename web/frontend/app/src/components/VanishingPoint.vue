<template>
    <div id="vanishing-points">
      <!-- Affichage des résultats -->
      <div class="results-section">
        <h2>Detected Vanishing Points</h2>
        <ul>
          <li v-for="(point, index) in vanishingPoints" :key="index">
            Vanishing Point {{ index + 1 }}: (x : {{ point.x.toFixed(2) }}, y : {{ point.y.toFixed(2) }})
          </li>
        </ul>
      </div>
    </div>
  </template>
  
  <script>
  import axios from "axios";
  
  export default {
    props: {
      imageFile: {
        type: File, // La prop accepte un fichier
        required: false,
      },
    },
    data() {
      return {
        vanishingPoints: null, // Points de fuite détectés
      };
    },
    watch: {
      // Détecte les changements sur la prop `imageFile`
      imageFile: {
        immediate: true, // Appelle le gestionnaire au chargement initial
        handler(newFile) {
          if (newFile) {
            this.detectVanishingPoints(newFile);
          }
        },
      },
    },
    methods: {
      detectVanishingPoints(file) {
        const formData = new FormData();
        formData.append("file", file);
  
        const params = {
          sigma: 5.0,
          iterations: 3000,
          line_len: 11,
          line_gap: 7,
          threshold: 2.0,
        };
  
        axios
          .post("http://127.0.0.1:8000/detect-vanishing-points/", formData, {
            params,
          })
          .then((response) => {
            this.vanishingPoints = response.data.vanishing_points;
          })
          .catch((error) => {
            console.error("Error detecting vanishing points:", error);
          });
      },
    },
  };
  </script>
  
  <style>
  #vanishing-points {
    font-family: Arial, sans-serif;
    text-align: center;
    margin: auto;
    background-color: #313030;
  }
  
  .results-section {
    margin-top: 20px;
    border: 1px solid #367ae0;
    border-radius: 5px;
  }
  </style>
  