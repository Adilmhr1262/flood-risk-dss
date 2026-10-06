import '../../../core/api_client.dart';
import '../../../core/app_error.dart';
import '../../../core/cache_service.dart';

/// Risk data for the home dashboard and risk assessment screens.
class RiskRepository {
  RiskRepository({required ApiClient api, required CacheService cache})
      : _api = api,
        _cache = cache;

  final ApiClient _api;
  final CacheService _cache;

  /// Latest stored assessment for a district (or GPS-matched district).
  /// Falls back to the offline cache when the network fails.
  Future<({Map<String, dynamic> risk, bool offline})> myRisk({
    String? districtName,
    double? lat,
    double? lon,
  }) async {
    final query = <String, dynamic>{};
    if (districtName != null) query['district_name'] = districtName;
    if (lat != null && lon != null) {
      query['lat'] = lat;
      query['lon'] = lon;
    }
    try {
      final data = await _api.get('/mobile/my-risk', query: query)
          as Map<String, dynamic>;
      await _cache.saveRisk(data);
      return (risk: data, offline: false);
    } on NetworkException {
      final cached = await _cache.readRisk();
      if (cached != null) return (risk: cached, offline: true);
      rethrow;
    }
  }

  /// Fresh on-demand assessment via the prediction service.
  Future<Map<String, dynamic>> assess(Map<String, dynamic> input,
      {String model = 'mlp-v1'}) async {
    final data = await _api.post('/risk/predict?model=$model', data: input)
        as Map<String, dynamic>;
    return data;
  }

  /// District list for the dropdown (cached offline).
  Future<List<Map<String, dynamic>>> districts() async {
    try {
      final data = await _api.get('/gis/districts') as Map<String, dynamic>;
      final features = (data['features'] as List).cast<Map<String, dynamic>>();
      final districts = features
          .map((f) => (f['properties'] as Map).cast<String, dynamic>())
          .toList();
      await _cache.saveDistricts(districts);
      return districts;
    } on NetworkException {
      final cached = await _cache.readDistricts();
      return cached.cast<Map<String, dynamic>>();
    }
  }
}
