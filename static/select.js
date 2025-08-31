document.addEventListener('DOMContentLoaded', () => {
  const genSelect = document.querySelector('select[name="generation"]');
  const gameSelect = document.querySelector('select[name="game"]');
  if (!genSelect || !gameSelect) return;
  genSelect.addEventListener('change', () => {
    fetch(`/games/${genSelect.value}`)
      .then(resp => resp.json())
      .then(data => {
        gameSelect.innerHTML = '';
        data.games.forEach(g => {
          const opt = document.createElement('option');
          opt.value = g;
          opt.textContent = g;
          gameSelect.appendChild(opt);
        });
        if (gameSelect.options.length > 0) {
          gameSelect.selectedIndex = 0;
        }
      });
  });
});
