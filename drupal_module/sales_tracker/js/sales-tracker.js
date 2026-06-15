/**
 * Sales Tracker — client-side behaviors.
 *
 *  - salesTrackerGeolocate : fill lat/lon (hidden inputs) + reverse-geocode
 *                            the result into the visible address field.
 *  - salesTrackerSelfie    : webcam capture for proof-of-visit photo.
 */
(function (Drupal, once) {
  'use strict';

  /* ===================  GEOLOCATE  =================== */
  Drupal.behaviors.salesTrackerGeolocate = {
    attach: function (context) {
      once('st-geolocate', '.js-st-geolocate', context).forEach(function (btn) {
        btn.addEventListener('click', function (ev) {
          ev.preventDefault();

          var latId    = btn.getAttribute('data-st-target-lat');
          var lonId    = btn.getAttribute('data-st-target-lon');
          var addrId   = btn.getAttribute('data-st-target-address');
          var statusId = btn.getAttribute('data-st-status');
          var statusEl = statusId ? document.getElementById(statusId) : null;
          var origLabel = btn.textContent;

          function setStatus(text, cls) {
            if (!statusEl) return;
            statusEl.textContent = text;
            statusEl.className = 'st-field__help ' + (cls || '');
          }

          if (!('geolocation' in navigator)) {
            setStatus(Drupal.t('Geolocation is not available in this browser.'), 'is-err');
            alert(Drupal.t('Geolocation not supported by this browser.'));
            return;
          }
          if (!window.isSecureContext) {
            setStatus(Drupal.t('Browser blocks geolocation on insecure pages.'), 'is-err');
            return;
          }

          btn.disabled = true;
          btn.textContent = Drupal.t('Locating…');
          setStatus(Drupal.t('Locating you…'));

          navigator.geolocation.getCurrentPosition(
            function (p) {
              var lat = p.coords.latitude;
              var lon = p.coords.longitude;
              var latEl = latId ? document.getElementById(latId) : null;
              var lonEl = lonId ? document.getElementById(lonId) : null;
              if (latEl) latEl.value = lat.toFixed(6);
              if (lonEl) lonEl.value = lon.toFixed(6);

              // If an address target is wired up, reverse-geocode via the
              // Drupal proxy (same origin, no CORS) and fill the field.
              if (addrId) {
                setStatus(Drupal.t('Looking up address…'));
                fetch('/sales/api/reverse_geocode?lat=' + lat + '&lon=' + lon, {
                  credentials: 'same-origin'
                }).then(function (r) { return r.json(); })
                  .then(function (j) {
                    var addrEl = document.getElementById(addrId);
                    if (j && j.ok && j.address && addrEl) {
                      addrEl.value = j.address;
                      setStatus(Drupal.t('Address filled — edit if needed.'), 'is-ok');
                    } else {
                      setStatus(Drupal.t('Location captured. Please type the address.'), 'is-warn');
                    }
                  })
                  .catch(function () {
                    setStatus(Drupal.t('Location captured. Address lookup failed.'), 'is-warn');
                  })
                  .finally(function () {
                    btn.disabled = false;
                    btn.textContent = origLabel;
                  });
              } else {
                setStatus(Drupal.t('Location captured.'), 'is-ok');
                btn.disabled = false;
                btn.textContent = origLabel;
              }
            },
            function (err) {
              btn.disabled = false;
              btn.textContent = origLabel;
              var hint = {
                1: Drupal.t('Permission denied — allow location for this site (click the lock icon in the address bar).'),
                2: Drupal.t('Position unavailable — turn on Windows Location Services and Wi-Fi.'),
                3: Drupal.t('Timed out — try again, or type the address manually.')
              }[err.code] || Drupal.t('Geolocation error');
              setStatus(hint, 'is-err');
              alert(hint);
            },
            { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
          );
        });
      });
    }
  };

  /* ===================  SELFIE CAPTURE  =================== */
  Drupal.behaviors.salesTrackerSelfie = {
    attach: function (context) {
      once('st-selfie', '.js-st-selfie', context).forEach(function (stage) {
        var video       = stage.querySelector('.js-st-selfie-video');
        var canvas      = stage.querySelector('.js-st-selfie-canvas');
        var preview     = stage.querySelector('.js-st-selfie-preview');
        var placeholder = stage.querySelector('.js-st-selfie-placeholder');
        var openBtn     = document.querySelector('.js-st-selfie-open');
        var capBtn      = document.querySelector('.js-st-selfie-capture');
        var retakeBtn   = document.querySelector('.js-st-selfie-retake');
        var fileInput   = document.querySelector('.js-st-selfie-input');
        var statusEl    = document.querySelector('.js-st-selfie-status');
        if (!video || !openBtn || !fileInput) return;
        var stream = null;

        function setStatus(t, cls) {
          if (!statusEl) return;
          statusEl.textContent = t;
          statusEl.className = 'st-field__help ' + (cls || '');
        }
        function stopStream() {
          if (stream) { stream.getTracks().forEach(function (t) { t.stop(); }); stream = null; }
        }

        openBtn.addEventListener('click', async function (ev) {
          ev.preventDefault();
          if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            setStatus(Drupal.t('Camera not supported by this browser.'), 'is-err');
            alert(Drupal.t('Camera not supported by this browser.'));
            return;
          }
          try {
            stream = await navigator.mediaDevices.getUserMedia({
              video: { facingMode: 'user', width: { ideal: 720 }, height: { ideal: 720 } },
              audio: false
            });
            video.srcObject = stream;
            video.style.display = '';
            if (placeholder) placeholder.style.display = 'none';
            if (preview) preview.style.display = 'none';
            openBtn.style.display = 'none';
            if (capBtn) capBtn.style.display = '';
            if (retakeBtn) retakeBtn.style.display = 'none';
            setStatus(Drupal.t('Camera ready — tap Capture when you\'re in frame.'), 'is-ok');
          } catch (e) {
            setStatus(Drupal.t('Camera denied or unavailable.'), 'is-err');
            alert(Drupal.t('Camera denied or unavailable. Check the camera icon in the address bar and allow access. On Windows, also verify Settings > Privacy > Camera is ON.'));
          }
        });

        if (capBtn) capBtn.addEventListener('click', function (ev) {
          ev.preventDefault();
          var w = video.videoWidth || 480, h = video.videoHeight || 480;
          canvas.width = w; canvas.height = h;
          canvas.getContext('2d').drawImage(video, 0, 0, w, h);
          canvas.toBlob(function (blob) {
            if (!blob) { setStatus(Drupal.t('Capture failed — try again.'), 'is-err'); return; }
            var file = new File([blob], 'selfie-' + Date.now() + '.jpg', { type: 'image/jpeg' });
            var dt = new DataTransfer();
            dt.items.add(file);
            fileInput.files = dt.files;
            if (preview) {
              preview.src = URL.createObjectURL(blob);
              preview.style.display = '';
            }
            video.style.display = 'none';
            stopStream();
            capBtn.style.display = 'none';
            if (retakeBtn) retakeBtn.style.display = '';
            setStatus(Drupal.t('Photo captured — it will upload with the visit.'), 'is-ok');
          }, 'image/jpeg', 0.85);
        });

        if (retakeBtn) retakeBtn.addEventListener('click', function (ev) {
          ev.preventDefault();
          if (preview) { preview.removeAttribute('src'); preview.style.display = 'none'; }
          fileInput.value = '';
          if (placeholder) placeholder.style.display = '';
          retakeBtn.style.display = 'none';
          openBtn.style.display = '';
          setStatus('', '');
        });
      });
    }
  };

}(Drupal, once));
