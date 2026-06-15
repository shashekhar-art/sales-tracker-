<?php

namespace Drupal\sales_tracker\Controller;

use Drupal\Core\Controller\ControllerBase;
use Drupal\sales_tracker\Service\SalesTrackerApiClient;
use Symfony\Component\DependencyInjection\ContainerInterface;
use Symfony\Component\HttpFoundation\RequestStack;
use Symfony\Component\HttpFoundation\Response;

/**
 * Reports page — period stats + chart.
 */
class ReportsController extends ControllerBase {

  protected SalesTrackerApiClient $api;
  protected RequestStack $requestStack;

  public static function create(ContainerInterface $container) {
    $instance = new static();
    $instance->api = $container->get('sales_tracker.api_client');
    $instance->requestStack = $container->get('request_stack');
    return $instance;
  }

  /**
   * /sales/reports — period tabs (day/week/month/quarter) + charts.
   */
  public function view() {
    $request = $this->requestStack->getCurrentRequest();
    $period = $request->query->get('period', 'week');
    if (!in_array($period, ['day', 'week', 'month', 'quarter'], TRUE)) {
      $period = 'week';
    }
    $stats = $this->api->getStats($period);
    return [
      '#theme' => 'sales_tracker_reports',
      '#period' => $period,
      '#stats' => $stats,
      '#attached' => ['library' => ['sales_tracker/sales_tracker']],
      '#cache' => ['max-age' => 0],
    ];
  }

  /**
   * /sales/reports/csv — Drupal-side passthrough for CSV downloads.
   * Adds the X-API-Key + X-Employee-* headers so the browser doesn't need them.
   */
  public function csv(string $type) {
    $request = $this->requestStack->getCurrentRequest();
    $params = $request->query->all();
    unset($params['type']);
    $res = $this->api->downloadCsv($type, $params);
    if (empty($res['ok'])) {
      return new Response('CSV export failed: ' . ($res['error'] ?? ''), 500);
    }
    $filename = 'sales-tracker-' . $type . '-' . date('Ymd-His') . '.csv';
    $response = new Response($res['csv'], 200, [
      'Content-Type' => 'text/csv; charset=utf-8',
      'Content-Disposition' => 'attachment; filename="' . $filename . '"',
    ]);
    return $response;
  }

}
