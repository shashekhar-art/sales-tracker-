<?php

namespace Drupal\sales_tracker\Controller;

use Drupal\Core\Controller\ControllerBase;
use Drupal\sales_tracker\Service\SalesTrackerApiClient;
use Symfony\Component\DependencyInjection\ContainerInterface;
use Symfony\Component\HttpFoundation\RequestStack;

/**
 * Visits history page (per-employee log of logged customer visits).
 */
class VisitsController extends ControllerBase {

  protected SalesTrackerApiClient $api;
  protected RequestStack $requestStack;

  public static function create(ContainerInterface $container) {
    $instance = new static();
    $instance->api = $container->get('sales_tracker.api_client');
    $instance->requestStack = $container->get('request_stack');
    return $instance;
  }

  /**
   * /sales/visits/history — list of logged visits, filterable.
   */
  public function history() {
    $request = $this->requestStack->getCurrentRequest();
    $filters = [
      'from' => $request->query->get('from', ''),
      'to' => $request->query->get('to', ''),
      'outcome' => $request->query->get('outcome', ''),
      'account_id' => $request->query->get('account_id', ''),
      'limit' => 100,
    ];
    $res = $this->api->listVisits($filters);
    $visits = $res['rows'] ?? [];

    $apiUrl = rtrim(\Drupal::config('sales_tracker.settings')->get('api_url') ?: 'http://127.0.0.1:5000', '/');
    return [
      '#theme' => 'sales_tracker_visits_history',
      '#visits' => $visits,
      '#filters' => $filters,
      '#flask_static_base' => $apiUrl . '/static/',
      '#attached' => ['library' => ['sales_tracker/sales_tracker']],
      '#cache' => ['max-age' => 0],
    ];
  }

}
