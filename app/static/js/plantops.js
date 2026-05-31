(function () {
  const stamp = new Date().toLocaleTimeString();
  document.documentElement.dataset.loadedAt = stamp;
})();
