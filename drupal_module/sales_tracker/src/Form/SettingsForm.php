<?php

namespace Drupal\sales_tracker\Form;

use Drupal\Core\Form\ConfigFormBase;
use Drupal\Core\Form\FormStateInterface;

/**
 * Configure the Flask API endpoint and shared key.
 */
class SettingsForm extends ConfigFormBase {

  public function getFormId() {
    return 'sales_tracker_settings';
  }

  protected function getEditableConfigNames() {
    return ['sales_tracker.settings'];
  }

  public function buildForm(array $form, FormStateInterface $form_state) {
    $cfg = $this->config('sales_tracker.settings');
    $form['api_url'] = [
      '#type' => 'textfield',
      '#title' => $this->t('Flask API URL'),
      '#default_value' => $cfg->get('api_url') ?: 'http://127.0.0.1:5000',
      '#description' => $this->t('Base URL of the Python backend, e.g. http://127.0.0.1:5000'),
      '#required' => TRUE,
    ];
    $form['api_key'] = [
      '#type' => 'textfield',
      '#title' => $this->t('Shared API key'),
      '#default_value' => $cfg->get('api_key'),
      '#description' => $this->t('Must match API_KEY in the Flask .env file.'),
      '#required' => TRUE,
    ];
    return parent::buildForm($form, $form_state);
  }

  public function submitForm(array &$form, FormStateInterface $form_state) {
    $this->config('sales_tracker.settings')
      ->set('api_url', rtrim($form_state->getValue('api_url'), '/'))
      ->set('api_key', $form_state->getValue('api_key'))
      ->save();
    parent::submitForm($form, $form_state);
  }

}
