<?php

namespace Drupal\sales_tracker\Form;

use Drupal\Core\Form\FormBase;
use Drupal\Core\Form\FormStateInterface;
use Drupal\Core\Render\Markup;
use Drupal\sales_tracker\Service\SalesTrackerApiClient;
use Symfony\Component\DependencyInjection\ContainerInterface;
use Symfony\Component\HttpFoundation\RequestStack;

/**
 * Log a customer visit — account picker from today's planned items + GPS/manual
 * + outcome + notes.
 *
 * Route: /sales/visit  (also accepts ?account_id=N to pre-select).
 */
class VisitForm extends FormBase {

  protected SalesTrackerApiClient $api;

  // Note: $requestStack is inherited from FormBase (untyped property), so we
  // must NOT redeclare it with a type — that would be a fatal "type must not
  // be defined" error on PHP 8.2+. Just assign it directly via create().

  public static function create(ContainerInterface $container) {
    $instance = new static();
    $instance->api = $container->get('sales_tracker.api_client');
    $instance->requestStack = $container->get('request_stack');
    return $instance;
  }

  public function getFormId() {
    return 'sales_tracker_visit_form';
  }

  public function buildForm(array $form, FormStateInterface $form_state) {
    $form['#attached']['library'][] = 'sales_tracker/sales_tracker';
    $form['#prefix'] = '<div class="sales-tracker"><div class="st-card st-card--focal st-form-card">';
    $form['#suffix'] = '</div></div>';
    // Required so the selfie file ride along with the form POST.
    $form['#attributes']['enctype'] = 'multipart/form-data';

    // Pull today's plan so we can show the planned accounts as the picker.
    $planRes = $this->api->getPlanToday();
    $items = $planRes['items'] ?? ($planRes['plan']['items'] ?? []);

    // Build option groups via Drupal's nested-array option syntax so we don't
    // need a sentinel '_' value that the user could accidentally select.
    $planned_opts = [];
    $planned_ids = [];
    foreach ($items as $it) {
      $aid = $it['account_id'] ?? ($it['id'] ?? NULL);
      $aname = $it['account_name'] ?? ($it['name'] ?? ('Account #' . $aid));
      $atype = $it['account_type'] ?? ($it['type'] ?? '');
      if ($aid) {
        $planned_opts[$aid] = $aname . ($atype ? ' (' . $atype . ')' : '');
        $planned_ids[$aid] = TRUE;
      }
    }
    $other_opts = [];
    $allAccounts = $this->api->listAccounts(['limit' => 200])['rows'] ?? [];
    foreach ($allAccounts as $a) {
      if (!isset($planned_ids[$a['id']])) {
        $other_opts[$a['id']] = $a['name'] . ' (' . $a['type'] . ')';
      }
    }
    $account_opts = ['' => $this->t('— Select an account —')];
    if ($planned_opts) {
      $account_opts[(string) $this->t('Today planned')] = $planned_opts;
    }
    if ($other_opts) {
      $account_opts[(string) $this->t('Other accounts')] = $other_opts;
    }

    $request = $this->requestStack->getCurrentRequest();
    $preselect = $request ? $request->query->get('account_id') : NULL;

    // Resolve preselected account's lat/lon so we can render an "Account
    // location" callout above the lat/lon fields. The .js-st-geolocate hook
    // is unchanged — it still fills the fields from the device on demand.
    $preselect_account_lat = NULL;
    $preselect_account_lon = NULL;
    $preselect_account_name = NULL;
    if ($preselect && is_numeric($preselect)) {
      $acc = $this->api->getAccount((int) $preselect);
      $row = $acc['account'] ?? ($acc['row'] ?? $acc);
      if (is_array($row)) {
        $preselect_account_name = $row['name'] ?? NULL;
        if (isset($row['lat']) && $row['lat'] !== NULL && $row['lat'] !== '') {
          $preselect_account_lat = $row['lat'];
        }
        if (isset($row['lon']) && $row['lon'] !== NULL && $row['lon'] !== '') {
          $preselect_account_lon = $row['lon'];
        }
      }
    }

    $form['account_id'] = [
      '#type' => 'select',
      '#title' => $this->t('Account visited'),
      '#options' => $account_opts,
      '#required' => TRUE,
      '#default_value' => $preselect ?: '',
      '#prefix' => '<div class="st-field">',
      '#suffix' => '</div>',
      '#attributes' => ['class' => ['form-select']],
    ];

    $form['outcome'] = [
      '#type' => 'select',
      '#title' => $this->t('Outcome'),
      '#required' => TRUE,
      '#options' => [
        'met' => $this->t('Met — productive visit'),
        'not_met' => $this->t('Not met — contact unavailable'),
        'rescheduled' => $this->t('Rescheduled'),
      ],
      '#default_value' => 'met',
      '#prefix' => '<div class="st-field">',
      '#suffix' => '</div>',
      '#attributes' => ['class' => ['form-select']],
    ];

    // Source is set automatically by the JS: 'gps' if Use my location was
    // clicked, 'manual' otherwise. We keep it as a hidden field so the
    // server still sees a value.
    $form['source'] = [
      '#type' => 'hidden',
      '#default_value' => 'manual',
      '#attributes' => ['id' => 'visit-source-mode'],
    ];

    $form['actual_place_name'] = [
      '#type' => 'textfield',
      '#title' => $this->t('Visit address'),
      '#placeholder' => 'House / Shop No., Area, City, State',
      '#description' => $this->t('Type the address freely, or tap the button below to fill it from your device.'),
      '#prefix' => '<div class="st-field">',
      '#suffix' => '</div>',
      '#attributes' => ['id' => 'visit-address', 'class' => ['form-text']],
    ];

    // v3: Geolocation subhead + optional "Account location" callout. The
    // .js-st-geolocate behavior below still owns the live device fetch — this
    // block is purely informational and does not change form field names.
    $geo_section_html = '<div class="st-geo-section">'
      . '<h3 class="st-geo-section__title">'
      . '<svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true" focusable="false">'
      . '<path d="M8 1.5c-2.6 0-4.7 2.1-4.7 4.7 0 3.4 4.7 8.3 4.7 8.3s4.7-4.9 4.7-8.3C12.7 3.6 10.6 1.5 8 1.5z" '
      . 'fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>'
      . '<circle cx="8" cy="6.2" r="1.7" fill="currentColor"/>'
      . '</svg>'
      . 'Geolocation'
      . '</h3>';
    if ($preselect_account_lat !== NULL && $preselect_account_lon !== NULL) {
      $lat_f = number_format((float) $preselect_account_lat, 4, '.', '');
      $lon_f = number_format((float) $preselect_account_lon, 4, '.', '');
      $lat_raw = htmlspecialchars((string) $preselect_account_lat, ENT_QUOTES, 'UTF-8');
      $lon_raw = htmlspecialchars((string) $preselect_account_lon, ENT_QUOTES, 'UTF-8');
      $label = htmlspecialchars((string) ($preselect_account_name ?? 'account'), ENT_QUOTES, 'UTF-8');
      $map_url = 'https://www.google.com/maps/?q=' . $lat_raw . ',' . $lon_raw;
      $geo_section_html .= '<p class="st-geo-callout">'
        . '<span class="st-geo-callout__label">Account location:</span>'
        . '<span class="st-geo" data-lat="' . $lat_raw . '" data-lon="' . $lon_raw . '">'
        . '<svg class="st-geo__pin" width="14" height="14" viewBox="0 0 16 16" aria-hidden="true" focusable="false">'
        . '<path d="M8 1.5c-2.6 0-4.7 2.1-4.7 4.7 0 3.4 4.7 8.3 4.7 8.3s4.7-4.9 4.7-8.3C12.7 3.6 10.6 1.5 8 1.5z" '
        . 'fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>'
        . '<circle cx="8" cy="6.2" r="1.7" fill="currentColor"/>'
        . '</svg>'
        . '<code class="st-geo__coord">' . $lat_f . ', ' . $lon_f . '</code>'
        . '<a class="st-geo__map" href="' . $map_url . '" target="_blank" rel="noopener noreferrer" '
        . 'aria-label="View ' . $label . ' on Google Maps (opens in new tab)">'
        . 'View on map'
        . '<svg width="11" height="11" viewBox="0 0 16 16" aria-hidden="true" focusable="false">'
        . '<path d="M6 3h7v7M13 3L6.5 9.5M3 6v7h7" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>'
        . '</svg>'
        . '</a>'
        . '</span>'
        . '</p>';
    }
    else {
      $geo_section_html .= '<p class="st-geo-callout st-muted">'
        . 'Use <strong>Get my location</strong> below to capture your current coordinates, '
        . 'or type them in manually.'
        . '</p>';
    }
    $geo_section_html .= '</div>';
    $form['geo_section'] = [
      '#type' => 'markup',
      // Markup::create() bypasses Xss filtering — required so the inline SVG
      // pin + map-link attributes (target, rel, href, aria-label) survive.
      // The HTML above is built from htmlspecialchars()'d values, so the only
      // dynamic content reaching the browser is properly escaped.
      '#markup' => Markup::create($geo_section_html),
    ];

    // Lat/lon ride along as hidden inputs — the JS Behavior fills them after
    // a successful getCurrentPosition() so the matcher still has coords.
    $form['lat'] = [
      '#type' => 'hidden',
      '#attributes' => ['id' => 'visit-lat'],
    ];
    $form['lon'] = [
      '#type' => 'hidden',
      '#attributes' => ['id' => 'visit-lon'],
    ];

    $form['use_loc'] = [
      '#type' => 'html_tag',
      '#tag' => 'button',
      '#value' => $this->t('Use my current location'),
      '#prefix' => '<p class="st-field">',
      '#suffix' => '<small id="visit-useloc-status" class="st-field__help">' . $this->t('Fills the address from your device GPS.') . '</small></p>',
      '#attributes' => [
        'type' => 'button',
        'class' => ['st-btn', 'st-btn--secondary', 'st-btn--sm', 'js-st-geolocate'],
        'data-st-target-lat' => 'visit-lat',
        'data-st-target-lon' => 'visit-lon',
        'data-st-target-address' => 'visit-address',
        'data-st-status' => 'visit-useloc-status',
      ],
    ];

    // ============== Proof-of-visit selfie ==============
    $selfie_html = '<div class="st-field selfie-field">'
      . '<span class="field-label">' . $this->t('Proof selfie') . ' <em class="req-text">(' . $this->t('optional') . ')</em></span>'
      . '<small class="st-field__help">' . $this->t("Take a quick photo at the location — it'll be attached to this visit as proof.") . '</small>'
      . '<div class="selfie-stage js-st-selfie">'
      .   '<video class="selfie-video js-st-selfie-video" autoplay muted playsinline style="display:none"></video>'
      .   '<canvas class="selfie-canvas js-st-selfie-canvas" style="display:none"></canvas>'
      .   '<img class="selfie-preview js-st-selfie-preview" alt="" style="display:none">'
      .   '<div class="selfie-placeholder js-st-selfie-placeholder">'
      .     '<svg viewBox="0 0 24 24" width="36" height="36" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
      .       '<rect x="3" y="6" width="18" height="13" rx="2"/>'
      .       '<circle cx="12" cy="12.5" r="3.5"/>'
      .       '<path d="M8 6l1.5-2h5L16 6"/>'
      .     '</svg>'
      .     '<span>' . $this->t('No photo yet') . '</span>'
      .   '</div>'
      . '</div>'
      . '<div class="selfie-controls">'
      .   '<button type="button" class="st-btn st-btn--secondary js-st-selfie-open">' . $this->t('Open camera') . '</button>'
      .   '<button type="button" class="st-btn st-btn--primary js-st-selfie-capture" style="display:none">' . $this->t('Capture') . '</button>'
      .   '<button type="button" class="st-btn st-btn--secondary js-st-selfie-retake" style="display:none">' . $this->t('Retake') . '</button>'
      . '</div>'
      . '<small class="st-field__help js-st-selfie-status"></small>'
      . '</div>';
    $form['selfie_ui'] = [
      '#type' => 'markup',
      '#markup' => Markup::create($selfie_html),
    ];
    // The real file input that travels with the POST. Drupal will receive
    // it under $request->files->get('files')['selfie'].
    $form['selfie'] = [
      '#type' => 'file',
      '#title' => $this->t('Selfie'),
      '#title_display' => 'invisible',
      '#attributes' => [
        'accept' => 'image/*',
        'capture' => 'user',
        'class' => ['js-st-selfie-input'],
        'style' => 'display:none',
      ],
    ];

    $form['visit_notes'] = [
      '#type' => 'textarea',
      '#title' => $this->t('Visit notes'),
      '#rows' => 3,
      '#placeholder' => 'Discussion summary, samples left, next-step',
      '#prefix' => '<div class="st-field">',
      '#suffix' => '</div>',
      '#attributes' => ['class' => ['form-textarea']],
    ];

    $form['actions']['#type'] = 'actions';
    $form['actions']['#prefix'] = '<div class="st-form-card__footer">';
    $form['actions']['#suffix'] = '</div>';
    $form['actions']['submit'] = [
      '#type' => 'submit',
      '#value' => $this->t('Log visit'),
      '#attributes' => ['class' => ['st-btn', 'st-btn--primary', 'st-btn--lg']],
    ];
    return $form;
  }

  public function validateForm(array &$form, FormStateInterface $form_state) {
    $aid = $form_state->getValue('account_id');
    if (!$aid) {
      $form_state->setErrorByName('account_id', $this->t('Pick an account.'));
    }
    foreach (['lat' => [-90, 90], 'lon' => [-180, 180]] as $field => [$min, $max]) {
      $v = $form_state->getValue($field);
      if ($v !== '' && $v !== NULL && (!is_numeric($v) || $v < $min || $v > $max)) {
        $form_state->setErrorByName($field, $this->t('@f must be between @min and @max.', [
          '@f' => ucfirst($field),
          '@min' => $min,
          '@max' => $max,
        ]));
      }
    }
    if (!in_array($form_state->getValue('outcome'), ['met', 'not_met', 'rescheduled'], TRUE)) {
      $form_state->setErrorByName('outcome', $this->t('Invalid outcome.'));
    }
  }

  public function submitForm(array &$form, FormStateInterface $form_state) {
    $payload = [
      'account_id' => (int) $form_state->getValue('account_id'),
      'outcome' => $form_state->getValue('outcome'),
      'source' => $form_state->getValue('source') ?: 'manual',
      'actual_place_name' => trim((string) $form_state->getValue('actual_place_name')) ?: NULL,
      'lat' => $form_state->getValue('lat') !== '' ? (float) $form_state->getValue('lat') : NULL,
      'lon' => $form_state->getValue('lon') !== '' ? (float) $form_state->getValue('lon') : NULL,
      'visit_notes' => trim((string) $form_state->getValue('visit_notes')) ?: NULL,
    ];
    // If the user captured a selfie, it arrives under $_FILES['files']['selfie']
    // (Drupal nests file fields under 'files'). Forward it to Flask as multipart.
    $request = \Drupal::request();
    $files = $request->files->get('files') ?: [];
    $selfie = $files['selfie'] ?? NULL;
    if ($selfie && $selfie->isValid() && $selfie->getSize() > 0) {
      $res = $this->api->logVisitWithSelfie($payload, $selfie->getPathname(), $selfie->getClientOriginalName() ?: 'selfie.jpg');
    }
    else {
      $res = $this->api->logVisit($payload);
    }
    if (empty($res['ok'])) {
      $this->messenger()->addError($this->t('Could not log visit: @e', [
        '@e' => $res['error'] ?? 'unknown error',
      ]));
      return;
    }
    $this->messenger()->addStatus($this->t('Visit logged.'));
    $form_state->setRedirect('sales_tracker.dashboard');
  }

}
