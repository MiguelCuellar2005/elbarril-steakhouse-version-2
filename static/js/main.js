// Menú hamburguesa (celular)
document.addEventListener('DOMContentLoaded', function () {
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', function () {
            navMenu.classList.toggle('active');
        });
    }

    // Selector Food Truck / Resto (en la página de menú)
    const tabsMenu = document.querySelectorAll('.menu-selector-btn');
    const bloquesMenu = document.querySelectorAll('.menu-bloque');

    tabsMenu.forEach(function (btn) {
        btn.addEventListener('click', function () {
            const tipo = btn.dataset.tipo;

            tabsMenu.forEach(function (b) { b.classList.remove('active'); });
            btn.classList.add('active');

            bloquesMenu.forEach(function (bloque) {
                if (bloque.id === 'menu-' + tipo) {
                    bloque.classList.add('active');
                } else {
                    bloque.classList.remove('active');
                }
            });
        });
    });
});