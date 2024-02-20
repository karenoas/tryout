function uploadImage() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];

    if (file) {
        const formData = new FormData();
        formData.append('image', file);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            window.location.href = `/imagen.html?product=${data.product}`;
        })
        .catch(error => console.error('Error:', error));
    } else {
        alert('Por favor selecciona una imagen.');
    }
}
