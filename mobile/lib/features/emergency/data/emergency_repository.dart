import '../../../core/api_client.dart';
import '../../../core/app_error.dart';
import '../../../core/cache_service.dart';

/// Emergency resources: nearby shelters, contacts, hospitals, reporting.
class EmergencyRepository {
  EmergencyRepository({required ApiClient api, required CacheService cache})
      : _api = api,
        _cache = cache;

  final ApiClient _api;
  final CacheService _cache;

  Future<({List<Map<String, dynamic>> shelters, bool offline})> nearbyShelters(
      double lat, double lon,
      {double radiusKm = 50}) async {
    try {
      final data = await _api.get('/mobile/shelters/nearby', query: {
        'lat': lat,
        'lon': lon,
        'radius_km': radiusKm,
      }) as List;
      final shelters = data.cast<Map<String, dynamic>>();
      await _cache.saveShelters(shelters);
      return (shelters: shelters, offline: false);
    } on NetworkException {
      final cached = await _cache.readShelters();
      return (shelters: cached.cast<Map<String, dynamic>>(), offline: true);
    }
  }

  Future<({List<Map<String, dynamic>> contacts, bool offline})> contacts(
      {String? districtName}) async {
    try {
      final data = await _api.get('/mobile/emergency-contacts',
          query: districtName != null ? {'district_name': districtName} : null) as List;
      final contacts = data.cast<Map<String, dynamic>>();
      await _cache.saveContacts(contacts);
      return (contacts: contacts, offline: false);
    } on NetworkException {
      final cached = await _cache.readContacts();
      return (contacts: cached.cast<Map<String, dynamic>>(), offline: true);
    }
  }

  Future<Map<String, dynamic>> infrastructure({String? type}) async {
    final data = await _api.get('/gis/infrastructure',
        query: type != null ? {'type': type} : null) as Map<String, dynamic>;
    return data;
  }

  Future<Map<String, dynamic>> reportEvent({
    required String districtName,
    required double lat,
    required double lon,
    required int severity,
    String? description,
  }) async {
    final data = await _api.post('/mobile/report-event', data: {
      'district_name': districtName,
      'lat': lat,
      'lon': lon,
      'severity': severity,
      if (description != null && description.isNotEmpty) 'description': description,
    }) as Map<String, dynamic>;
    return data;
  }
}
