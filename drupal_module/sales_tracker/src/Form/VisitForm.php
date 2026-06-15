<?php

namespace Drupal\sales_tracker\Form;

use Drupal\Core\Form\FormBase;
use Drupal\Core\Form\FormStateInterface;
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

    $form['source'] = [
      '#type' => 'select',
      '#title' => $this->t('Location source'),
      '#options' => [
        'manual' => $this->t('Manual (type place)'),
        'gps' => $this->t('GPS (use device location)'),
      ],
      '#default_value' => 'gps',
      '#prefix' => '<div class="st-field">',
      '#suffix' => '</div>',
      '#attributes' => ['class' => ['form-select']],
    ];

    $form['actual_place_name'] = [
      '#type' => 'textfield',
      '#title' => $this->t('Where are you now?'),
      '#placeholder' => 'e.g. Saket District Centre, New Delhi',
      '#description' => $this->t('Required for manual; auto-filled for GPS.'),
      '#prefix' => '<div class="st-field">',
      '#suffix' => '</div>',
      '#attributes' => ['class' => ['form-text']],
    ];

    $form['coords_open'] = [
      '#type' => 'markup',
      '#markup' => '<div class="st-grid-2">',
      '#allowed_tags' => ['div'],
    ];
    $form['lat'] = [
      '#type' => 'textfield',
      '#title' => $this->t('Latitude'),
      '#placeholder' => '12.9716',
      '#attributes' => ['id' => 'visit-lat', 'inputmode' => 'decimal', 'class' => ['form-text']],
      '#prefix' => '<div class="st-field st-field--mono">',
      '#suffix' => '</div>',
    ];
    $form['lon'] = [
      '#type' => 'textfield',
      '#title' => $this->t('Longitude'),
      '#placeholder' => '77.5946',
      '#attributes' => ['id' => 'visit-lon', 'inputmode' => 'decimal', 'class' => ['form-text']],
      '#prefix' => '<div class="st-field st-field--mono">',
      '#suffix' => '</div>',
    ];
    $form['coords_close'] = [
      '#type' => 'markup',
      '#markup' => '</div>',
      '#allowed_tags' => ['div'],
    ];

    $form['use_loc'] = [
      '#type' => 'html_tag',
      '#tag' => 'button',
      '#value' => $this->t('Get my location'),
      '#prefix' => '<p class="st-field">',
      '#suffix' => '</p>',
      '#attributes' => [
        'type' => 'button',
        'class' => ['st-btn', 'st-btn--secondary', 'st-btn--sm', 'js-st-geolocate'],
        'data-st-target-lat' => 'visit-lat',
        'data-st-target-lon' => 'visit-lon',
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
    $source = $form_state->getValue('source');
    if ($source === 'manual' && !trim((string) $form_state->getValue('actual_place_name'))) {
      $form_state->setErrorByName('actual_place_name', $this->t('Place name is required for a manual visit.'));
    }
    if ($source === 'gps' && (!$form_state->getValue('lat') || !$form_state->getValue('lon'))) {
      $form_state->setErrorByName('lat', $this->t('Latitude and longitude are required for a GPS visit.'));
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
      'source' => $form_state->getValue('source'),
      'actual_place_name' => trim((string) $form_state->getValue('actual_place_name')) ?: NULL,
      'lat' => $form_state->getValue('lat') !== '' ? (float) $form_state->getValue('lat') : NULL,
      'lon' => $form_state->getValue('lon') !== '' ? (float) $form_state->getValue('lon') : NULL,
      'visit_notes' => trim((string) $form_state->getValue('visit_notes')) ?: NULL,
    ];
    $res = $this->api->logVisit($payload);
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
