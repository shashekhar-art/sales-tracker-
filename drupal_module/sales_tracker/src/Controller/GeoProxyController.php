<?php

namespace Drupal\sales_tracker\Controller;

use Drupal\Core\Controller\ControllerBase;
use Drupal\sales_tracker\Service\SalesTrackerApiClient;
use Symfony\Component\DependencyInjection\ContainerInterface;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;

/**
 * Same-origin proxy for Flask's /api/reverse_geocode endpoint.
 *
 * The browser fetches /sales/api/reverse_geocode?lat=&lon=, this controller
 * forwards through the SalesTrackerApiClient (which adds the X-API-Key header),
 * and the JSON response is relayed back. This avoids CORS issues that would
 * arise from calling Flask directly across origins.
 */
class GeoProxyController extends ControllerBase {

  protected SalesTrackerApiClient $api;

  public static function create(ContainerInterface $container) {
    $instance = new static();
    $instance->api = $container->get('sales_tracker.api_client');
    return $instance;
  }

  public function reverseGeocode(Request $request) {
    $lat = $request->query->get('lat');
    $lon = $request->query->get('lon');
    if (!is_numeric($lat) || !is_numeric($lon)) {
      return new JsonResponse(['ok' => FALSE, 'error' => 'lat/lon required'], 400);
    }
    $latF = (float) $lat;
    $lonF = (float) $lon;
    if ($latF < -90 || $latF > 90 || $lonF < -180 || $lonF > 180) {
      return new JsonResponse(['ok' => FALSE, 'error' => 'lat/lon out of range'], 400);
    }
    $res = $this->api->reverseGeocode($latF, $lonF);
    return new JsonResponse($res ?: ['ok' => FALSE, 'error' => 'upstream failure']);
  }

}
