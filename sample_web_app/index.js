const MODEL = 'device'
const SERVER_URL = "http://127.0.0.1:5000"


// async function processImage() {
//   const imageInput = document.getElementById('imageInput');
//   const file = imageInput.files[0];
//   if (!file) {
//     alert("Please upload an image first!");
//     return;
//   }

//   // Display loading text while processing
//   const resultSection = document.getElementById("result-section-message");
//   resultSection.innerHTML = "<p>Processing image...</p>";

//   const formData = new FormData();
//   formData.append("image", file);

//   try {
//     // Send image to Flask backend for processing
//     const response = await fetch(`${SERVER_URL}/process_image`, {
//       method: "POST",
//       body: formData
//     });
//     const data = await response.json();

//     // Handle errors from the server
//     if (response.status !== 200) {
//       resultSection.innerHTML = `<p>${data.error}</p>`;
//       return;
//     }

//     // console.log("Got data: ", data);
//     // Display the uploaded image
//     const imageContainer = document.getElementById("imageContainer");
//     const imgElement = document.getElementById("processed-image");
//     imgElement.src = URL.createObjectURL(file);

//     // Wait for the image to load before adding overlays
//     imgElement.onload = () => {
//       // Clear any previous overlays
//       imageContainer.querySelectorAll(".bbox, .text-overlay").forEach(el => el.remove());

//       // Draw bounding boxes and add translated text
//       data.forEach(async (detection) => {
//         const [topLeft, bottomRight] = detection.bbox;
//         let translatedText = '';
//         if (MODEL == 'device') {
//           translatedText = await translateTextOnDevice(detection.text);
//         }
//         else {
//           translatedText = await translateTextExternal(detection.text, MODEL);
//         }
//         // Draw bounding box
//         const box = document.createElement("div");
//         box.classList.add("bbox");
//         box.style.left = `${topLeft[0]}px`;
//         box.style.top = `${topLeft[1]}px`;
//         box.style.width = `${bottomRight[0] - topLeft[0]}px`;
//         box.style.height = `${bottomRight[1] - topLeft[1]}px`;
//         imageContainer.appendChild(box);

//         // Display translated text overlay
//         const textOverlay = document.createElement("div");
//         textOverlay.classList.add("text-overlay");
//         textOverlay.style.left = `${topLeft[0]}px`;
//         textOverlay.style.top = `${topLeft[1]}px`;
//         textOverlay.textContent = translatedText;
//         imageContainer.appendChild(textOverlay);
//       });
//     };
//   } catch (error) {
//     console.error("Error processing image:", error);
//     resultSection.innerHTML = `<p>Failed to process image.</p>`;
//   }
// }

async function processImage() {
  const imageInput = document.getElementById('imageInput');
  const file = imageInput.files[0];
  if (!file) {
    alert("Please upload an image first!");
    return;
  }

  // Display loading text while processing
  const resultSection = document.getElementById("result-section-message");
  resultSection.innerHTML = "<p>Processing image...</p>";

  const formData = new FormData();
  formData.append("image", file);

  try {
    // Send image to Flask backend for processing
    const response = await fetch(`${SERVER_URL}/process_image`, {
      method: "POST",
      body: formData
    });
    const data = await response.json();

    // Handle errors from the server
    if (response.status !== 200) {
      resultSection.innerHTML = `<p>${data.error}</p>`;
      return;
    }

    // Display the uploaded image
    const imgElement = document.getElementById("processed-image");
    imgElement.src = URL.createObjectURL(file);

    imgElement.onload = async () => {
      // Prepare canvas to draw on
      const canvas = document.createElement("canvas");
      canvas.width = imgElement.width;
      canvas.height = imgElement.height;
      const ctx = canvas.getContext("2d");

      // Draw the uploaded image onto the canvas
      ctx.drawImage(imgElement, 0, 0, imgElement.width, imgElement.height);

      // Loop through each detection and replace the text in the image
      for (const detection of data) {
        const [topLeft, bottomRight] = detection.bbox;
        let translatedText = '';

        if (MODEL === 'device') {
          translatedText = await translateTextOnDevice(detection.text);
        } else {
          translatedText = await translateTextExternal(detection.text, MODEL);
        }

        // Calculate bounding box dimensions
        const boxWidth = bottomRight[0] - topLeft[0];
        const boxHeight = bottomRight[1] - topLeft[1];

        // Clear area in the image where text will go
        ctx.fillStyle = 'white';
        ctx.fillRect(topLeft[0], topLeft[1], boxWidth, boxHeight);

        // Initial font size, large enough to fit the box height at start
        let fontSize = boxHeight * 0.8;
        ctx.font = `${fontSize}px Arial`;
        ctx.fillStyle = 'black';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';

        // Helper function to split text into lines that fit within box width
        function splitTextIntoLines(text, maxWidth) {
          const words = text.split(' ');
          const lines = [];
          let currentLine = words[0];

          for (let i = 1; i < words.length; i++) {
            const word = words[i];
            const testLine = `${currentLine} ${word}`;
            const testWidth = ctx.measureText(testLine).width;
            if (testWidth > maxWidth) {
              lines.push(currentLine);
              currentLine = word;
            } else {
              currentLine = testLine;
            }
          }
          lines.push(currentLine);
          return lines;
        }

        // Split the translated text into multiple lines
        let lines = splitTextIntoLines(translatedText, boxWidth);

        // Reduce font size if text block height exceeds box height
        while (fontSize > 1 && (lines.length * fontSize > boxHeight)) {
          fontSize -= 1;
          ctx.font = `${fontSize}px Arial`;
          lines = splitTextIntoLines(translatedText, boxWidth);
        }

        // Draw each line of text within the bounding box
        const textX = topLeft[0] + boxWidth / 2;
        let textY = topLeft[1] + (boxHeight - lines.length * fontSize) / 2;

        for (const line of lines) {
          ctx.fillText(line, textX, textY);
          textY += fontSize;
        }
      }

      // Update image source to the modified canvas
      imgElement.src = canvas.toDataURL();
      resultSection.innerHTML = "<p>Image processed successfully!</p>";
    };
  } catch (error) {
    console.error("Error processing image:", error);
    resultSection.innerHTML = `<p>Failed to process image.</p>`;
  }
}


// Mock translation function - replace with API call
async function translateTextOnDevice(text) {
  // code to use the inbuilt gemini nano model in google chrome canary 
  const session = await ai.languageModel.create();
  let result = (await session.prompt(`Translate to English, only one answer, json format with attribute 'translation' containing the english translated sentence, no explanation needed: ${text}`)).trim();

  if (result.substring(0, 7) == '```json') {
    console.log('Triggered');
    result = result.slice(7)
    result = result.slice(0, result.length - 3)
    result = result.replaceAll('`', '')
  }
  try {
    result = JSON.parse(result);
  }
  catch (error) {
    console.log("Invalid conversion from model: ", error);
    console.log("Orignal result: ", result);
  }
  //console.log("Got Translated result: ", result);
  return result.translation;
}

async function translateTextExternal(text, model) {

}
