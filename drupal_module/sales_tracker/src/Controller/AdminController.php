<?php

namespace Drupal\sales_tracker\Controller;

use Drupal\Core\Controller\ControllerBase;
use Drupal\sales_tracker\Service\SalesTrackerApiClient;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Admin dashboard: today's status + anomaly flags.
 */
class AdminController extends ControllerBase {

  protected SalesTrackerApiClient $api;

  public static function create(ContainerInterface $container) {
    $instance = new static();
    $instance->api = $container->get('sales_tracker.api_client');
    return $instance;
  }

  public function view() {
    $summary = $this->api->adminSummary()['rows'] ?? [];
    $flags = $this->api->adminFlags()['rows'] ?? [];

    return [
      '#theme' => 'sales_tracker_admin',
      '#summary' => $summary,
      '#flags' => $flags,
      '#attached' => ['library' => ['sales_tracker/sales_tracker']],
      '#cache' => ['max-age' => 0],
    ];
  }

}
