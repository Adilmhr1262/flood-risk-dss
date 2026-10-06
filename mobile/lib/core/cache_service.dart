import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

/// Offline cache for the last-known risk, alerts, shelters, contacts and
/// district list. Each entry stores a JSON payload plus a timestamp; entries
/// older than [AppConfig.cacheTtl] are treated as stale but are still
/// returned so the app can show something useful offline.
class CacheService {
  CacheService({SharedPreferences? prefs}) : _prefs = prefs;

  final SharedPreferences? _prefs;

  static const _kRisk = 'cache.risk';
  static const _kAlerts = 'cache.alerts';
  static const _kShelters = 'cache.shelters';
  static const _kContacts = 'cache.contacts';
  static const _kDistricts = 'cache.districts';
  static const _kTsSuffix = '.ts';

  Future<SharedPreferences> get _store async =>
      _prefs ?? await SharedPreferences.getInstance();

  Future<void> _write(String key, Object value) async {
    final store = await _store;
    await store.setString(key, jsonEncode(value));
    await store.setInt('$key$_kTsSuffix', DateTime.now().millisecondsSinceEpoch);
  }

  Future<Map<String, dynamic>?> _read(String key) async {
    final store = await _store;
    final raw = store.getString(key);
    if (raw == null) return null;
    return jsonDecode(raw) as Map<String, dynamic>;
  }

  Future<void> saveRisk(Map<String, dynamic> risk) => _write(_kRisk, risk);
  Future<Map<String, dynamic>?> readRisk() => _read(_kRisk);

  Future<void> saveAlerts(List<dynamic> alerts) => _write(_kAlerts, {'items': alerts});
  Future<List<dynamic>> readAlerts() async {
    final data = await _read(_kAlerts);
    return (data?['items'] as List<dynamic>?) ?? [];
  }

  Future<void> saveShelters(List<dynamic> shelters) => _write(_kShelters, {'items': shelters});
  Future<List<dynamic>> readShelters() async {
    final data = await _read(_kShelters);
    return (data?['items'] as List<dynamic>?) ?? [];
  }

  Future<void> saveContacts(List<dynamic> contacts) => _write(_kContacts, {'items': contacts});
  Future<List<dynamic>> readContacts() async {
    final data = await _read(_kContacts);
    return (data?['items'] as List<dynamic>?) ?? [];
  }

  Future<void> saveDistricts(List<dynamic> districts) =>
      _write(_kDistricts, {'items': districts});
  Future<List<dynamic>> readDistricts() async {
    final data = await _read(_kDistricts);
    return (data?['items'] as List<dynamic>?) ?? [];
  }
}
