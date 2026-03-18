const toggle = document.getElementById('darkToggle');
toggle.addEventListener('change', () => {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('dark-mode', toggle.checked);
});

if(localStorage.getItem('dark-mode') === 'true'){
    document.body.classList.add('dark-mode');
    toggle.checked = true;
}