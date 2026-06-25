// frontend/static/js/main.js

document.addEventListener("DOMContentLoaded", function() {

    // 1. FORMAT RUPIAH OTOMATIS (Tampilan Teks)
    document.querySelectorAll('.tampil-rupiah').forEach(function(el) {
        let originalText = el.innerText;
        if (!originalText.includes('Rp')) { 
            let cleanText = originalText.split(',')[0].replace(/\./g, '').replace(/[^0-9-]/g, '');
            let val = parseFloat(cleanText);
            if(!isNaN(val)) {
                el.innerText = 'Rp ' + val.toLocaleString('id-ID') + ',00'; 
            }
        }
    });

    // 2. FORMAT LUAS METER OTOMATIS (Tampilan Teks)
    document.querySelectorAll('.tampil-luas').forEach(function(el) {
        let originalText = el.innerText;
        if (!originalText.includes('m²')) {
            let cleanText = originalText.split(',')[0].replace(/\./g, '').replace(/[^0-9-]/g, '');
            let val = parseFloat(cleanText);
            if(!isNaN(val)) {
                el.innerText = val.toLocaleString('id-ID') + ' m²'; 
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
        if(input.value) { input.value = formatNumber(input.value); }
        input.addEventListener('keyup', function(e) { this.value = formatNumber(this.value); });
    });

    // 4. AUTO TITLE CASE (Huruf Kapital Tiap Kata)
    document.querySelectorAll('.auto-title-case').forEach(function(input) {
        input.addEventListener('input', function() {
            this.value = this.value.toLowerCase().split(' ').map(function(word) {
                return word.charAt(0).toUpperCase() + word.slice(1);
            }).join(' ');
        });
    });

    // 5. URUTKAN DROPDOWN DARI A-Z
    document.querySelectorAll('.sort-az').forEach(function(select) {
        let options = Array.from(select.options);
        let firstOption = options.shift(); 
        options.sort((a, b) => a.text.localeCompare(b.text));
        select.innerHTML = '';
        select.appendChild(firstOption);
        options.forEach(opt => select.appendChild(opt));
    });

    // 6. PERBAIKAN OFFCANVAS BOOTSTRAP (Mencegah bug z-index)
    document.querySelectorAll('.offcanvas').forEach(function(offcanvas) {
        document.body.appendChild(offcanvas);
    });

});