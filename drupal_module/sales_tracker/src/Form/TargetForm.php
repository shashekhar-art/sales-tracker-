<?php

namespace Drupal\sales_tracker\Form;

use Drupal\Core\Form\FormBase;
use Drupal\Core\Form\FormStateInterface;
use Drupal\sales_tracker\Service\SalesTrackerApiClient;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Set a sales target — admin only.
 *
 * Targets can be scoped to company / region / district / employee, with an
 * account_type filter and a period_type (daily / weekly / monthly / quarterly).
 */
class TargetForm extends FormBase {

  protected SalesTrackerApiClient $api;

  public static function create(ContainerInterface $container) {
    $instance = new static();
    $instance->api = $container->get('sales_tracker.api_client');
    return $instance;
  }

  public function getFormId() {
    return 'sales_tracker_target_form';
  }

  public function buildForm(array $form, FormStateInterface $form_state) {
    $form['#attached']['library'][] = 'sales_tracker/sales_tracker';
    $form['#prefix'] = '<div class="sales-tracker"><div class="st-card st-card--focal st-form-card">';
    $form['#suffix'] = '</div></div>';

    $regions = $this->api->getRegions()['rows'] ?? [];
    $region_opts = ['' => $this->t('— Any —')];
    foreach ($regions as $r) {
      $region_opts[$r['id']] = $r['name'];
    }

    $form['scope'] = [
      '#type' => 'select',
      '#title' => $this->t('Scope'),
      '#required' => TRUE,
      '#options' => [
        'company' => $this->t('Company-wide'),
        'region' => $this->t('Per region (state)'),
        'district' => $this->t('Per district'),
        'employee' => $this->t('Per employee'),
      ],
      '#default_value' => 'company',
      '#prefix' => '<div class="st-field">',
      '#suffix' => '</div>',
      '#attributes' => ['class' => ['form-select']],
    ];

    $form['account_type'] = [
      '#type' => 'select',
      '#title' => $this->t('Account type'),
      '#required' => TRUE,
      '#options' => [
        'any' => $this->t('Any (all account types)'),
        'doctor' => $this->t('Doctor'),
        'chemist' => $this->t('Chemist'),
        'stockist' => $this->t('Stockist'),
        'retailer' => $this->t('Retailer'),
        'wholesaler' => $this->t('Wholesaler'),
      ],
      '#default_value' => 'any',
      '#prefix' => '<div class="st-field">',
      '#suffix' => '</div>',
      '#attributes' => ['class' => ['form-select']],
    ];

    $form['period_type'] = [
      '#type' => 'select',
      '#title' => $this->t('Period'),
      '#required' => TRUE,
      '#options' => [
        'daily' => $this->t('Daily'),
        'weekly' => $this->t('Weekly'),
        'monthly' => $this->t('Monthly'),
        'quarterly' => $this->t('Quarterly'),
      ],
      '#default_value' => 'monthly',
      '#prefix' => '<div class="st-field">',
      '#suffix' => '</div>',
      '#attributes' => ['class' => ['form-select']],
    ];

    $form['target_count'] = [
      '#type' => 'number',
      '#title' => $this->t('Target count'),
      '#required' => TRUE,
      '#min' => 0,
      '#default_value' => 100,
      '#description' => $this->t('Number of visits expected in one period.'),
      '#prefix' => '<div class="st-field">',
      '#suffix' => '</div>',
      '#attributes' => ['class' => ['form-number']],
    ];

    $form['region_id'] = [
      '#type' => 'select',
      '#title' => $this->t('Region (if scoped)'),
      '#options' => $region_opts,
      '#prefix' => '<div class="st-field">',
      '#suffix' => '</div>',
      '#attributes' => ['class' => ['form-select']],
    ];

    $form['district_id'] = [
      '#type' => 'number',
      '#title' => $this->t('District ID (if scoped)'),
      '#prefix' => '<div class="st-field">',
      '#suffix' => '</div>',
      '#attributes' => ['class' => ['form-number']],
    ];

    $form['employee_id'] = [
      '#type' => 'number',
      '#title' => $this->t('Employee ID (if scoped)'),
      '#prefix' => '<div class="st-field">',
      '#suffix' => '</div>',
      '#attributes' => ['class' => ['form-number']],
    ];

    $form['dates_open'] = [
      '#type' => 'markup',
      '#markup' => '<div class="st-grid-2">',
      '#allowed_tags' => ['div'],
    ];
    $form['effective_from'] = [
      '#type' => 'date',
      '#title' => $this->t('Effective from'),
      '#required' => TRUE,
      '#default_value' => date('Y-m-d'),
      '#prefix' => '<div class="st-field">',
      '#suffix' => '</div>',
    ];
    $form['effective_to'] = [
      '#type' => 'date',
      '#title' => $this->t('Effective to'),
      '#prefix' => '<div class="st-field">',
      '#suffix' => '</div>',
    ];
    $form['dates_close'] = [
      '#type' => 'markup',
      '#markup' => '</div>',
      '#allowed_tags' => ['div'],
    ];

    $form['actions']['#type'] = 'actions';
    $form['actions']['#prefix'] = '<div class="st-form-card__footer">';
    $form['actions']['#suffix'] = '</div>';
    $form['actions']['submit'] = [
      '#type' => 'submit',
      '#value' => $this->t('Save target'),
      '#attributes' => ['class' => ['st-btn', 'st-btn--primary']],
    ];
    return $form;
  }

  public function validateForm(array &$form, FormStateInterface $form_state) {
    $scope = $form_state->getValue('scope');
    if ($scope === 'region' && !$form_state->getValue('region_id')) {
      $form_state->setErrorByName('region_id', $this->t('Region is required for a region-scoped target.'));
    }
    if ($scope === 'district' && !$form_state->getValue('district_id')) {
      $form_state->setErrorByName('district_id', $this->t('District ID is required for a district-scoped target.'));
    }
    if ($scope === 'employee' && !$form_state->getValue('employee_id')) {
      $form_state->setErrorByName('employee_id', $this->t('Employee ID is required for an employee-scoped target.'));
    }
  }

  public function submitForm(array &$form, FormStateInterface $form_state) {
    $payload = [
      'scope' => $form_state->getValue('scope'),
      'account_type' => $form_state->getValue('account_type'),
      'period_type' => $form_state->getValue('period_type'),
      'target_count' => (int) $form_state->getValue('target_count'),
      'region_id' => $form_state->getValue('region_id') ?: NULL,
      'district_id' => $form_state->getValue('district_id') ?: NULL,
      'employee_id' => $form_state->getValue('employee_id') ?: NULL,
      'effective_from' => $form_state->getValue('effective_from'),
      'effective_to' => $form_state->getValue('effective_to') ?: NULL,
    ];
    $res = $this->api->saveTarget($payload);
    if (!empty($res['ok'])) {
      $this->messenger()->addStatus($this->t('Target saved.'));
      $form_state->setRedirect('sales_tracker.admin');
    }
    else {
      $this->messenger()->addError($this->t('Could not save target: @e', [
        '@e' => $res['error'] ?? 'unknown error',
      ]));
    }
  }

}
