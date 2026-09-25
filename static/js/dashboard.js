document.addEventListener('DOMContentLoaded', () => {
    // ---- Upload picker ----

    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const fileSelected = document.getElementById('file-selected');
    const fileName = document.getElementById('file-name');
    const removeFile = document.getElementById('remove-file');
    const submitBtn = document.getElementById('submit-btn');
    const uploadForm = document.getElementById('upload-form');

    if (dropZone && fileInput) {
        const openPicker = () => fileInput.click();

        dropZone.addEventListener('click', openPicker);
        dropZone.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                openPicker();
            }
        });

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('is-active');
        });

        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('is-active'));

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('is-active');
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                showSelectedFile();
            }
        });

        fileInput.addEventListener('change', showSelectedFile);

        function showSelectedFile() {
            if (!fileInput.files.length) return;
            fileName.textContent = fileInput.files[0].name;
            fileSelected.classList.remove('hidden');
            dropZone.classList.add('hidden');
        }

        if (removeFile) {
            removeFile.addEventListener('click', () => {
                fileInput.value = '';
                fileSelected.classList.add('hidden');
                dropZone.classList.remove('hidden');
            });
        }
    }

    if (uploadForm && submitBtn) {
        uploadForm.addEventListener('submit', () => {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Uploading…';
        });
    }

    // ---- Meaning lookup progress ----

    const processingRows = document.querySelectorAll('.processing-row');
    if (processingRows.length) {
        let failures = 0;

        const poll = setInterval(async () => {
            let stillWorking = false;

            for (const row of processingRows) {
                try {
                    const response = await fetch(`/api/lists/${row.dataset.listId}/progress/`);
                    if (!response.ok) throw new Error(`Request failed with ${response.status}`);
                    const data = await response.json();
                    row.querySelector('.processing-bar').style.width = `${data.progress_percentage}%`;
                    row.querySelector('.processing-pct').textContent = `${data.progress_percentage}%`;
                    if (data.status === 'pending' || data.status === 'processing') stillWorking = true;
                } catch (error) {
                    // Give up after a few failures instead of polling a dead endpoint forever.
                    failures++;
                    stillWorking = failures < 5;
                }
            }

            if (!stillWorking) {
                clearInterval(poll);
                window.location.reload();
            }
        }, 3000);
    }

    // ---- Share codes ----

    document.querySelectorAll('.copy-code').forEach(button => {
        button.addEventListener('click', async () => {
            const label = button.textContent;
            try {
                await navigator.clipboard.writeText(button.dataset.code);
                button.textContent = 'Copied';
            } catch (error) {
                button.textContent = button.dataset.code;
            }
            setTimeout(() => { button.textContent = label; }, 1500);
        });
    });
});
