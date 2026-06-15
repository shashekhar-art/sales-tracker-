<?php

namespace Drupal\sales_tracker\Controller;

use Drupal\Core\Controller\ControllerBase;
use Drupal\Core\Url;
use Drupal\sales_tracker\Service\SalesTrackerApiClient;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Employee dashboard + history pages.
 */
class DashboardController extends ControllerBase {

  protected SalesTrackerApiClient $api;

  public static function create(ContainerInterface $container) {
    $instance = new static();
    $instance->api = $container->get('sales_tracker.api_client');
    return $instance;
  }

  public function view() {
    $planRes = $this->api->getPlanToday();
    $plan = $planRes['plan'] ?? NULL;
    // The plan endpoint now also returns "items" — the list of accounts
    // planned for today. Older v1 servers omit it; default to [].
    $planned_items = $planRes['items'] ?? ($plan['items'] ?? []);
    $history = $this->api->history(10)['rows'] ?? [];

    // Today's visit-type counts + period rollups.
    $today_visits_res = $this->api->todayVisits();
    $today_visits = $today_visits_res['rows'] ?? [];
    // /api/visits/today only returns rows — derive the counts in PHP so the
    // 'Visits today / Doctors / Chemists / Stockists' tiles show real values.
    if (isset($today_visits_res['counts']) && is_array($today_visits_res['counts'])) {
      $today_counts = $today_visits_res['counts'];
    }
    else {
      $today_counts = [
        'doctor' => 0,
        'chemist' => 0,
        'stockist' => 0,
        'total' => 0,
      ];
      foreach ($today_visits as $v) {
        $t = $v['account_type'] ?? '';
        if (isset($today_counts[$t])) {
          $today_counts[$t]++;
          $today_counts['total']++;
        }
      }
    }

    // Period stats — 4 buckets so the dashboard period-tabs work without ajax.
    $stats = [
      'day' => $this->api->getStats('day'),
      'week' => $this->api->getStats('week'),
      'month' => $this->api->getStats('month'),
      'quarter' => $this->api->getStats('quarter'),
    ];

    return [
      '#theme' => 'sales_tracker_dashboard',
      '#plan' => $plan,
      '#planned_items' => $planned_items,
      '#history' => $history,
      '#flags' => [],
      '#today_visits' => $today_visits,
      '#today_counts' => $today_counts,
      '#stats' => $stats,
      '#attached' => ['library' => ['sales_tracker/sales_tracker']],
      '#cache' => ['max-age' => 0],
      'links' => [
        '#type' => 'markup',
        '#markup' => '<p>'
          . '<a href="' . Url::fromRoute('sales_tracker.plan')->toString() . '">Edit plan</a> · '
          . '<a href="' . Url::fromRoute('sales_tracker.checkin')->toString() . '">Check in</a> · '
          . '<a href="' . Url::fromRoute('sales_tracker.visit')->toString() . '">Log visit</a> · '
          . '<a href="' . Url::fromRoute('sales_tracker.history')->toString() . '">Full history</a>'
          . '</p>',
      ],
    ];
  }

  public function history() {
    $rows = $this->api->history(200)['rows'] ?? [];
    return [
      '#theme' => 'sales_tracker_history',
      '#rows' => $rows,
      '#attached' => ['library' => ['sales_tracker/sales_tracker']],
      '#cache' => ['max-age' => 0],
    ];
  }

}
