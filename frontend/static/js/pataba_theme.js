// frontend/static/js/pataba_theme.js

document.addEventListener("DOMContentLoaded", function() {

    // ==========================================
    // 1. ENGINE DARK MODE & PREFERENSI SISTEM MAC
    // ==========================================
    const darkModeSwitch = document.getElementById('darkModeSwitch');

    if (darkModeSwitch) {
        // Cek memori browser ATAU preferensi sistem operasi user saat web baru dimuat
        const currentTheme = localStorage.getItem('theme');
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

        if (currentTheme === 'dark' || (!currentTheme && systemPrefersDark)) {
            document.documentElement.setAttribute('data-theme', 'dark');
            darkModeSwitch.checked = true;
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
            darkModeSwitch.checked = false;
        }

        // Jika tombol gerigi diklik manual
        darkModeSwitch.addEventListener('change', function(e) {
            const newTheme = e.target.checked ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        });

        // KUNCI UTAMA: Jika user mengganti Dark Mode langsung dari System Mac/iOS
        // Ini akan menimpa pilihan manual dan ikut sistem secara real-time!
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
            const newTheme = e.matches ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', newTheme);
            darkModeSwitch.checked = e.matches;
            localStorage.setItem('theme', newTheme); // Timpa memori dengan sistem
        });
    }

    // ==========================================
    // 2. PENGENDALI POP-UP GEAR & GLOBE
    // ==========================================
    const gearToggle = document.getElementById('settingsToggle');
    const globeToggle = document.getElementById('globeToggle');
    const gearPopup = document.getElementById('settingsPopup');
    const globePopup = document.getElementById('languagePopup');

    if (gearToggle && gearPopup) {
        gearToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            gearPopup.classList.toggle('show');
            if (globePopup) globePopup.classList.remove('show');
        });
    }

    if (globeToggle && globePopup) {
        globeToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            globePopup.classList.toggle('show');
            if (gearPopup) gearPopup.classList.remove('show');
        });
    }

    document.addEventListener('click', function(e) {
        if (gearPopup && !gearPopup.contains(e.target) && !gearToggle.contains(e.target)) {
            gearPopup.classList.remove('show');
        }
        if (globePopup && !globePopup.contains(e.target) && !globeToggle.contains(e.target)) {
            globePopup.classList.remove('show');
        }
    });

});