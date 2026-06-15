<?php

namespace Drupal\sales_tracker\Service;

use Drupal\Core\Config\ConfigFactoryInterface;
use Drupal\Core\Logger\LoggerChannelFactoryInterface;
use Drupal\Core\Session\AccountInterface;
use GuzzleHttp\ClientInterface;
use GuzzleHttp\Exception\RequestException;

/**
 * Thin wrapper around the Python Flask /api/* endpoints.
 *
 * Sends shared-secret + current Drupal user identity headers on every call.
 */
class SalesTrackerApiClient {

  protected ClientInterface $http;
  protected ConfigFactoryInterface $configFactory;
  protected AccountInterface $currentUser;
  protected LoggerChannelFactoryInterface $loggerFactory;

  public function __construct(
    ClientInterface $http,
    ConfigFactoryInterface $configFactory,
    AccountInterface $currentUser,
    LoggerChannelFactoryInterface $loggerFactory
  ) {
    $this->http = $http;
    $this->configFactory = $configFactory;
    $this->currentUser = $currentUser;
    $this->loggerFactory = $loggerFactory;
  }

  protected function baseUrl(): string {
    return rtrim($this->configFactory->get('sales_tracker.settings')->get('api_url') ?: 'http://127.0.0.1:5000', '/');
  }

  protected function headers(): array {
    $cfg = $this->configFactory->get('sales_tracker.settings');
    // Promote proctor users so Flask's require_proctor_or_admin lets them through.
    if ($this->currentUser->hasPermission('administer sales tracker')) {
      $role = 'admin';
    }
    elseif ($this->currentUser->hasPermission('view sales tracker proctor')) {
      $role = 'proctor';
    }
    else {
      $role = 'employee';
    }
    return [
      'X-API-Key' => $cfg->get('api_key') ?: '',
      'X-Employee-Email' => $this->currentUser->getEmail() ?: '',
      'X-Employee-Name' => $this->currentUser->getDisplayName() ?: '',
      'X-Employee-Role' => $role,
      'Accept' => 'application/json',
    ];
  }

  protected function request(string $method, string $path, array $options = []): array {
    $options['headers'] = ($options['headers'] ?? []) + $this->headers();
    $options['http_errors'] = FALSE;
    $options['timeout'] = 10;
    try {
      $response = $this->http->request($method, $this->baseUrl() . $path, $options);
      $body = (string) $response->getBody();
      $data = json_decode($body, TRUE) ?: [];
      if ($response->getStatusCode() >= 400) {
        $this->loggerFactory->get('sales_tracker')->error('API @method @path failed (@code): @msg', [
          '@method' => $method,
          '@path' => $path,
          '@code' => $response->getStatusCode(),
          '@msg' => $data['error'] ?? $body,
        ]);
      }
      return $data;
    }
    catch (RequestException $e) {
      $this->loggerFactory->get('sales_tracker')->error('API call to @path threw: @msg', [
        '@path' => $path,
        '@msg' => $e->getMessage(),
      ]);
      return ['ok' => FALSE, 'error' => 'Cannot reach Sales Tracker API: ' . $e->getMessage()];
    }
  }

  public function getPlanToday(): array {
    return $this->request('GET', '/api/plan/today');
  }

  public function savePlan(array $data): array {
    return $this->request('POST', '/api/plan', ['json' => $data]);
  }

  public function checkin(array $data): array {
    return $this->request('POST', '/api/checkin', ['json' => $data]);
  }

  public function history(int $limit = 50): array {
    return $this->request('GET', '/api/history?limit=' . $limit);
  }

  public function adminSummary(): array {
    return $this->request('GET', '/api/admin/summary');
  }

  public function adminFlags(): array {
    return $this->request('GET', '/api/admin/flags');
  }

  // ---------------------------------------------------------------------
  // v2 — Accounts (doctor / chemist / stockist directory)
  // ---------------------------------------------------------------------

  /**
   * List accounts. $filters may contain: q, type, district_id, region_id, limit.
   */
  public function listAccounts(array $filters = []): array {
    $qs = http_build_query(array_filter($filters, function ($v) {
      return $v !== NULL && $v !== '';
    }));
    return $this->request('GET', '/api/accounts' . ($qs ? '?' . $qs : ''));
  }

  public function getAccount(int $id): array {
    return $this->request('GET', '/api/accounts/' . $id);
  }

  public function createAccount(array $data): array {
    return $this->request('POST', '/api/accounts', ['json' => $data]);
  }

  public function updateAccount(int $id, array $data): array {
    return $this->request('PUT', '/api/accounts/' . $id, ['json' => $data]);
  }

  public function deleteAccount(int $id): array {
    return $this->request('DELETE', '/api/accounts/' . $id);
  }

  // ---------------------------------------------------------------------
  // v2 — Visits (a checkin tied to an account, with outcome)
  // ---------------------------------------------------------------------

  /**
   * Log a visit. $data: account_id, source, lat, lon, actual_place_name,
   * outcome, visit_notes.
   */
  public function logVisit(array $data): array {
    return $this->request('POST', '/api/visits', ['json' => $data]);
  }

  /**
   * List historical visits. $filters: from, to, account_id, outcome, limit.
   */
  public function listVisits(array $filters = []): array {
    $qs = http_build_query(array_filter($filters, function ($v) {
      return $v !== NULL && $v !== '';
    }));
    return $this->request('GET', '/api/visits' . ($qs ? '?' . $qs : ''));
  }

  public function todayVisits(): array {
    return $this->request('GET', '/api/visits/today');
  }

  // ---------------------------------------------------------------------
  // v2 — Geography (regions = states/UTs, districts under each)
  // ---------------------------------------------------------------------

  public function getRegions(): array {
    return $this->request('GET', '/api/regions');
  }

  public function getDistricts(int $regionId): array {
    return $this->request('GET', '/api/regions/' . $regionId . '/districts');
  }

  // ---------------------------------------------------------------------
  // v2 — Stats (period roll-ups for the dashboard / reports)
  // ---------------------------------------------------------------------

  /**
   * Period stats for the current employee. $period: day | week | month | quarter.
   */
  public function getStats(string $period = 'day'): array {
    return $this->request('GET', '/api/stats?period=' . urlencode($period));
  }

  // ---------------------------------------------------------------------
  // v2 — Proctor (national rollup for the proctor role)
  // ---------------------------------------------------------------------

  public function proctorIndia(): array {
    return $this->request('GET', '/api/proctor/india');
  }

  public function proctorRegion(int $rid): array {
    return $this->request('GET', '/api/proctor/region/' . $rid);
  }

  public function proctorDistrict(int $did): array {
    return $this->request('GET', '/api/proctor/district/' . $did);
  }

  public function proctorEmployee(int $eid): array {
    return $this->request('GET', '/api/proctor/employee/' . $eid);
  }

  // ---------------------------------------------------------------------
  // v2 — Targets
  // ---------------------------------------------------------------------

  public function saveTarget(array $data): array {
    return $this->request('POST', '/api/targets', ['json' => $data]);
  }

  public function listTargets(array $filters = []): array {
    $qs = http_build_query(array_filter($filters, function ($v) {
      return $v !== NULL && $v !== '';
    }));
    return $this->request('GET', '/api/targets' . ($qs ? '?' . $qs : ''));
  }

  // ---------------------------------------------------------------------
  // v2 — CSV export
  // ---------------------------------------------------------------------

  /**
   * Build the URL the browser should hit for a CSV download.
   * We don't proxy the bytes through Drupal — the user follows a link
   * that hits Flask directly (Flask streams the CSV with the same auth
   * headers, which the browser cannot supply, so the controller exposes
   * a Drupal-side passthrough endpoint that adds them).
   *
   * Returns the raw CSV string under ['csv'] for in-PHP use.
   *
   * @param string $type "visits" | "accounts" | "anomalies"
   * @param array  $params query params (from, to, region_id, district_id ...)
   */
  public function downloadCsv(string $type, array $params = []): array {
    $params['type'] = $type;
    $qs = http_build_query(array_filter($params, fn($v) => $v !== NULL && $v !== ''));
    $path = '/api/reports/csv' . ($qs ? '?' . $qs : '');
    // We need the raw text, not a parsed JSON envelope.
    $options = ['headers' => $this->headers(), 'http_errors' => FALSE, 'timeout' => 30];
    try {
      $response = $this->http->request('GET', $this->baseUrl() . $path, $options);
      $body = (string) $response->getBody();
      if ($response->getStatusCode() >= 400) {
        return ['ok' => FALSE, 'error' => 'CSV export failed (' . $response->getStatusCode() . ')'];
      }
      return ['ok' => TRUE, 'csv' => $body];
    }
    catch (RequestException $e) {
      $this->loggerFactory->get('sales_tracker')->error('CSV export @path failed: @msg', [
        '@path' => $path,
        '@msg' => $e->getMessage(),
      ]);
      return ['ok' => FALSE, 'error' => $e->getMessage()];
    }
  }

}
