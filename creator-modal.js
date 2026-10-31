(() => {
  const openButton = document.getElementById('creatorOpen');
  const dialog = document.getElementById('creatorModal');
  const closeButton = document.getElementById('creatorClose');
  const frame = document.getElementById('creatorFrame');
  if (!openButton || !dialog || !closeButton || !frame) return;
  function openModal() {
    dialog.hidden = false;
    dialog.setAttribute('aria-hidden', 'false');
    document.body.classList.add('creator-modal-open');
    if (!frame.src) frame.src = frame.dataset.src;
    closeButton.focus();
  }
  function closeModal() {
    dialog.hidden = true;
    dialog.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('creator-modal-open');
    openButton.focus();
  }
  openButton.addEventListener('click', openModal);
  closeButton.addEventListener('click', closeModal);
  dialog.addEventListener('click', event => { if (event.target === dialog) closeModal(); });
  document.addEventListener('keydown', event => {
    if (dialog.hidden) return;
    if (event.key === 'Escape') closeModal();
    if (event.key === 'Tab') {
      // Keyboard focus remains on the close button while the overlay is open.
      if (document.activeElement === openButton) closeButton.focus();
    }
  });
})();
