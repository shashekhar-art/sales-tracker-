<?php

namespace Drupal\sales_tracker\Controller;

use Drupal\Core\Controller\ControllerBase;
use Drupal\Core\Url;
use Drupal\sales_tracker\Service\SalesTrackerApiClient;
use Symfony\Component\DependencyInjection\ContainerInterface;
use Symfony\Component\HttpFoundation\RedirectResponse;
use Symfony\Component\HttpFoundation\RequestStack;

/**
 * Accounts directory pages (doctor / chemist / stockist).
 */
class AccountsController extends ControllerBase {

  protected SalesTrackerApiClient $api;
  protected RequestStack $requestStack;

  public static function create(ContainerInterface $container) {
    $instance = new static();
    $instance->api = $container->get('sales_tracker.api_client');
    $instance->requestStack = $container->get('request_stack');
    return $instance;
  }

  /**
   * /sales/accounts — searchable, filterable list.
   */
  public function listPage() {
    $request = $this->requestStack->getCurrentRequest();
    $filters = [
      'q' => trim((string) $request->query->get('q', '')),
      'type' => $request->query->get('type', ''),
      'district_id' => $request->query->get('district_id', ''),
      'region_id' => $request->query->get('region_id', ''),
    ];
    $res = $this->api->listAccounts($filters);
    $accounts = $res['rows'] ?? [];

    return [
      '#theme' => 'sales_tracker_accounts',
      '#accounts' => $accounts,
      '#filters' => $filters,
      '#attached' => ['library' => ['sales_tracker/sales_tracker']],
      '#cache' => ['max-age' => 0],
    ];
  }

  /**
   * /sales/accounts/{id} — single account detail with visit history.
   */
  public function viewPage(int $id) {
    $res = $this->api->getAccount($id);
    $account = $res['account'] ?? NULL;
    if (!$account) {
      $this->messenger()->addError($this->t('Account #@id not found.', ['@id' => $id]));
      return new RedirectResponse(Url::fromRoute('sales_tracker.accounts')->toString());
    }
    $visits = $res['visits'] ?? [];
    return [
      '#theme' => 'sales_tracker_account_detail',
      '#account' => $account,
      '#visits' => $visits,
      '#attached' => ['library' => ['sales_tracker/sales_tracker']],
      '#cache' => ['max-age' => 0],
    ];
  }

  /**
   * /sales/accounts/{id}/delete — POST-only delete, redirects back to list.
   */
  public function deletePage(int $id) {
    $res = $this->api->deleteAccount($id);
    if (!empty($res['ok'])) {
      $this->messenger()->addStatus($this->t('Account deleted.'));
    }
    else {
      $this->messenger()->addError($this->t('Could not delete account: @e', [
        '@e' => $res['error'] ?? 'unknown error',
      ]));
    }
    return new RedirectResponse(Url::fromRoute('sales_tracker.accounts')->toString());
  }

}
