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

    // Source set automatically by JS: 'gps' if location button was used, 'manual' otherwise.
    $form['source'] = [
      '#type' => 'hidden',
      '#default_value' => 'manual',
      '#attributes' => ['id' => 'checkin-source-mode'],
    ];
    $form['actual_place_name'] = [
      '#type' => 'textfield',
      '#title' => $this->t('Where are you now?'),
      '#placeholder' => 'House / Shop No., Area, City, State',
      '#description' => $this->t('Type the address freely, or tap the button below.'),
      '#prefix' => '<div class="st-field">',
      '#suffix' => '</div>',
      '#attributes' => ['id' => 'checkin-address', 'class' => ['form-text']],
    ];

    $form['lat'] = [
      '#type' => 'hidden',
      '#attributes' => ['id' => 'checkin-lat'],
    ];
    $form['lon'] = [
      '#type' => 'hidden',
      '#attributes' => ['id' => 'checkin-lon'],
    ];

    $form['use_loc'] = [
      '#type' => 'html_tag',
      '#tag' => 'button',
      '#value' => $this->t('Use my current location'),
      '#prefix' => '<p class="st-field">',
      '#suffix' => '<small id="checkin-useloc-status" class="st-field__help">' . $this->t('Fills the address from your device GPS.') . '</small></p>',
      '#attributes' => [
        'type' => 'button',
        'class' => ['st-btn', 'st-btn--secondary', 'st-btn--sm', 'js-st-geolocate'],
        'data-st-target-lat' => 'checkin-lat',
        'data-st-target-lon' => 'checkin-lon',
        'data-st-target-address' => 'checkin-address',
        'data-st-status' => 'checkin-useloc-status',
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
    if (!trim((string) $form_state->getValue('actual_place_name'))) {
      $form_state->setErrorByName('actual_place_name', $this->t('Address is required.'));
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
