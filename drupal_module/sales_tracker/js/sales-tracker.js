/**
 * Sales Tracker — client-side behaviors.
 * Currently: geolocation fill-in for any button carrying .js-st-geolocate
 *            and data-st-target-lat / data-st-target-lon attributes.
 */
(function (Drupal, once) {
  'use strict';

  Drupal.behaviors.salesTrackerGeolocate = {
    attach: function (context) {
      once('st-geolocate', '.js-st-geolocate', context).forEach(function (btn) {
        btn.addEventListener('click', function (ev) {
          ev.preventDefault();
          if (!('geolocation' in navigator)) {
            alert(Drupal.t('Geolocation is not available in this browser.'));
            return;
          }
          var latId = btn.getAttribute('data-st-target-lat');
          var lonId = btn.getAttribute('data-st-target-lon');
          var originalLabel = btn.textContent;
          btn.disabled = true;
          btn.textContent = Drupal.t('Locating…');
          navigator.geolocation.getCurrentPosition(
            function (p) {
              var latEl = latId ? document.getElementById(latId) : null;
              var lonEl = lonId ? document.getElementById(lonId) : null;
              if (latEl) latEl.value = p.coords.latitude.toFixed(6);
              if (lonEl) lonEl.value = p.coords.longitude.toFixed(6);
              btn.disabled = false;
              btn.textContent = originalLabel;
            },
            function (err) {
              btn.disabled = false;
              btn.textContent = originalLabel;
              alert(Drupal.t('Could not get your location: @msg', {'@msg': err.message || err.code}));
            },
            { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 }
          );
        });
      });
    }
  };

}(Drupal, once));
