<?php

namespace Drupal\sales_tracker\Form;

use Drupal\Core\Form\FormBase;
use Drupal\Core\Form\FormStateInterface;
use Drupal\sales_tracker\Service\SalesTrackerApiClient;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Create or edit an account (doctor / chemist / stockist).
 *
 * Same form class handles both /sales/accounts/add and /sales/accounts/{id}/edit
 * — when route arg account_id is null we create, otherwise we update.
 */
class AccountForm extends FormBase {

  protected SalesTrackerApiClient $api;

  public static function create(ContainerInterface $container) {
    $instance = new static();
    $instance->api = $container->get('sales_tracker.api_client');
    return $instance;
  }

  public function getFormId() {
    return 'sales_tracker_account_form';
  }

  public function buildForm(array $form, FormStateInterface $form_state, $account_id = NULL) {
    $form['#attached']['library'][] = 'sales_tracker/sales_tracker';
    $form['#prefix'] = '<div class="sales-tracker"><div class="st-card st-card--focal st-form-card">';
    $form['#suffix'] = '</div></div>';

    $existing = NULL;
    if ($account_id) {
      $res = $this->api->getAccount((int) $account_id);
      $existing = $res['account'] ?? NULL;
    }

    // Stash for submit handler.
    $form_state->set('account_id', $account_id ? (int) $account_id : NULL);

    // Build region/district options from API.
    $regions = $this->api->getRegions()['rows'] ?? [];
    $region_opts = ['' => $this->t('— Select region —')];
    foreach ($regions as $r) {
      $region_opts[$r['id']] = $r['name'];
    }

    // Resolve the currently-selected region: prefer the live form-state value
    // (AJAX rebuild), then a submitted user input, then the stored existing
    // value. This lets the district dropdown refresh after a region change
    // without a full page reload.
    $current_region = $form_state->getValue('region_id');
    if ($current_region === NULL || $current_region === '') {
      $current_region = $existing['region_id'] ?? NULL;
    }
    $districts = [];
    if ($current_region) {
      $districts = $this->api->getDistricts((int) $current_region)['rows'] ?? [];
    }
    $district_opts = ['' => $this->t('— Select district —')];
    foreach ($districts as $d) {
      $district_opts[$d['id']] = $d['name'];
    }

    $form['name'] = [
      '#type' => 'textfield',
      '#title' => $this->t('Account name'),
      '#required' => TRUE,
      '#default_value' => $existing['name'] ?? '',
      '#placeholder' => 'e.g. Dr. R. Sharma / Apollo Pharmacy / Medplus Stockist',
      '#prefix' => '<div class="st-field">',
      '#suffix' => '</div>',
      '#attributes' => ['class' => ['form-text']],
    ];

    $form['type'] = [
      '#type' => 'select',
      '#title' => $this->t('Type'),
      '#required' => TRUE,
      '#options' => [
        'doctor' => $this->t('Doctor'),
        'chemist' => $this->t('Chemist'),
        'stockist' => $this->t('Stockist'),
      ],
      '#default_value' => $existing['type'] ?? 'doctor',
      '#prefix' => '<div class="st-field">',
      '#suffix' => '</div>',
      '#attributes' => ['class' => ['form-select']],
    ];

    $form['specialty'] = [
      '#type' => 'textfield',
      '#title' => $this->t('Specialty / category'),
      '#default_value' => $existing['specialty'] ?? '',
      '#placeholder' => 'e.g. Cardiology, General Practice, Stockist (OTC)',
      '#description' => $this->t('Useful for doctors (specialty); for chemists/stockists this is a free-text category.'),
      '#prefix' => '<div class="st-field">',
      '#suffix' => '</div>',
      '#attributes' => ['class' => ['form-text']],
    ];

    // Region + district as a 2-column grid.
    $form['geo_open'] = [
      '#type' => 'markup',
      '#markup' => '<div class="st-grid-2">',
      '#allowed_tags' => ['div'],
    ];
    $form['region_id'] = [
      '#type' => 'select',
      '#title' => $this->t('Region (State / UT)'),
      '#options' => $region_opts,
      '#default_value' => $current_region ?? '',
      '#prefix' => '<div class="st-field">',
      '#suffix' => '</div>',
      '#attributes' => ['class' => ['form-select']],
      '#ajax' => [
        'callback' => '::districtAjax',
        'wrapper' => 'sales-tracker-district-wrap',
        'event' => 'change',
      ],
    ];
    $form['district_id'] = [
      '#type' => 'select',
      '#title' => $this->t('District'),
      '#options' => $district_opts,
      '#default_value' => $existing['district_id'] ?? '',
      '#description' => $this->t('Pick a region first; districts load automatically.'),
      '#prefix' => '<div class="st-field" id="sales-tracker-district-wrap">',
      '#suffix' => '</div>',
      '#attributes' => ['class' => ['form-select']],
    ];
    $form['geo_close'] = [
      '#type' => 'markup',
      '#markup' => '</div>',
      '#allowed_tags' => ['div'],
    ];

    $form['address'] = [
      '#type' => 'textarea',
      '#title' => $this->t('Address'),
      '#rows' => 2,
      '#default_value' => $existing['address'] ?? '',
      '#prefix' => '<div class="st-field">',
      '#suffix' => '</div>',
      '#attributes' => ['class' => ['form-textarea']],
    ];

    $form['contact_open'] = [
      '#type' => 'markup',
      '#markup' => '<div class="st-grid-2">',
      '#allowed_tags' => ['div'],
    ];
    $form['phone'] = [
      '#type' => 'tel',
      '#title' => $this->t('Phone'),
      '#default_value' => $existing['phone'] ?? '',
      '#placeholder' => '+91 98xxxxxxxx',
      '#prefix' => '<div class="st-field">',
      '#suffix' => '</div>',
      '#attributes' => ['class' => ['form-text']],
    ];
    $form['email'] = [
      '#type' => 'email',
      '#title' => $this->t('Email'),
      '#default_value' => $existing['email'] ?? '',
      '#prefix' => '<div class="st-field">',
      '#suffix' => '</div>',
      '#attributes' => ['class' => ['form-text']],
    ];
    $form['contact_close'] = [
      '#type' => 'markup',
      '#markup' => '</div>',
      '#allowed_tags' => ['div'],
    ];

    // Optional coordinates.
    $form['coords_open'] = [
      '#type' => 'markup',
      '#markup' => '<div class="st-grid-2">',
      '#allowed_tags' => ['div'],
    ];
    $form['lat'] = [
      '#type' => 'textfield',
      '#title' => $this->t('Latitude (optional)'),
      '#default_value' => $existing['lat'] ?? '',
      '#placeholder' => '12.9716',
      '#attributes' => ['inputmode' => 'decimal', 'class' => ['form-text']],
      '#prefix' => '<div class="st-field st-field--mono">',
      '#suffix' => '</div>',
    ];
    $form['lon'] = [
      '#type' => 'textfield',
      '#title' => $this->t('Longitude (optional)'),
      '#default_value' => $existing['lon'] ?? '',
      '#placeholder' => '77.5946',
      '#attributes' => ['inputmode' => 'decimal', 'class' => ['form-text']],
      '#prefix' => '<div class="st-field st-field--mono">',
      '#suffix' => '</div>',
    ];
    $form['coords_close'] = [
      '#type' => 'markup',
      '#markup' => '</div>',
      '#allowed_tags' => ['div'],
    ];

    $form['actions']['#type'] = 'actions';
    $form['actions']['#prefix'] = '<div class="st-form-card__footer">';
    $form['actions']['#suffix'] = '</div>';
    $form['actions']['submit'] = [
      '#type' => 'submit',
      '#value' => $account_id ? $this->t('Save changes') : $this->t('Create account'),
      '#attributes' => ['class' => ['st-btn', 'st-btn--primary']],
    ];
    return $form;
  }

  /**
   * AJAX callback — returns the (now re-built) district_id sub-element.
   */
  public function districtAjax(array &$form, FormStateInterface $form_state) {
    return $form['district_id'];
  }

  public function validateForm(array &$form, FormStateInterface $form_state) {
    $type = $form_state->getValue('type');
    if (!in_array($type, ['doctor', 'chemist', 'stockist'], TRUE)) {
      $form_state->setErrorByName('type', $this->t('Invalid type.'));
    }
    // Require a district when a region has been picked — half-classified
    // accounts (region but no district) are not persistable today and would
    // be invisible to the district-scoped roll-ups.
    if ($form_state->getValue('region_id') && !$form_state->getValue('district_id')) {
      $form_state->setErrorByName('district_id', $this->t('Pick a district within the selected region.'));
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
      'name' => trim($form_state->getValue('name')),
      'type' => $form_state->getValue('type'),
      'specialty' => trim($form_state->getValue('specialty')) ?: NULL,
      'region_id' => $form_state->getValue('region_id') ?: NULL,
      'district_id' => $form_state->getValue('district_id') ?: NULL,
      'address' => trim($form_state->getValue('address')) ?: NULL,
      'phone' => trim($form_state->getValue('phone')) ?: NULL,
      'email' => trim($form_state->getValue('email')) ?: NULL,
      'lat' => $form_state->getValue('lat') !== '' ? (float) $form_state->getValue('lat') : NULL,
      'lon' => $form_state->getValue('lon') !== '' ? (float) $form_state->getValue('lon') : NULL,
    ];
    $account_id = $form_state->get('account_id');
    if ($account_id) {
      $res = $this->api->updateAccount($account_id, $payload);
    }
    else {
      $res = $this->api->createAccount($payload);
    }
    if (!empty($res['ok'])) {
      $this->messenger()->addStatus($account_id
        ? $this->t('Account updated.')
        : $this->t('Account created.'));
      $form_state->setRedirect('sales_tracker.accounts');
    }
    else {
      $this->messenger()->addError($this->t('Could not save account: @e', [
        '@e' => $res['error'] ?? 'unknown error',
      ]));
    }
  }

}
