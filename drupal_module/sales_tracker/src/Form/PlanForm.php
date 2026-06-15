<?php

namespace Drupal\sales_tracker\Form;

use Drupal\Core\Form\FormBase;
use Drupal\Core\Form\FormStateInterface;
use Drupal\sales_tracker\Service\SalesTrackerApiClient;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Declare today's planned work location.
 */
class PlanForm extends FormBase {

  protected SalesTrackerApiClient $api;

  public static function create(ContainerInterface $container) {
    $instance = new static();
    $instance->api = $container->get('sales_tracker.api_client');
    return $instance;
  }

  public function getFormId() {
    return 'sales_tracker_plan_form';
  }

  public function buildForm(array $form, FormStateInterface $form_state) {
    $form['#attached']['library'][] = 'sales_tracker/sales_tracker';
    // Outer .sales-tracker scopes all our component CSS; the inner
    // .st-card.st-form-card.st-card--focal wrapper gives the form the same
    // hero-style top gradient stripe used elsewhere in the dashboard.
    $form['#prefix'] = '<div class="sales-tracker"><div class="st-card st-card--focal st-form-card">';
    $form['#suffix'] = '</div></div>';

    $existing = $this->api->getPlanToday();
    $plan = $existing['plan'] ?? NULL;

    $form['place'] = [
      '#type' => 'textfield',
      '#title' => $this->t('Planned location'),
      '#required' => TRUE,
      '#default_value' => $plan['planned_place_name'] ?? '',
      '#placeholder' => 'e.g. Connaught Place, New Delhi',
      '#description' => $this->t('The customer site or branch you plan to visit.'),
      '#prefix' => '<div class="st-field">',
      '#suffix' => '</div>',
      '#attributes' => ['class' => ['form-text']],
    ];

    // Lat/lon sit in a 2-column grid using .st-grid-2.
    $form['coords_open'] = [
      '#type' => 'markup',
      '#markup' => '<div class="st-grid-2">',
      '#allowed_tags' => ['div'],
    ];
    $form['lat'] = [
      '#type' => 'textfield',
      '#title' => $this->t('Latitude (optional)'),
      '#default_value' => $plan['planned_lat'] ?? '',
      '#description' => $this->t('Decimal degrees, e.g. 12.9716'),
      '#placeholder' => '12.9716',
      '#attributes' => ['id' => 'plan-lat', 'inputmode' => 'decimal', 'class' => ['form-text']],
      '#prefix' => '<div class="st-field st-field--mono">',
      '#suffix' => '</div>',
    ];
    $form['lon'] = [
      '#type' => 'textfield',
      '#title' => $this->t('Longitude (optional)'),
      '#default_value' => $plan['planned_lon'] ?? '',
      '#description' => $this->t('Decimal degrees, e.g. 77.5946'),
      '#placeholder' => '77.5946',
      '#attributes' => ['id' => 'plan-lon', 'inputmode' => 'decimal', 'class' => ['form-text']],
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
      '#value' => $this->t('Use my current location'),
      '#prefix' => '<p class="st-field">',
      '#suffix' => '</p>',
      '#attributes' => [
        'type' => 'button',
        'class' => ['st-btn', 'st-btn--secondary', 'st-btn--sm', 'js-st-geolocate'],
        'data-st-target-lat' => 'plan-lat',
        'data-st-target-lon' => 'plan-lon',
      ],
    ];
    $form['notes'] = [
      '#type' => 'textarea',
      '#title' => $this->t('Notes'),
      '#rows' => 2,
      '#default_value' => $plan['notes'] ?? '',
      '#placeholder' => 'Optional context for your manager',
      '#prefix' => '<div class="st-field">',
      '#suffix' => '</div>',
      '#attributes' => ['class' => ['form-textarea']],
    ];

    // ----- v2: planned account picker (multi-select checkboxes) ----------
    // Show every account in the employee's district (or all, fallback) so
    // they can tick the customers they intend to visit today. The plan POST
    // sends an account_ids[] array which the Flask side persists into
    // planned_visit_items.
    $accountsRes = $this->api->listAccounts(['limit' => 200]);
    $allAccounts = $accountsRes['rows'] ?? [];
    $account_opts = [];
    foreach ($allAccounts as $a) {
      $label = $a['name'];
      if (!empty($a['type'])) {
        $label .= ' (' . $a['type'] . ')';
      }
      $account_opts[$a['id']] = $label;
    }

    // Pre-tick the accounts that are already on today's plan.
    $existing_items = $existing['items'] ?? ($plan['items'] ?? []);
    $defaultIds = [];
    foreach ($existing_items as $it) {
      $aid = $it['account_id'] ?? ($it['id'] ?? NULL);
      if ($aid) {
        $defaultIds[$aid] = $aid;
      }
    }

    $form['account_ids'] = [
      '#type' => 'checkboxes',
      '#title' => $this->t('Accounts to visit today'),
      '#options' => $account_opts,
      '#default_value' => $defaultIds,
      '#description' => $account_opts
        ? $this->t('Tick the doctors, chemists, or stockists you plan to call on today.')
        : $this->t('No accounts yet — add some via /sales/accounts/add first.'),
      '#prefix' => '<div class="st-field st-field--checkboxes">',
      '#suffix' => '</div>',
    ];
    $form['actions']['#type'] = 'actions';
    $form['actions']['#prefix'] = '<div class="st-form-card__footer">';
    $form['actions']['#suffix'] = '</div>';
    $form['actions']['submit'] = [
      '#type' => 'submit',
      '#value' => $this->t('Save plan'),
      '#attributes' => ['class' => ['st-btn', 'st-btn--primary']],
    ];
    return $form;
  }

  public function validateForm(array &$form, FormStateInterface $form_state) {
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
    // Multi-select checkboxes returns an associative array keyed by id; we
    // want only the truthy values (the ticked ones), as integers.
    $raw_ids = $form_state->getValue('account_ids') ?: [];
    $account_ids = [];
    foreach ($raw_ids as $k => $v) {
      if ($v) {
        $account_ids[] = (int) $k;
      }
    }
    $payload = [
      'place' => $form_state->getValue('place'),
      'lat' => $form_state->getValue('lat') ?: NULL,
      'lon' => $form_state->getValue('lon') ?: NULL,
      'notes' => $form_state->getValue('notes'),
      'account_ids' => $account_ids,
    ];
    $res = $this->api->savePlan($payload);
    if (!empty($res['ok'])) {
      $this->messenger()->addStatus($this->t('Plan saved for today.'));
      $form_state->setRedirect('sales_tracker.dashboard');
    }
    else {
      $this->messenger()->addError($this->t('Could not save plan: @e', ['@e' => $res['error'] ?? 'unknown error']));
    }
  }

}
