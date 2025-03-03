document.addEventListener('DOMContentLoaded', function () {
    const logoutBtn = document.getElementById('logoutBtn');
    const modal = document.getElementById('logoutConfirmModal');
    const cancelLogout = document.getElementById('cancelLogout');
    const confirmLogout = document.getElementById('confirmLogout');

    logoutBtn.addEventListener('click', function () {
        modal.classList.remove('d-none');
        modal.style.display = 'flex';
    });

    cancelLogout.addEventListener('click', function () {
        modal.classList.add('d-none');
    });

    confirmLogout.addEventListener('click', function () {
        window.location.href = "/logout";
    });
});
