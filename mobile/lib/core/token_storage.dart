import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Secure on-device storage for the JWT access/refresh token pair and the
/// signed-in user's profile snapshot.
class TokenStorage {
  TokenStorage({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  final FlutterSecureStorage _storage;

  static const _kAccess = 'frdss.access_token';
  static const _kRefresh = 'frdss.refresh_token';
  static const _kRole = 'frdss.role';
  static const _kName = 'frdss.name';
  static const _kEmail = 'frdss.email';

  Future<void> saveSession({
    required String accessToken,
    required String refreshToken,
    required String role,
    required String name,
    required String email,
  }) async {
    await Future.wait([
      _storage.write(key: _kAccess, value: accessToken),
      _storage.write(key: _kRefresh, value: refreshToken),
      _storage.write(key: _kRole, value: role),
      _storage.write(key: _kName, value: name),
      _storage.write(key: _kEmail, value: email),
    ]);
  }

  Future<String?> readAccessToken() => _storage.read(key: _kAccess);
  Future<String?> readRefreshToken() => _storage.read(key: _kRefresh);
  Future<String?> readRole() => _storage.read(key: _kRole);
  Future<String?> readName() => _storage.read(key: _kName);
  Future<String?> readEmail() => _storage.read(key: _kEmail);

  Future<bool> hasSession() async => await readAccessToken() != null;

  Future<void> updateAccessToken(String accessToken, String refreshToken) async {
    await Future.wait([
      _storage.write(key: _kAccess, value: accessToken),
      _storage.write(key: _kRefresh, value: refreshToken),
    ]);
  }

  Future<void> clear() => _storage.deleteAll();
}
