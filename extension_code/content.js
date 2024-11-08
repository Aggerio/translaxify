// content.js
(() => {
    const imagesArray = []; 

    const collectImages = async () => {
        const images = Array.from(document.images).map(img => img.src);

        for (const src of images) {
            if (src.startsWith('blob:')) {
                try {
                    // Fetch the Blob data from Blob URL
                    const response = await fetch(src);
                    const blob = await response.blob();

                    // Create a FileReader to read the Blob
                    const reader = new FileReader();
                    reader.onloadend = () => {
                        imagesArray.push(reader.result);
                    };
                    reader.readAsDataURL(blob);
                } catch (error) {
                    console.error('Error fetching Blob URL:', error);
                }
            } else {
                // For regular image URLs, push them directly into the array
                imagesArray.push(src);
            }
        }
    };

    // Call the function to collect images
    collectImages();

    // You can expose the imagesArray for further processing
    window.imagesArray = imagesArray; // Optionally expose the array globally
})();

