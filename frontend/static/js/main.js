// frontend/static/js/main.js

document.addEventListener("DOMContentLoaded", function() {

    // 🔥 1. FORMAT RUPIAH OTOMATIS (MENDUKUNG HOVER MOUSE)
    document.querySelectorAll('.tampil-rupiah').forEach(function(el) {
        let val = el.getAttribute('data-raw') || el.innerText;
        // Gunakan regex baru yang mempertahankan titik desimal (.) jika ada
        let cleanVal = val.replace(/[^0-9.]/g, ''); 
        if (cleanVal) {
            let num = parseFloat(cleanVal);
            let hasilFormat = 'Rp ' + Math.floor(num).toLocaleString('id-ID');
            
            el.innerText = hasilFormat;
            
            // KUNCI HOVER: Jika elemen memiliki atribut title (tooltip), ikut format!
            if (el.hasAttribute('title')) {
                el.setAttribute('title', hasilFormat);
            }
        }
    });

    // 🔥 2. FORMAT LUAS METER OTOMATIS (ANTI-LOMPAT DESIMAL)
    document.querySelectorAll('.tampil-luas').forEach(function(el) {
        let val = el.getAttribute('data-raw') || el.innerText;
        let cleanVal = val.replace(/[^0-9.]/g, ''); 
        if (cleanVal) {
            let num = parseFloat(cleanVal);
            // Kunci id-ID: Maksimal 2 angka di belakang koma untuk gaya Indonesia
            el.innerText = num.toLocaleString('id-ID', { minimumFractionDigits: 0, maximumFractionDigits: 2 }) + ' m²';
            
            if (el.hasAttribute('title')) {
                el.setAttribute('title', num.toLocaleString('id-ID') + ' m²');
            }
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
        if(input.value) {
            if (input.value.includes('.') && !input.value.includes(',')) {
                input.value = input.value.replace(/\./g, ',');
            }
            input.value = formatNumber(input.value); 
        }
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