// frontend/static/js/main.js

document.addEventListener("DOMContentLoaded", function() {

    // 1. FORMAT RUPIAH OTOMATIS
    document.querySelectorAll('.tampil-rupiah').forEach(function(el) {
        // Gunakan data-raw jika ada, jika tidak ada baru gunakan innerText
        let val = el.getAttribute('data-raw') || el.innerText.replace(/[^0-9]/g, '');
        if (val) {
            el.innerText = 'Rp ' + parseInt(val, 10).toLocaleString('id-ID');
        }
    });

    // 2. FORMAT LUAS METER OTOMATIS
    document.querySelectorAll('.tampil-luas').forEach(function(el) {
        // Gunakan data-raw jika ada, agar tidak mengolah angka yang sudah terformat
        let val = el.getAttribute('data-raw') || el.innerText.replace(/[^0-9]/g, '');
        if (val) {
            el.innerText = parseInt(val, 10).toLocaleString('id-ID') + ' m²';
        }
    });

    // 3. FORMAT RIBUAN SAAT MENGETIK (Input Form)
    const numberInputs = document.querySelectorAll('.format-ribuan');
    function formatNumber(angka) {
        var number_string = angka.replace(/[^,\d]/g, '').toString(),
            split = number_string.split(','),
            sisa = split[0].length % 3,
            rupiah = split[0].substr(0, sisa),
            ribuan = split[0].substr(sisa).match(/\d{3}/gi);

        if (ribuan) {
            let separator = sisa ? '.' : '';
            rupiah += separator + ribuan.join('.');
        }
        return split[1] != undefined ? rupiah + ',' + split[1] : rupiah;
    }
    numberInputs.forEach(function(input) {
        if(input.value) { input.value = formatNumber(input.value); }
        input.addEventListener('keyup', function(e) { this.value = formatNumber(this.value); });
    });

    // 4. AUTO TITLE CASE (Huruf Kapital Tiap Kata) & AUTO UPPERCASE
    const titleCaseInputs = document.querySelectorAll('.auto-title-case');
    titleCaseInputs.forEach(input => {
        input.addEventListener('blur', function() {
            let words = this.value.split(' ');
            for (let i = 0; i < words.length; i++) {
                let word = words[i];
                if (!word) continue;
                
                // Jika kata diketik KAPITAL SEMUA (contoh: STQ, BPKAD), biarkan!
                let isAlpha = /[a-zA-Z]/.test(word);
                if (isAlpha && word === word.toUpperCase()) {
                    continue; 
                }
                
                words[i] = word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
            }
            this.value = words.join(' ');
        });
    });

    const uppercaseInputs = document.querySelectorAll('.auto-uppercase');
    uppercaseInputs.forEach(input => {
        input.addEventListener('input', function() {
            this.value = this.value.toUpperCase(); 
        });
    });

    // 5. URUTKAN DROPDOWN DARI A-Z (Kebal Error)
    document.querySelectorAll('.sort-az').forEach(function(select) {
        let options = Array.from(select.options);
        // Pastikan dropdown ada isinya sebelum diurutkan
        if (options.length > 0) {
            let firstOption = options.shift(); // Amankan opsi "-- Pilih --"
            
            // Urutkan sisa opsi berdasarkan abjad
            options.sort((a, b) => a.text.localeCompare(b.text));
            
            // Render ulang ke dalam dropdown
            select.innerHTML = '';
            select.appendChild(firstOption);
            options.forEach(opt => select.appendChild(opt));
        }
    });

    // 6. PERBAIKAN OFFCANVAS BOOTSTRAP (Mencegah bug z-index)
    document.querySelectorAll('.offcanvas').forEach(function(offcanvas) {
        document.body.appendChild(offcanvas);
    });

});