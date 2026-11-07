(() => {
  'use strict';
  if (window.top !== window.self || window.__nemuPwaLoaded) return;
  window.__nemuPwaLoaded = true;
  let pendingInstall = null;
  let installButton;
  let offlineNotice;
  const standalone = () => window.matchMedia('(display-mode: standalone)').matches ||
    navigator.standalone === true;
  const ios = /iPad|iPhone|iPod/.test(navigator.userAgent) ||
    (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);

  // Capture the event before DOMContentLoaded, but never prompt without a click.
  window.addEventListener('beforeinstallprompt', event => {
    event.preventDefault();
    pendingInstall = event;
    if (installButton && !standalone()) installButton.hidden = false;
  });
  window.addEventListener('appinstalled', () => {
    pendingInstall = null;
    if (installButton) installButton.hidden = true;
  });

  function init() {
    const style = document.createElement('style');
    style.textContent = `
      #nemu-pwa-tools{position:relative;order:-1;width:100%;z-index:90;font:13px/1.5 system-ui,sans-serif;color:#382059;background:#fff}
      #nemu-pwa-tools:has(>button:not([hidden])),#nemu-pwa-tools:has(>div:not([hidden])){padding:10px 12px;border-bottom:1px solid #e9defa}
      #nemu-pwa-tools [hidden]{display:none!important}
      #nemu-pwa-install{display:block;margin-left:auto;border:1px solid #fff;border-radius:999px;padding:10px 16px;background:#753cfa;color:#fff;font:600 13px/1.5 system-ui,sans-serif;cursor:pointer;box-shadow:0 3px 14px #38205922}
      #nemu-pwa-tools button:focus-visible{outline:3px solid #382059;outline-offset:3px}
      #nemu-pwa-help,#nemu-pwa-offline{margin-top:8px;padding:12px;border:1px solid #d9c5ff;border-radius:14px;background:#f5f0ff;box-shadow:0 3px 14px #38205922}
      #nemu-pwa-help button{margin-top:8px;border:0;border-radius:8px;padding:6px 12px;background:#753cfa;color:#fff;cursor:pointer}
    `;
    document.head.append(style);
    const panel = document.createElement('aside');
    panel.id = 'nemu-pwa-tools';
    panel.setAttribute('aria-label', 'Instalasi aplikasi dan status koneksi');
    installButton = document.createElement('button');
    installButton.id = 'nemu-pwa-install';
    installButton.type = 'button';
    installButton.textContent = 'Instal aplikasi';
    installButton.hidden = standalone() || (!pendingInstall && !ios);
    const help = document.createElement('div');
    help.id = 'nemu-pwa-help';
    help.hidden = true;
    const instructions = document.createElement('p');
    instructions.textContent = 'Di Safari, buka menu Bagikan, lalu pilih Tambahkan ke Layar Utama. Jika pilihan ini tidak muncul, buka halaman ini langsung di Safari.';
    const close = document.createElement('button');
    close.type = 'button';
    close.textContent = 'Tutup';
    close.addEventListener('click', () => { help.hidden = true; installButton.focus(); });
    help.append(instructions, close);
    installButton.addEventListener('click', async () => {
      if (pendingInstall) {
        const prompt = pendingInstall;
        pendingInstall = null;
        installButton.hidden = true;
        try { await prompt.prompt(); await prompt.userChoice; }
        catch (_) { /* A new browser event is required before another attempt. */ }
      } else if (ios) {
        help.hidden = !help.hidden;
        if (!help.hidden) close.focus();
      }
    });
    offlineNotice = document.createElement('div');
    offlineNotice.id = 'nemu-pwa-offline';
    offlineNotice.setAttribute('role', 'status');
    offlineNotice.textContent = 'Kamu sedang offline. Data tersimpan mungkin tidak terbaru. Hubungkan internet untuk cek stok, harga, dan bertransaksi.';
    const connectionChanged = () => { offlineNotice.hidden = navigator.onLine; };
    window.addEventListener('online', connectionChanged);
    window.addEventListener('offline', connectionChanged);
    connectionChanged();
    panel.append(installButton, help, offlineNotice);
    document.body.prepend(panel);

    if ('serviceWorker' in navigator && window.isSecureContext &&
        location.pathname.startsWith('/preloved/')) {
      navigator.serviceWorker.register('/preloved/sw.js', {
        scope: '/preloved/', updateViaCache: 'none'
      }).catch(error => console.warn('Preloved offline support unavailable:', error));
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
