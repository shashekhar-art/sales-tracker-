<?php

namespace Drupal\sales_tracker\Form;

use Drupal\Core\Form\FormBase;
use Drupal\Core\Form\FormStateInterface;
use Drupal\sales_tracker\Service\SalesTrackerApiClient;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Record a check-in for today's plan.
 */
class CheckinForm extends FormBase {

  protected SalesTrackerApiClient $api;

  public static function create(ContainerInterface $container) {
    $instance = new static();
    $instance->api = $container->get('sales_tracker.api_client');
    return $instance;
  }

  public function getFormId() {
    return 'sales_tracker_checkin_form';
  }

  public function buildForm(array $form, FormStateInterface $form_state) {
    $form['#attached']['library'][] = 'sales_tracker/sales_tracker';
    $form['#prefix'] = '<div class="sales-tracker"><div class="st-card st-card--focal st-form-card">';
    $form['#suffix'] = '</div></div>';

    $form['source'] = [
      '#type' => 'select',
      '#title' => $this->t('Source'),
      '#options' => [
        'manual' => $this->t('Manual (type place)'),
        'gps' => $this->t('GPS (use device location)'),
      ],
      '#default_value' => 'manual',
      '#prefix' => '<div class="st-field">',
      '#suffix' => '</div>',
      '#attributes' => ['class' => ['form-select']],
    ];
    $form['actual_place_name'] = [
      '#type' => 'textfield',
      '#title' => $this->t('Where are you now?'),
      '#placeholder' => 'e.g. Janpath, New Delhi',
      '#description' => $this->t('Required for manual; ignored for GPS.'),
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
      '#description' => $this->t('Decimal degrees, 4 places'),
      '#attributes' => ['id' => 'checkin-lat', 'inputmode' => 'decimal', 'class' => ['form-text']],
      '#prefix' => '<div class="st-field st-field--mono">',
      '#suffix' => '</div>',
    ];
    $form['lon'] = [
      '#type' => 'textfield',
      '#title' => $this->t('Longitude'),
      '#placeholder' => '77.5946',
      '#description' => $this->t('Decimal degrees, 4 places'),
      '#attributes' => ['id' => 'checkin-lon', 'inputmode' => 'decimal', 'class' => ['form-text']],
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
        'data-st-target-lat' => 'checkin-lat',
        'data-st-target-lon' => 'checkin-lon',
      ],
    ];
    $form['actions']['#type'] = 'actions';
    $form['actions']['#prefix'] = '<div class="st-form-card__footer">';
    $form['actions']['#suffix'] = '</div>';
    $form['actions']['submit'] = [
      '#type' => 'submit',
      '#value' => $this->t('Check in now'),
      '#attributes' => ['class' => ['st-btn', 'st-btn--primary', 'st-btn--lg']],
    ];
    return $form;
  }

  public function validateForm(array &$form, FormStateInterface $form_state) {
    $source = $form_state->getValue('source');
    if ($source === 'manual' && !trim($form_state->getValue('actual_place_name'))) {
      $form_state->setErrorByName('actual_place_name', $this->t('Place name is required for a manual check-in.'));
    }
    if ($source === 'gps' && (!$form_state->getValue('lat') || !$form_state->getValue('lon'))) {
      $form_state->setErrorByName('lat', $this->t('Latitude and longitude are required for a GPS check-in.'));
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
  }

  public function submitForm(array &$form, FormStateInterface $form_state) {
    $payload = [
      'source' => $form_state->getValue('source'),
      'actual_place_name' => $form_state->getValue('actual_place_name'),
      'lat' => $form_state->getValue('lat') ?: NULL,
      'lon' => $form_state->getValue('lon') ?: NULL,
    ];
    $res = $this->api->checkin($payload);
    if (empty($res['ok'])) {
      $this->messenger()->addError($this->t('Check-in failed: @e', ['@e' => $res['error'] ?? 'unknown error']));
      return;
    }
    $m = $res['match'];
    if (!empty($res['anomaly']['is_anomaly'])) {
      $this->messenger()->addWarning($this->t('Recorded but FLAGGED — @r', ['@r' => $res['anomaly']['reason']]));
    }
    elseif ($m['matched']) {
      $this->messenger()->addStatus($this->t('Check-in matched the plan (score @s).', ['@s' => $m['match_score']]));
    }
    else {
      $this->messenger()->addWarning($this->t('Check-in did NOT match the plan (score @s).', ['@s' => $m['match_score']]));
    }
    $form_state->setRedirect('sales_tracker.dashboard');
  }

}
