import '../../../core/api_client.dart';
import '../../../core/app_error.dart';
import '../../../core/cache_service.dart';

/// Alert inbox for the mobile app.
class AlertsRepository {
  AlertsRepository({required ApiClient api, required CacheService cache})
      : _api = api,
        _cache = cache;

  final ApiClient _api;
  final CacheService _cache;

  Future<({List<Map<String, dynamic>> alerts, bool offline})> activeAlerts() async {
    try {
      final data = await _api.get('/mobile/alerts') as List;
      final alerts = data.cast<Map<String, dynamic>>();
      await _cache.saveAlerts(alerts);
      return (alerts: alerts, offline: false);
    } on NetworkException {
      final cached = await _cache.readAlerts();
      return (alerts: cached.cast<Map<String, dynamic>>(), offline: true);
    }
  }
}
