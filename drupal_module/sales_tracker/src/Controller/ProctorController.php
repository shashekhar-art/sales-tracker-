<?php

namespace Drupal\sales_tracker\Controller;

use Drupal\Core\Controller\ControllerBase;
use Drupal\sales_tracker\Service\SalesTrackerApiClient;
use Symfony\Component\DependencyInjection\ContainerInterface;

/**
 * Proctor (national rollup) pages.
 * 4-level drill-down: India -> Region (state) -> District -> Employee.
 */
class ProctorController extends ControllerBase {

  protected SalesTrackerApiClient $api;

  public static function create(ContainerInterface $container) {
    $instance = new static();
    $instance->api = $container->get('sales_tracker.api_client');
    return $instance;
  }

  /**
   * /sales/proctor — India rollup: one card per state/UT.
   */
  public function india() {
    $data = $this->api->proctorIndia();
    return [
      '#theme' => 'sales_tracker_proctor',
      '#regions' => $data['regions'] ?? [],
      '#totals' => $data['totals'] ?? [],
      '#attached' => ['library' => ['sales_tracker/sales_tracker']],
      '#cache' => ['max-age' => 0],
    ];
  }

  /**
   * /sales/proctor/region/{rid} — per-district rollup for a single state.
   */
  public function region(int $rid) {
    $data = $this->api->proctorRegion($rid);
    return [
      '#theme' => 'sales_tracker_proctor_region',
      '#region' => $data['region'] ?? NULL,
      '#districts' => $data['districts'] ?? [],
      '#totals' => $data['totals'] ?? [],
      '#attached' => ['library' => ['sales_tracker/sales_tracker']],
      '#cache' => ['max-age' => 0],
    ];
  }

  /**
   * /sales/proctor/district/{did} — per-employee rollup for a single district.
   */
  public function district(int $did) {
    $data = $this->api->proctorDistrict($did);
    return [
      '#theme' => 'sales_tracker_proctor_district',
      '#district' => $data['district'] ?? NULL,
      '#region' => $data['region'] ?? NULL,
      '#employees' => $data['employees'] ?? [],
      '#totals' => $data['totals'] ?? [],
      '#attached' => ['library' => ['sales_tracker/sales_tracker']],
      '#cache' => ['max-age' => 0],
    ];
  }

  /**
   * /sales/proctor/employee/{eid} — single employee detail page.
   */
  public function employee(int $eid) {
    $data = $this->api->proctorEmployee($eid);
    return [
      '#theme' => 'sales_tracker_proctor_employee',
      '#employee' => $data['employee'] ?? NULL,
      '#stats' => $data['stats'] ?? [],
      '#recent' => $data['recent'] ?? [],
      '#flags' => $data['flags'] ?? [],
      '#attached' => ['library' => ['sales_tracker/sales_tracker']],
      '#cache' => ['max-age' => 0],
    ];
  }

}
